"""
Gene preprocessing: normalization, deduplication, and unmapped-gene tracking.

This module handles the transformation from raw user input to a clean, deduplicated
list of gene symbols ready for KEGG lookup, without performing any KEGG calls itself.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingResult:
    """Outcome of gene preprocessing."""
    # Unique, normalized gene symbols (preserving user's original casing for display)
    unique_genes: list[str] = field(default_factory=list)
    # Original tokens submitted by the user (after basic cleaning)
    original_tokens: list[str] = field(default_factory=list)
    # Duplicates that were removed (case-insensitive)
    duplicates_removed: list[str] = field(default_factory=list)
    # Count of duplicates
    duplicate_count: int = 0


def preprocess_genes(raw_genes: list[str]) -> PreprocessingResult:
    """
    Normalize and deduplicate a list of gene symbols.

    Steps:
    1. Trim whitespace from every token.
    2. Remove empty tokens.
    3. Deduplicate case-insensitively, keeping the first occurrence's casing.
    4. Track which duplicates were removed.

    Args:
        raw_genes: List of gene symbol strings (already split from the input string).

    Returns:
        PreprocessingResult with unique genes, originals, and duplicate info.
    """
    original_tokens: list[str] = []
    seen_upper: set[str] = set()
    unique_genes: list[str] = []
    duplicates_removed: list[str] = []

    for gene in raw_genes:
        trimmed = gene.strip()
        if not trimmed:
            continue
        original_tokens.append(trimmed)
        upper = trimmed.upper()
        if upper in seen_upper:
            duplicates_removed.append(trimmed)
            logger.debug("Duplicate gene removed: '%s'", trimmed)
        else:
            seen_upper.add(upper)
            unique_genes.append(trimmed)

    logger.info(
        "Preprocessing complete: %d tokens → %d unique genes, %d duplicates removed",
        len(original_tokens),
        len(unique_genes),
        len(duplicates_removed),
    )

    return PreprocessingResult(
        unique_genes=unique_genes,
        original_tokens=original_tokens,
        duplicates_removed=duplicates_removed,
        duplicate_count=len(duplicates_removed),
    )
