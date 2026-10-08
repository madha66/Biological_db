"""Focused tests for Ensembl transcript retrieval."""
from __future__ import annotations

import asyncio

import httpx
import pytest

from app.api.disease_analysis import _ensembl_transcripts


class FakeResponse:
    def __init__(self, payload: dict | None = None, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://rest.ensembl.org")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("request failed", request=request, response=response)

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("invalid JSON")
        return self._payload


class FakeClient:
    def __init__(self, responses: dict[str, FakeResponse | list[FakeResponse]]):
        self.responses = responses
        self.headers_seen: list[dict[str, str]] = []
        self.calls: dict[str, int] = {}

    async def get(self, url: str, *, headers: dict[str, str], timeout: float) -> FakeResponse:
        self.headers_seen.append(headers)
        token = url.split("?", 1)[0].rsplit("/", 1)[1]
        gene = token
        if token.startswith("ENSG"):
            gene = next(
                name for name, response in self.responses.items()
                if (
                    any(
                        item._payload and item._payload.get("id") == token
                        for item in (response if isinstance(response, list) else [response])
                    )
                )
            )
        response = self.responses[gene]
        if isinstance(response, list):
            call_number = self.calls.get(gene, 0)
            self.calls[gene] = call_number + 1
            return response[min(call_number, len(response) - 1)]
        return response


def run(coro):
    return asyncio.run(coro)


@pytest.mark.parametrize(
    ("gene", "gene_id", "transcript_id"),
    [
        ("TP53", "ENSG00000141510", "ENST00000269305"),
        ("BRCA1", "ENSG00000012048", "ENST00000357654"),
        ("BRCA2", "ENSG00000139618", "ENST00000380152"),
    ],
)
def test_known_gene_transcripts(gene: str, gene_id: str, transcript_id: str):
    client = FakeClient({
        gene: FakeResponse({
            "id": gene_id,
            "Transcript": [{
                "id": transcript_id,
                "display_name": transcript_id,
                "biotype": "protein_coding",
            }],
        }),
    })
    transcripts, warnings = run(_ensembl_transcripts([gene], client))
    assert warnings == []
    assert transcripts[0].gene_symbol == gene
    assert transcripts[0].gene_id == gene_id
    assert transcripts[0].ensembl_transcript_id == transcript_id
    assert transcripts[0].transcript_type == "protein_coding"
    assert client.headers_seen[0]["Accept"] == "application/json"


def test_invalid_gene_warns():
    client = FakeClient({"INVALID": FakeResponse({}, status_code=500)})
    transcripts, warnings = run(_ensembl_transcripts(["INVALID"], client))
    assert transcripts == []
    assert "Ensembl transcript lookup failed for INVALID (HTTP 500)." in warnings


def test_tp53_transient_http_500_then_success():
    client = FakeClient({"TP53": [
        FakeResponse(None, status_code=500),
        FakeResponse({"id": "ENSG00000141510"}),
        FakeResponse({
            "id": "ENSG00000141510",
            "Transcript": [{"id": "ENST00000269305", "biotype": "protein_coding"}],
        }),
    ]})
    transcripts, warnings = run(_ensembl_transcripts(["TP53"], client))
    assert [item.transcript_id for item in transcripts] == ["ENST00000269305"]
    assert warnings == []


def test_tp53_persistent_http_500_warns():
    client = FakeClient({"TP53": FakeResponse(None, status_code=500)})
    transcripts, warnings = run(_ensembl_transcripts(["TP53"], client))
    assert transcripts == []
    assert warnings == ["Ensembl transcript lookup failed for TP53 (HTTP 500)."]


def test_partial_failure_preserves_successes():
    client = FakeClient({
        "TP53": FakeResponse(None, status_code=500),
        "BRCA1": FakeResponse({
            "id": "ENSG00000012048",
            "Transcript": [{"id": "ENST00000357654", "biotype": "protein_coding"}],
        }),
        "BRCA2": FakeResponse({
            "id": "ENSG00000139618",
            "Transcript": [{"id": "ENST00000380152", "biotype": "protein_coding"}],
        }),
    })
    transcripts, warnings = run(_ensembl_transcripts(["TP53", "BRCA1", "BRCA2"], client))
    assert {item.gene_symbol for item in transcripts} == {"BRCA1", "BRCA2"}
    assert len(warnings) == 1
    assert warnings[0].startswith("Ensembl transcript lookup failed for TP53")
