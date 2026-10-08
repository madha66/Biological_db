"""RNA normalization and public relationship lookups.

The public RNA databases do not expose one stable, unauthenticated API for
every relationship type.  These services therefore preserve source status
explicitly instead of turning unavailable data into fabricated associations.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Dict, List, Tuple

import httpx

from app.api.models import InputResolution, LncRNAAssociation, RNAInteraction

logger = logging.getLogger(__name__)

MIRTARBASE_API_URL = os.getenv("PATHWEAVE_MIRTARBASE_API_URL", "")
ENSEMBL_REST = "https://rest.ensembl.org"


def detect_rna_type(identifier: str, requested_type: str) -> str:
    value = identifier.strip()
    lower = value.lower()
    if requested_type == "miRNA" or re.match(r"^(hsa-)?mir[-_]", lower):
        return "miRNA"
    if requested_type == "lncRNA":
        return "lncRNA"
    if re.match(r"^(linc|lnc|hotair|malat1|neat1|xist)", lower):
        return "lncRNA"
    return "gene"


def normalize_identifier(identifier: str, detected_type: str) -> str:
    value = identifier.strip()
    if detected_type == "miRNA":
        value = value.replace("_", "-")
        if value.lower().startswith("mir-"):
            value = f"hsa-{value}"
    return value


def build_input_resolutions(
    inputs: List[str],
    requested_type: str,
    resolved_gene_ids: Dict[str, str],
) -> List[InputResolution]:
    resolutions: List[InputResolution] = []
    for original in inputs:
        detected = detect_rna_type(original, requested_type)
        normalized = normalize_identifier(original, detected)
        if detected == "gene" and original in resolved_gene_ids:
            resolutions.append(InputResolution(
                original_input=original,
                normalized_identifier=normalized,
                detected_type=detected,
                resolved_identifier=resolved_gene_ids[original],
                source_db="KEGG",
                confidence=1.0,
                status="resolved",
            ))
        elif detected == "gene":
            resolutions.append(InputResolution(
                original_input=original,
                normalized_identifier=normalized,
                detected_type=detected,
                status="unresolved",
                warning="Gene identifier could not be resolved by KEGG.",
            ))
        else:
            resolutions.append(InputResolution(
                original_input=original,
                normalized_identifier=normalized,
                detected_type=detected,
                resolved_identifier=normalized,
                source_db="PathWeave normalization",
                confidence=0.8,
                status="normalized",
            ))
    return resolutions


async def fetch_mirna_relationships(
    mirnas: List[str],
    client: httpx.AsyncClient,
) -> Tuple[List[RNAInteraction], List[str]]:
    relationships: List[RNAInteraction] = []
    warnings: List[str] = []
    if not mirnas:
        return relationships, warnings
    if not MIRTARBASE_API_URL:
        warnings.append(
            "miRTarBase target service is not configured; no miRNA targets were inferred."
        )
        return relationships, warnings
    for mirna in dict.fromkeys(mirnas):
        try:
            response = await client.get(
                MIRTARBASE_API_URL,
                params={"mirna": mirna},
                headers={"Accept": "application/json"},
                timeout=20.0,
            )
            response.raise_for_status()
            payload = response.json()
            records = payload.get("results", payload) if isinstance(payload, (dict, list)) else []
            if not isinstance(records, list):
                records = []
            for record in records:
                if not isinstance(record, dict):
                    continue
                target = record.get("target_gene") or record.get("target") or record.get("gene")
                if target:
                    relationships.append(RNAInteraction(
                        rna=mirna,
                        target_gene=str(target),
                        target_identifier=record.get("target_id") or record.get("entrez_id"),
                        source_db="miRTarBase",
                        evidence=record.get("evidence") or record.get("support_type"),
                        evidence_category=record.get("support_type") or record.get("category"),
                    ))
            if not records:
                warnings.append(f"miRTarBase returned no targets for {mirna}.")
        except (httpx.TimeoutException, httpx.HTTPError, ValueError, AttributeError) as exc:
            logger.warning("miRTarBase lookup failed for %s: %s", mirna, exc)
            warnings.append(f"miRTarBase unavailable for {mirna}; no miRNA targets were inferred.")
    return relationships, warnings


async def fetch_lncrna_relationships(
    lncrnas: List[str],
    client: httpx.AsyncClient,
) -> Tuple[List[LncRNAAssociation], List[str]]:
    associations: List[LncRNAAssociation] = []
    warnings: List[str] = []
    for lncrna in dict.fromkeys(lncrnas):
        try:
            response = await client.get(
                f"{ENSEMBL_REST}/lookup/symbol/homo_sapiens/{lncrna}",
                headers={"Accept": "application/json"},
                timeout=20.0,
            )
            response.raise_for_status()
            payload = response.json()
            identifier = payload.get("id") if isinstance(payload, dict) else None
            biotype = payload.get("biotype") if isinstance(payload, dict) else None
            if not identifier:
                warnings.append(f"Ensembl could not resolve lncRNA {lncrna}.")
                continue
            if biotype and "lnc" not in biotype.lower():
                warnings.append(f"Ensembl resolved {lncrna}, but it is not annotated as a lncRNA.")
                continue
            associations.append(LncRNAAssociation(
                lncrna=lncrna,
                source_db="Ensembl REST",
                evidence=f"Resolved as {identifier}; no curated lncRNA target source was queried.",
                status="resolved_no_target_source",
            ))
            warnings.append(
                f"No curated lncRNA target/disease source is configured for {lncrna}; "
                "identifier resolution succeeded but no associations were inferred."
            )
        except (httpx.TimeoutException, httpx.HTTPError, ValueError, AttributeError) as exc:
            logger.warning("lncRNA lookup failed for %s: %s", lncrna, exc)
            warnings.append(f"lncRNA identifier lookup failed for {lncrna}.")
    return associations, warnings
