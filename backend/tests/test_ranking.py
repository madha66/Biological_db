"""
Tests for the pathway ranking module.
"""

import pytest
import math

from app.analysis.ranking import (
    compute_pathway_score,
    compute_ranking_score,
    rank_pathways,
)
from app.config import PVALUE_EPSILON


class TestPathwayScore:
    """Test pathway representation score computation."""

    def test_basic_score(self) -> None:
        """3 out of 6 genes → 0.5"""
        assert compute_pathway_score(3, 6) == 0.5

    def test_all_genes(self) -> None:
        """All genes in pathway → 1.0"""
        assert compute_pathway_score(6, 6) == 1.0

    def test_single_gene(self) -> None:
        """1 out of 10 → 0.1"""
        assert compute_pathway_score(1, 10) == 0.1

    def test_zero_total(self) -> None:
        """Zero total genes → 0.0 (avoid division by zero)."""
        assert compute_pathway_score(0, 0) == 0.0


class TestRankingScore:
    """Test the combined ranking score formula."""

    def test_highly_significant(self) -> None:
        """
        Worked example:
        Pathway Score = 0.5, Adjusted p-value = 1e-10
        Ranking Score = 0.5 × -log10(1e-10) = 0.5 × 10 = 5.0
        """
        score = compute_ranking_score(0.5, 1e-10)
        assert abs(score - 5.0) < 0.001

    def test_not_significant(self) -> None:
        """
        Pathway Score = 0.3, Adjusted p-value = 0.5
        Ranking Score = 0.3 × -log10(0.5) = 0.3 × 0.301 ≈ 0.090
        """
        score = compute_ranking_score(0.3, 0.5)
        expected = 0.3 * (-math.log10(0.5))
        assert abs(score - round(expected, 6)) < 0.001

    def test_pvalue_floor(self) -> None:
        """Very small p-value should be clamped at epsilon."""
        score = compute_ranking_score(1.0, 0.0)
        expected = 1.0 * (-math.log10(PVALUE_EPSILON))
        assert abs(score - round(expected, 6)) < 0.001

    def test_pvalue_one(self) -> None:
        """p-value = 1.0 → -log10(1) = 0 → ranking score = 0."""
        score = compute_ranking_score(0.5, 1.0)
        assert score == 0.0


class TestRankPathways:
    """Test the full pathway ranking and sorting."""

    def test_ranking_order(self) -> None:
        """Pathways should be sorted by ranking score descending."""
        ranked = rank_pathways(
            pathway_to_genes={
                "pw1": ["A", "B"],
                "pw2": ["A", "B", "C", "D"],
                "pw3": ["A"],
            },
            pathway_names={"pw1": "Path 1", "pw2": "Path 2", "pw3": "Path 3"},
            pathway_total_genes={"pw1": 50, "pw2": 100, "pw3": 200},
            p_values={"pw1": 0.001, "pw2": 0.0001, "pw3": 0.5},
            adjusted_p_values={"pw1": 0.003, "pw2": 0.0003, "pw3": 0.5},
            total_valid_genes=5,
        )
        # pw2 should rank highest (4/5 genes + very significant)
        assert ranked[0].pathway_id == "pw2"
        assert ranked[0].rank == 1
        # All should have ascending ranks
        for i, rp in enumerate(ranked):
            assert rp.rank == i + 1
        # Ranking scores should be non-increasing
        for i in range(len(ranked) - 1):
            assert ranked[i].ranking_score >= ranked[i + 1].ranking_score

    def test_deterministic_ranking(self) -> None:
        """Same input should always produce same output."""
        kwargs = dict(
            pathway_to_genes={"pw1": ["A"], "pw2": ["B"]},
            pathway_names={"pw1": "P1", "pw2": "P2"},
            pathway_total_genes={"pw1": 50, "pw2": 50},
            p_values={"pw1": 0.01, "pw2": 0.01},
            adjusted_p_values={"pw1": 0.01, "pw2": 0.01},
            total_valid_genes=2,
        )
        result1 = rank_pathways(**kwargs)
        result2 = rank_pathways(**kwargs)
        assert [r.pathway_id for r in result1] == [r.pathway_id for r in result2]
