"""Focused tests for Reactome, Gene Ontology, and cross-validation."""
from __future__ import annotations

import asyncio

import httpx

from app.api.disease_analysis import (
    _cross_validate,
    _go_annotations,
    _reactome_pathways,
)
from app.api.models import DiseasePathway, GOAnnotation, ReactomePathway


class FakeResponse:
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


class FakeClient:
    def __init__(self, *, reactome: object | None = None, go_failure: bool = False):
        self.reactome = reactome
        self.go_failure = go_failure

    async def post(self, *args, **kwargs) -> FakeResponse:
        if isinstance(self.reactome, Exception):
            raise self.reactome
        return FakeResponse(self.reactome or {"pathways": []})

    async def get(self, url: str, *, params=None, **kwargs) -> FakeResponse:
        if self.go_failure:
            raise httpx.ConnectError("GO unavailable")
        if "/xrefs/" in url:
            return FakeResponse([{"dbname": "Uniprot_gn", "primary_id": "P04637"}])
        if "/annotation/search" in url:
            return FakeResponse({"results": [{"goId": "GO:0006281"}]})
        return FakeResponse({"results": [{"id": "GO:0006281", "name": "DNA repair"}]})


def run(coro):
    return asyncio.run(coro)


def test_tp53_reactome_lookup():
    pathways, warnings = run(_reactome_pathways(
        {"TP53": "ENSG00000141510"},
        FakeClient(reactome={"pathways": [{"stId": "R-HSA-74160", "name": "DNA Repair"}]}),
    ))
    assert pathways[0].pathway_id == "R-HSA-74160"
    assert pathways[0].input_gene == "TP53"
    assert warnings == []


def test_brca1_reactome_lookup():
    pathways, warnings = run(_reactome_pathways(
        {"BRCA1": "ENSG00000012048"},
        FakeClient(reactome={"pathways": [{"stId": "R-HSA-5693538", "name": "Homology Directed Repair"}]}),
    ))
    assert pathways[0].pathway_name == "Homology Directed Repair"
    assert warnings == []


def test_tp53_go_lookup():
    annotations, warnings = run(_go_annotations({"TP53": "ENSG00000141510"}, FakeClient()))
    assert annotations[0].go_id == "GO:0006281"
    assert annotations[0].term_name == "DNA repair"
    assert warnings == []


def test_brca1_go_lookup():
    annotations, warnings = run(_go_annotations({"BRCA1": "ENSG00000012048"}, FakeClient()))
    assert annotations[0].input_gene == "BRCA1"
    assert warnings == []


def test_external_api_failure_is_reported():
    pathways, warnings = run(_reactome_pathways(
        {"TP53": "ENSG00000141510"},
        FakeClient(reactome=httpx.ConnectError("Reactome unavailable")),
    ))
    assert pathways == []
    assert warnings == ["Reactome pathway lookup failed for TP53."]


def test_cross_database_matching_is_transparent():
    themes = _cross_validate(
        [DiseasePathway(
            pathway_id="hsa04010",
            pathway_name="DNA repair",
            source_db="KEGG",
            input_genes=["TP53"],
            overlap_count=1,
        )],
        [ReactomePathway(
            input_gene="TP53",
            pathway_id="R-HSA-74160",
            pathway_name="DNA repair",
        )],
        [GOAnnotation(
            input_gene="BRCA1",
            go_id="GO:0006281",
            term_name="DNA repair",
            namespace="biological_process",
        )],
    )
    assert len(themes) == 1
    assert themes[0].match_method == "exact normalized name"
    assert themes[0].supporting_inputs == ["BRCA1", "TP53"]
