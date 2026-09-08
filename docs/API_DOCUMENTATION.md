# REST API Reference

The KEGGPathRank backend is powered by FastAPI, offering standard JSON REST endpoints and auto-generated Swagger UI / OpenAPI schemas.

- **Base URL**: `http://localhost:8000/api`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## Endpoints

### 1. Health Check
Checks backend health status, API version, and cache health.

- **Method**: `GET`
- **Path**: `/api/health`
- **Response** (`200 OK`):
  ```json
  {
    "status": "ok",
    "version": "1.0.0",
    "kegg_api": "reachable"
  }
  ```

---

### 2. Supported Organisms
Retrieves list of supported model organisms with their 3-letter KEGG codes.

- **Method**: `GET`
- **Path**: `/api/organisms`
- **Response** (`200 OK`):
  ```json
  [
    { "code": "hsa", "name": "Human (Homo sapiens)" },
    { "code": "mmu", "name": "Mouse (Mus musculus)" },
    { "code": "rno", "name": "Rat (Rattus norvegicus)" },
    { "code": "dre", "name": "Zebrafish (Danio rerio)" },
    { "code": "dme", "name": "Fruit fly (Drosophila melanogaster)" }
  ]
  ```

---

### 3. Analyze Gene Set
Executes the full pathway enrichment, statistical testing (Fisher's exact test), Benjamini–Hochberg FDR correction, and ranking.

- **Method**: `POST`
- **Path**: `/api/analyze`
- **Request Body**:
  ```json
  {
    "genes": ["TP53", "BRCA1", "EGFR", "AKT1", "PTEN", "MYC"],
    "organism": "hsa",
    "top_n": 20
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "summary": {
      "organism": "hsa",
      "total_submitted_genes": 6,
      "valid_genes_count": 6,
      "unmapped_genes_count": 0,
      "unmapped_genes": [],
      "total_pathways_found": 142,
      "significant_pathways_count": 28
    },
    "pathways": [
      {
        "rank": 1,
        "pathway_id": "hsa05200",
        "pathway_name": "Pathways in cancer",
        "pathway_score": 0.8333,
        "raw_p_value": 1.45e-07,
        "adjusted_p_value": 2.06e-05,
        "ranking_score": 3.904,
        "is_significant": true,
        "input_genes_in_pathway": ["TP53", "EGFR", "AKT1", "PTEN", "MYC"],
        "input_genes_count": 5,
        "total_pathway_genes_count": 530
      }
    ]
  }
  ```

---

### 4. Pathway Detail
Fetches detailed metadata, description, and KEGG external links for a specific pathway.

- **Method**: `GET`
- **Path**: `/api/pathway/{pathway_id}`
- **Parameters**: `pathway_id` (e.g. `hsa05200`)
- **Response** (`200 OK`):
  ```json
  {
    "pathway_id": "hsa05200",
    "name": "Pathways in cancer - Homo sapiens (human)",
    "kegg_url": "https://www.kegg.jp/entry/hsa05200",
    "genes": ["TP53", "EGFR", "AKT1", "PTEN", "MYC", ...]
  }
  ```

---

## Error Responses

| Status Code | Reason | Description |
|-------------|--------|-------------|
| `400 Bad Request` | Validation Error | Empty gene list, invalid organism code, or non-string inputs. |
| `404 Not Found` | Pathway Not Found | Pathway ID does not exist in the KEGG database. |
| `502 Bad Gateway` | KEGG Unreachable | External KEGG REST API failed to respond after retries. |
| `500 Internal Error`| Server Error | Unexpected internal computation exception. |
