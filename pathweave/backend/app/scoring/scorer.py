"""Gene weighting and pathway scoring for PathWeave."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class RNAInteraction:
    rna_id: str
    rna_type: str          # miRNA | lncRNA | circRNA
    target_gene: str
    evidence: str          # validated | predicted
    source_db: str


@dataclass
class GeneWeight:
    gene: str
    weight: float
    supporting_rnas: List[str] = field(default_factory=list)
    evidence_levels: List[str] = field(default_factory=list)


@dataclass
class PathwayResult:
    pathway_id: str
    pathway_name: str
    pvalue: float
    fdr: float
    odds_ratio: float
    overlap_count: int
    pathway_size: int
    coverage: float               # overlap / pathway_size
    evidence_strength: float      # sum w_g(overlap) / sum w_g(all)
    composite_score: float
    overlapping_genes: List[str]
    inflammation_tag: Optional[str] = None
    merged_pathways: List[str] = field(default_factory=list)
    merged_pathway_names: List[str] = field(default_factory=list)


@dataclass
class ScoringConfig:
    evidence_weights: Dict[str, float] = field(
        default_factory=lambda: {"validated": 1.0, "predicted": 0.4}
    )
    composite_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "fdr": 0.4,
            "odds_ratio": 0.2,
            "coverage": 0.2,
            "evidence_strength": 0.2,
        }
    )
    min_overlap: int = 2
    fdr_threshold: float = 0.05
    jaccard_threshold: float = 0.5


# ---------------------------------------------------------------------------
# Gene weighting
# ---------------------------------------------------------------------------


def compute_gene_weights(
    interactions: List[RNAInteraction],
    seed_genes: List[str],
    evidence_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, GeneWeight]:
    """
    Compute w_g for every gene touched by the RNA interactions.

    w_g = base_evidence × (1 + log2(n_independent_rnas))

    The seed genes themselves get a weight of 1.0 (they are the entry point).
    """
    if evidence_weights is None:
        evidence_weights = {"validated": 1.0, "predicted": 0.4}

    # Collect per-gene info
    gene_rna_map: Dict[str, List[Tuple[str, str]]] = {}  # gene → [(rna_id, evidence)]
    for ix in interactions:
        gene_rna_map.setdefault(ix.target_gene, []).append((ix.rna_id, ix.evidence))

    weights: Dict[str, GeneWeight] = {}

    # Seed genes themselves
    for g in seed_genes:
        weights[g] = GeneWeight(gene=g, weight=1.0, supporting_rnas=[], evidence_levels=[])

    # Target genes
    for gene, rna_ev_list in gene_rna_map.items():
        # Best evidence across supporting RNAs
        ev_values = [evidence_weights.get(ev, 0.4) for _, ev in rna_ev_list]
        base = max(ev_values)
        n_rnas = len(set(rna for rna, _ in rna_ev_list))  # unique RNA IDs
        w = base * (1 + math.log2(max(n_rnas, 1)))

        rna_ids = [r for r, _ in rna_ev_list]
        evs = [e for _, e in rna_ev_list]

        if gene in weights:
            # Seed gene that also appears as target – boost weight
            weights[gene].weight = max(weights[gene].weight, w)
            weights[gene].supporting_rnas.extend(rna_ids)
            weights[gene].evidence_levels.extend(evs)
        else:
            weights[gene] = GeneWeight(
                gene=gene,
                weight=w,
                supporting_rnas=rna_ids,
                evidence_levels=evs,
            )

    return weights


# ---------------------------------------------------------------------------
# Pathway scoring
# ---------------------------------------------------------------------------


def _normalize_series(s: pd.Series) -> pd.Series:
    """Min-max normalise to [0, 1]; handle constant series."""
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(0.5, index=s.index)
    return (s - mn) / (mx - mn)


def score_pathways(
    weighted_genes: Dict[str, GeneWeight],
    pathway_gene_sets: Dict[str, Tuple[str, List[str]]],  # id → (name, [genes])
    background_size: int,
    config: ScoringConfig,
    seed_genes: Optional[List[str]] = None,
) -> List[PathwayResult]:
    """
    Run Fisher's exact test per pathway and compute composite scores.

    Parameters
    ----------
    weighted_genes   : gene → GeneWeight
    pathway_gene_sets: kegg_id → (name, gene_list)
    background_size  : total number of genes in the organism's KEGG universe
    config           : ScoringConfig
    seed_genes       : optional – used to compute evidence strength denominator
    """
    query_genes = set(weighted_genes.keys())
    total_w = sum(gw.weight for gw in weighted_genes.values())

    rows = []
    for pid, (pname, pgenes) in pathway_gene_sets.items():
        pgenes_set = set(pgenes)
        overlap = query_genes & pgenes_set
        if len(overlap) < config.min_overlap:
            continue

        # Contingency table for Fisher's exact test
        a = len(overlap)                          # in query AND pathway
        b = len(query_genes) - a                  # in query, NOT pathway
        c = len(pgenes_set) - a                   # NOT in query, in pathway
        d = background_size - a - b - c           # neither
        d = max(d, 0)

        _, pval = fisher_exact([[a, b], [c, d]], alternative="greater")

        or_val = ((a * max(d, 1)) / (max(b, 1) * max(c, 1)))
        coverage = a / len(pgenes_set) if pgenes_set else 0.0

        # Evidence strength: sum of w_g over overlap / total
        ev_strength = sum(weighted_genes[g].weight for g in overlap if g in weighted_genes)
        ev_strength_norm = ev_strength / total_w if total_w > 0 else 0.0

        rows.append(
            dict(
                pathway_id=pid,
                pathway_name=pname,
                pvalue=pval,
                odds_ratio=or_val,
                overlap_count=a,
                pathway_size=len(pgenes_set),
                coverage=coverage,
                evidence_strength=ev_strength_norm,
                overlapping_genes=sorted(overlap),
            )
        )

    if not rows:
        return []

    df = pd.DataFrame(rows)

    # BH-FDR correction
    reject, fdr_vals, _, _ = multipletests(df["pvalue"].values, method="fdr_bh")
    df["fdr"] = fdr_vals

    # Composite score = weighted normalised components
    w = config.composite_weights
    neg_log_fdr = _normalize_series(-np.log10(df["fdr"].clip(lower=1e-300)))
    log2_or = _normalize_series(np.log2(df["odds_ratio"].clip(lower=1e-6)))
    cov_norm = _normalize_series(df["coverage"])
    ev_norm = _normalize_series(df["evidence_strength"])

    df["composite_score"] = (
        w.get("fdr", 0.4) * neg_log_fdr
        + w.get("odds_ratio", 0.2) * log2_or
        + w.get("coverage", 0.2) * cov_norm
        + w.get("evidence_strength", 0.2) * ev_norm
    )

    df.sort_values("composite_score", ascending=False, inplace=True)

    results = []
    for _, row in df.iterrows():
        results.append(
            PathwayResult(
                pathway_id=row["pathway_id"],
                pathway_name=row["pathway_name"],
                pvalue=row["pvalue"],
                fdr=row["fdr"],
                odds_ratio=row["odds_ratio"],
                overlap_count=int(row["overlap_count"]),
                pathway_size=int(row["pathway_size"]),
                coverage=row["coverage"],
                evidence_strength=row["evidence_strength"],
                composite_score=row["composite_score"],
                overlapping_genes=row["overlapping_genes"],
            )
        )
    return results


# ---------------------------------------------------------------------------
# Jaccard-based redundancy clustering
# ---------------------------------------------------------------------------


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = len(a | b)
    return len(a & b) / union if union > 0 else 0.0


def merge_redundant_pathways(
    results: List[PathwayResult],
    threshold: float = 0.5,
) -> List[PathwayResult]:
    """
    Cluster pathways whose gene-overlap Jaccard ≥ threshold.
    Keep the representative with the highest composite score.
    """
    if not results:
        return results

    gene_sets = [set(r.overlapping_genes) for r in results]
    n = len(results)
    assigned = [-1] * n
    cluster_id = 0

    for i in range(n):
        if assigned[i] != -1:
            continue
        assigned[i] = cluster_id
        for j in range(i + 1, n):
            if assigned[j] == -1 and jaccard(gene_sets[i], gene_sets[j]) >= threshold:
                assigned[j] = cluster_id
        cluster_id += 1

    # Build clusters
    clusters: Dict[int, List[int]] = {}
    for idx, cid in enumerate(assigned):
        clusters.setdefault(cid, []).append(idx)

    merged: List[PathwayResult] = []
    for cid, members in clusters.items():
        # Representative = highest composite score
        rep_idx = max(members, key=lambda i: results[i].composite_score)
        rep = results[rep_idx]
        merged_ids = [results[i].pathway_id for i in members if i != rep_idx]
        merged_names = [results[i].pathway_name for i in members if i != rep_idx]
        rep.merged_pathways = merged_ids
        rep.merged_pathway_names = merged_names
        merged.append(rep)

    merged.sort(key=lambda r: r.composite_score, reverse=True)
    return merged
