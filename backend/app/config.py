"""
Configuration module for KEGGPathRank backend.

All configuration values are loaded from environment variables with sensible defaults.
No secrets are required — the KEGG REST API is public and needs no API key.
"""

import os
import logging
from pathlib import Path


# Base directory of the project (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# KEGG API Configuration
KEGG_API_BASE_URL: str = os.getenv("KEGG_API_BASE_URL", "https://rest.kegg.jp")
KEGG_REQUEST_TIMEOUT: int = int(os.getenv("KEGG_REQUEST_TIMEOUT", "30"))
KEGG_REQUEST_DELAY: float = float(os.getenv("KEGG_REQUEST_DELAY", "0.35"))
KEGG_MAX_RETRIES: int = int(os.getenv("KEGG_MAX_RETRIES", "3"))

# Cache Configuration
CACHE_DIR: Path = BASE_DIR / "data" / "cached"
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", str(24 * 60 * 60)))  # 24 hours

# Supported Organisms: mapping of KEGG organism code to display name
SUPPORTED_ORGANISMS: dict[str, str] = {
    "hsa": "Human (Homo sapiens)",
    "mmu": "Mouse (Mus musculus)",
    "rno": "Rat (Rattus norvegicus)",
    "dre": "Zebrafish (Danio rerio)",
    "dme": "Fruit fly (Drosophila melanogaster)",
}

DEFAULT_ORGANISM: str = "hsa"

# Statistical Analysis Configuration
PVALUE_EPSILON: float = float(os.getenv("PVALUE_EPSILON", "1e-300"))
FDR_ALPHA: float = float(os.getenv("FDR_ALPHA", "0.05"))

# Logging Configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# CORS Configuration
CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")


def configure_logging() -> None:
    """Set up structured logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=LOG_FORMAT,
    )
    # Suppress overly verbose third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
