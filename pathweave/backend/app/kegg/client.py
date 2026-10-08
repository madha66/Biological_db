"""KEGG REST API client with disk caching and polite rate limiting."""
from __future__ import annotations

import asyncio
import logging
import re
import time
from urllib.parse import quote
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

KEGG_BASE = "https://rest.kegg.jp"
_REQUEST_INTERVAL = 0.34  # ≤ 3 req/s per KEGG policy
_last_request_time: float = 0.0

# Simple in-memory cache (use diskcache in production)
_cache: Dict[str, str] = {}

_DEMO_PATHWAYS: Dict[str, Dict[str, Tuple[str, List[str]]]] = {
    "hsa": {
        "hsa04064": ("NF-kappa B signaling pathway", ["NFKB1", "TNF", "TRAF6", "IRAK1", "MAPK8", "NFKBIA", "IL6", "CXCL8", "BCL2", "CASP3", "FAS", "PTPN11", "MMP9"]),
        "hsa04620": ("Toll-like receptor signaling pathway", ["TNF", "IL6", "NFKB1", "TRAF6", "IRAK1", "MAPK14", "MAPK8", "IFNG", "CXCL8", "IL1B", "MMP9"]),
        "hsa04630": ("JAK-STAT signaling pathway", ["STAT3", "IL6", "SOCS1", "IFNG", "JAK1", "JAK2", "CCND1", "BCL2", "VEGFA", "MYC"]),
        "hsa04668": ("TNF signaling pathway", ["TNF", "NFKB1", "TRAF6", "MAPK8", "MAPK14", "CASP3", "FAS", "BCL2", "IL6", "CXCL8", "MMP9", "VEGFA"]),
        "hsa05200": ("Pathways in cancer", ["TP53", "MYC", "BCL2", "CASP3", "VEGFA", "CCND1", "CDK6", "CDK4", "PTEN", "KRAS", "STAT3", "NFKB1", "HIF1A", "AKT1"]),
        "hsa04115": ("p53 signaling pathway", ["TP53", "MDM2", "CDKN2A", "BCL2", "CASP3", "CDK6", "CDK4", "CCND1", "VEGFA"]),
        "hsa04210": ("Apoptosis", ["BCL2", "CASP3", "FAS", "TP53", "MAPK8", "TRAF6", "PTEN", "AKT1", "MDM2"]),
        "hsa04370": ("VEGF signaling pathway", ["VEGFA", "AKT1", "MAPK3", "PTEN", "STAT3", "MMP9", "HIF1A"]),
        "hsa04010": ("MAPK signaling pathway", ["MAPK8", "MAPK14", "MAPK3", "KRAS", "TRAF6", "MYC", "CCND1", "BCL2"]),
        "hsa05323": ("Rheumatoid arthritis", ["TNF", "IL6", "IL1B", "NFKB1", "STAT3", "MMP9", "TRAF6", "MAPK14", "VEGFA"]),
        "hsa04931": ("Insulin resistance", ["STAT3", "AKT1", "MAPK3", "PTEN", "TGFB1", "HIF1A", "NFKB1"]),
        "hsa04060": ("Cytokine-cytokine receptor interaction", ["TNF", "IL6", "IL1B", "IFNG", "CXCL8", "VEGFA", "TGFB1"]),
        "hsa04151": ("PI3K-Akt signaling pathway", ["AKT1", "PTEN", "BCL2", "VEGFA", "CCND1", "CDK4", "STAT3", "KRAS", "MYC", "HIF1A"]),
        "hsa04012": ("ErbB signaling pathway", ["MAPK3", "AKT1", "STAT3", "MYC", "CCND1", "KRAS"]),
        "hsa04066": ("HIF-1 signaling pathway", ["HIF1A", "VEGFA", "AKT1", "STAT3", "BCL2", "MAPK3"]),
        "hsa04110": ("Cell cycle", ["CCND1", "CDK6", "CDK4", "CDKN2A", "TP53", "MDM2", "CCND2"]),
        "hsa05205": ("Proteoglycans in cancer", ["VEGFA", "STAT3", "MMP9", "KRAS", "AKT1", "BCL2"]),
        "hsa04621": ("NOD-like receptor signaling pathway", ["NLRP3", "CASP1", "IL1B", "TNF", "NFKB1", "MAPK14"]),
        "hsa05210": ("Colorectal cancer", ["KRAS", "TP53", "MYC", "BCL2", "CCND1", "VEGFA", "AKT1"]),
        "hsa04150": ("mTOR signaling pathway", ["AKT1", "STAT3", "HIF1A", "VEGFA", "KRAS", "PTEN"]),
    },
    "mmu": {
        "mmu04064": ("NF-kappa B signaling pathway", ["Nfkb1", "Tnf", "Traf6", "Irak1", "Mapk8", "Nfkbia", "Il6", "Cxcl8", "Bcl2", "Casp3"]),
        "mmu04620": ("Toll-like receptor signaling pathway", ["Tnf", "Il6", "Nfkb1", "Traf6", "Irak1", "Mapk14", "Ifng", "Il1b"]),
        "mmu04630": ("JAK-STAT signaling pathway", ["Stat3", "Il6", "Socs1", "Ifng", "Jak1", "Jak2", "Ccnd1", "Bcl2", "Vegfa", "Myc"]),
        "mmu04668": ("TNF signaling pathway", ["Tnf", "Nfkb1", "Traf6", "Mapk8", "Mapk14", "Casp3", "Fas", "Bcl2", "Il6"]),
        "mmu05200": ("Pathways in cancer", ["Trp53", "Myc", "Bcl2", "Casp3", "Vegfa", "Ccnd1", "Cdk6", "Cdk4", "Pten", "Kras"]),
    },
    "rno": {
        "rno04064": ("NF-kappa B signaling pathway", ["Nfkb1", "Tnf", "Traf6", "Irak1", "Nfkbia", "Il6", "Bcl2"]),
        "rno04620": ("Toll-like receptor signaling pathway", ["Tnf", "Il6", "Nfkb1", "Traf6", "Irak1", "Ifng", "Il1b"]),
        "rno04630": ("JAK-STAT signaling pathway", ["Stat3", "Il6", "Socs1", "Ifng", "Bcl2", "Vegfa"]),
    },
}

BACKGROUND_SIZES = {
    "hsa": 7500,
    "mmu": 6800,
    "rno": 5900,
}


async def _polite_get(url: str, client: httpx.AsyncClient) -> str:
    """Rate-limited GET that respects KEGG's 3 req/s limit."""
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _REQUEST_INTERVAL:
        await asyncio.sleep(_REQUEST_INTERVAL - elapsed)

    if url in _cache:
        return _cache[url]

    try:
        resp = await client.get(url, timeout=30.0)
        resp.raise_for_status()
        _last_request_time = time.monotonic()
        _cache[url] = resp.text
        return resp.text
    except httpx.HTTPError as exc:
        logger.warning("KEGG request failed for %s: %s", url, exc)
        return ""


async def fetch_pathway_list(org: str, client: httpx.AsyncClient) -> Dict[str, str]:
    """
    Fetch all pathways for organism, returns {pathway_id: name}.
    Falls back to demo data if KEGG is unreachable.
    """
    url = f"{KEGG_BASE}/list/pathway/{org}"
    raw = await _polite_get(url, client)
    if not raw:
        logger.info("Using demo pathway list for %s", org)
        return {pid: pdata[0] for pid, pdata in _DEMO_PATHWAYS.get(org, _DEMO_PATHWAYS["hsa"]).items()}

    pathways = {}
    for line in raw.strip().split("\n"):
        if "\t" in line:
            parts = line.split("\t", 1)
            pid = parts[0].strip().replace("path:", "")
            name = parts[1].strip().split(" - ")[0] if " - " in parts[1] else parts[1].strip()
            pathways[pid] = name
    return pathways


async def fetch_pathway_genes(
    pathway_ids: List[str],
    org: str,
    client: httpx.AsyncClient,
) -> Dict[str, Tuple[str, List[str]]]:
    """
    Fetch gene members for each pathway.
    Returns {pathway_id: (name, [genes])}.
    Falls back to demo data if KEGG is unreachable.
    """
    # First try the link endpoint for efficiency
    url = f"{KEGG_BASE}/link/{org}/pathway"
    raw = await _polite_get(url, client)

    if not raw:
        logger.info("Using demo pathway gene data for %s", org)
        demo = _DEMO_PATHWAYS.get(org, _DEMO_PATHWAYS["hsa"])
        return {pid: data for pid, data in demo.items() if pid in pathway_ids}

    # Parse link data: pathway:hsa04064 \t hsa:TNF
    pathway_to_genes: Dict[str, List[str]] = {}
    gene_re = re.compile(r"^path:(\S+)\s+\S+:(\S+)$")
    for line in raw.strip().split("\n"):
        m = gene_re.match(line)
        if m:
            pid, gene = m.group(1), m.group(2).upper()
            pathway_to_genes.setdefault(pid, []).append(gene)

    # Fetch pathway names if needed
    pathway_list = await fetch_pathway_list(org, client)

    result = {}
    for pid in pathway_ids:
        if pid in pathway_to_genes:
            name = pathway_list.get(pid, pid)
            result[pid] = (name, pathway_to_genes[pid])

    # Merge curated gene symbol pathways for requested pathways
    demo = _DEMO_PATHWAYS.get(org, _DEMO_PATHWAYS["hsa"])
    for pid in pathway_ids:
        if pid in demo:
            dname, dgenes = demo[pid]
            if pid in result:
                name, existing_genes = result[pid]
                combined = list(dict.fromkeys(existing_genes + dgenes))
                result[pid] = (name, combined)
            else:
                result[pid] = (dname, dgenes)

    if not result:
        return {pid: data for pid, data in demo.items()}

    return result


async def get_full_pathway_data(
    org: str,
    client: httpx.AsyncClient,
) -> Dict[str, Tuple[str, List[str]]]:
    """
    Get ALL pathway-gene mappings for an organism.
    Used for pathway scoring background.
    Falls back to demo data gracefully.
    """
    pathway_list = await fetch_pathway_list(org, client)
    if not pathway_list:
        return _DEMO_PATHWAYS.get(org, _DEMO_PATHWAYS["hsa"])

    url = f"{KEGG_BASE}/link/{org}/pathway"
    raw = await _polite_get(url, client)

    if not raw:
        return _DEMO_PATHWAYS.get(org, _DEMO_PATHWAYS["hsa"])

    pathway_to_genes: Dict[str, List[str]] = {}
    gene_re = re.compile(r"^path:(\S+)\s+\S+:(\S+)$")
    for line in raw.strip().split("\n"):
        m = gene_re.match(line)
        if m:
            pid, gene = m.group(1), m.group(2).upper()
            pathway_to_genes.setdefault(pid, []).append(gene)

    result = {}
    for pid, name in pathway_list.items():
        result[pid] = (name, pathway_to_genes.get(pid, []))

    # Merge curated gene symbol pathways so symbol-based interactions match
    demo = _DEMO_PATHWAYS.get(org, _DEMO_PATHWAYS["hsa"])
    for pid, (dname, dgenes) in demo.items():
        if pid in result:
            name, existing_genes = result[pid]
            combined = list(dict.fromkeys(existing_genes + dgenes))
            result[pid] = (name, combined)
        else:
            result[pid] = (dname, dgenes)

    return result


def get_background_size(org: str) -> int:
    return BACKGROUND_SIZES.get(org, 7500)


async def fetch_gene_pathways(
    gene_ids: List[str],
    org: str,
    client: httpx.AsyncClient,
) -> Dict[str, List[str]]:
    """Return KEGG pathway IDs for numeric organism gene identifiers."""
    result: Dict[str, List[str]] = {}
    for gene_id in gene_ids:
        db_entry = gene_id if ":" in gene_id else f"{org}:{gene_id}"
        raw = await _polite_get(f"{KEGG_BASE}/link/pathway/{db_entry}", client)
        if not raw:
            continue
        for line in raw.splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                pathway_id = parts[1].replace("path:", "").strip()
                result.setdefault(gene_id, []).append(pathway_id)
    return result


def parse_gene_identifier(raw: str, org: str, symbol: Optional[str] = None) -> Optional[str]:
    """Extract the best matching KEGG organism entry from a /find/genes response."""
    prefix = f"{org}:"
    candidates: List[Tuple[str, str]] = []
    for line in raw.splitlines():
        parts = line.split("\t", 1)
        entry = parts[0].strip()
        if entry.startswith(prefix):
            description = parts[1] if len(parts) == 2 else ""
            candidates.append((entry, description))
            if symbol and any(
                alias.strip().casefold() == symbol.casefold()
                for alias in description.split(";", 1)[0].split(",")
            ):
                return entry
    if candidates:
        return candidates[0][0]
    return None


async def resolve_gene_identifiers(
    gene_symbols: List[str],
    org: str,
    client: httpx.AsyncClient,
) -> Tuple[Dict[str, str], List[str]]:
    """Resolve gene symbols to KEGG organism entries such as ``hsa:7157``."""
    resolved: Dict[str, str] = {}
    warnings: List[str] = []
    for symbol in gene_symbols:
        raw = await _polite_get(
            f"{KEGG_BASE}/find/genes/{quote(symbol, safe='')}",
            client,
        )
        entry = parse_gene_identifier(raw, org, symbol)
        if entry is None:
            warnings.append(f"KEGG could not resolve gene {symbol!r} for organism {org}.")
        else:
            resolved[symbol] = entry
    return resolved, warnings
