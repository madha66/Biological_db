# System Architecture

## Overview

KEGGPathRank follows a clean three-tier architecture: **Frontend (React)** → **Backend (FastAPI)** → **External Data Source (KEGG REST API)**.

## Architecture Diagram

```mermaid
graph TD
    subgraph Frontend["Frontend (React + Vite)"]
        UI["User Interface"]
        API_Client["API Service Layer"]
        Charts["Recharts Visualization"]
    end

    subgraph Backend["Backend (FastAPI)"]
        Routes["API Routes (routes.py)"]
        Schemas["Pydantic Schemas"]
        
        subgraph Services["Service Layer"]
            PathwaySvc["PathwayAnalysisService"]
            GeneSvc["GeneService"]
            KEGGSvc["KEGGService"]
            RankingSvc["RankingService"]
        end
        
        subgraph Analysis["Analysis Layer"]
            Preprocess["Preprocessing"]
            Enrichment["Enrichment (Fisher's)"]
            Ranking["Ranking"]
            Stats["Statistics (FDR)"]
        end
        
        subgraph Utils["Utilities"]
            Validators["Input Validators"]
            Cache["File-based Cache"]
            Config["Configuration"]
        end
    end

    subgraph External["External"]
        KEGG["KEGG REST API"]
    end

    UI --> API_Client
    API_Client -->|HTTP POST/GET| Routes
    Routes --> PathwaySvc
    PathwaySvc --> GeneSvc
    PathwaySvc --> Enrichment
    PathwaySvc --> Ranking
    GeneSvc --> KEGGSvc
    KEGGSvc -->|HTTP GET| KEGG
    KEGGSvc --> Cache
    Routes --> Schemas
    Enrichment --> Stats
    Charts --> UI
```

## Request Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant React as React Frontend
    participant FastAPI as FastAPI Backend
    participant PW as PathwayAnalysisService
    participant Gene as GeneService
    participant KEGG as KEGG REST API
    participant Stats as Statistics Module

    User->>React: Enter genes + organism, click Analyze
    React->>FastAPI: POST /api/analyze {genes, organism}
    FastAPI->>PW: analyze(genes, organism)
    PW->>PW: validate_organism()
    PW->>PW: preprocess_genes() [normalize, dedupe]
    PW->>Gene: validate_genes(symbols, organism)
    loop For each gene
        Gene->>KEGG: GET /find/{org}/{gene}
        KEGG-->>Gene: KEGG gene ID or empty
    end
    Gene-->>PW: valid_genes, unmapped_genes
    PW->>Gene: build_pathway_mapping(validation)
    loop For each valid gene
        Gene->>KEGG: GET /link/pathway/{gene_id}
        KEGG-->>Gene: pathway list
    end
    PW->>KEGG: GET /link/pathway/{organism} [gene universe]
    KEGG-->>PW: background gene set
    PW->>Stats: compute_enrichment() [Fisher's exact test]
    PW->>Stats: apply_fdr_correction() [Benjamini-Hochberg]
    PW->>PW: rank_pathways() [score + sort]
    PW-->>FastAPI: AnalysisResult
    FastAPI-->>React: AnalyzeResponse JSON
    React->>React: Render dashboard, chart, table
    React-->>User: Interactive results
```

## Design Decisions

### Why an explicit organism dropdown instead of auto-detection?
Gene symbols are not unique across organisms. For example, "TP53" exists in human, mouse, and rat with different KEGG identifiers. Automatic species detection from bare gene symbols is unreliable because symbols collide across species. An explicit dropdown eliminates ambiguity.

### Why no database?
KEGGPathRank performs stateless analyses. Each request is self-contained: genes go in, results come out. A file-based cache handles KEGG response caching. Adding a database (PostgreSQL, SQLite, etc.) would add deployment complexity without meaningful benefit for this use case.

### Why a separate KEGG service layer?
All KEGG communication is isolated in `kegg_service.py` so that:
1. Tests can substitute a mock with zero network calls.
2. Rate limiting, caching, and retry logic are centralized.
3. If KEGG changes its API, only one file needs updating.

### Why two chart libraries?
- **Recharts** (frontend): Interactive tooltips, click handlers, responsive — ideal for the live web dashboard where users explore results.
- **Matplotlib** (scripts/): Publication-quality raster/vector output — ideal for reports, papers, and offline use where interactivity isn't needed.
