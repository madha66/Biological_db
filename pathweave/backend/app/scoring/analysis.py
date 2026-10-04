"""Null-model control and inflammation classification for PathWeave."""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .scorer import (
    GeneWeight,
    PathwayResult,
    ScoringConfig,
    compute_gene_weights,
    merge_redundant_pathways,
    score_pathways,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inflammation tagging
# ---------------------------------------------------------------------------

def _resolve_inflammation_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / "data" / "inflammation_tags.json",
        Path(__file__).resolve().parents[2] / "data" / "inflammation_tags.json",
        Path(__file__).resolve().parents[4] / "data" / "inflammation_tags.json",
        Path.cwd() / "data" / "inflammation_tags.json",
        Path.cwd().parent / "data" / "inflammation_tags.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path(__file__).resolve().parents[3] / "data" / "inflammation_tags.json"

_DEFAULT_TAG_PATH = _resolve_inflammation_path()


def load_inflammation_tags(path: Optional[Path] = None) -> dict:
    tag_path = path or _DEFAULT_TAG_PATH
    try:
        with open(tag_path) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("inflammation_tags.json not found at %s", tag_path)
        return {}


def tag_pathway(
    pathway_id: str,
    pathway_name: str,
    tags: dict,
) -> Optional[str]:
    """Return the inflammation category key that best matches a pathway."""
    pid_lower = pathway_id.lower()
    name_lower = pathway_name.lower()

    for category, info in tags.items():
        if pid_lower in [p.lower() for p in info.get("pathway_ids", [])]:
            return category
        for kw in info.get("keywords", []):
            if kw.lower() in name_lower:
                return category
    return None


def tag_pathways(results: List[PathwayResult], tags: dict) -> List[PathwayResult]:
    for r in results:
        r.inflammation_tag = tag_pathway(r.pathway_id, r.pathway_name, tags)
    return results


# ---------------------------------------------------------------------------
# Null model
# ---------------------------------------------------------------------------


def run_null_model(
    n_iterations: int,
    all_genes: List[str],
    n_seed: int,
    pathway_gene_sets: Dict[str, Tuple[str, List[str]]],
    background_size: int,
    config: ScoringConfig,
    rng_seed: int = 42,
) -> Tuple[List[float], float]:
    """
    Run N random seeds of size n_seed through the same scoring pipeline.
    Returns (null_top_scores, mean_null_score).
    """
    rng = random.Random(rng_seed)
    null_scores: List[float] = []

    for _ in range(n_iterations):
        rand_genes = rng.sample(all_genes, min(n_seed, len(all_genes)))
        # Give random genes uniform weight 1.0
        fake_weights = {g: GeneWeight(gene=g, weight=1.0) for g in rand_genes}
        results = score_pathways(fake_weights, pathway_gene_sets, background_size, config)
        if results:
            null_scores.append(results[0].composite_score)
        else:
            null_scores.append(0.0)

    mean_null = float(np.mean(null_scores)) if null_scores else 0.0
    return null_scores, mean_null


def compute_empirical_pvalue(real_score: float, null_scores: List[float]) -> float:
    """Proportion of null runs that scored ≥ real_score."""
    if not null_scores:
        return 1.0
    return sum(s >= real_score for s in null_scores) / len(null_scores)


# ---------------------------------------------------------------------------
# Inflammation source summary
# ---------------------------------------------------------------------------


def summarise_inflammation(
    results: List[PathwayResult],
) -> Dict[str, int]:
    """Count pathways per inflammation trigger category."""
    counts: Dict[str, int] = {}
    for r in results:
        if r.fdr <= 0.05:
            tag = r.inflammation_tag or "unclassified"
            counts[tag] = counts.get(tag, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Plain-language summary
# ---------------------------------------------------------------------------


def generate_plain_summary(
    seed_genes: List[str],
    organism: str,
    results: List[PathwayResult],
    inflammation_counts: Dict[str, int],
    n_genes: int,
    n_rnas: int,
) -> str:
    """Generate a human-readable one-paragraph summary."""
    if not results:
        return (
            f"No significant pathways were found for {', '.join(seed_genes)}. "
            "Try increasing the gene list or lowering the FDR threshold."
        )

    top = results[:3]
    top_names = " and ".join(f"**{r.pathway_name}**" for r in top)

    dominant_tag = (
        max(inflammation_counts, key=inflammation_counts.get)
        if inflammation_counts
        else "unclassified"
    )
    tag_labels = {
        "infection": "infection-driven",
        "autoimmunity": "autoimmune",
        "metabolic": "metabolically driven",
        "cancer": "cancer-associated",
        "tissue_damage": "tissue-damage",
        "unclassified": "mixed-category",
    }
    tag_label = tag_labels.get(dominant_tag, dominant_tag)

    seed_str = ", ".join(seed_genes[:3])
    return (
        f"The RNA neighborhood of **{seed_str}** spans **{n_genes} genes** "
        f"connected through **{n_rnas} regulatory RNAs**. "
        f"Pathway enrichment highlights {top_names} as the most strongly "
        f"associated pathways. "
        f"The dominant inflammation signal is **{tag_label}**, "
        f"with {len(results)} pathways reaching FDR significance."
    )
