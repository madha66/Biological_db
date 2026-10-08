"""External-data disease and transcript analysis service."""
from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import httpx

from app.api.models import (
    CrossValidationTheme,
    DiseaseAnalysisRequest,
    DiseaseAnalysisResult,
    DiseaseAnalysisSummary,
    DiseaseAssociation,
    DiseaseCluster,
    DiseaseNetworkEdge,
    DiseasePathway,
    GOAnnotation,
    ReactomePathway,
    TranscriptInfo,
)
from app.interactions.string_client import fetch_protein_interactions
from app.kegg.client import (
    KEGG_BASE,
    _polite_get,
    fetch_gene_pathways,
    resolve_gene_identifiers,
)
from app.network.analysis import (
    build_integrated_network,
    cluster_network,
    shared_unique_associations,
)
from app.rna.services import (
    build_input_resolutions,
    detect_rna_type,
    fetch_lncrna_relationships,
    fetch_mirna_relationships,
)

logger = logging.getLogger(__name__)

REACTOME_BASE = "https://reactome.org/AnalysisService"
QUICKGO_BASE = "https://www.ebi.ac.uk/QuickGO/services"


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str:
    try:
        response = await client.get(url, timeout=20.0)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as exc:
        logger.warning("External request failed for %s: %s", url, exc)
        return ""


def _parse_kegg_table(raw: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in raw.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            values[parts[0].replace("ds:", "").replace("path:", "").strip()] = parts[1].strip()
    return values


async def _kegg_diseases(
    inputs: Dict[str, str],
    org: str,
    disease_query: str | None,
    client: httpx.AsyncClient,
) -> Tuple[List[DiseaseAssociation], Dict[str, str], List[str]]:
    warnings: List[str] = []
    disease_raw = await _polite_get(f"{KEGG_BASE}/list/disease", client)
    disease_names = _parse_kegg_table(disease_raw)
    query = disease_query.lower().strip() if disease_query else ""
    if query:
        disease_names = {key: value for key, value in disease_names.items() if query in value.lower() or query in key.lower()}

    associations: List[DiseaseAssociation] = []
    for gene, kegg_entry in inputs.items():
        raw = await _polite_get(f"{KEGG_BASE}/link/disease/{kegg_entry}", client)
        disease_ids = [
            value.replace("ds:", "").replace("disease:", "").strip()
            for line in raw.splitlines()
            for value in (line.split("\t", 1)[1:] or [])
            if value.strip()
        ]
        for disease_id in dict.fromkeys(disease_ids):
            name = disease_names.get(disease_id)
            if name:
                associations.append(DiseaseAssociation(
                    input_name=gene,
                    disease_id=disease_id,
                    disease_name=name,
                    source_db="KEGG Disease",
                ))
    if not disease_raw and inputs:
        warnings.append("KEGG Disease was unavailable; no disease associations were returned.")
    return associations, disease_names, warnings


async def _ensembl_transcripts(
    inputs: List[str],
    client: httpx.AsyncClient,
) -> Tuple[List[TranscriptInfo], List[str]]:
    transcripts: List[TranscriptInfo] = []
    warnings: List[str] = []
    for gene in inputs:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async def get_json(url: str) -> tuple[dict | None, str | None]:
            last_error: str | None = None
            retryable_statuses = {500, 502, 503, 504}
            for attempt in range(4):
                try:
                    response = await client.get(url, headers=headers, timeout=30.0)
                    response.raise_for_status()
                    payload = response.json()
                    if not isinstance(payload, dict):
                        return None, "invalid JSON object"
                    return payload, None
                except httpx.TimeoutException:
                    last_error = "request timed out"
                except httpx.HTTPStatusError as exc:
                    last_error = f"HTTP {exc.response.status_code}"
                    if exc.response.status_code not in retryable_statuses or attempt == 3:
                        break
                except (httpx.HTTPError, ValueError) as exc:
                    last_error = str(exc)
                    break
                if attempt < 3:
                    await asyncio.sleep(0.5 * (2 ** attempt))
            return None, last_error

        symbol_payload, error = await get_json(
            f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{gene}"
        )
        if symbol_payload is None:
            logger.warning("Ensembl lookup failed for %s: %s", gene, error)
            warnings.append(f"Ensembl transcript lookup failed for {gene} ({error}).")
            continue
        gene_id = symbol_payload.get("id")
        if not isinstance(gene_id, str) or not gene_id.startswith("ENSG"):
            warnings.append(f"Ensembl could not resolve gene {gene}.")
            continue

        expanded_urls = [
            f"https://rest.ensembl.org/lookup/id/{gene_id}?expand=1;content-type=application/json",
            f"https://rest.ensembl.org/lookup/id/{gene_id}?expand=1",
        ]
        payload: dict | None = None
        error: str | None = None
        for expanded_url in expanded_urls:
            payload, error = await get_json(expanded_url)
            if payload is not None:
                break
        if payload is None:
            logger.warning("Ensembl transcript expansion failed for %s: %s", gene, error)
            warnings.append(f"Ensembl transcript lookup failed for {gene} ({error}).")
            continue
        transcript_data = payload.get("Transcript")
        if not isinstance(transcript_data, list) or not transcript_data:
            warnings.append(f"Ensembl returned no transcripts for {gene} ({gene_id}).")
            continue

        for transcript in transcript_data[:100]:
            transcript_id = transcript.get("id")
            if transcript_id:
                transcripts.append(TranscriptInfo(
                    gene_symbol=gene,
                    gene_id=gene_id,
                    transcript_id=transcript_id,
                    transcript_name=transcript.get("display_name"),
                    ensembl_transcript_id=transcript_id,
                    transcript_type=transcript.get("biotype"),
                    source_db="Ensembl REST",
                ))
    return transcripts, warnings


async def _reactome_pathways(
    gene_ids: Dict[str, str],
    client: httpx.AsyncClient,
) -> Tuple[List[ReactomePathway], List[str]]:
    pathways: List[ReactomePathway] = []
    warnings: List[str] = []
    for gene, gene_id in gene_ids.items():
        try:
            response = await client.post(
                f"{REACTOME_BASE}/identifiers/projection",
                content=gene_id,
                headers={"Accept": "application/json", "Content-Type": "text/plain"},
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
            for pathway in payload.get("pathways", []):
                pathway_id = pathway.get("stId") or str(pathway.get("dbId", ""))
                pathway_name = pathway.get("name")
                if pathway_id and pathway_name:
                    pathways.append(ReactomePathway(
                        input_gene=gene,
                        pathway_id=pathway_id,
                        pathway_name=pathway_name,
                        evidence="Reactome AnalysisService projection",
                    ))
            if not payload.get("pathways"):
                warnings.append(f"Reactome returned no pathways for {gene} ({gene_id}).")
        except (httpx.TimeoutException, httpx.HTTPError, ValueError, AttributeError) as exc:
            logger.warning("Reactome lookup failed for %s: %s", gene, exc)
            warnings.append(f"Reactome pathway lookup failed for {gene}.")
    return pathways, warnings


async def _go_annotations(
    gene_ids: Dict[str, str],
    client: httpx.AsyncClient,
) -> Tuple[List[GOAnnotation], List[str]]:
    annotations: List[GOAnnotation] = []
    warnings: List[str] = []
    for gene, gene_id in gene_ids.items():
        try:
            xref_response = await client.get(
                f"https://rest.ensembl.org/xrefs/id/{gene_id}",
                headers={"Accept": "application/json"},
                timeout=30.0,
            )
            xref_response.raise_for_status()
            xrefs = xref_response.json()
            uniprot_ids = [
                item.get("primary_id")
                for item in xrefs
                if item.get("dbname") == "Uniprot_gn" and item.get("primary_id")
            ]
            uniprot_ids.sort(key=lambda value: (not bool(re.match(r"^[OPQ][0-9][A-Z0-9]{3}[0-9]$", value)), value))
            if not uniprot_ids:
                warnings.append(f"No UniProt cross-reference was found for {gene} ({gene_id}); GO unavailable.")
                continue
            response = await client.get(
                f"{QUICKGO_BASE}/annotation/search",
                params={
                    "geneProductId": f"UniProtKB:{uniprot_ids[0]}",
                    "aspect": "biological_process",
                    "limit": "100",
                },
                headers={"Accept": "application/json"},
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
            term_ids = list(dict.fromkeys(
                item.get("goId") for item in payload.get("results", []) if item.get("goId")
            ))
            if term_ids:
                term_response = await client.get(
                    f"{QUICKGO_BASE}/ontology/go/terms/{','.join(term_ids)}",
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )
                term_response.raise_for_status()
                term_payload = term_response.json()
                term_names = {
                    term.get("id"): term.get("name")
                    for term in term_payload.get("results", [])
                    if term.get("id") and term.get("name")
                }
                for term_id in term_ids:
                    if term_id in term_names:
                        annotations.append(GOAnnotation(
                            input_gene=gene,
                            go_id=term_id,
                            term_name=term_names[term_id],
                            namespace="biological_process",
                        ))
        except (httpx.TimeoutException, httpx.HTTPError, ValueError, AttributeError) as exc:
            logger.warning("GO lookup failed for %s: %s", gene, exc)
            warnings.append(f"Gene Ontology lookup failed for {gene}.")
    return annotations, warnings


def _normalise_theme(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _cross_validate(
    pathways: List[DiseasePathway],
    reactome: List[ReactomePathway],
    go_terms: List[GOAnnotation],
) -> List[CrossValidationTheme]:
    sources: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
    labels: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
    for item in pathways:
        key = _normalise_theme(item.pathway_name)
        sources[key]["KEGG"].add(item.pathway_name)
        labels[key]["inputs"].update(item.input_genes)
    for item in reactome:
        key = _normalise_theme(item.pathway_name)
        sources[key]["Reactome"].add(item.pathway_name)
        labels[key]["inputs"].add(item.input_gene)
    for item in go_terms:
        key = _normalise_theme(item.term_name)
        sources[key]["GO"].add(item.term_name)
        labels[key]["inputs"].add(item.input_gene)

    results: List[CrossValidationTheme] = []
    for key, by_source in sources.items():
        if len(by_source) >= 2:
            results.append(CrossValidationTheme(
                theme=next(iter(next(iter(by_source.values())))),
                kegg_pathways=sorted(by_source.get("KEGG", set())),
                reactome_pathways=sorted(by_source.get("Reactome", set())),
                go_terms=sorted(by_source.get("GO", set())),
                supporting_inputs=sorted(labels[key]["inputs"]),
                match_method="exact normalized name",
            ))
    return sorted(results, key=lambda item: item.theme)


async def build_disease_analysis(request: DiseaseAnalysisRequest) -> DiseaseAnalysisResult:
    inputs = list(dict.fromkeys(value.strip() for value in request.inputs if value.strip()))
    if not inputs:
        raise ValueError("At least one input molecule is required.")
    warnings: List[str] = []
    detected_types = {
        value: detect_rna_type(value, request.input_type)
        for value in inputs
    }
    gene_inputs = [
        value for value in inputs
        if detected_types[value] == "gene"
    ]
    mirna_inputs = [
        value for value in inputs
        if detected_types[value] == "miRNA"
    ]
    lncrna_inputs = [
        value for value in inputs
        if detected_types[value] == "lncRNA"
    ]
    if mirna_inputs and request.organism.value != "hsa":
        warnings.append("miRNA relationship lookup currently supports human identifiers only.")
    async with httpx.AsyncClient() as client:
        resolved_gene_ids, resolution_warnings = await resolve_gene_identifiers(
            gene_inputs, request.organism.value, client
        )
        warnings.extend(resolution_warnings)
        associations, _, association_warnings = await _kegg_diseases(
            resolved_gene_ids, request.organism.value, request.disease_query, client
        )
        warnings.extend(association_warnings)
        transcripts, transcript_warnings = await _ensembl_transcripts(gene_inputs, client)
        warnings.extend(transcript_warnings)
        ensembl_gene_ids = {
            transcript.gene_symbol: transcript.gene_id
            for transcript in transcripts
            if transcript.gene_id
        }
        reactome_pathways: List[ReactomePathway] = []
        go_annotations: List[GOAnnotation] = []
        if request.organism.value == "hsa":
            reactome_pathways, reactome_warnings = await _reactome_pathways(
                ensembl_gene_ids, client
            )
            go_annotations, go_warnings = await _go_annotations(ensembl_gene_ids, client)
            warnings.extend(reactome_warnings)
            warnings.extend(go_warnings)
        elif gene_inputs:
            warnings.append("Reactome and Gene Ontology cross-validation currently supports human genes only.")
        mirna_relationships, mirna_warnings = await fetch_mirna_relationships(
            mirna_inputs, client
        )
        lncrna_relationships, lncrna_warnings = await fetch_lncrna_relationships(
            lncrna_inputs, client
        )
        protein_interactions, interaction_warnings = await fetch_protein_interactions(
            gene_inputs, client, request.interaction_score
        )
        warnings.extend(mirna_warnings)
        warnings.extend(lncrna_warnings)
        warnings.extend(interaction_warnings)
        gene_pathways = await fetch_gene_pathways(
            list(resolved_gene_ids.values()), request.organism.value, client
        )
        pathway_names = _parse_kegg_table(await _polite_get(
            f"{KEGG_BASE}/list/pathway/{request.organism.value}", client
        ))

    entry_to_symbol = {entry: symbol for symbol, entry in resolved_gene_ids.items()}
    pathway_members: Dict[str, Set[str]] = defaultdict(set)
    for entry, pathway_ids in gene_pathways.items():
        gene = entry_to_symbol.get(entry, entry)
        for pathway_id in pathway_ids:
            pathway_members[pathway_id].add(gene)
    if gene_inputs and not pathway_members:
        warnings.append("KEGG returned no pathway links for the resolved gene identifiers.")
    pathways = [
        DiseasePathway(
            pathway_id=pathway_id,
            pathway_name=pathway_names.get(pathway_id, pathway_id),
            source_db="KEGG",
            input_genes=sorted(genes),
            overlap_count=len(genes),
        )
        for pathway_id, genes in sorted(pathway_members.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    cross_validation = _cross_validate(pathways, reactome_pathways, go_annotations)

    input_resolutions = build_input_resolutions(
        inputs, request.input_type, resolved_gene_ids
    )
    input_types = {
        item.normalized_identifier: item.detected_type
        for item in input_resolutions
    }
    input_types.update({
        item.original_input: item.detected_type
        for item in input_resolutions
    })
    network = build_integrated_network(
        inputs,
        input_types,
        associations,
        pathways,
        mirna_relationships,
        lncrna_relationships,
        protein_interactions,
    )
    network_clusters = cluster_network(network, associations, pathways)

    edges = [
        DiseaseNetworkEdge(
            source=edge.source,
            target=edge.target,
            edge_type=edge.edge_type,
            source_db=edge.source_db,
            evidence=edge.evidence,
            score=edge.score,
        )
        for edge in network.edges
    ]

    diseases_by_input: Dict[str, Set[str]] = defaultdict(set)
    pathways_by_input: Dict[str, Set[str]] = defaultdict(set)
    for association in associations:
        diseases_by_input[association.input_name].add(association.disease_name)
    for pathway in pathways:
        for gene in pathway.input_genes:
            pathways_by_input[gene].add(pathway.pathway_name)
    shared_disease_models, unique_diseases = shared_unique_associations(diseases_by_input)
    shared_pathway_models, unique_pathways = shared_unique_associations(pathways_by_input)
    shared_diseases = [
        item.association for item in shared_disease_models
        if item.scope == "all inputs"
    ]
    shared_pathways = [
        item.association for item in shared_pathway_models
        if item.scope == "all inputs"
    ]
    shared_associations = shared_disease_models + shared_pathway_models
    clusters = [
        DiseaseCluster(
            cluster_id=cluster.cluster_id,
            members=cluster.members,
            shared_diseases=[
                value for value in cluster.associated_diseases
                if value in shared_diseases
            ],
            shared_pathways=[
                value for value in cluster.associated_pathways
                if value in shared_pathways
            ],
            node_count=cluster.node_count,
            node_types=cluster.node_types,
            major_genes=cluster.major_genes,
        )
        for cluster in network_clusters
    ]

    return DiseaseAnalysisResult(
        inputs=inputs,
        input_type=request.input_type,
        disease_query=request.disease_query,
        organism=request.organism.value,
        resolved_gene_ids=resolved_gene_ids,
        input_resolutions=input_resolutions,
        summary=DiseaseAnalysisSummary(
            input_count=len(inputs),
            disease_association_count=len(associations),
            pathway_count=len(pathways),
            interaction_count=len(edges),
        ),
        associations=associations,
        pathways=pathways,
        reactome_pathways=reactome_pathways,
        go_annotations=go_annotations,
        cross_validation=cross_validation,
        mirna_relationships=mirna_relationships,
        lncrna_relationships=lncrna_relationships,
        protein_interactions=protein_interactions,
        network=network,
        network_clusters=network_clusters,
        shared_associations=shared_associations,
        unique_associations={
            **{f"diseases:{key}": value for key, value in unique_diseases.items()},
            **{f"pathways:{key}": value for key, value in unique_pathways.items()},
        },
        transcripts=transcripts,
        network_edges=edges,
        clusters=clusters,
        shared_diseases=shared_diseases,
        unique_diseases=unique_diseases,
        shared_pathways=shared_pathways,
        unique_pathways=unique_pathways,
        warnings=list(dict.fromkeys(warnings)),
    )
