"""
Tests for statistical analysis: contingency table, Fisher's exact test, and FDR correction.

Includes hand-calculated expected values to verify correctness.
"""

import pytest
import math
from scipy.stats import fisher_exact as scipy_fisher

from app.analysis.enrichment import (
    build_contingency_table,
    fisher_exact_test,
    compute_enrichment,
    apply_fdr_correction,
    ContingencyTable,
)


class TestContingencyTable:
    """Test contingency table construction."""

    def test_basic_construction(self) -> None:
        """Verify a/b/c/d values for a known scenario."""
        # Scenario: 3 out of 6 input genes in a pathway that has 50 genes total,
        # universe of 5000 genes.
        table = build_contingency_table(
            input_genes_in_pathway=3,
            total_valid_input_genes=6,
            total_pathway_genes=50,
            universe_size=5000,
        )
        assert table.a == 3   # input genes in pathway
        assert table.b == 3   # input genes NOT in pathway (6 - 3)
        assert table.c == 47  # background genes in pathway (50 - 3)
        assert table.d == 4947  # background genes not in pathway (5000 - 6 - 47)

    def test_all_input_in_pathway(self) -> None:
        """When all input genes are in the pathway, b should be 0."""
        table = build_contingency_table(
            input_genes_in_pathway=5,
            total_valid_input_genes=5,
            total_pathway_genes=100,
            universe_size=1000,
        )
        assert table.a == 5
        assert table.b == 0
        assert table.c == 95
        assert table.d == 900

    def test_single_gene_in_pathway(self) -> None:
        """Single gene overlap."""
        table = build_contingency_table(
            input_genes_in_pathway=1,
            total_valid_input_genes=10,
            total_pathway_genes=30,
            universe_size=2000,
        )
        assert table.a == 1
        assert table.b == 9
        assert table.c == 29
        assert table.d == 1961


class TestFisherExactTest:
    """Test Fisher's exact test computation."""

    def test_significant_enrichment(self) -> None:
        """A strongly enriched pathway should have a small p-value."""
        # 5 out of 6 input genes in a pathway of 50 genes, universe 5000
        table = ContingencyTable(a=5, b=1, c=45, d=4949)
        odds_ratio, p_value = fisher_exact_test(table)
        assert p_value < 0.001  # Should be highly significant
        assert odds_ratio > 1.0  # Overrepresented

    def test_no_enrichment(self) -> None:
        """A pathway with proportional representation should not be significant."""
        # 1 out of 100 input genes in a pathway of 50 genes, universe 5000
        table = ContingencyTable(a=1, b=99, c=49, d=4851)
        odds_ratio, p_value = fisher_exact_test(table)
        assert p_value > 0.05  # Should not be significant

    def test_hand_calculated_value(self) -> None:
        """
        Verify against a hand-calculated Fisher's exact test.

        Table: [[3, 7], [47, 4943]]
        Using scipy for reference:
        """
        table = ContingencyTable(a=3, b=7, c=47, d=4943)
        _, p_value = fisher_exact_test(table)
        # Verify against scipy directly
        _, expected_p = scipy_fisher([[3, 7], [47, 4943]], alternative="greater")
        assert abs(p_value - expected_p) < 1e-10


class TestFDRCorrection:
    """Test Benjamini–Hochberg FDR correction."""

    def test_basic_correction(self) -> None:
        """FDR-corrected p-values should be >= raw p-values."""
        raw = [0.001, 0.01, 0.04, 0.05, 0.10, 0.50]
        adjusted = apply_fdr_correction(raw)
        for raw_p, adj_p in zip(raw, adjusted):
            assert adj_p >= raw_p

    def test_single_pvalue(self) -> None:
        """A single p-value should be returned unchanged."""
        adjusted = apply_fdr_correction([0.03])
        assert adjusted == [0.03]

    def test_empty_list(self) -> None:
        """Empty input should return empty output."""
        assert apply_fdr_correction([]) == []

    def test_known_correction(self) -> None:
        """
        Verify BH correction against known expected values.

        For p-values [0.01, 0.03, 0.04] with 3 tests:
        - Sorted: p1=0.01 (rank 1), p2=0.03 (rank 2), p3=0.04 (rank 3)
        - Adjusted: p1_adj = min(0.01 * 3/1, 1) = 0.03
        - Adjusted: p2_adj = min(0.03 * 3/2, 1) = 0.045
        - Adjusted: p3_adj = min(0.04 * 3/3, 1) = 0.04
        - Enforce monotonicity: [0.03, 0.04, 0.04]
        """
        raw = [0.01, 0.03, 0.04]
        adjusted = apply_fdr_correction(raw)
        assert abs(adjusted[0] - 0.03) < 1e-10
        # statsmodels BH enforces non-decreasing order from bottom-up:
        # p3_adj = 0.04, p2_adj = min(0.045, next_adj=0.04) → 0.04
        assert abs(adjusted[1] - 0.04) < 1e-10
        assert abs(adjusted[2] - 0.04) < 1e-10


class TestComputeEnrichment:
    """Test the full enrichment computation."""

    def test_basic_enrichment(self) -> None:
        """Compute enrichment for two pathways."""
        results = compute_enrichment(
            pathway_gene_counts={"pw1": 4, "pw2": 1},
            pathway_total_genes={"pw1": 50, "pw2": 200},
            total_valid_genes=6,
            universe_size=5000,
        )
        assert len(results) == 2
        # pw1 should have a lower p-value (more enriched)
        pw1 = next(r for r in results if r.pathway_id == "pw1")
        pw2 = next(r for r in results if r.pathway_id == "pw2")
        assert pw1.p_value < pw2.p_value
