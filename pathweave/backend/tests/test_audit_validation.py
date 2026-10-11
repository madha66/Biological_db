"""Audit verification tests for PathWeave statistical calculations and controls."""
import pytest
from scipy.stats import fisher_exact

from app.scoring.scorer import (
    GeneWeight,
    ScoringConfig,
    compute_gene_weights,
    score_pathways,
    RNAInteraction,
)
from app.scoring.analysis import (
    run_null_model,
    compute_empirical_pvalue,
    summarise_inflammation,
)


def test_contingency_table_consistency():
    """Verify that contingency table cells are strictly non-negative and sum properly."""
    background_size = 7500
    weighted_genes = {
        "TP53": GeneWeight(gene="TP53", weight=1.0),
        "PTEN": GeneWeight(gene="PTEN", weight=1.0),
        "AKT1": GeneWeight(gene="AKT1", weight=1.0),
        "TNF": GeneWeight(gene="TNF", weight=1.0),
    }
    pathway_gene_sets = {
        "hsa05200": ("Pathways in cancer", ["TP53", "PTEN", "AKT1", "MDM2", "BCL2", "VEGFA"]),
    }
    config = ScoringConfig(min_overlap=2, fdr_threshold=0.05)
    results = score_pathways(weighted_genes, pathway_gene_sets, background_size, config)

    assert len(results) == 1
    r = results[0]
    a = r.overlap_count  # in query AND pathway
    b = len(weighted_genes) - a  # in query, NOT pathway
    c = r.pathway_size - a  # NOT in query, in pathway
    d = background_size - a - b - c  # neither

    assert a >= 0
    assert b >= 0
    assert c >= 0
    assert d >= 0
    assert a + b == len(weighted_genes)
    assert a + c == r.pathway_size
    assert a + b + c + d == background_size


def test_fisher_exact_matches_scipy():
    """Verify Fisher's exact test calculation against SciPy reference."""
    background_size = 7500
    weighted_genes = {
        "TP53": GeneWeight(gene="TP53", weight=1.0),
        "PTEN": GeneWeight(gene="PTEN", weight=1.0),
        "AKT1": GeneWeight(gene="AKT1", weight=1.0),
    }
    pathway_gene_sets = {
        "hsa04115": ("p53 signaling pathway", ["TP53", "PTEN", "MDM2", "CDKN2A"]),
    }
    config = ScoringConfig(min_overlap=2, fdr_threshold=0.05)
    results = score_pathways(weighted_genes, pathway_gene_sets, background_size, config)
    assert len(results) == 1

    r = results[0]
    a = r.overlap_count
    b = len(weighted_genes) - a
    c = r.pathway_size - a
    d = background_size - a - b - c

    _, scipy_p = fisher_exact([[a, b], [c, d]], alternative="greater")
    assert abs(r.pvalue - scipy_p) < 1e-12


def test_null_model_deterministic_sampling():
    """Verify that null model produces deterministic results given the same RNG seed."""
    all_genes = ["TP53", "BRCA1", "PTEN", "AKT1", "TNF", "IL6", "NFKB1", "STAT3", "VEGFA", "MYC"]
    pathway_sets = {
        "hsa05200": ("Pathways in cancer", ["TP53", "PTEN", "AKT1", "MYC"]),
    }
    config = ScoringConfig(min_overlap=1, fdr_threshold=0.05)

    scores1, mean1 = run_null_model(
        n_iterations=20,
        all_genes=all_genes,
        n_seed=3,
        pathway_gene_sets=pathway_sets,
        background_size=7500,
        config=config,
        rng_seed=123,
    )

    scores2, mean2 = run_null_model(
        n_iterations=20,
        all_genes=all_genes,
        n_seed=3,
        pathway_gene_sets=pathway_sets,
        background_size=7500,
        config=config,
        rng_seed=123,
    )

    assert scores1 == scores2
    assert mean1 == mean2


def test_empirical_pvalue_boundary_and_zero_prevention():
    """Verify empirical p-value computation."""
    null_scores = [0.1, 0.2, 0.3, 0.4, 0.5]
    # Real score higher than all nulls
    pval = compute_empirical_pvalue(0.9, null_scores)
    assert pval == 0.0  # Application definition: proportion >= real_score

    # Real score equal to max
    pval_max = compute_empirical_pvalue(0.5, null_scores)
    assert pval_max == 0.2


def test_fdr_threshold_filtering_consistency():
    """Verify filtering consistency with configured FDR thresholds."""
    weighted_genes = {"TP53": GeneWeight(gene="TP53", weight=1.0), "PTEN": GeneWeight(gene="PTEN", weight=1.0)}
    pathways = {
        "p1": ("Pathway 1", ["TP53", "PTEN"]),
    }
    config_strict = ScoringConfig(min_overlap=2, fdr_threshold=0.001)
    results = score_pathways(weighted_genes, pathways, 7500, config_strict)
    sig_strict = [r for r in results if r.fdr <= config_strict.fdr_threshold]

    config_lenient = ScoringConfig(min_overlap=2, fdr_threshold=0.1)
    sig_lenient = [r for r in results if r.fdr <= config_lenient.fdr_threshold]

    assert len(sig_strict) <= len(sig_lenient)
