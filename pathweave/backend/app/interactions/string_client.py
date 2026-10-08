"""Small client for the public STRING interaction endpoint."""
from __future__ import annotations

import logging
from typing import List, Tuple

import httpx

from app.api.models import ProteinInteraction

logger = logging.getLogger(__name__)
STRING_URL = "https://string-db.org/api/json/network"


async def fetch_protein_interactions(
    genes: List[str],
    client: httpx.AsyncClient,
    minimum_score: float = 0.4,
) -> Tuple[List[ProteinInteraction], List[str]]:
    interactions: List[ProteinInteraction] = []
    warnings: List[str] = []
    if not genes:
        return interactions, warnings
    try:
        response = await client.get(
            STRING_URL,
            params={
                "identifiers": "%0d".join(dict.fromkeys(genes)),
                "species": "9606",
                "required_score": str(round(minimum_score * 1000)),
                "caller_identity": "pathweave",
            },
            headers={"Accept": "application/json"},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            payload = []
        for record in payload:
            if not isinstance(record, dict):
                continue
            source = record.get("preferredName_A") or record.get("stringId_A")
            target = record.get("preferredName_B") or record.get("stringId_B")
            if not source or not target:
                continue
            score = record.get("score")
            interactions.append(ProteinInteraction(
                source_gene=str(source),
                target_gene=str(target),
                source_db="STRING",
                score=float(score) if score is not None else None,
                interaction_type="protein_protein",
            ))
        if not interactions:
            warnings.append("STRING returned no interactions above the configured score threshold.")
    except (httpx.TimeoutException, httpx.HTTPError, ValueError, TypeError) as exc:
        logger.warning("STRING lookup failed: %s", exc)
        warnings.append("STRING interaction service unavailable; other analysis results were preserved.")
    return interactions, warnings
