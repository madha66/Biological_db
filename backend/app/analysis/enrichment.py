"""
Statistical enrichment analysis: Fisher's exact test and FDR correction.

This module implements the core statistical methods for pathway enrichment:
1. Construction of the 2×2 contingency table for each pathway.
2. Fisher's exact test (one-sided, testing for overrepresentation).
3. Benjamini–Hochberg FDR correction across all tested pathways.
"""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)


@dataclass
class ContingencyTable:
    """
    2×2 contingency table for Fisher's exact test.

                      In pathway    Not in pathway
    Input genes          a               b
    Background genes     c               d

    Where:
      a = input genes mapped to this pathway
      b = input genes NOT mapped to this pathway
      c = background genes (excl. input) mapped to this pathway
      d = background genes (excl. input) NOT mapped to this pathway
    """
    a: int  # input genes in pathway
    b: int  # input genes not in pathway
    c: int  # background genes in pathway (excluding input)
    d: int  # background genes not in pathway (excluding input)


@dataclass
class EnrichmentResult:
    """Result of enrichment analysis for a single pathway."""
    pathway_id: str
    input_gene_count: int  # = a
    total_pathway_genes: int  # genes in this pathway in KEGG
    p_value: float
    odds_ratio: float


def build_contingency_table(
    input_genes_in_pathway: int,
    total_valid_input_genes: int,
    total_pathway_genes: int,
    universe_size: int,
) -> ContingencyTable:
    """
    Construct the 2×2 contingency table for Fisher's exact test.

    Args:
        input_genes_in_pathway: Number of user's valid input genes found in this pathway (a).
        total_valid_input_genes: Total number of valid input genes (a + b).
        total_pathway_genes: Total genes annotated to this pathway in KEGG (a + c).
        universe_size: Total genes in the background universe for this organism.

    Returns:
        ContingencyTable with a, b, c, d values.
    """
    a = input_genes_in_pathway
    b = total_valid_input_genes - a
    c = total_pathway_genes - a
    d = universe_size - total_valid_input_genes - c

    # Ensure non-negative values (defensive; shouldn't happen with correct data)
    c = max(c, 0)
    d = max(d, 0)

    return ContingencyTable(a=a, b=b, c=c, d=d)


def fisher_exact_test(table: ContingencyTable) -> tuple[float, float]:
    """
    Perform Fisher's exact test for overrepresentation (one-sided, greater).

    Args:
        table: The 2×2 contingency table.

    Returns:
        Tuple of (odds_ratio, p_value).
    """
    contingency = [[table.a, table.b], [table.c, table.d]]
    odds_ratio, p_value = fisher_exact(contingency, alternative="greater")
    return odds_ratio, p_value


def compute_enrichment(
    pathway_gene_counts: dict[str, int],
    pathway_total_genes: dict[str, int],
    total_valid_genes: int,
    universe_size: int,
) -> list[EnrichmentResult]:
    """
    Compute Fisher's exact test for all pathways.

    Args:
        pathway_gene_counts: {pathway_id: number of input genes in this pathway}
        pathway_total_genes: {pathway_id: total genes in this pathway in KEGG}
        total_valid_genes: Total valid input genes.
        universe_size: Background universe size.

    Returns:
        List of EnrichmentResult, one per pathway, with raw p-values.
    """
    results: list[EnrichmentResult] = []

    for pathway_id, input_count in pathway_gene_counts.items():
        total_in_pathway = pathway_total_genes.get(pathway_id, input_count)
        # Ensure total_in_pathway >= input_count
        total_in_pathway = max(total_in_pathway, input_count)

        table = build_contingency_table(
            input_genes_in_pathway=input_count,
            total_valid_input_genes=total_valid_genes,
            total_pathway_genes=total_in_pathway,
            universe_size=universe_size,
        )

        odds_ratio, p_value = fisher_exact_test(table)

        results.append(EnrichmentResult(
            pathway_id=pathway_id,
            input_gene_count=input_count,
            total_pathway_genes=total_in_pathway,
            p_value=p_value,
            odds_ratio=odds_ratio,
        ))

        logger.debug(
            "Pathway %s: table=[%d,%d,%d,%d], OR=%.4f, p=%.6e",
            pathway_id, table.a, table.b, table.c, table.d, odds_ratio, p_value,
        )

    logger.info("Enrichment analysis complete for %d pathways", len(results))
    return results


def apply_fdr_correction(p_values: list[float]) -> list[float]:
    """
    Apply Benjamini–Hochberg FDR correction to a list of p-values.

    This controls the expected proportion of false discoveries among
    pathways called significant when testing many pathways simultaneously.

    Args:
        p_values: List of raw p-values.

    Returns:
        List of adjusted p-values (same order as input).
    """
    if not p_values:
        return []

    if len(p_values) == 1:
        return list(p_values)

    # statsmodels.multipletests returns: (reject, pvals_corrected, alphac_sidak, alphac_bonf)
    _, adjusted, _, _ = multipletests(
        np.array(p_values),
        method="fdr_bh",
        is_sorted=False,
    )

    adjusted_list = [float(p) for p in adjusted]
    logger.info(
        "FDR correction applied to %d p-values (min raw=%.2e, min adj=%.2e)",
        len(p_values),
        min(p_values),
        min(adjusted_list),
    )
    return adjusted_list
