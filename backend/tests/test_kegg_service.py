"""
Tests for the KEGG service layer — all using mocked HTTP responses.

No real network calls are made in these tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.kegg_service import KEGGService, FileCache, KEGGUnreachableError


class MockCache:
    """In-memory mock cache for testing."""

    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def get(self, key: str) -> dict | list | None:
        return self._store.get(key)

    def set(self, key: str, value: dict | list) -> None:
        self._store[key] = value


class TestKEGGServiceFindGene:
    """Test gene symbol resolution."""

    def _make_service(self) -> KEGGService:
        return KEGGService(cache=MockCache())  # type: ignore[arg-type]

    @patch("app.services.kegg_service.KEGGService._request")
    def test_find_gene_success(self, mock_request: MagicMock) -> None:
        """A known gene should resolve to its KEGG ID."""
        mock_request.return_value = "hsa:7157\tTP53, p53; tumor protein p53\n"
        service = self._make_service()
        result = service.find_gene("TP53", "hsa")
        assert result == "hsa:7157"

    @patch("app.services.kegg_service.KEGGService._request")
    def test_find_gene_not_found(self, mock_request: MagicMock) -> None:
        """An unknown gene should return None."""
        mock_request.return_value = ""
        service = self._make_service()
        result = service.find_gene("FAKEGENE", "hsa")
        assert result is None

    @patch("app.services.kegg_service.KEGGService._request")
    def test_find_gene_multiple_results(self, mock_request: MagicMock) -> None:
        """When multiple genes match, the one with exact symbol match should be preferred."""
        mock_request.return_value = (
            "hsa:2064\tERBB2, HER2, NEU; erb-b2 receptor tyrosine kinase 2\n"
            "hsa:1956\tEGFR, ERBB1; epidermal growth factor receptor\n"
        )
        service = self._make_service()
        result = service.find_gene("EGFR", "hsa")
        assert result == "hsa:1956"

    @patch("app.services.kegg_service.KEGGService._request")
    def test_find_gene_caches_result(self, mock_request: MagicMock) -> None:
        """Results should be cached — second call should not hit the API."""
        mock_request.return_value = "hsa:7157\tTP53, p53; tumor protein p53\n"
        service = self._make_service()
        service.find_gene("TP53", "hsa")
        service.find_gene("TP53", "hsa")
        mock_request.assert_called_once()


class TestKEGGServiceGetPathways:
    """Test pathway retrieval for genes."""

    def _make_service(self) -> KEGGService:
        return KEGGService(cache=MockCache())  # type: ignore[arg-type]

    @patch("app.services.kegg_service.KEGGService._request")
    def test_get_pathways(self, mock_request: MagicMock) -> None:
        """Pathways should be parsed from KEGG link response."""
        mock_request.return_value = (
            "hsa:7157\tpath:hsa04115\n"
            "hsa:7157\tpath:hsa04010\n"
            "hsa:7157\tpath:map04115\n"  # Global map, should be filtered out
        )
        service = self._make_service()
        pathways = service.get_pathways_for_gene("hsa:7157")
        assert len(pathways) == 2
        assert pathways[0]["pathway_id"] == "hsa04115"
        assert pathways[1]["pathway_id"] == "hsa04010"

    @patch("app.services.kegg_service.KEGGService._request")
    def test_get_pathways_empty(self, mock_request: MagicMock) -> None:
        """No pathways should return empty list."""
        mock_request.return_value = ""
        service = self._make_service()
        pathways = service.get_pathways_for_gene("hsa:99999")
        assert pathways == []


class TestKEGGServicePathwayMeta:
    """Test pathway metadata retrieval."""

    def _make_service(self) -> KEGGService:
        return KEGGService(cache=MockCache())  # type: ignore[arg-type]

    @patch("app.services.kegg_service.KEGGService._request")
    def test_get_pathway_name(self, mock_request: MagicMock) -> None:
        """Pathway name should be parsed from the KEGG flat file."""
        mock_request.return_value = (
            "ENTRY       hsa04151  Pathway\n"
            "NAME        PI3K-Akt signaling pathway - Homo sapiens (human)\n"
            "DESCRIPTION Some description here\n"
        )
        service = self._make_service()
        meta = service.get_pathway_metadata("hsa04151")
        assert meta["name"] == "PI3K-Akt signaling pathway"
        assert meta["pathway_id"] == "hsa04151"
