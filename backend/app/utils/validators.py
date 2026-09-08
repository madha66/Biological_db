"""
Input validators for KEGGPathRank.

All validation logic is centralized here so route handlers stay thin.
"""

import re
import logging
from app.config import SUPPORTED_ORGANISMS

logger = logging.getLogger(__name__)

# Gene symbols are alphanumeric, may contain hyphens or dots (e.g. HLA-A, TP53)
_GENE_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ValidationError(Exception):
    """Raised when user input fails validation."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


def validate_organism(organism: str) -> str:
    """
    Validate that the organism code is supported.

    Returns the validated organism code (lowercase-stripped).
    Raises ValidationError if the organism is not supported.
    """
    organism = organism.strip().lower()
    if organism not in SUPPORTED_ORGANISMS:
        supported = ", ".join(f"{k} ({v})" for k, v in SUPPORTED_ORGANISMS.items())
        raise ValidationError(
            f"Unsupported organism: '{organism}'. Supported organisms: {supported}",
            details={"supported_organisms": list(SUPPORTED_ORGANISMS.keys())},
        )
    return organism


def validate_gene_list(raw_genes: list[str]) -> list[str]:
    """
    Validate that the gene list is non-empty and contains plausible gene symbols.

    This does NOT check whether genes exist in KEGG — that happens during mapping.
    This only rejects syntactically invalid tokens (empty strings, pure punctuation, etc.).

    Returns a list of syntactically plausible gene symbol strings.
    Raises ValidationError if the list is entirely empty after cleaning.
    """
    cleaned: list[str] = []
    for raw in raw_genes:
        token = raw.strip()
        if not token:
            continue
        if _GENE_SYMBOL_PATTERN.match(token):
            cleaned.append(token)
        else:
            logger.debug("Rejected syntactically invalid gene token: '%s'", token)

    if not cleaned:
        raise ValidationError(
            "No valid gene identifiers found. Please provide at least one gene symbol "
            "(e.g. TP53, BRCA1, EGFR).",
            details={"raw_count": len(raw_genes)},
        )

    return cleaned
