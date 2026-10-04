"""Unit tests for PathWeave scoring module."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# Allow imports from backend/app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scoring.scorer import (
    GeneWeight,
    PathwayResult,
    RNAInteraction,
    ScoringConfig,
    compute_gene_weights,
    jaccard,
    merge_redundant_pathways,
    score_pathways,
)


# ---------------------------------------------------------------------------
# Gene weighting
# ---------------------------------------------------------------------------


def test_gene_weight_validated_single_rna():
    """Single validated RNA → base=1.0, n_rnas=1 → w = 1.0 * (1+0) = 1.0"""
    ix = [RNAInteraction("mir-1", "miRNA", "GENE_A", "validated", "DB")]
    weights = compute_gene_weights(ix, seed_genes=[])
    assert "GENE_A" in weights
    w = weights["GENE_A"].weight
    assert abs(w - 1.0) < 1e-9, f"Expected 1.0, got {w}"


def test_gene_weight_predicted_single_rna():
    """Single predicted RNA → base=0.4 → w = 0.4"""
    ix = [RNAInteraction("mir-1", "miRNA", "GENE_A", "predicted", "DB")]
    weights = compute_gene_weights(ix, seed_genes=[])
    w = weights["GENE_A"].weight
    assert abs(w - 0.4) < 1e-9, f"Expected 0.4, got {w}"


def test_gene_weight_two_validated_rnas():
    """Two validated RNAs → base=1.0, n_rnas=2 → w = 1.0*(1+log2(2)) = 2.0"""
    ix = [
        RNAInteraction("mir-1", "miRNA", "GENE_A", "validated", "DB"),
        RNAInteraction("mir-2", "miRNA", "GENE_A", "validated", "DB"),
    ]
    weights = compute_gene_weights(ix, seed_genes=[])
    w = weights["GENE_A"].weight
    expected = 1.0 * (1 + math.log2(2))
    assert abs(w - expected) < 1e-9, f"Expected {expected}, got {w}"


def test_gene_weight_mixed_evidence():
    """Best of validated(1.0) and predicted(0.4) should be 1.0 as base."""
    ix = [
        RNAInteraction("mir-1", "miRNA", "GENE_A", "validated", "DB"),
        RNAInteraction("mir-2", "miRNA", "GENE_A", "predicted", "DB"),
    ]
    weights = compute_gene_weights(ix, seed_genes=[])
    w = weights["GENE_A"].weight
    expected = 1.0 * (1 + math.log2(2))
    assert abs(w - expected) < 1e-9


def test_seed_gene_gets_weight_one():
    """Seed gene with no RNA interactions should have weight=1.0."""
    weights = compute_gene_weights([], seed_genes=["TNF"])
    assert "TNF" in weights
    assert weights["TNF"].weight == 1.0


def test_four_rnas_weight():
    """4 validated RNAs → w = 1*(1+log2(4)) = 3.0"""
    ix = [RNAInteraction(f"mir-{i}", "miRNA", "GENE_A", "validated", "DB") for i in range(4)]
    weights = compute_gene_weights(ix, seed_genes=[])
    w = weights["GENE_A"].weight
    expected = 1.0 * (1 + math.log2(4))
    assert abs(w - expected) < 1e-9, f"Expected {expected}, got {w}"


# ---------------------------------------------------------------------------
# Jaccard coefficient
# ---------------------------------------------------------------------------


def test_jaccard_identical():
    assert jaccard({1, 2, 3}, {1, 2, 3}) == 1.0


def test_jaccard_disjoint():
    assert jaccard({1, 2}, {3, 4}) == 0.0


def test_jaccard_partial():
    j = jaccard({1, 2, 3}, {2, 3, 4})
    assert abs(j - 2 / 4) < 1e-9


def test_jaccard_empty():
    assert jaccard(set(), set()) == 1.0


# ---------------------------------------------------------------------------
# Fisher's exact + scoring pipeline
# ---------------------------------------------------------------------------


def _make_weights(*genes: str) -> dict:
    return {g: GeneWeight(gene=g, weight=1.0) for g in genes}


def test_score_pathways_high_overlap():
    """All query genes in pathway → should yield very low p-value."""
    query = _make_weights("A", "B", "C")
    pathways = {"pw1": ("Pathway 1", ["A", "B", "C", "D", "E"])}
    config = ScoringConfig(min_overlap=2)
    results = score_pathways(query, pathways, background_size=1000, config=config)
    assert len(results) == 1
    assert results[0].pvalue < 0.05


def test_score_pathways_min_overlap_filter():
    """Pathway with only 1 overlapping gene should be filtered."""
    query = _make_weights("A", "B", "C")
    pathways = {"pw1": ("Pathway 1", ["A", "X", "Y"])}
    config = ScoringConfig(min_overlap=2)
    results = score_pathways(query, pathways, background_size=1000, config=config)
    assert len(results) == 0


def test_score_pathways_coverage():
    """Coverage = overlap / pathway_size."""
    query = _make_weights("A", "B", "C", "D")
    pathways = {"pw1": ("Pathway 1", ["A", "B", "C", "D", "E", "F", "G", "H"])}
    config = ScoringConfig(min_overlap=2)
    results = score_pathways(query, pathways, background_size=1000, config=config)
    assert len(results) == 1
    assert abs(results[0].coverage - 4 / 8) < 1e-9


def test_score_pathways_multiple_fdr():
    """BH-FDR should be >= raw p-value."""
    query = _make_weights("A", "B", "C")
    pathways = {
        f"pw{i}": (f"Pathway {i}", ["A", "B", "C"] + [f"X{j}" for j in range(10)])
        for i in range(10)
    }
    config = ScoringConfig(min_overlap=2)
    results = score_pathways(query, pathways, background_size=2000, config=config)
    for r in results:
        assert r.fdr >= r.pvalue - 1e-12


# ---------------------------------------------------------------------------
# Jaccard-based merging
# ---------------------------------------------------------------------------


def _make_result(pid, name, genes, score=0.5):
    return PathwayResult(
        pathway_id=pid,
        pathway_name=name,
        pvalue=0.01,
        fdr=0.01,
        odds_ratio=2.0,
        overlap_count=len(genes),
        pathway_size=len(genes) + 5,
        coverage=len(genes) / (len(genes) + 5),
        evidence_strength=0.5,
        composite_score=score,
        overlapping_genes=genes,
    )


def test_merge_identical_pathways():
    """Two pathways with identical gene sets should merge into one."""
    r1 = _make_result("pw1", "Pathway 1", ["A", "B", "C"], score=0.9)
    r2 = _make_result("pw2", "Pathway 2", ["A", "B", "C"], score=0.7)
    merged = merge_redundant_pathways([r1, r2], threshold=0.5)
    assert len(merged) == 1
    assert merged[0].pathway_id == "pw1"  # higher score wins
    assert "pw2" in merged[0].merged_pathways


def test_merge_disjoint_pathways():
    """Two pathways with no gene overlap should stay separate."""
    r1 = _make_result("pw1", "P1", ["A", "B", "C"])
    r2 = _make_result("pw2", "P2", ["X", "Y", "Z"])
    merged = merge_redundant_pathways([r1, r2], threshold=0.5)
    assert len(merged) == 2


def test_merge_partial_overlap_above_threshold():
    """Jaccard(A B C, A B C D) = 3/4 = 0.75 ≥ 0.5 → merge."""
    r1 = _make_result("pw1", "P1", ["A", "B", "C"], score=0.9)
    r2 = _make_result("pw2", "P2", ["A", "B", "C", "D"], score=0.7)
    merged = merge_redundant_pathways([r1, r2], threshold=0.5)
    assert len(merged) == 1


def test_merge_partial_overlap_below_threshold():
    """Jaccard({A,B},{A,C,D,E}) = 1/5 = 0.2 < 0.5 → separate."""
    r1 = _make_result("pw1", "P1", ["A", "B"])
    r2 = _make_result("pw2", "P2", ["A", "C", "D", "E"])
    merged = merge_redundant_pathways([r1, r2], threshold=0.5)
    assert len(merged) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
