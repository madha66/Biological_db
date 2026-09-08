"""
Ranking service — re-exports ranking functions from the analysis layer.

Kept as a thin service wrapper for organizational symmetry with other services.
The actual ranking logic lives in app.analysis.ranking.
"""

from app.analysis.ranking import (
    compute_pathway_score,
    compute_ranking_score,
    rank_pathways,
    RankedPathway,
)

__all__ = [
    "compute_pathway_score",
    "compute_ranking_score",
    "rank_pathways",
    "RankedPathway",
]
