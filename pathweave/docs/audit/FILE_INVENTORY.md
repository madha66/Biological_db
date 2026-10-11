# PathWeave — Complete File Inventory & Module Responsibilities

This document details every tracked file within the PathWeave repository, its size, and its functional responsibility in the architecture.

| Relative Path | Size (Bytes) | Module / Area | Description & Responsibility |
|---|---|---|---|
| `.gitignore` | 29 | `root` | Git ignore rules for virtual environments, node modules, build artifacts, and caches. |
| `README.md` | 13515 | `root` | Project documentation: features, architecture, installation, limitations, and examples. |
| `backend/app/__init__.py` | 49 | `backend` | Backend application package initialization. |
| `backend/app/api/disease_analysis.py` | 21238 | `backend` | External service integration for KEGG disease, Ensembl transcripts, Reactome pathways, GO, and STRING. |
| `backend/app/api/models.py` | 9760 | `backend` | Pydantic v2 schemas for all requests, responses, graph models, and intermediate data. |
| `backend/app/api/pipeline.py` | 14589 | `backend` | Orchestrates end-to-end RNA expansion, gene weighting, KEGG enrichment, null model, and graph building. |
| `backend/app/interactions/__init__.py` | 37 | `backend` | Protein interaction module initialization. |
| `backend/app/interactions/string_client.py` | 2291 | `backend` | Client for retrieving protein-protein interactions from STRING DB REST API. |
| `backend/app/kegg/__init__.py` | 325 | `backend` | KEGG module initialization. |
| `backend/app/kegg/client.py` | 11520 | `backend` | Client for the KEGG REST API with rate limiting, background sizes, and offline demo pathways. |
| `backend/app/main.py` | 7118 | `backend` | FastAPI ASGI application entry point, route registrations, CORS setup, and export endpoints. |
| `backend/app/network/__init__.py` | 55 | `backend` | Network analysis module initialization. |
| `backend/app/network/analysis.py` | 6425 | `backend` | Connected-component clustering, graph summarization, and shared/unique association extraction. |
| `backend/app/providers/__init__.py` | 4959 | `backend` | Pluggable RNA interaction providers; implements CSVInteractionProvider for neighborhood expansion. |
| `backend/app/rna/__init__.py` | 49 | `backend` | RNA services module initialization. |
| `backend/app/rna/services.py` | 6930 | `backend` | RNA identifier normalization (miRNA, lncRNA), Ensembl cross-referencing, and miRTarBase boundary. |
| `backend/app/scoring/__init__.py` | 756 | `backend` | Scoring module initialization. |
| `backend/app/scoring/analysis.py` | 5911 | `backend` | Implements the empirical null-model control, inflammation tagging, and plain-language summaries. |
| `backend/app/scoring/scorer.py` | 9913 | `backend` | Calculates gene weights, Fisher's exact test, odds ratio, BH-FDR correction, and composite ranking. |
| `backend/requirements.txt` | 185 | `backend` | Python dependencies specification (FastAPI, scipy, statsmodels, httpx, etc.). |
| `backend/tests/test_cross_validation.py` | 4041 | `backend` | Unit tests for Reactome, GO, and cross-database pathway matching. |
| `backend/tests/test_ensembl_transcripts.py` | 4935 | `backend` | Unit tests for Ensembl transcript retrieval, identifier mapping, and error resilience. |
| `backend/tests/test_kegg_identifiers.py` | 2632 | `backend` | Unit tests for KEGG gene identifier parsing, organism prefixes, and disease links. |
| `backend/tests/test_rna_network.py` | 5689 | `backend` | Unit tests for RNA input normalization, STRING PPI deduplication, and network clustering. |
| `backend/tests/test_scoring.py` | 7327 | `backend` | Unit tests for gene weighting, Fisher enrichment, FDR correction, and Jaccard redundancy merging. |
| `data/inflammation_tags.json` | 3344 | `data` | Rule-based tagging configuration mapping KEGG pathway IDs and keywords to inflammation categories. |
| `data/sample_interactions.csv` | 5100 | `data` | Bundled interaction dataset containing 110 RNA-target records across miRNA, lncRNA, and circRNA. |
| `docs/audit/DATASET_STATISTICS.json` | 3548 | `docs` | Source code or configuration asset. |
| `docs/audit/DATASET_STATISTICS.md` | 2045 | `docs` | Source code or configuration asset. |
| `frontend/.gitignore` | 253 | `frontend` | Source code or configuration asset. |
| `frontend/.oxlintrc.json` | 245 | `frontend` | Source code or configuration asset. |
| `frontend/README.md` | 1278 | `frontend` | Source code or configuration asset. |
| `frontend/dist/assets/cytoscape.esm-D6xx22XN.js` | 434861 | `frontend` | Source code or configuration asset. |
| `frontend/dist/assets/index-BudZZ0s_.js` | 972344 | `frontend` | Source code or configuration asset. |
| `frontend/dist/assets/index-icxgZS2V.css` | 27303 | `frontend` | Source code or configuration asset. |
| `frontend/dist/favicon.svg` | 1006 | `frontend` | Source code or configuration asset. |
| `frontend/dist/icons.svg` | 5031 | `frontend` | Source code or configuration asset. |
| `frontend/dist/index.html` | 1064 | `frontend` | Source code or configuration asset. |
| `frontend/index.html` | 966 | `frontend` | Source code or configuration asset. |
| `frontend/package-lock.json` | 162456 | `frontend` | Source code or configuration asset. |
| `frontend/package.json` | 1312 | `frontend` | Frontend npm package configuration, dependencies, and build scripts. |
| `frontend/postcss.config.js` | 80 | `frontend` | Source code or configuration asset. |
| `frontend/public/favicon.svg` | 1006 | `frontend` | Source code or configuration asset. |
| `frontend/public/icons.svg` | 5031 | `frontend` | Source code or configuration asset. |
| `frontend/src/App.css` | 2891 | `frontend` | Source code or configuration asset. |
| `frontend/src/App.tsx` | 289 | `frontend` | Root React application layout component with persistent Header and Outlet. |
| `frontend/src/api/client.ts` | 1484 | `frontend` | TypeScript Axios/Fetch API client communicating with FastAPI backend. |
| `frontend/src/assets/hero.png` | 13057 | `frontend` | Source code or configuration asset. |
| `frontend/src/assets/react.svg` | 4126 | `frontend` | Source code or configuration asset. |
| `frontend/src/assets/vite.svg` | 8709 | `frontend` | Source code or configuration asset. |
| `frontend/src/components/layout/Header.tsx` | 3407 | `frontend` | Source code or configuration asset. |
| `frontend/src/components/results/BubblePlot.tsx` | 7051 | `frontend` | Visualization displaying pathway coverage, significance (-log10 FDR), and odds ratio. |
| `frontend/src/components/results/DiseaseNetworkView.tsx` | 2960 | `frontend` | Source code or configuration asset. |
| `frontend/src/components/results/InflammationPanel.tsx` | 5060 | `frontend` | Categorical breakdown of enriched pathways across inflammatory triggers. |
| `frontend/src/components/results/KPICards.tsx` | 3101 | `frontend` | High-level summary metric tiles (seed count, RNA count, pathways tested, top pathway). |
| `frontend/src/components/results/NetworkView.tsx` | 10534 | `frontend` | Interactive Cytoscape.js canvas rendering regulatory RNA-gene-pathway graphs. |
| `frontend/src/components/results/NullModelPanel.tsx` | 8405 | `frontend` | Visual distribution of empirical null scores with observed score indicator. |
| `frontend/src/components/results/PathwayDrawer.tsx` | 9796 | `frontend` | Slide-out details drawer showing overlapping genes, contingency tables, and merged pathways. |
| `frontend/src/components/results/PathwayTable.tsx` | 12726 | `frontend` | Interactive table of enriched KEGG pathways with filtering, sorting, and drawer triggers. |
| `frontend/src/index.css` | 4739 | `frontend` | Source code or configuration asset. |
| `frontend/src/main.tsx` | 1506 | `frontend` | React application entry point with React Query client and React Router setup. |
| `frontend/src/pages/AboutPage.tsx` | 9612 | `frontend` | Information page describing project methodology and external database attributions. |
| `frontend/src/pages/AnalyzePage.tsx` | 28450 | `frontend` | Primary user input form for seed genes, RNA types, and analysis options. |
| `frontend/src/pages/DiseaseResultsPage.tsx` | 13056 | `frontend` | Dedicated results view for multi-database disease and transcript associations. |
| `frontend/src/pages/ResultsPage.tsx` | 11073 | `frontend` | Primary results view rendering KPI cards, pathway table, bubble plot, network, and null model. |
| `frontend/src/types/api.ts` | 8285 | `frontend` | Source code or configuration asset. |
| `frontend/tailwind.config.js` | 3348 | `frontend` | Tailwind CSS design token configuration. |
| `frontend/tsconfig.app.json` | 726 | `frontend` | Source code or configuration asset. |
| `frontend/tsconfig.json` | 119 | `frontend` | Source code or configuration asset. |
| `frontend/tsconfig.node.json` | 558 | `frontend` | Source code or configuration asset. |
| `frontend/vite.config.ts` | 517 | `frontend` | Vite build tool configuration. |
| `scripts/generate_audit_data.py` | 59380 | `scripts` | Source code or configuration asset. |