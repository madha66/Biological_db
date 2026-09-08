# KEGG REST API Reference

## Overview

KEGGPathRank uses the official KEGG REST API exclusively. The API is public and requires no authentication or API key.

- **Base URL**: `https://rest.kegg.jp`
- **Protocol**: HTTPS GET requests
- **Response format**: Plain text (tab-separated or flat-file format, depending on endpoint)

## Endpoints Used

### 1. `GET /find/{organism}/{query}`

**Purpose**: Resolve a gene symbol to a KEGG gene ID.

**Example Request**:
```
GET https://rest.kegg.jp/find/hsa/TP53
```

**Example Response** (tab-separated, one result per line):
```
hsa:7157	TP53, p53, BCC7; tumor protein p53
```

**Identifier format**: `{organism}:{gene_number}` (e.g., `hsa:7157`)

**Parsing**: Split on `\t`. First column is the KEGG gene ID. Second column contains comma-separated aliases and a semicolon-separated description. We match the query symbol against the aliases for exact matching.

**Error cases**:
- No matching gene → empty response (HTTP 200 with empty body or 404)
- Invalid organism → HTTP 400

---

### 2. `GET /link/pathway/{kegg_gene_id}`

**Purpose**: Get all pathways linked to a specific gene.

**Example Request**:
```
GET https://rest.kegg.jp/link/pathway/hsa:7157
```

**Example Response** (tab-separated):
```
hsa:7157	path:hsa04010
hsa:7157	path:hsa04115
hsa:7157	path:hsa05200
```

**Identifier format**: Pathway IDs prefixed with `path:`, e.g., `path:hsa04115`. We strip the `path:` prefix for internal use.

**Filtering**: Global/reference maps (IDs starting with `map`, e.g., `path:map04010`) are filtered out; only organism-specific pathways (e.g., `hsa04010`) are retained.

---

### 3. `GET /get/{pathway_id}`

**Purpose**: Get metadata (name, description) for a pathway.

**Example Request**:
```
GET https://rest.kegg.jp/get/hsa04115
```

**Example Response** (flat-file format):
```
ENTRY       hsa04115    Pathway
NAME        p53 signaling pathway - Homo sapiens (human)
DESCRIPTION ...
CLASS       ...
PATHWAY_MAP ...
...
```

**Parsing**: We extract the `NAME` line and strip the organism suffix (e.g., ` - Homo sapiens (human)`).

---

### 4. `GET /link/pathway/{organism}`

**Purpose**: Get all gene-pathway links for an organism (used to build the background gene universe).

**Example Request**:
```
GET https://rest.kegg.jp/link/pathway/hsa
```

**Example Response** (tab-separated, thousands of lines):
```
hsa:10    path:hsa00232
hsa:10    path:hsa00983
hsa:100   path:hsa04014
...
```

**Usage**: We extract all unique gene IDs from the first column to form the background universe for statistical testing.

**Note**: This is a large response (~500KB–2MB depending on organism). It is cached with a 24-hour TTL.

---

### 5. `GET /link/{organism}/{pathway_id}`

**Purpose**: Get all genes in a specific pathway for a specific organism.

**Example Request**:
```
GET https://rest.kegg.jp/link/hsa/hsa04115
```

**Example Response**:
```
path:hsa04115	hsa:51426
path:hsa04115	hsa:545
path:hsa04115	hsa:7157
...
```

**Usage**: Count the number of genes annotated to each pathway for constructing the contingency table.

---

### 6. `GET /info/kegg`

**Purpose**: Health check — verify KEGG API reachability.

**Example Request**:
```
GET https://rest.kegg.jp/info/kegg
```

**Expected**: HTTP 200 with KEGG database information text.

---

## Error Handling

| Condition | KEGG Behavior | Our Handling |
|-----------|--------------|-------------|
| Gene not found | Empty response or HTTP 404 | Return `None`, mark gene as unmapped |
| Invalid organism | HTTP 400 | Validate organism before calling KEGG |
| Timeout | No response | Retry up to 3 times with backoff |
| Rate limiting | HTTP 429 | Wait 2ˢ (exponential backoff), retry |
| Server error | HTTP 5xx | Retry, then raise KEGGServiceError |
| Connection error | No connection | Retry, then raise KEGGUnreachableError |

## Rate Limiting

KEGG's public API does not officially document rate limits, but excessive requests may trigger temporary blocks. Our mitigations:

- **Request spacing**: Minimum 350ms between consecutive requests (`KEGG_REQUEST_DELAY`).
- **Retry with backoff**: Up to 3 retries with exponential backoff for 429 responses.
- **Caching**: All responses are cached (file-based, 24-hour TTL) to avoid redundant requests.

## Caching Behavior

- **Cache location**: `data/cached/` directory (JSON files)
- **Cache key format**: `{operation}:{organism}:{identifier}` (e.g., `find_gene:hsa:TP53`)
- **TTL**: 24 hours (configurable via `CACHE_TTL_SECONDS`)
- **Invalidation**: Expired entries are deleted on next access; manual invalidation by deleting cache files.
- **Stale data risk**: If KEGG updates pathway annotations, cached data may be outdated until TTL expires. For critical analyses, delete the cache directory before running.

## Known KEGG API Limitations

1. No batch query endpoint — each gene must be looked up individually.
2. Response format is plain text (not JSON), requiring custom parsing.
3. No API key or authentication — but also no SLA or uptime guarantee.
4. Gene symbol matching is substring-based; we apply exact-match filtering on top.
5. Pathway annotations may lag behind primary literature by months or years.
