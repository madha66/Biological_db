"""
Integration tests for the API endpoints.

Uses FastAPI's TestClient with mocked KEGG service.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import init_services
from app.services.kegg_service import KEGGService


class MockKEGGService:
    """
    Mock KEGG service for integration tests.

    Returns deterministic, pre-defined responses for known genes.
    """

    def __init__(self) -> None:
        self._gene_map = {
            ("TP53", "hsa"): "hsa:7157",
            ("BRCA1", "hsa"): "hsa:672",
            ("EGFR", "hsa"): "hsa:1956",
        }
        self._gene_pathways = {
            "hsa:7157": [
                {"gene_id": "hsa:7157", "pathway_id": "hsa04115"},
                {"gene_id": "hsa:7157", "pathway_id": "hsa04010"},
            ],
            "hsa:672": [
                {"gene_id": "hsa:672", "pathway_id": "hsa04115"},
                {"gene_id": "hsa:672", "pathway_id": "hsa03440"},
            ],
            "hsa:1956": [
                {"gene_id": "hsa:1956", "pathway_id": "hsa04010"},
                {"gene_id": "hsa:1956", "pathway_id": "hsa04151"},
            ],
        }
        self._pathway_names = {
            "hsa04115": "p53 signaling pathway",
            "hsa04010": "MAPK signaling pathway",
            "hsa03440": "Homologous recombination",
            "hsa04151": "PI3K-Akt signaling pathway",
        }

    def find_gene(self, gene_symbol: str, organism: str) -> str | None:
        return self._gene_map.get((gene_symbol.upper(), organism))

    def get_pathways_for_gene(self, kegg_gene_id: str) -> list[dict[str, str]]:
        return self._gene_pathways.get(kegg_gene_id, [])

    def get_pathway_metadata(self, pathway_id: str) -> dict[str, str]:
        if pathway_id not in self._pathway_names:
            from app.services.kegg_service import KEGGServiceError
            raise KEGGServiceError(f"Unknown pathway: {pathway_id}")
        return {
            "pathway_id": pathway_id,
            "name": self._pathway_names.get(pathway_id, pathway_id),
            "description": "",
        }

    def get_organism_gene_universe(self, organism: str) -> set[str]:
        return {f"hsa:{i}" for i in range(1, 5001)}

    def get_all_pathway_genes(self, pathway_id: str, organism: str) -> set[str]:
        sizes = {
            "hsa04115": 72,
            "hsa04010": 295,
            "hsa03440": 41,
            "hsa04151": 354,
        }
        count = sizes.get(pathway_id, 50)
        return {f"hsa:{i}" for i in range(1, count + 1)}

    def get_pathway_gene_count(self, pathway_id: str) -> int:
        return len(self.get_all_pathway_genes(pathway_id, "hsa"))

    def is_reachable(self) -> bool:
        return True


@pytest.fixture
def client() -> TestClient:
    """Create a test client with mocked KEGG service."""
    mock_kegg = MockKEGGService()
    init_services(mock_kegg)  # type: ignore[arg-type]
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client: TestClient) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "kegg_reachable" in data
        assert "timestamp" in data


class TestOrganismsEndpoint:
    def test_list_organisms(self, client: TestClient) -> None:
        resp = client.get("/api/organisms")
        assert resp.status_code == 200
        data = resp.json()
        assert "hsa" in data
        assert "mmu" in data


class TestAnalyzeEndpoint:
    def test_successful_analysis(self, client: TestClient) -> None:
        """Full analysis pipeline should succeed with valid genes."""
        resp = client.post("/api/analyze", json={
            "genes": ["TP53", "BRCA1", "EGFR"],
            "organism": "hsa",
        })
        assert resp.status_code == 200
        data = resp.json()

        # Input summary
        assert data["input_summary"]["total_submitted"] == 3
        assert data["input_summary"]["valid_count"] == 3
        assert data["input_summary"]["unmapped_count"] == 0

        # Valid/unmapped genes
        assert len(data["valid_genes"]) == 3
        assert len(data["unmapped_genes"]) == 0

        # Pathways
        assert len(data["pathways"]) > 0
        for pw in data["pathways"]:
            assert "rank" in pw
            assert "pathway_id" in pw
            assert "pathway_name" in pw
            assert "pathway_score" in pw
            assert "p_value" in pw
            assert "adjusted_p_value" in pw
            assert "ranking_score" in pw
            assert "contributing_genes" in pw
            assert "kegg_url" in pw
            assert pw["kegg_url"].startswith("https://www.kegg.jp/pathway/")

        # Metadata
        assert data["metadata"]["organism"] == "hsa"
        assert data["metadata"]["background_universe_size"] > 0
        assert data["metadata"]["pathways_tested"] > 0

    def test_partial_mapping(self, client: TestClient) -> None:
        """Analysis should succeed even when some genes can't be mapped."""
        resp = client.post("/api/analyze", json={
            "genes": ["TP53", "FAKEGENE1", "BRCA1", "NOTREAL"],
            "organism": "hsa",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["input_summary"]["valid_count"] == 2
        assert data["input_summary"]["unmapped_count"] == 2
        assert "FAKEGENE1" in data["unmapped_genes"]
        assert "NOTREAL" in data["unmapped_genes"]

    def test_empty_genes(self, client: TestClient) -> None:
        """Empty gene list should return 422 (Pydantic validation)."""
        resp = client.post("/api/analyze", json={
            "genes": [],
            "organism": "hsa",
        })
        assert resp.status_code == 422

    def test_invalid_organism(self, client: TestClient) -> None:
        """Invalid organism should return 400."""
        resp = client.post("/api/analyze", json={
            "genes": ["TP53"],
            "organism": "zzz",
        })
        assert resp.status_code == 400

    def test_all_genes_unmapped(self, client: TestClient) -> None:
        """When all genes are unmapped, should return 400."""
        resp = client.post("/api/analyze", json={
            "genes": ["FAKEGENE1", "FAKEGENE2"],
            "organism": "hsa",
        })
        assert resp.status_code == 400


class TestPathwayDetailEndpoint:
    def test_pathway_after_analysis(self, client: TestClient) -> None:
        """Pathway detail should be available after running analysis."""
        # First, run an analysis
        client.post("/api/analyze", json={
            "genes": ["TP53", "BRCA1", "EGFR"],
            "organism": "hsa",
        })
        # Then query a pathway
        resp = client.get("/api/pathway/hsa04115")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pathway_id"] == "hsa04115"
        assert len(data["contributing_genes"]) > 0

    def test_unknown_pathway(self, client: TestClient) -> None:
        """Unknown pathway should return 404."""
        resp = client.get("/api/pathway/hsa99999")
        assert resp.status_code == 404
