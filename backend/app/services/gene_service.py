"""
Gene service: validation against KEGG and gene→pathway mapping.

Coordinates between the preprocessing layer and the KEGG service to:
1. Validate gene symbols against the selected organism in KEGG.
2. Track valid vs. unmapped genes.
3. Build the gene-to-pathway mapping used by downstream analysis.
"""

import logging
from dataclasses import dataclass, field

from app.services.kegg_service import KEGGService, KEGGServiceError

logger = logging.getLogger(__name__)


@dataclass
class GeneValidationResult:
    """Result of validating genes against KEGG."""
    valid_genes: list[str] = field(default_factory=list)
    unmapped_genes: list[str] = field(default_factory=list)
    # Maps user gene symbol → KEGG gene ID (e.g. "TP53" → "hsa:7157")
    gene_id_map: dict[str, str] = field(default_factory=dict)


@dataclass
class GenePathwayMapping:
    """Complete mapping of genes to pathways."""
    # gene_symbol → list of pathway IDs
    gene_to_pathways: dict[str, list[str]] = field(default_factory=dict)
    # pathway_id → list of gene symbols
    pathway_to_genes: dict[str, list[str]] = field(default_factory=dict)
    # pathway_id → pathway name
    pathway_names: dict[str, str] = field(default_factory=dict)
    # pathway_id → total gene count in KEGG for that pathway
    pathway_total_genes: dict[str, int] = field(default_factory=dict)


class GeneService:
    """Service for gene validation and mapping using the KEGG service."""

    def __init__(self, kegg_service: KEGGService):
        self._kegg = kegg_service

    def validate_genes(
        self, gene_symbols: list[str], organism: str
    ) -> GeneValidationResult:
        """
        Validate a list of gene symbols against KEGG for the given organism.

        For each gene symbol, attempts to resolve it to a KEGG gene ID.
        Returns which genes were successfully mapped and which were not.
        """
        result = GeneValidationResult()

        for symbol in gene_symbols:
            try:
                kegg_id = self._kegg.find_gene(symbol, organism)
                if kegg_id:
                    result.valid_genes.append(symbol)
                    result.gene_id_map[symbol] = kegg_id
                    logger.info("Gene '%s' → KEGG ID '%s'", symbol, kegg_id)
                else:
                    result.unmapped_genes.append(symbol)
                    logger.info("Gene '%s' not found in KEGG for organism '%s'", symbol, organism)
            except KEGGServiceError as exc:
                logger.warning(
                    "KEGG error while resolving gene '%s': %s. Marking as unmapped.",
                    symbol, exc,
                )
                result.unmapped_genes.append(symbol)

        logger.info(
            "Gene validation: %d valid, %d unmapped out of %d",
            len(result.valid_genes),
            len(result.unmapped_genes),
            len(gene_symbols),
        )
        return result

    def build_pathway_mapping(
        self, validation_result: GeneValidationResult, organism: str
    ) -> GenePathwayMapping:
        """
        Build the complete gene↔pathway mapping for all validated genes.

        For each valid gene, queries KEGG for linked pathways and constructs
        bidirectional mappings (gene→pathways and pathway→genes).
        """
        mapping = GenePathwayMapping()

        for symbol in validation_result.valid_genes:
            kegg_id = validation_result.gene_id_map[symbol]
            try:
                pathways = self._kegg.get_pathways_for_gene(kegg_id)
                pathway_ids: list[str] = []

                for pw in pathways:
                    pid = pw["pathway_id"]
                    pathway_ids.append(pid)

                    # Build pathway→genes reverse mapping
                    if pid not in mapping.pathway_to_genes:
                        mapping.pathway_to_genes[pid] = []
                    if symbol not in mapping.pathway_to_genes[pid]:
                        mapping.pathway_to_genes[pid].append(symbol)

                mapping.gene_to_pathways[symbol] = pathway_ids
                logger.debug("Gene '%s' maps to %d pathways", symbol, len(pathway_ids))

            except KEGGServiceError as exc:
                logger.warning(
                    "KEGG error retrieving pathways for gene '%s' (%s): %s",
                    symbol, kegg_id, exc,
                )

        # Fetch pathway names and total gene counts
        for pid in mapping.pathway_to_genes:
            try:
                meta = self._kegg.get_pathway_metadata(pid)
                mapping.pathway_names[pid] = meta.get("name", pid)
            except KEGGServiceError:
                mapping.pathway_names[pid] = pid
                logger.warning("Could not retrieve metadata for pathway %s", pid)

            try:
                genes_in_pathway = self._kegg.get_all_pathway_genes(pid, organism)
                mapping.pathway_total_genes[pid] = len(genes_in_pathway)
            except KEGGServiceError:
                mapping.pathway_total_genes[pid] = 0
                logger.warning("Could not retrieve gene count for pathway %s", pid)

        logger.info(
            "Pathway mapping complete: %d genes map to %d pathways",
            len(mapping.gene_to_pathways),
            len(mapping.pathway_to_genes),
        )
        return mapping
