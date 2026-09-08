"""
Pathway ranking: computes the final ranking score and sorts pathways.

Ranking Formula:
    Ranking Score = Pathway Score × -log10(Adjusted p-value)

Where:
    Pathway Score = (Number of input genes mapped to pathway) / (Total valid input genes)
    Adjusted p-value is the Benjamini–Hochberg FDR-corrected p-value.

The adjusted p-value is floored at PVALUE_EPSILON (1e-300) to avoid -log10(0).

This formula balances:
- Representation (how many of the user's genes overlap with a pathway)
- Statistical significance (whether that overlap is more than expected by chance)

A pathway with high gene overlap but low significance, or low overlap but high
significance, will rank lower than a pathway that is both well-represented AND
statistically enriched.

See docs/RANKING_ALGORITHM.md for worked numeric examples.
"""

import math
import logging
from dataclasses import dataclass

from app.config import PVALUE_EPSILON

logger = logging.getLogger(__name__)


@dataclass
class RankedPathway:
    """A pathway with all computed scores, ready for ranking."""
    pathway_id: str
    pathway_name: str
    input_gene_count: int
    total_pathway_genes: int
    pathway_score: float
    p_value: float
    adjusted_p_value: float
    ranking_score: float
    contributing_genes: list[str]
    rank: int = 0  # Set after sorting


def compute_pathway_score(input_gene_count: int, total_valid_genes: int) -> float:
    """
    Compute the pathway representation score.

    Pathway Score = input_gene_count / total_valid_genes

    This measures how much of the user's gene set is captured by this pathway.
    """
    if total_valid_genes == 0:
        return 0.0
    return input_gene_count / total_valid_genes


def compute_ranking_score(pathway_score: float, adjusted_p_value: float) -> float:
    """
    Compute the final ranking score for a pathway.

    Ranking Score = Pathway Score × -log10(Adjusted p-value)

    The adjusted p-value is floored at PVALUE_EPSILON to avoid log(0).
    For a very significant pathway (adj_p ≈ 1e-10) with high representation (score ≈ 0.5):
        Ranking Score = 0.5 × -log10(1e-10) = 0.5 × 10 = 5.0

    For a non-significant pathway (adj_p ≈ 0.5) with moderate representation (score ≈ 0.3):
        Ranking Score = 0.3 × -log10(0.5) = 0.3 × 0.301 = 0.090

    Args:
        pathway_score: The representation score (0 to 1).
        adjusted_p_value: The BH-FDR corrected p-value.

    Returns:
        The ranking score (higher = more important).
    """
    # Floor the p-value to avoid -log10(0)
    clamped_p = max(adjusted_p_value, PVALUE_EPSILON)
    neg_log_p = -math.log10(clamped_p)
    score = pathway_score * neg_log_p
    return round(score, 6)


def rank_pathways(
    pathway_to_genes: dict[str, list[str]],
    pathway_names: dict[str, str],
    pathway_total_genes: dict[str, int],
    p_values: dict[str, float],
    adjusted_p_values: dict[str, float],
    total_valid_genes: int,
) -> list[RankedPathway]:
    """
    Compute scores and rank all pathways.

    Args:
        pathway_to_genes: {pathway_id: [contributing_gene_symbols]}
        pathway_names: {pathway_id: human-readable name}
        pathway_total_genes: {pathway_id: total genes in pathway in KEGG}
        p_values: {pathway_id: raw Fisher's exact p-value}
        adjusted_p_values: {pathway_id: BH-FDR adjusted p-value}
        total_valid_genes: Total number of valid input genes.

    Returns:
        List of RankedPathway sorted by ranking_score descending, with rank assigned.
    """
    ranked: list[RankedPathway] = []

    for pid in pathway_to_genes:
        genes = pathway_to_genes[pid]
        input_count = len(genes)
        pw_score = compute_pathway_score(input_count, total_valid_genes)
        raw_p = p_values.get(pid, 1.0)
        adj_p = adjusted_p_values.get(pid, 1.0)
        r_score = compute_ranking_score(pw_score, adj_p)

        ranked.append(RankedPathway(
            pathway_id=pid,
            pathway_name=pathway_names.get(pid, pid),
            input_gene_count=input_count,
            total_pathway_genes=pathway_total_genes.get(pid, 0),
            pathway_score=round(pw_score, 6),
            p_value=raw_p,
            adjusted_p_value=adj_p,
            ranking_score=r_score,
            contributing_genes=genes,
        ))

    # Sort by ranking score descending; ties broken by input_gene_count descending
    ranked.sort(key=lambda r: (-r.ranking_score, -r.input_gene_count))

    # Assign ranks
    for i, pathway in enumerate(ranked, start=1):
        pathway.rank = i

    logger.info(
        "Ranked %d pathways. Top pathway: %s (score=%.4f)",
        len(ranked),
        ranked[0].pathway_name if ranked else "N/A",
        ranked[0].ranking_score if ranked else 0,
    )
    return ranked
