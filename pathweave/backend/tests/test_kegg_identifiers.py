"""Focused tests for KEGG gene resolution and link parsing."""
from __future__ import annotations

import asyncio
import pytest

from app.api import disease_analysis
from app.kegg import client as kegg_client


class FakeClient:
    pass


def run(coro):
    return asyncio.run(coro)


def test_parse_gene_identifier():
    raw = "hsa:7157\tTP53, tumor protein p53\nmmu:22059\tTrp53"
    assert kegg_client.parse_gene_identifier(raw, "hsa", "TP53") == "hsa:7157"


def test_resolve_tp53_identifier(monkeypatch: pytest.MonkeyPatch):
    async def fake_get(url: str, client: FakeClient) -> str:
        assert url.endswith("/find/genes/TP53")
        return "hsa:7157\tTP53, tumor protein p53\n"

    monkeypatch.setattr(kegg_client, "_polite_get", fake_get)
    resolved, warnings = run(
        kegg_client.resolve_gene_identifiers(["TP53"], "hsa", FakeClient())
    )
    assert resolved == {"TP53": "hsa:7157"}
    assert warnings == []


@pytest.mark.parametrize(
    ("symbol", "entry"),
    [("TP53", "hsa:7157"), ("BRCA1", "hsa:672")],
)
def test_gene_pathway_lookup_uses_resolved_entry(
    monkeypatch: pytest.MonkeyPatch,
    symbol: str,
    entry: str,
):
    async def fake_get(url: str, client: FakeClient) -> str:
        assert url.endswith(f"/link/pathway/{entry}")
        return f"{entry}\tpath:hsa04115\n"

    monkeypatch.setattr(kegg_client, "_polite_get", fake_get)
    result = run(kegg_client.fetch_gene_pathways([entry], "hsa", FakeClient()))
    assert result == {entry: ["hsa04115"]}


def test_invalid_gene_warns(monkeypatch: pytest.MonkeyPatch):
    async def fake_get(url: str, client: FakeClient) -> str:
        return ""

    monkeypatch.setattr(kegg_client, "_polite_get", fake_get)
    resolved, warnings = run(
        kegg_client.resolve_gene_identifiers(["NOT_A_REAL_GENE"], "hsa", FakeClient())
    )
    assert resolved == {}
    assert warnings == ["KEGG could not resolve gene 'NOT_A_REAL_GENE' for organism hsa."]


def test_kegg_disease_links_parse_ds_entries(monkeypatch: pytest.MonkeyPatch):
    async def fake_get(url: str, client: FakeClient) -> str:
        if url.endswith("/list/disease"):
            return "H00001\tCancer\n"
        return "hsa:7157\tds:H00001\n"

    monkeypatch.setattr(disease_analysis, "_polite_get", fake_get)
    associations, _, warnings = run(
        disease_analysis._kegg_diseases(
            {"TP53": "hsa:7157"}, "hsa", "cancer", FakeClient()
        )
    )
    assert [association.disease_id for association in associations] == ["H00001"]
    assert warnings == []
