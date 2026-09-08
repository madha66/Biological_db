"""
Pathway service: orchestrates the full analysis pipeline.

This is the main coordinator that ties together:
1. Gene preprocessing
2. KEGG gene validation
3. Gene→pathway mapping
4. Statistical enrichment (Fisher's exact test)
5. FDR correction
6. Pathway ranking

It returns a complete analysis result ready for API serialization.
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field

from app.config import SUPPORTED_ORGANISMS, FDR_ALPHA
from app.analysis.preprocessing import preprocess_genes
from app.analysis.enrichment import compute_enrichment, apply_fdr_correction
from app.analysis.ranking import rank_pathways, RankedPathway
from app.services.kegg_service import KEGGService
from app.services.gene_service import GeneService
from app.utils.validators import validate_organism, validate_gene_list, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Complete result of the pathway analysis pipeline."""
    # Input summary
    total_submitted: int = 0
    valid_genes: list[str] = field(default_factory=list)
    unmapped_genes: list[str] = field(default_factory=list)
    duplicate_count: int = 0

    # Results
    ranked_pathways: list[RankedPathway] = field(default_factory=list)

    # Metadata
    organism: str = ""
    organism_name: str = ""
    background_universe_size: int = 0
    pathways_tested: int = 0
    significant_pathways: int = 0
    timestamp: str = ""


class PathwayAnalysisService:
    """
    Orchestrates the complete pathway enrichment analysis pipeline.

    This is the primary entry point for an analysis run. It coordinates all
    sub-services and analysis modules in the correct sequence.
    """

    def __init__(self, kegg_service: KEGGService):
        self._kegg = kegg_service
        self._gene_service = GeneService(kegg_service)

    def analyze(self, raw_genes: list[str], organism: str) -> AnalysisResult:
        """
        Run the full pathway analysis pipeline.

        Steps:
        1. Validate organism
        2. Preprocess genes (normalize, deduplicate)
        3. Validate genes against KEGG
        4. Build gene→pathway mapping
        5. Retrieve background universe
        6. Compute enrichment statistics
        7. Apply FDR correction
        8. Rank pathways

        Args:
            raw_genes: List of raw gene symbol strings from user input.
            organism: KEGG organism code (e.g. 'hsa').

        Returns:
            AnalysisResult with all computed data.

        Raises:
            ValidationError: If input is fundamentally invalid (no valid genes at all).
        """
        result = AnalysisResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Step 1: Validate organism
        organism = validate_organism(organism)
        result.organism = organism
        result.organism_name = SUPPORTED_ORGANISMS.get(organism, organism)
        logger.info("Starting analysis for organism: %s (%s)", organism, result.organism_name)

        # Step 2: Preprocess genes
        validated_tokens = validate_gene_list(raw_genes)
        preprocessing = preprocess_genes(validated_tokens)
        result.total_submitted = len(raw_genes)
        result.duplicate_count = preprocessing.duplicate_count

        # Step 3: Validate against KEGG
        logger.info("Validating %d unique genes against KEGG...", len(preprocessing.unique_genes))
        validation = self._gene_service.validate_genes(preprocessing.unique_genes, organism)
        result.valid_genes = validation.valid_genes
        result.unmapped_genes = validation.unmapped_genes

        if not validation.valid_genes:
            raise ValidationError(
                "None of the submitted genes could be mapped in KEGG for the selected organism. "
                "Please check your gene symbols and organism selection.",
                details={"unmapped_genes": validation.unmapped_genes},
            )

        # Step 4: Build gene→pathway mapping
        logger.info("Building gene→pathway mapping for %d valid genes...", len(validation.valid_genes))
        mapping = self._gene_service.build_pathway_mapping(validation, organism)

        if not mapping.pathway_to_genes:
            logger.warning("No pathways found for any of the valid genes.")
            result.pathways_tested = 0
            result.significant_pathways = 0
            return result

        # Step 5: Retrieve background universe
        logger.info("Retrieving background gene universe for organism '%s'...", organism)
        universe = self._kegg.get_organism_gene_universe(organism)
        result.background_universe_size = len(universe) if universe else 0

        # Fallback: if universe retrieval fails, use an approximate universe size
        # based on the pathway data we already have (documented in LIMITATIONS.md)
        if result.background_universe_size == 0:
            logger.warning(
                "Could not retrieve gene universe for '%s'. "
                "Using total pathway genes as approximate universe.",
                organism,
            )
            # Approximate: sum of unique genes across all pathways
            all_pathway_genes: set[str] = set()
            for pid in mapping.pathway_to_genes:
                try:
                    pg = self._kegg.get_all_pathway_genes(pid, organism)
                    all_pathway_genes.update(pg)
                except Exception:
                    pass
            result.background_universe_size = max(len(all_pathway_genes), len(validation.valid_genes) * 10)

        # Step 6: Compute enrichment
        logger.info("Computing enrichment for %d pathways...", len(mapping.pathway_to_genes))
        pathway_gene_counts = {
            pid: len(genes) for pid, genes in mapping.pathway_to_genes.items()
        }
        enrichment_results = compute_enrichment(
            pathway_gene_counts=pathway_gene_counts,
            pathway_total_genes=mapping.pathway_total_genes,
            total_valid_genes=len(validation.valid_genes),
            universe_size=result.background_universe_size,
        )

        # Step 7: FDR correction
        pathway_ids_ordered = [er.pathway_id for er in enrichment_results]
        raw_p_values = [er.p_value for er in enrichment_results]
        adjusted_p_values = apply_fdr_correction(raw_p_values)

        p_value_map = dict(zip(pathway_ids_ordered, raw_p_values))
        adj_p_value_map = dict(zip(pathway_ids_ordered, adjusted_p_values))

        # Step 8: Rank pathways
        logger.info("Ranking pathways...")
        ranked = rank_pathways(
            pathway_to_genes=mapping.pathway_to_genes,
            pathway_names=mapping.pathway_names,
            pathway_total_genes=mapping.pathway_total_genes,
            p_values=p_value_map,
            adjusted_p_values=adj_p_value_map,
            total_valid_genes=len(validation.valid_genes),
        )

        result.ranked_pathways = ranked
        result.pathways_tested = len(ranked)
        result.significant_pathways = sum(
            1 for rp in ranked if rp.adjusted_p_value < FDR_ALPHA
        )

        logger.info(
            "Analysis complete: %d pathways tested, %d significant (adj_p < %.2f)",
            result.pathways_tested,
            result.significant_pathways,
            FDR_ALPHA,
        )
        return result
