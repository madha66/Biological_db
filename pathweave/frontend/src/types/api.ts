// PathWeave API types (mirrors Pydantic models)

export interface AnalysisOptions {
  include_types: ('miRNA' | 'lncRNA' | 'circRNA')[];
  evidence_weights: { validated: number; predicted: number };
  min_overlap: number;
  null_iterations: number;
  fdr_threshold: number;
  composite_weights: {
    fdr: number;
    odds_ratio: number;
    coverage: number;
    evidence_strength: number;
  };
  demo_mode: boolean;
}

export interface AnalyzeRequest {
  seed_gene?: string;
  gene_list?: string[];
  organism: 'hsa' | 'mmu' | 'rno';
  options: AnalysisOptions;
}

export interface DiseaseAnalysisRequest {
  inputs: string[];
  input_type: 'gene' | 'miRNA' | 'lncRNA' | 'mixed';
  disease_query?: string;
  organism: 'hsa' | 'mmu' | 'rno';
}

export interface DiseaseAssociation {
  input_name: string;
  disease_id: string;
  disease_name: string;
  source_db: string;
  evidence: string | null;
  score: number | null;
}

export interface TranscriptInfo {
  gene_symbol: string;
  gene_id: string | null;
  transcript_id: string;
  transcript_name: string | null;
  refseq_accession: string | null;
  ensembl_transcript_id: string | null;
  transcript_type: string | null;
  source_db: string;
}

export interface DiseasePathway {
  pathway_id: string;
  pathway_name: string;
  source_db: string;
  input_genes: string[];
  overlap_count: number;
  coverage: number | null;
}

export interface ReactomePathway {
  input_gene: string;
  pathway_id: string;
  pathway_name: string;
  source_db: string;
  evidence: string | null;
}

export interface GOAnnotation {
  input_gene: string;
  go_id: string;
  term_name: string;
  namespace: string;
  source_db: string;
}

export interface CrossValidationTheme {
  theme: string;
  kegg_pathways: string[];
  reactome_pathways: string[];
  go_terms: string[];
  supporting_inputs: string[];
  match_method: string;
}

export interface DiseaseNetworkEdge {
  source: string;
  target: string;
  edge_type: string;
  source_db: string;
}

export interface DiseaseCluster {
  cluster_id: string;
  members: string[];
  shared_diseases: string[];
  shared_pathways: string[];
}

export interface DiseaseAnalysisResult {
  inputs: string[];
  input_type: string;
  disease_query: string | null;
  organism: string;
  resolved_gene_ids: Record<string, string>;
  summary: {
    input_count: number;
    disease_association_count: number;
    pathway_count: number;
    interaction_count: number;
  };
  associations: DiseaseAssociation[];
  pathways: DiseasePathway[];
  reactome_pathways: ReactomePathway[];
  go_annotations: GOAnnotation[];
  cross_validation: CrossValidationTheme[];
  transcripts: TranscriptInfo[];
  network_edges: DiseaseNetworkEdge[];
  clusters: DiseaseCluster[];
  shared_diseases: string[];
  unique_diseases: Record<string, string[]>;
  shared_pathways: string[];
  unique_pathways: Record<string, string[]>;
  warnings: string[];
}

export interface PathwayResult {
  rank: number;
  pathway_id: string;
  pathway_name: string;
  composite_score: number;
  pvalue: number;
  fdr: number;
  odds_ratio: number;
  overlap_count: number;
  pathway_size: number;
  coverage: number;
  evidence_strength: number;
  overlapping_genes: string[];
  inflammation_tag: string | null;
  merged_pathways: string[];
  merged_pathway_names: string[];
}

export interface GeneNode {
  gene: string;
  weight: number;
  supporting_rnas: string[];
  is_seed: boolean;
}

export interface RNANode {
  rna_id: string;
  rna_type: string;
  evidence: string;
  source_db: string;
}

export interface PathwayNode {
  pathway_id: string;
  pathway_name: string;
  composite_score: number;
  fdr: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  edge_type: 'rna_to_gene' | 'gene_to_pathway';
  evidence?: string;
}

export interface RegulationGraph {
  gene_nodes: GeneNode[];
  rna_nodes: RNANode[];
  pathway_nodes: PathwayNode[];
  edges: GraphEdge[];
}

export interface NullModelResult {
  null_scores: number[];
  mean_null: number;
  real_score: number;
  empirical_pvalue: number;
  percentile: number;
}

export interface InflammationSummary {
  category: string;
  label: string;
  color: string;
  count: number;
  top_pathways: string[];
}

export interface SummaryStats {
  n_seed_genes: number;
  n_neighborhood_genes: number;
  n_mirna: number;
  n_lncrna: number;
  n_circrna: number;
  n_total_rnas: number;
  n_pathways_tested: number;
  n_pathways_significant: number;
  top_pathway: string | null;
  run_time_seconds: number;
}

export interface AnalysisResult {
  job_id: string;
  organism: string;
  seed_genes: string[];
  summary: SummaryStats;
  plain_summary: string;
  ranked_pathways: PathwayResult[];
  graph: RegulationGraph;
  null_model: NullModelResult | null;
  inflammation_by_source: InflammationSummary[];
  without_seed_pathways: PathwayResult[];
}

export interface JobProgress {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
  stage: string;
  percent: number;
  result?: AnalysisResult;
  error?: string;
}

export interface OrganismInfo {
  code: string;
  name: string;
  common_name: string;
}

export interface GeneSuggestion {
  gene: string;
  aliases: string[];
}

export const INFLATION_TAG_COLORS: Record<string, string> = {
  infection: '#F97316',
  autoimmunity: '#8B5CF6',
  metabolic: '#10B981',
  cancer: '#EF4444',
  tissue_damage: '#F59E0B',
  unclassified: '#6B7280',
};

export const INFLATION_TAG_LABELS: Record<string, string> = {
  infection: 'Infection',
  autoimmunity: 'Autoimmunity',
  metabolic: 'Metabolic',
  cancer: 'Cancer',
  tissue_damage: 'Tissue Damage',
  unclassified: 'Unclassified',
};

export const DEFAULT_OPTIONS: AnalysisOptions = {
  include_types: ['miRNA', 'lncRNA', 'circRNA'],
  evidence_weights: { validated: 1.0, predicted: 0.4 },
  min_overlap: 2,
  null_iterations: 200,
  fdr_threshold: 0.05,
  composite_weights: {
    fdr: 0.4,
    odds_ratio: 0.2,
    coverage: 0.2,
    evidence_strength: 0.2,
  },
  demo_mode: false,
};
