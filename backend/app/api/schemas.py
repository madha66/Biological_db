"""
Pydantic schemas for all API request/response models.

Every field is typed and documented. These schemas serve as the single source of truth
for the REST API contract between frontend and backend.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Request body for POST /api/analyze."""
    genes: list[str] = Field(
        ...,
        min_length=1,
        description="List of gene identifiers (symbols) to analyze.",
        json_schema_extra={"example": ["TP53", "BRCA1", "EGFR", "AKT1", "PTEN", "MYC"]},
    )
    organism: str = Field(
        default="hsa",
        description="KEGG organism code (e.g. 'hsa' for human, 'mmu' for mouse).",
    )


# ── Pathway Result Schemas ───────────────────────────────────────────────────

class PathwayResult(BaseModel):
    """A single pathway in the ranked results."""
    rank: int = Field(..., description="Rank position (1 = most significant/represented).")
    pathway_id: str = Field(..., description="KEGG pathway identifier (e.g. 'hsa04151').")
    pathway_name: str = Field(..., description="Human-readable pathway name.")
    input_gene_count: int = Field(..., description="Number of valid input genes mapped to this pathway.")
    total_pathway_genes: int = Field(..., description="Total genes in this pathway in the KEGG database.")
    pathway_score: float = Field(..., description="Representation score: input_gene_count / total_valid_genes.")
    p_value: float = Field(..., description="Raw Fisher's exact test p-value (one-sided, greater).")
    adjusted_p_value: float = Field(..., description="Benjamini–Hochberg FDR-corrected p-value.")
    ranking_score: float = Field(..., description="Combined score: pathway_score × -log10(adjusted_p_value).")
    contributing_genes: list[str] = Field(..., description="Input gene symbols that mapped to this pathway.")
    kegg_url: str = Field(..., description="Direct link to view this pathway on KEGG.")


class InputSummary(BaseModel):
    """Summary of gene input processing."""
    total_submitted: int = Field(..., description="Total gene identifiers submitted by the user.")
    valid_count: int = Field(..., description="Number of genes successfully mapped in KEGG.")
    unmapped_count: int = Field(..., description="Number of genes that could not be mapped.")
    duplicate_count: int = Field(..., description="Number of duplicate genes removed.")


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis run."""
    organism: str = Field(..., description="KEGG organism code used.")
    organism_name: str = Field(..., description="Human-readable organism name.")
    background_universe_size: int = Field(..., description="Number of genes in the background universe.")
    pathways_tested: int = Field(..., description="Number of pathways tested for enrichment.")
    significant_pathways: int = Field(
        ..., description="Number of pathways with adjusted p-value < 0.05."
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp of the analysis.")
    ranking_formula: str = Field(
        default="Ranking Score = Pathway Score × -log10(Adjusted p-value)",
        description="The formula used to compute the ranking score.",
    )


# ── Response Schemas ─────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    """Full response body for POST /api/analyze."""
    input_summary: InputSummary
    valid_genes: list[str] = Field(..., description="Gene symbols that were successfully mapped.")
    unmapped_genes: list[str] = Field(..., description="Gene symbols that could not be mapped.")
    pathways: list[PathwayResult] = Field(..., description="Ranked pathway results, descending by ranking score.")
    metadata: AnalysisMetadata


class PathwayDetailResponse(BaseModel):
    """Detailed response for GET /api/pathway/{pathway_id}."""
    pathway_id: str
    pathway_name: str
    input_gene_count: int
    total_pathway_genes: int
    pathway_score: float
    p_value: float
    adjusted_p_value: float
    ranking_score: float
    contributing_genes: list[str]
    kegg_url: str
    description: str = Field(default="", description="Extended pathway description from KEGG, if available.")


class HealthResponse(BaseModel):
    """Response body for GET /api/health."""
    status: str = Field(..., description="Application status: 'healthy' or 'degraded'.")
    kegg_reachable: bool = Field(..., description="Whether the KEGG REST API is currently reachable.")
    timestamp: str = Field(..., description="ISO 8601 timestamp.")
    version: str = Field(default="1.0.0", description="Application version.")


class ErrorResponse(BaseModel):
    """Standard error response returned for all error conditions."""
    error: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error description.")
    details: dict | None = Field(default=None, description="Additional error context, if any.")
