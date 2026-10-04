"""PathWeave scoring package."""
from .scorer import (
    GeneWeight,
    PathwayResult,
    RNAInteraction,
    ScoringConfig,
    compute_gene_weights,
    merge_redundant_pathways,
    score_pathways,
    jaccard,
)
from .analysis import (
    compute_empirical_pvalue,
    generate_plain_summary,
    load_inflammation_tags,
    run_null_model,
    summarise_inflammation,
    tag_pathways,
)

__all__ = [
    "GeneWeight",
    "PathwayResult",
    "RNAInteraction",
    "ScoringConfig",
    "compute_gene_weights",
    "merge_redundant_pathways",
    "score_pathways",
    "jaccard",
    "compute_empirical_pvalue",
    "generate_plain_summary",
    "load_inflammation_tags",
    "run_null_model",
    "summarise_inflammation",
    "tag_pathways",
]
