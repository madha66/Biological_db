"""
FastAPI route handlers for KEGGPathRank.

All endpoints are thin — they validate input, delegate to services, and serialize output.
No business logic lives here.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    PathwayResult,
    InputSummary,
    AnalysisMetadata,
    PathwayDetailResponse,
    HealthResponse,
    ErrorResponse,
)
from app.config import SUPPORTED_ORGANISMS
from app.services.kegg_service import KEGGService, KEGGServiceError
from app.services.pathway_service import PathwayAnalysisService
from app.utils.validators import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level service instances (initialized in main.py via lifespan)
_kegg_service: KEGGService | None = None
_pathway_service: PathwayAnalysisService | None = None
_last_analysis_result: dict | None = None


def init_services(kegg_service: KEGGService) -> None:
    """Initialize services. Called from main.py during application startup."""
    global _kegg_service, _pathway_service
    _kegg_service = kegg_service
    _pathway_service = PathwayAnalysisService(kegg_service)
    logger.info("API services initialized.")


def _get_pathway_service() -> PathwayAnalysisService:
    """Get the pathway service, raising if not initialized."""
    if _pathway_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized.")
    return _pathway_service


# ── POST /api/analyze ────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        503: {"model": ErrorResponse, "description": "KEGG API unavailable"},
    },
    summary="Analyze gene set for pathway enrichment",
    description=(
        "Submit a set of gene symbols and an organism code. "
        "Returns ranked pathways with representation scores, "
        "Fisher's exact test p-values, and BH-FDR adjusted p-values."
    ),
)
async def analyze_genes(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run the full pathway enrichment analysis pipeline."""
    global _last_analysis_result
    service = _get_pathway_service()

    try:
        result = service.analyze(request.genes, request.organism)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_error", "message": exc.message, "details": exc.details},
        ) from exc
    except KEGGServiceError as exc:
        logger.error("KEGG service error during analysis: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "kegg_unavailable",
                "message": f"The KEGG API is currently unavailable: {exc}",
            },
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during analysis")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
            },
        ) from exc

    # Build response
    pathways = [
        PathwayResult(
            rank=rp.rank,
            pathway_id=rp.pathway_id,
            pathway_name=rp.pathway_name,
            input_gene_count=rp.input_gene_count,
            total_pathway_genes=rp.total_pathway_genes,
            pathway_score=rp.pathway_score,
            p_value=rp.p_value,
            adjusted_p_value=rp.adjusted_p_value,
            ranking_score=rp.ranking_score,
            contributing_genes=rp.contributing_genes,
            kegg_url=f"https://www.kegg.jp/pathway/{rp.pathway_id}",
        )
        for rp in result.ranked_pathways
    ]

    response = AnalyzeResponse(
        input_summary=InputSummary(
            total_submitted=result.total_submitted,
            valid_count=len(result.valid_genes),
            unmapped_count=len(result.unmapped_genes),
            duplicate_count=result.duplicate_count,
        ),
        valid_genes=result.valid_genes,
        unmapped_genes=result.unmapped_genes,
        pathways=pathways,
        metadata=AnalysisMetadata(
            organism=result.organism,
            organism_name=result.organism_name,
            background_universe_size=result.background_universe_size,
            pathways_tested=result.pathways_tested,
            significant_pathways=result.significant_pathways,
            timestamp=result.timestamp,
        ),
    )

    # Cache the last analysis for the pathway detail endpoint
    _last_analysis_result = {rp.pathway_id: rp for rp in pathways}

    return response


# ── GET /api/pathway/{pathway_id} ────────────────────────────────────────────

@router.get(
    "/pathway/{pathway_id}",
    response_model=PathwayDetailResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get detailed information about a specific pathway",
)
async def get_pathway_detail(pathway_id: str) -> PathwayDetailResponse:
    """
    Return detailed information about a pathway from the most recent analysis.

    If no recent analysis is available, attempts to fetch basic metadata from KEGG.
    """
    # Check cached analysis results first
    if _last_analysis_result and pathway_id in _last_analysis_result:
        pw = _last_analysis_result[pathway_id]
        return PathwayDetailResponse(
            pathway_id=pw.pathway_id,
            pathway_name=pw.pathway_name,
            input_gene_count=pw.input_gene_count,
            total_pathway_genes=pw.total_pathway_genes,
            pathway_score=pw.pathway_score,
            p_value=pw.p_value,
            adjusted_p_value=pw.adjusted_p_value,
            ranking_score=pw.ranking_score,
            contributing_genes=pw.contributing_genes,
            kegg_url=pw.kegg_url,
        )

    # Fallback: try to get basic metadata from KEGG
    if _kegg_service:
        try:
            meta = _kegg_service.get_pathway_metadata(pathway_id)
            return PathwayDetailResponse(
                pathway_id=pathway_id,
                pathway_name=meta.get("name", pathway_id),
                input_gene_count=0,
                total_pathway_genes=0,
                pathway_score=0.0,
                p_value=1.0,
                adjusted_p_value=1.0,
                ranking_score=0.0,
                contributing_genes=[],
                kegg_url=f"https://www.kegg.jp/pathway/{pathway_id}",
                description=meta.get("description", ""),
            )
        except KEGGServiceError:
            pass

    raise HTTPException(
        status_code=404,
        detail={
            "error": "pathway_not_found",
            "message": f"Pathway '{pathway_id}' not found. Run an analysis first or check the pathway ID.",
        },
    )


# ── GET /api/health ──────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check application status and KEGG API reachability.",
)
async def health_check() -> HealthResponse:
    """Simple liveness/readiness check including KEGG reachability."""
    kegg_reachable = False
    if _kegg_service:
        try:
            kegg_reachable = _kegg_service.is_reachable()
        except Exception:
            kegg_reachable = False

    return HealthResponse(
        status="healthy" if kegg_reachable else "degraded",
        kegg_reachable=kegg_reachable,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ── GET /api/organisms ──────────────────────────────────────────────────────

@router.get(
    "/organisms",
    summary="List supported organisms",
    description="Returns the list of supported KEGG organism codes and their names.",
)
async def list_organisms() -> dict[str, str]:
    """Return supported organisms."""
    return SUPPORTED_ORGANISMS
