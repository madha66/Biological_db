"""Pydantic v2 response models for PathWeave API."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Organism(str, Enum):
    human = "hsa"
    mouse = "mmu"
    rat = "rno"


class EvidenceType(str, Enum):
    validated = "validated"
    predicted = "predicted"


class RNAType(str, Enum):
    miRNA = "miRNA"
    lncRNA = "lncRNA"
    circRNA = "circRNA"


class AnalysisOptions(BaseModel):
    include_types: List[RNAType] = Field(
        default=[RNAType.miRNA, RNAType.lncRNA, RNAType.circRNA]
    )
    evidence_weights: Dict[str, float] = Field(
        default={"validated": 1.0, "predicted": 0.4}
    )
    min_overlap: int = Field(default=2, ge=1, le=20)
    null_iterations: int = Field(default=200, ge=10, le=1000)
    fdr_threshold: float = Field(default=0.05, gt=0, le=1)
    composite_weights: Dict[str, float] = Field(
        default={"fdr": 0.4, "odds_ratio": 0.2, "coverage": 0.2, "evidence_strength": 0.2}
    )
    demo_mode: bool = False


class AnalyzeRequest(BaseModel):
    seed_gene: Optional[str] = None
    gene_list: Optional[List[str]] = None
    organism: Organism = Organism.human
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class RNANode(BaseModel):
    rna_id: str
    rna_type: str
    evidence: str
    source_db: str


class GeneNode(BaseModel):
    gene: str
    weight: float
    supporting_rnas: List[str]
    is_seed: bool


class PathwayNode(BaseModel):
    pathway_id: str
    pathway_name: str
    composite_score: float
    fdr: float


class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str     # "rna_to_gene" | "gene_to_pathway"
    evidence: Optional[str] = None


class RegulationGraph(BaseModel):
    gene_nodes: List[GeneNode]
    rna_nodes: List[RNANode]
    pathway_nodes: List[PathwayNode]
    edges: List[GraphEdge]


class PathwayResultModel(BaseModel):
    rank: int
    pathway_id: str
    pathway_name: str
    composite_score: float
    pvalue: float
    fdr: float
    odds_ratio: float
    overlap_count: int
    pathway_size: int
    coverage: float
    evidence_strength: float
    overlapping_genes: List[str]
    inflammation_tag: Optional[str] = None
    merged_pathways: List[str] = []
    merged_pathway_names: List[str] = []


class InflammationSummary(BaseModel):
    category: str
    label: str
    color: str
    count: int
    top_pathways: List[str]


class NullModelResult(BaseModel):
    null_scores: List[float]
    mean_null: float
    real_score: float
    empirical_pvalue: float
    percentile: float


class SummaryStats(BaseModel):
    n_seed_genes: int
    n_neighborhood_genes: int
    n_mirna: int
    n_lncrna: int
    n_circrna: int
    n_total_rnas: int
    n_pathways_tested: int
    n_pathways_significant: int
    top_pathway: Optional[str]
    run_time_seconds: float


class AnalysisResult(BaseModel):
    job_id: str
    organism: str
    seed_genes: List[str]
    summary: SummaryStats
    plain_summary: str
    ranked_pathways: List[PathwayResultModel]
    graph: RegulationGraph
    null_model: Optional[NullModelResult]
    inflammation_by_source: List[InflammationSummary]
    without_seed_pathways: List[PathwayResultModel]


class JobProgress(BaseModel):
    job_id: str
    status: str   # pending | running | done | error
    stage: str
    percent: int
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


class OrganismInfo(BaseModel):
    code: str
    name: str
    common_name: str


class GeneSuggestion(BaseModel):
    gene: str
    aliases: List[str] = []
