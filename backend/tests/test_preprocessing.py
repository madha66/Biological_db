"""
Tests for gene preprocessing: normalization, deduplication, and cleaning.
"""

import pytest
from app.analysis.preprocessing import preprocess_genes


class TestPreprocessGenes:
    """Test the preprocess_genes function."""

    def test_basic_dedup(self) -> None:
        """Duplicate genes (case-insensitive) should be removed."""
        result = preprocess_genes(["TP53", "tp53", "BRCA1", "Tp53"])
        assert result.unique_genes == ["TP53", "BRCA1"]
        assert result.duplicate_count == 2
        assert "tp53" in result.duplicates_removed
        assert "Tp53" in result.duplicates_removed

    def test_whitespace_trimming(self) -> None:
        """Whitespace should be trimmed from gene symbols."""
        result = preprocess_genes(["  TP53  ", "\tBRCA1\t", "  EGFR "])
        assert result.unique_genes == ["TP53", "BRCA1", "EGFR"]

    def test_empty_tokens_removed(self) -> None:
        """Empty and whitespace-only tokens should be removed."""
        result = preprocess_genes(["TP53", "", "  ", "BRCA1", ""])
        assert result.unique_genes == ["TP53", "BRCA1"]
        assert result.duplicate_count == 0

    def test_preserves_first_casing(self) -> None:
        """The first occurrence's casing should be preserved."""
        result = preprocess_genes(["tp53", "TP53", "Tp53"])
        assert result.unique_genes == ["tp53"]
        assert result.duplicate_count == 2

    def test_all_empty_input(self) -> None:
        """All-empty input should produce empty result."""
        result = preprocess_genes(["", "  ", "\t"])
        assert result.unique_genes == []
        assert result.duplicate_count == 0

    def test_single_gene(self) -> None:
        """Single gene should pass through unchanged."""
        result = preprocess_genes(["TP53"])
        assert result.unique_genes == ["TP53"]
        assert result.duplicate_count == 0
        assert len(result.original_tokens) == 1

    def test_original_tokens_tracked(self) -> None:
        """All non-empty tokens should be tracked in original_tokens."""
        result = preprocess_genes(["TP53", "BRCA1", "TP53", ""])
        assert result.original_tokens == ["TP53", "BRCA1", "TP53"]
