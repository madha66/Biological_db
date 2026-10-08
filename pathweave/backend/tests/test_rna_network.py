"""Unit tests for RNA services and integrated network analysis."""
from __future__ import annotations

import asyncio

import httpx

import app.rna.services as rna_services
from app.api.models import (
    DiseaseAssociation,
    DiseasePathway,
    IntegratedNetwork,
    NetworkEdge,
    NetworkNode,
    RNAInteraction,
)
from app.interactions.string_client import fetch_protein_interactions
from app.network.analysis import (
    build_integrated_network,
    cluster_network,
    shared_unique_associations,
)
from app.rna.services import (
    build_input_resolutions,
    fetch_lncrna_relationships,
    fetch_mirna_relationships,
)


class Response:
    def __init__(self, payload: object, status_code: int = 200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://example.test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("failed", request=request, response=response)

    def json(self) -> object:
        return self.payload


class Client:
    def __init__(self, *, fail: bool = False):
        self.fail = fail

    async def get(self, url: str, *, params=None, **kwargs) -> Response:
        if self.fail:
            raise httpx.ConnectError("unavailable")
        if "string-db.org" in url:
            return Response([{
                "preferredName_A": "TP53",
                "preferredName_B": "MDM2",
                "score": 0.91,
            }])
        if "mirtarbase" in url:
            return Response({"results": [{
                "target_gene": "TP53",
                "target_id": "7157",
                "support_type": "Functional MTI",
            }]})
        if "/lookup/symbol/" in url:
            return Response({"id": "ENSG00000000001", "biotype": "lncRNA"})
        raise AssertionError(f"unexpected URL: {url}")


def run(coro):
    return asyncio.run(coro)


def test_mixed_input_resolution_never_treats_rnas_as_genes():
    resolutions = build_input_resolutions(
        ["TP53", "miR-21-5p", "HOTAIR"],
        "mixed",
        {"TP53": "hsa:7157"},
    )
    assert [item.detected_type for item in resolutions] == ["gene", "miRNA", "lncRNA"]
    assert resolutions[0].resolved_identifier == "hsa:7157"
    assert resolutions[1].normalized_identifier == "hsa-miR-21-5p"
    assert resolutions[2].resolved_identifier == "HOTAIR"


def test_mirna_relationships_are_normalized():
    rna_services.MIRTARBASE_API_URL = "https://mirtarbase.test/targets"
    relationships, warnings = run(fetch_mirna_relationships(["hsa-miR-21-5p"], Client()))
    assert warnings == []
    assert relationships[0].target_gene == "TP53"
    assert relationships[0].evidence_category == "Functional MTI"


def test_lncrna_resolution_reports_missing_curated_targets():
    associations, warnings = run(fetch_lncrna_relationships(["HOTAIR"], Client()))
    assert associations[0].status == "resolved_no_target_source"
    assert associations[0].target_genes == []
    assert any("no curated" in warning.lower() and "target" in warning.lower() for warning in warnings)


def test_external_failure_isolated_for_string():
    interactions, warnings = run(fetch_protein_interactions(["TP53"], Client(fail=True)))
    assert interactions == []
    assert "STRING interaction service unavailable" in warnings[0]


def test_string_interactions_and_network_edges_are_deduplicated():
    interactions, warnings = run(fetch_protein_interactions(["TP53"], Client()))
    assert warnings == []
    network = build_integrated_network(
        ["TP53", "hsa-miR-21-5p"],
        {"TP53": "gene", "hsa-miR-21-5p": "miRNA"},
        [],
        [],
        [
            RNAInteraction(
                rna="hsa-miR-21-5p",
                target_gene="TP53",
                source_db="miRTarBase",
            )
        ],
        [],
        interactions + interactions,
    )
    assert len([edge for edge in network.edges if edge.edge_type == "interacts_with"]) == 1
    assert len([edge for edge in network.edges if edge.edge_type == "targets"]) == 1


def test_network_clustering_and_shared_unique_associations():
    network = IntegratedNetwork(
        nodes=[
            NetworkNode(id="TP53", label="TP53", node_type="gene"),
            NetworkNode(id="BRCA1", label="BRCA1", node_type="gene"),
            NetworkNode(id="D1", label="D1", node_type="disease"),
        ],
        edges=[
            NetworkEdge(source="TP53", target="D1", edge_type="associated_with", source_db="KEGG"),
            NetworkEdge(source="BRCA1", target="D1", edge_type="associated_with", source_db="KEGG"),
        ],
    )
    clusters = cluster_network(
        network,
        [
            DiseaseAssociation(input_name="TP53", disease_id="D1", disease_name="Cancer", source_db="KEGG"),
            DiseaseAssociation(input_name="BRCA1", disease_id="D1", disease_name="Cancer", source_db="KEGG"),
        ],
        [DiseasePathway(
            pathway_id="P1",
            pathway_name="DNA repair",
            source_db="KEGG",
            input_genes=["TP53", "BRCA1"],
            overlap_count=2,
        )],
    )
    assert clusters[0].members == ["BRCA1", "D1", "TP53"]
    shared, unique = shared_unique_associations({
        "TP53": ["Cancer", "p53 signaling"],
        "BRCA1": ["Cancer"],
    })
    assert shared[0].association == "Cancer"
    assert unique["TP53"] == ["p53 signaling"]
