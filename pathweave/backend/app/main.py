"""PathWeave FastAPI application."""
from __future__ import annotations

import csv
import io
import json
import logging
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.api.models import (
    AnalyzeRequest,
    DiseaseAnalysisRequest,
    DiseaseAnalysisResult,
    DiseaseSearchResult,
    GeneSuggestion,
    JobProgress,
    OrganismInfo,
)
from app.api.disease_analysis import build_disease_analysis
from app.api.pipeline import get_job, start_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PathWeave API",
    description=(
        "PathWeave — From one gene to the whole inflammatory story. "
        "Bioinformatics API for RNA-regulatory-network-driven KEGG pathway enrichment."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Known genes for autocomplete
# ---------------------------------------------------------------------------

KNOWN_GENES = [
    "TNF", "IL6", "NFKB1", "TP53", "STAT3", "IL1B", "IFNG", "VEGFA",
    "BCL2", "CASP3", "MYC", "KRAS", "PTEN", "AKT1", "MAPK1", "MAPK3",
    "MAPK8", "MAPK14", "TRAF6", "IRAK1", "SOCS1", "PDCD4", "NLRP3",
    "CASP1", "HIF1A", "MDM2", "CDKN2A", "CDK4", "CDK6", "CCND1", "CCND2",
    "MMP9", "TGFB1", "EZH2", "VCAM1", "SPRED1", "FAS", "NFKBIA", "PTPN11",
    "JAK1", "JAK2", "CXCL8", "IGF2", "VEGFB", "TNF", "IL10", "IL17A",
    "FOXP3", "CTLA4", "PDCD1", "CD274", "BRCA1", "BRCA2", "EGFR", "ALK",
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "PathWeave API"}


@app.get("/api/organisms", response_model=List[OrganismInfo])
async def get_organisms() -> List[OrganismInfo]:
    return [
        OrganismInfo(code="hsa", name="Homo sapiens", common_name="Human"),
        OrganismInfo(code="mmu", name="Mus musculus", common_name="Mouse"),
        OrganismInfo(code="rno", name="Rattus norvegicus", common_name="Rat"),
    ]


@app.get("/api/genes/suggest", response_model=List[GeneSuggestion])
async def suggest_genes(q: str = Query("", min_length=0)) -> List[GeneSuggestion]:
    if not q:
        return []
    q_upper = q.upper()
    matches = [g for g in KNOWN_GENES if g.startswith(q_upper)][:10]
    return [GeneSuggestion(gene=g) for g in matches]


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest) -> dict:
    """Start an analysis job; returns a job id immediately."""
    job_id = await start_analysis(request)
    return {"job_id": job_id, "message": "Analysis started. Poll /api/jobs/{id} for progress."}


@app.post("/api/disease-analysis", response_model=DiseaseAnalysisResult)
async def disease_analysis(request: DiseaseAnalysisRequest) -> DiseaseAnalysisResult:
    """Retrieve disease, pathway, and transcript associations from public sources."""
    try:
        return await build_disease_analysis(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/diseases/search", response_model=List[DiseaseSearchResult])
async def search_diseases(q: str = Query(..., min_length=1, max_length=120)) -> List[DiseaseSearchResult]:
    """Search the public KEGG Disease catalogue by name or identifier."""
    import httpx
    from app.api.disease_analysis import _parse_kegg_table
    from app.kegg.client import KEGG_BASE, _polite_get

    async with httpx.AsyncClient() as client:
        diseases = _parse_kegg_table(await _polite_get(f"{KEGG_BASE}/list/disease", client))
    query = q.lower().strip()
    return [
        DiseaseSearchResult(disease_id=disease_id, disease_name=name)
        for disease_id, name in diseases.items()
        if query in disease_id.lower() or query in name.lower()
    ][:50]


@app.get("/api/jobs/{job_id}", response_model=JobProgress)
async def get_job_status(job_id: str) -> JobProgress:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
    return job


@app.get("/api/demo")
async def get_demo() -> dict:
    """
    Return a precomputed demo result for TNF / human without hitting KEGG.
    Uses demo mode so the app works fully offline.
    """
    from app.api.models import AnalysisOptions, RNAType, Organism

    demo_request = AnalyzeRequest(
        seed_gene="TNF",
        organism=Organism.human,
        options=AnalysisOptions(
            include_types=[RNAType.miRNA, RNAType.lncRNA, RNAType.circRNA],
            null_iterations=50,
            demo_mode=True,
        ),
    )
    job_id = await start_analysis(demo_request)
    return {"job_id": job_id, "message": "Demo analysis started"}


@app.get("/api/export/{job_id}")
async def export_results(
    job_id: str,
    format: str = Query("json", regex="^(csv|json)$"),
) -> StreamingResponse:
    job = get_job(job_id)
    if job is None or job.result is None:
        raise HTTPException(status_code=404, detail="Job not found or not complete")

    result = job.result

    if format == "json":
        content = result.model_dump_json(indent=2)
        return StreamingResponse(
            io.StringIO(content),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="pathweave_{job_id[:8]}.json"'},
        )

    # CSV export of ranked pathways
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "rank", "pathway_id", "pathway_name", "composite_score",
        "pvalue", "fdr", "odds_ratio", "overlap_count", "pathway_size",
        "coverage", "evidence_strength", "inflammation_tag",
        "overlapping_genes", "merged_pathways",
    ])
    for r in result.ranked_pathways:
        writer.writerow([
            r.rank, r.pathway_id, r.pathway_name, r.composite_score,
            r.pvalue, r.fdr, r.odds_ratio, r.overlap_count, r.pathway_size,
            r.coverage, r.evidence_strength, r.inflammation_tag or "",
            ";".join(r.overlapping_genes),
            ";".join(r.merged_pathways),
        ])
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="pathweave_{job_id[:8]}.csv"'},
    )


@app.get("/api/__init__")
async def api_init() -> dict:
    """PathWeave API package init."""
    return {"package": "pathweave-api", "version": "1.0.0"}
