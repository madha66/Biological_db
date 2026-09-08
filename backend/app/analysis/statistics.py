"""
Statistics utilities — a thin wrapper module for clarity.

In KEGGPathRank, the heavy statistical work lives in enrichment.py.
This module exposes convenience imports and any additional statistical helpers.
"""

from app.analysis.enrichment import (
    build_contingency_table,
    fisher_exact_test,
    compute_enrichment,
    apply_fdr_correction,
    ContingencyTable,
    EnrichmentResult,
)

__all__ = [
    "build_contingency_table",
    "fisher_exact_test",
    "compute_enrichment",
    "apply_fdr_correction",
    "ContingencyTable",
    "EnrichmentResult",
]
