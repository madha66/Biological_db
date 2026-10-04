"""Core analysis pipeline that ties together all PathWeave components."""
from __future__ import annotations

import asyncio
import io
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Callable, Dict, List, Optional

import httpx
import numpy as np

from app.api.models import (
    AnalysisResult,
    AnalyzeRequest,
    GraphEdge,
    GeneNode,
    InflammationSummary,
    JobProgress,
    NullModelResult,
    PathwayNode,
    PathwayResultModel,
    RegulationGraph,
    RNANode,
    SummaryStats,
)
from app.kegg.client import get_background_size, get_full_pathway_data
from app.providers import CSVInteractionProvider
from app.scoring import (
    ScoringConfig,
    compute_gene_weights,
    compute_empirical_pvalue,
    generate_plain_summary,
    load_inflammation_tags,
    merge_redundant_pathways,
    run_null_model,
    score_pathways,
    summarise_inflammation,
    tag_pathways,
)

logger = logging.getLogger(__name__)

def _resolve_data_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / "data",
        Path(__file__).resolve().parents[2] / "data",
        Path(__file__).resolve().parents[4] / "data",
        Path.cwd() / "data",
        Path.cwd().parent / "data",
    ]
    for c in candidates:
        if (c / "sample_interactions.csv").exists():
            return c
    return Path(__file__).resolve().parents[3] / "data"

DATA_DIR = _resolve_data_dir()
SAMPLE_CSV = DATA_DIR / "sample_interactions.csv"
INFLAMMATION_JSON = DATA_DIR / "inflammation_tags.json"

# Shared job store (in-memory; replace with Redis for prod)
_jobs: Dict[str, JobProgress] = {}

# Cached provider
_provider: Optional[CSVInteractionProvider] = None


def get_provider() -> CSVInteractionProvider:
    global _provider
    if _provider is None:
        _provider = CSVInteractionProvider(SAMPLE_CSV)
    return _provider


def get_job(job_id: str) -> Optional[JobProgress]:
    return _jobs.get(job_id)


def list_jobs() -> List[JobProgress]:
    return list(_jobs.values())


async def run_analysis(
    request: AnalyzeRequest,
    job_id: str,
    progress_cb: Optional[Callable] = None,
) -> None:
    """Full async analysis pipeline with progress updates."""
    start_time = time.monotonic()

    def update(stage: str, pct: int) -> None:
        if job_id in _jobs:
            _jobs[job_id].stage = stage
            _jobs[job_id].percent = pct
            _jobs[job_id].status = "running"

    try:
        # Resolve seed genes
        seed_genes: List[str] = []
        if request.seed_gene:
            seed_genes = [request.seed_gene.strip().upper()]
        if request.gene_list:
            seed_genes += [g.strip().upper() for g in request.gene_list if g.strip()]
        seed_genes = list(dict.fromkeys(seed_genes))  # deduplicate

        if not seed_genes:
            raise ValueError("At least one seed gene is required.")

        org = request.organism.value
        opts = request.options
        rna_types = [t.value for t in opts.include_types]

        config = ScoringConfig(
            evidence_weights=opts.evidence_weights,
            composite_weights=opts.composite_weights,
            min_overlap=opts.min_overlap,
            fdr_threshold=opts.fdr_threshold,
        )

        # ── Stage 1: Expand RNA network ──────────────────────────────────────
        update("Expanding RNA network…", 10)
        await asyncio.sleep(0)  # yield to event loop

        provider = get_provider()
        interactions = provider.expand_neighborhood(seed_genes, rna_types=rna_types)

        # ── Stage 2: Weight genes ─────────────────────────────────────────────
        update("Weighting genes…", 25)
        await asyncio.sleep(0)

        weighted_genes = compute_gene_weights(interactions, seed_genes, opts.evidence_weights)

        # ── Stage 3: Map KEGG pathways ────────────────────────────────────────
        update("Mapping KEGG pathways…", 40)
        await asyncio.sleep(0)

        if opts.demo_mode:
            from app.kegg.client import _DEMO_PATHWAYS
            pathway_data = _DEMO_PATHWAYS.get(org, _DEMO_PATHWAYS["hsa"])
        else:
            async with httpx.AsyncClient() as client:
                pathway_data = await get_full_pathway_data(org, client)

        background_size = get_background_size(org)

        # ── Stage 4: Enrichment & FDR ─────────────────────────────────────────
        update("Enrichment & FDR correction…", 55)
        await asyncio.sleep(0)

        results = score_pathways(weighted_genes, pathway_data, background_size, config)

        # Tag inflammation
        tags = load_inflammation_tags(INFLAMMATION_JSON)
        results = tag_pathways(results, tags)

        # Merge redundant
        results = merge_redundant_pathways(results, threshold=0.5)

        # Filter by FDR
        sig_results = [r for r in results if r.fdr <= opts.fdr_threshold]

        # ── Stage 5: Null model ───────────────────────────────────────────────
        update("Running null-model control…", 70)
        await asyncio.sleep(0)

        all_genes = list({g for genes in pathway_data.values() for g in genes[1]})

        null_scores, mean_null = run_null_model(
            n_iterations=opts.null_iterations,
            all_genes=all_genes,
            n_seed=len(seed_genes),
            pathway_gene_sets=pathway_data,
            background_size=background_size,
            config=config,
        )

        real_top_score = results[0].composite_score if results else 0.0
        emp_pval = compute_empirical_pvalue(real_top_score, null_scores)
        null_percentile = float(np.mean([s <= real_top_score for s in null_scores])) * 100

        null_result = NullModelResult(
            null_scores=null_scores[:200],  # cap for transport
            mean_null=mean_null,
            real_score=real_top_score,
            empirical_pvalue=emp_pval,
            percentile=null_percentile,
        )

        # ── Stage 6: Without-seed comparison ─────────────────────────────────
        update("Classifying inflammation…", 85)
        await asyncio.sleep(0)

        # Run without seed genes
        no_seed_interactions = [ix for ix in interactions if ix.target_gene not in set(seed_genes)]
        no_seed_weights = compute_gene_weights(no_seed_interactions, [], opts.evidence_weights)
        no_seed_results_raw = score_pathways(no_seed_weights, pathway_data, background_size, config)
        no_seed_results = tag_pathways(no_seed_results_raw, tags)

        # ── Stage 7: Build response ───────────────────────────────────────────
        update("Building results…", 95)
        await asyncio.sleep(0)

        inflammation_counts = summarise_inflammation(sig_results)
        infl_summary = _build_inflammation_summary(sig_results, tags, inflammation_counts)

        plain = generate_plain_summary(
            seed_genes=seed_genes,
            organism=org,
            results=sig_results,
            inflammation_counts=inflammation_counts,
            n_genes=len(weighted_genes),
            n_rnas=len({ix.rna_id for ix in interactions}),
        )

        graph = _build_graph(seed_genes, weighted_genes, interactions, results[:15])

        ranked = [
            PathwayResultModel(
                rank=i + 1,
                pathway_id=r.pathway_id,
                pathway_name=r.pathway_name,
                composite_score=round(r.composite_score, 4),
                pvalue=r.pvalue,
                fdr=r.fdr,
                odds_ratio=round(r.odds_ratio, 3),
                overlap_count=r.overlap_count,
                pathway_size=r.pathway_size,
                coverage=round(r.coverage, 4),
                evidence_strength=round(r.evidence_strength, 4),
                overlapping_genes=r.overlapping_genes,
                inflammation_tag=r.inflammation_tag,
                merged_pathways=r.merged_pathways,
                merged_pathway_names=r.merged_pathway_names,
            )
            for i, r in enumerate(results)
        ]

        without_seed = [
            PathwayResultModel(
                rank=i + 1,
                pathway_id=r.pathway_id,
                pathway_name=r.pathway_name,
                composite_score=round(r.composite_score, 4),
                pvalue=r.pvalue,
                fdr=r.fdr,
                odds_ratio=round(r.odds_ratio, 3),
                overlap_count=r.overlap_count,
                pathway_size=r.pathway_size,
                coverage=round(r.coverage, 4),
                evidence_strength=round(r.evidence_strength, 4),
                overlapping_genes=r.overlapping_genes,
                inflammation_tag=r.inflammation_tag,
                merged_pathways=[],
                merged_pathway_names=[],
            )
            for i, r in enumerate(no_seed_results[:10])
        ]

        rna_type_counts = {
            "miRNA": len({ix.rna_id for ix in interactions if ix.rna_type == "miRNA"}),
            "lncRNA": len({ix.rna_id for ix in interactions if ix.rna_type == "lncRNA"}),
            "circRNA": len({ix.rna_id for ix in interactions if ix.rna_type == "circRNA"}),
        }

        run_time = time.monotonic() - start_time
        summary = SummaryStats(
            n_seed_genes=len(seed_genes),
            n_neighborhood_genes=len(weighted_genes),
            n_mirna=rna_type_counts["miRNA"],
            n_lncrna=rna_type_counts["lncRNA"],
            n_circrna=rna_type_counts["circRNA"],
            n_total_rnas=len({ix.rna_id for ix in interactions}),
            n_pathways_tested=len(results),
            n_pathways_significant=len(sig_results),
            top_pathway=results[0].pathway_name if results else None,
            run_time_seconds=round(run_time, 2),
        )

        analysis_result = AnalysisResult(
            job_id=job_id,
            organism=org,
            seed_genes=seed_genes,
            summary=summary,
            plain_summary=plain,
            ranked_pathways=ranked,
            graph=graph,
            null_model=null_result,
            inflammation_by_source=infl_summary,
            without_seed_pathways=without_seed,
        )

        _jobs[job_id].status = "done"
        _jobs[job_id].percent = 100
        _jobs[job_id].stage = "Complete"
        _jobs[job_id].result = analysis_result

    except Exception as exc:
        logger.exception("Analysis failed for job %s", job_id)
        if job_id in _jobs:
            _jobs[job_id].status = "error"
            _jobs[job_id].error = str(exc)


def _build_graph(
    seed_genes,
    weighted_genes,
    interactions,
    top_pathways,
) -> RegulationGraph:
    seed_set = set(seed_genes)
    seen_genes = set()
    gene_nodes = []
    rna_nodes = []
    edges = []

    rna_map: Dict[str, set] = {}
    for ix in interactions:
        rna_map.setdefault(ix.rna_id, set()).add(ix.target_gene)

    # Gene nodes
    for gene, gw in weighted_genes.items():
        if gene not in seen_genes:
            gene_nodes.append(
                GeneNode(
                    gene=gene,
                    weight=round(gw.weight, 3),
                    supporting_rnas=list(set(gw.supporting_rnas))[:10],
                    is_seed=gene in seed_set,
                )
            )
            seen_genes.add(gene)

    # RNA nodes
    seen_rnas = set()
    for ix in interactions:
        if ix.rna_id not in seen_rnas:
            rna_nodes.append(
                RNANode(
                    rna_id=ix.rna_id,
                    rna_type=ix.rna_type,
                    evidence=ix.evidence,
                    source_db=ix.source_db,
                )
            )
            seen_rnas.add(ix.rna_id)
        # Edge: RNA → gene
        edges.append(
            GraphEdge(
                source=ix.rna_id,
                target=ix.target_gene,
                edge_type="rna_to_gene",
                evidence=ix.evidence,
            )
        )

    # Pathway nodes + gene→pathway edges
    pathway_nodes = []
    for r in top_pathways[:12]:
        pathway_nodes.append(
            PathwayNode(
                pathway_id=r.pathway_id,
                pathway_name=r.pathway_name,
                composite_score=round(r.composite_score, 4),
                fdr=r.fdr,
            )
        )
        for g in r.overlapping_genes:
            edges.append(
                GraphEdge(
                    source=g,
                    target=r.pathway_id,
                    edge_type="gene_to_pathway",
                )
            )

    return RegulationGraph(
        gene_nodes=gene_nodes,
        rna_nodes=rna_nodes,
        pathway_nodes=pathway_nodes,
        edges=edges,
    )


def _build_inflammation_summary(results, tags, counts) -> List[InflammationSummary]:
    tag_info = {
        "infection": ("Infection", "#F97316"),
        "autoimmunity": ("Autoimmunity", "#8B5CF6"),
        "metabolic": ("Metabolic Stress", "#10B981"),
        "cancer": ("Cancer-Associated", "#EF4444"),
        "tissue_damage": ("Tissue Damage", "#F59E0B"),
        "unclassified": ("Unclassified", "#6B7280"),
    }
    summary = []
    for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
        label, color = tag_info.get(cat, (cat, "#6B7280"))
        top_pws = [r.pathway_name for r in results if r.inflammation_tag == cat][:3]
        summary.append(
            InflammationSummary(
                category=cat,
                label=label,
                color=color,
                count=count,
                top_pathways=top_pws,
            )
        )
    return summary


async def start_analysis(request: AnalyzeRequest) -> str:
    """Create a job and start the analysis as a background task."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = JobProgress(
        job_id=job_id,
        status="pending",
        stage="Queued",
        percent=0,
    )
    asyncio.create_task(run_analysis(request, job_id))
    return job_id
