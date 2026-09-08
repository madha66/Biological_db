"""
KEGG REST API service layer.

This is the ONLY module that communicates with the KEGG REST API.
All other code in the project uses this service to access KEGG data.

Responsibilities:
- Gene symbol → KEGG gene ID resolution
- Gene → pathway mapping
- Pathway metadata retrieval
- Organism gene universe retrieval (for statistical background)
- Caching of responses to avoid redundant API calls
- Rate limiting and retry logic

The service is designed for testability: all methods operate on a class instance,
allowing easy substitution with a mock in tests.
"""

import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Protocol

import requests

from app.config import (
    KEGG_API_BASE_URL,
    KEGG_REQUEST_TIMEOUT,
    KEGG_REQUEST_DELAY,
    KEGG_MAX_RETRIES,
    CACHE_DIR,
    CACHE_TTL_SECONDS,
)

logger = logging.getLogger(__name__)


# ── Exceptions ───────────────────────────────────────────────────────────────

class KEGGServiceError(Exception):
    """Base exception for KEGG service errors."""


class KEGGUnreachableError(KEGGServiceError):
    """Raised when the KEGG API is unreachable or times out."""


class KEGGRateLimitError(KEGGServiceError):
    """Raised when KEGG returns HTTP 429 (rate limited)."""


class KEGGParseError(KEGGServiceError):
    """Raised when a KEGG response cannot be parsed."""


# ── Protocol for mocking ────────────────────────────────────────────────────

class KEGGServiceProtocol(Protocol):
    """Protocol defining the KEGG service interface for dependency injection."""

    def find_gene(self, gene_symbol: str, organism: str) -> str | None: ...
    def get_pathways_for_gene(self, kegg_gene_id: str) -> list[dict[str, str]]: ...
    def get_pathway_metadata(self, pathway_id: str) -> dict[str, str]: ...
    def get_organism_gene_universe(self, organism: str) -> set[str]: ...
    def get_pathway_gene_count(self, pathway_id: str) -> int: ...
    def is_reachable(self) -> bool: ...


# ── File-based cache ────────────────────────────────────────────────────────

class FileCache:
    """
    Simple file-based JSON cache with TTL.

    Cache files are stored as JSON under CACHE_DIR with deterministic filenames
    derived from the cache key. Entries older than CACHE_TTL_SECONDS are ignored.
    """

    def __init__(self, cache_dir: Path = CACHE_DIR, ttl: int = CACHE_TTL_SECONDS):
        self._cache_dir = cache_dir
        self._ttl = ttl
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        """Derive a deterministic file path from a cache key."""
        hashed = hashlib.sha256(key.encode()).hexdigest()[:24]
        safe_key = key.replace(":", "_").replace("/", "_")[:60]
        return self._cache_dir / f"{safe_key}_{hashed}.json"

    def get(self, key: str) -> dict | list | None:
        """Return cached data if present and not expired, else None."""
        path = self._key_to_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached_at = data.get("_cached_at", 0)
            if time.time() - cached_at > self._ttl:
                logger.debug("Cache expired for key: %s", key)
                path.unlink(missing_ok=True)
                return None
            return data.get("value")
        except (json.JSONDecodeError, KeyError):
            logger.warning("Corrupt cache file for key '%s', removing.", key)
            path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: dict | list) -> None:
        """Store data in the cache."""
        path = self._key_to_path(key)
        payload = {"_cached_at": time.time(), "value": value}
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        logger.debug("Cached key: %s", key)


# ── KEGG Service Implementation ─────────────────────────────────────────────

class KEGGService:
    """
    Production KEGG REST API client.

    All KEGG communication is encapsulated here. Includes caching,
    rate limiting (request spacing), and retry logic with backoff.
    """

    def __init__(
        self,
        base_url: str = KEGG_API_BASE_URL,
        timeout: int = KEGG_REQUEST_TIMEOUT,
        delay: float = KEGG_REQUEST_DELAY,
        max_retries: int = KEGG_MAX_RETRIES,
        cache: FileCache | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._delay = delay
        self._max_retries = max_retries
        self._cache = cache or FileCache()
        self._last_request_time: float = 0.0
        self._session = requests.Session()

    # ── Internal helpers ──────────────────────────────────────────────────

    def _throttle(self) -> None:
        """Enforce minimum spacing between requests to respect KEGG's public API."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

    def _request(self, path: str) -> str:
        """
        Make a GET request to the KEGG API with retry and error handling.

        Returns the response body as text.
        Raises KEGGUnreachableError, KEGGRateLimitError, or KEGGServiceError.
        """
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            self._throttle()
            try:
                logger.debug("KEGG request [attempt %d]: GET %s", attempt, url)
                resp = self._session.get(url, timeout=self._timeout)
                self._last_request_time = time.time()

                if resp.status_code == 429:
                    wait = min(2 ** attempt, 30)
                    logger.warning("KEGG rate limit (429). Waiting %ds before retry.", wait)
                    time.sleep(wait)
                    last_error = KEGGRateLimitError(f"Rate limited on {url}")
                    continue

                if resp.status_code == 404:
                    return ""  # KEGG returns 404 for "no results"

                resp.raise_for_status()
                return resp.text

            except requests.exceptions.Timeout:
                logger.warning("KEGG timeout [attempt %d]: %s", attempt, url)
                last_error = KEGGUnreachableError(f"Timeout: {url}")
            except requests.exceptions.ConnectionError:
                logger.warning("KEGG connection error [attempt %d]: %s", attempt, url)
                last_error = KEGGUnreachableError(f"Connection error: {url}")
            except requests.exceptions.HTTPError:
                logger.error("KEGG HTTP error [attempt %d]: %s %s", attempt, resp.status_code, url)
                last_error = KEGGServiceError(f"HTTP {resp.status_code}: {url}")

        raise last_error or KEGGServiceError(f"Failed after {self._max_retries} attempts: {url}")

    # ── Public API ────────────────────────────────────────────────────────

    def find_gene(self, gene_symbol: str, organism: str) -> str | None:
        """
        Resolve a gene symbol to a KEGG gene ID for a given organism.

        Uses KEGG /find/genes endpoint: /find/<organism>/<gene_symbol>
        Returns the first matching KEGG gene ID (e.g. 'hsa:7157') or None.
        """
        cache_key = f"find_gene:{organism}:{gene_symbol.upper()}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached.get("kegg_id")  # type: ignore[union-attr]

        text = self._request(f"/find/{organism}/{gene_symbol}")
        if not text.strip():
            self._cache.set(cache_key, {"kegg_id": None})
            return None

        # Parse the tab-separated KEGG response.
        # Each line: <kegg_gene_id>\t<description>
        # We look for exact gene symbol matches in the description.
        best_match: str | None = None
        symbol_upper = gene_symbol.upper()

        for line in text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            kegg_id = parts[0].strip()
            description = parts[1].strip().upper()

            # KEGG descriptions often have format: "GENE_SYMBOL; full name"
            # or "GENE_SYMBOL, ALIAS; full name"
            desc_symbols = description.split(";")[0] if ";" in description else description
            symbols_in_desc = [s.strip() for s in desc_symbols.split(",")]

            if symbol_upper in symbols_in_desc:
                best_match = kegg_id
                break

            # Fallback: if the gene ID ends with the symbol (e.g., kegg_id contains gene number)
            if best_match is None:
                best_match = kegg_id  # Use first result as fallback

        self._cache.set(cache_key, {"kegg_id": best_match})
        logger.info("Resolved gene '%s' (%s) → %s", gene_symbol, organism, best_match)
        return best_match

    def get_pathways_for_gene(self, kegg_gene_id: str) -> list[dict[str, str]]:
        """
        Get all KEGG pathways linked to a gene.

        Uses KEGG /link/pathway/<gene_id>
        Returns list of dicts with 'gene_id' and 'pathway_id' keys.
        """
        cache_key = f"link_pathway:{kegg_gene_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        text = self._request(f"/link/pathway/{kegg_gene_id}")
        if not text.strip():
            self._cache.set(cache_key, [])
            return []

        pathways: list[dict[str, str]] = []
        for line in text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                gene_id = parts[0].strip()
                pathway_id = parts[1].strip().replace("path:", "")
                # Skip global/reference maps (those starting with 'map')
                if not pathway_id.startswith("map"):
                    pathways.append({"gene_id": gene_id, "pathway_id": pathway_id})

        self._cache.set(cache_key, pathways)
        logger.info("Gene %s → %d pathways", kegg_gene_id, len(pathways))
        return pathways

    def get_pathway_metadata(self, pathway_id: str) -> dict[str, str]:
        """
        Get metadata (name/title) for a KEGG pathway.

        Uses KEGG /get/<pathway_id> and parses the flat-file response.
        Returns dict with 'pathway_id' and 'name' keys.
        """
        cache_key = f"pathway_meta:{pathway_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        text = self._request(f"/get/{pathway_id}")
        if not text.strip():
            result = {"pathway_id": pathway_id, "name": pathway_id}
            self._cache.set(cache_key, result)
            return result

        name = pathway_id
        description = ""
        for line in text.split("\n"):
            if line.startswith("NAME"):
                # NAME line may contain organism suffix like " - Homo sapiens (human)"
                raw_name = line[len("NAME"):].strip()
                # Remove organism suffix if present
                if " - " in raw_name:
                    raw_name = raw_name.split(" - ")[0].strip()
                name = raw_name
            elif line.startswith("DESCRIPTION"):
                description = line[len("DESCRIPTION"):].strip()

        result = {"pathway_id": pathway_id, "name": name, "description": description}
        self._cache.set(cache_key, result)
        return result

    def get_organism_gene_universe(self, organism: str) -> set[str]:
        """
        Get the set of all gene IDs recognized by KEGG for an organism.

        Implementation: retrieves all genes across all KEGG pathways for the organism
        using /link/genes/<organism>. This is a practical approximation of the
        "gene universe" — see docs/LIMITATIONS.md for why this is an approximation.

        Returns a set of KEGG gene IDs (e.g. {'hsa:7157', 'hsa:672', ...}).
        """
        cache_key = f"gene_universe:{organism}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return set(cached)  # type: ignore[arg-type]

        # Get all pathway-gene links for the organism
        text = self._request(f"/link/pathway/{organism}")
        if not text.strip():
            logger.warning("No gene universe data returned for organism '%s'", organism)
            return set()

        gene_ids: set[str] = set()
        for line in text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                gene_id = parts[0].strip()
                gene_ids.add(gene_id)

        # Cache as a list (sets aren't JSON-serializable)
        self._cache.set(cache_key, list(gene_ids))
        logger.info("Organism '%s' gene universe: %d genes", organism, len(gene_ids))
        return gene_ids

    def get_pathway_gene_count(self, pathway_id: str) -> int:
        """
        Get the total number of genes in a KEGG pathway.

        Uses /link/genes/<pathway_id> to count all genes annotated to the pathway.
        """
        cache_key = f"pathway_gene_count:{pathway_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        # Use the link endpoint to get genes for this pathway
        text = self._request(f"/link/{pathway_id.split(':')[0] if ':' in pathway_id else pathway_id[:3]}/{pathway_id}")
        if not text.strip():
            # Fallback: try /get endpoint and count GENE entries
            text2 = self._request(f"/get/{pathway_id}")
            count = 0
            in_gene_section = False
            for line in text2.split("\n"):
                if line.startswith("GENE"):
                    in_gene_section = True
                    count += 1
                elif in_gene_section and line.startswith("    ") and not line.startswith("  "):
                    break
                elif in_gene_section and line.startswith("    "):
                    count += 1
                elif in_gene_section and not line.startswith(" "):
                    break
            self._cache.set(cache_key, count)
            return count

        count = len([l for l in text.strip().split("\n") if l.strip()])
        self._cache.set(cache_key, count)
        return count

    def get_all_pathway_genes(self, pathway_id: str, organism: str) -> set[str]:
        """
        Get all gene IDs annotated to a specific pathway for a given organism.

        Uses /link/<organism>/<pathway_id>.
        Returns set of KEGG gene IDs.
        """
        cache_key = f"pathway_genes:{pathway_id}:{organism}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return set(cached)  # type: ignore[arg-type]

        text = self._request(f"/link/{organism}/{pathway_id}")
        if not text.strip():
            self._cache.set(cache_key, [])
            return set()

        gene_ids: set[str] = set()
        for line in text.strip().split("\n"):
            parts = line.split("\t")
            if len(parts) >= 2:
                gene_id = parts[1].strip()
                gene_ids.add(gene_id)

        self._cache.set(cache_key, list(gene_ids))
        return gene_ids

    def is_reachable(self) -> bool:
        """Check if the KEGG REST API is reachable."""
        try:
            resp = self._session.get(
                f"{self._base_url}/info/kegg",
                timeout=10,
            )
            return resp.status_code == 200
        except (requests.exceptions.RequestException, Exception):
            return False
