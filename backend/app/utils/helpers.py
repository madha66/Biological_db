"""
General helper utilities for KEGGPathRank.
"""

import re


def parse_gene_input(raw_input: str) -> list[str]:
    """
    Parse a raw gene input string into individual gene tokens.

    Accepts comma-separated, space-separated, newline-separated, or any mix.
    Example: "TP53, BRCA1\\nEGFR AKT1" → ["TP53", "BRCA1", "EGFR", "AKT1"]
    """
    # Split on any combination of commas, whitespace, newlines, tabs, semicolons
    tokens = re.split(r"[,;\s]+", raw_input.strip())
    return [t.strip() for t in tokens if t.strip()]
