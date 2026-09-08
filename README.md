# KEGGPathRank

**A Python-Based System for Ranking Biologically Relevant KEGG Pathways from Gene Sets**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## Problem Statement

Researchers often have lists of gene identifiers from experiments but lack a quick, statistically rigorous way to determine which biological pathways those genes belong to — and which pathways are *significantly* enriched beyond what chance would predict. KEGGPathRank solves this by providing a complete analysis pipeline from gene input to ranked, statistically validated pathway results.

## Motivation

- Gene-to-pathway mapping is a fundamental step in understanding experimental results.
- Simple overlap counting is misleading without statistical testing.
- Existing tools often lack transparency about their scoring methods.
- Students and researchers need an approachable, well-documented tool.

## Objectives

1. Accept flexible gene input and validate against the KEGG database.
2. Map genes to KEGG pathways and compute representation scores.
3. Test enrichment significance with Fisher's exact test.
4. Correct for multiple testing with Benjamini–Hochberg FDR.
5. Rank pathways using a transparent, deterministic formula.
6. Present results in a clean, interactive web dashboard.

---

## Features

- **Multi-organism support**: Human, Mouse, Rat, Zebrafish, Fruit fly
- **Flexible input**: Comma, space, newline, or mixed-delimiter gene lists
- **Graceful partial failure**: Unmapped genes are reported, not fatal
- **Statistical rigor**: Fisher's exact test + Benjamini–Hochberg FDR
- **Transparent ranking**: Documented formula with worked examples
- **Interactive visualization**: Recharts bar charts with significance coloring
- **Drill-down details**: Click any pathway to see contributing genes and KEGG links
- **Offline charts**: Matplotlib script for publication-quality static charts
- **Complete documentation**: Methodology, API reference, statistical methods, limitations

---

## System Architecture

```
┌─────────────┐    HTTP    ┌───────────────────────────────────────────────┐
│   React UI  │ ◄────────► │            FastAPI Backend                    │
│   (Vite)    │            │  ┌─────────┐  ┌──────────┐  ┌────────────┐  │
│             │            │  │  Routes  │→ │ Services │→ │  Analysis  │  │
└─────────────┘            │  └─────────┘  └──────────┘  └────────────┘  │
                           │       │            │                         │
                           │       │       ┌────▼────┐                    │
                           │       │       │  KEGG   │ ← REST API        │
                           │       │       │ Service │   (rest.kegg.jp)   │
                           │       │       └────┬────┘                    │
                           │       │            │                         │
                           │       │       ┌────▼────┐                    │
                           │       │       │  Cache  │                    │
                           │       │       │ (files) │                    │
                           │       │       └─────────┘                    │
                           └───────────────────────────────────────────────┘
```

## Workflow

```
USER ENTERS GENES
  → INPUT VALIDATION
  → GENE NORMALIZATION (trim, case, dedupe)
  → KEGG GENE IDENTIFICATION (organism-scoped)
  → KEGG API QUERY
  → GENE → PATHWAY MAPPING
  → PATHWAY AGGREGATION
  → PATHWAY REPRESENTATION SCORE
  → FISHER'S EXACT TEST
  → MULTIPLE TESTING CORRECTION (Benjamini–Hochberg FDR)
  → PATHWAY RANKING (deterministic formula)
  → VISUALIZATION
  → RESULTS + BIOLOGICAL INTERPRETATION
```

---

## Technologies Used

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.11+, FastAPI | REST API server |
| Data Validation | Pydantic | Request/response schema validation |
| Statistics | SciPy, statsmodels | Fisher's test, FDR correction |
| Data Handling | Pandas, NumPy | Tabular data processing |
| KEGG API Client | Requests | HTTP calls to KEGG REST API |
| Frontend | React 18 + Vite | Interactive web dashboard |
| Charts (interactive) | Recharts | Browser-based bar charts |
| Charts (static) | Matplotlib | Publication-quality PNG charts |
| Logging | Python `logging` | Structured application logging |

### Why Two Chart Libraries?

- **Recharts** (frontend): Interactive hover tooltips, click handlers, responsive layout — ideal for the live web dashboard.
- **Matplotlib** (backend script): Publication-quality vector/raster output — ideal for reports, papers, and offline use.

---

## Installation

See [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for full details.

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd KEGGPathRank

# Backend
cd backend
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### Running

**Backend** (from project root):
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend** (from project root):
```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

---

## Example Input/Output

**Input:**
```json
{
  "genes": ["TP53", "BRCA1", "EGFR", "AKT1", "PTEN", "MYC"],
  "organism": "hsa"
}
```

**Output (summary):**
- 6 genes submitted, N valid, M unmapped
- K pathways detected, J statistically significant (adj. p < 0.05)
- Top pathway: e.g., "Pathways in cancer" with ranking score X.XX

---

## Pathway Scoring Formula

```
Pathway Score = (Input genes in pathway) / (Total valid input genes)
```

## Fisher's Exact Test

For each pathway, a 2×2 contingency table is constructed and tested (one-sided, greater) for overrepresentation. See [`docs/STATISTICAL_METHODS.md`](docs/STATISTICAL_METHODS.md).

## FDR Correction

Benjamini–Hochberg FDR correction is applied across all tested pathways to control the expected proportion of false discoveries. See [`docs/STATISTICAL_METHODS.md`](docs/STATISTICAL_METHODS.md).

## Ranking Algorithm

```
Ranking Score = Pathway Score × -log₁₀(Adjusted p-value)
```

This balances representation and significance. See [`docs/RANKING_ALGORITHM.md`](docs/RANKING_ALGORITHM.md) for worked examples.

---

## KEGG API Usage

KEGGPathRank uses the official KEGG REST API (`https://rest.kegg.jp`) exclusively. No KEGG API key is required (public API). All KEGG calls are isolated in `backend/app/services/kegg_service.py`. See [`docs/KEGG_API.md`](docs/KEGG_API.md).

---

## Limitations

- Background gene universe is an approximation (union of pathway-annotated genes)
- Dependent on KEGG API availability and data currency
- Pathway overlap (shared genes) not modeled
- Gene symbols can be ambiguous across organisms
- Representation ≠ causation

See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) for full details.

---

## Future Enhancements

- Support for additional gene ID formats (Entrez, Ensembl)
- Gene Ontology (GO) enrichment alongside KEGG
- Pathway network/interaction visualization
- Batch analysis for multiple gene sets
- Export results as CSV/PDF
- Persistent analysis history

---

## Suggested Git Workflow

```
1. Initial project setup (structure, config, .gitignore)
2. KEGG integration service layer
3. Gene preprocessing and validation
4. Statistical analysis (Fisher's test, FDR)
5. Ranking algorithm
6. REST API endpoints
7. React frontend (input, results, charts)
8. Visualization (Recharts + Matplotlib)
9. Automated test suite
10. Documentation (all docs/ files)
11. Final verification and cleanup
```

---

## Project Structure

```
KEGGPathRank/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration from environment
│   │   ├── api/
│   │   │   ├── routes.py        # API route handlers
│   │   │   └── schemas.py       # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── kegg_service.py  # KEGG REST API client (sole KEGG interface)
│   │   │   ├── gene_service.py  # Gene validation and mapping
│   │   │   ├── pathway_service.py # Analysis pipeline orchestrator
│   │   │   └── ranking_service.py
│   │   ├── analysis/
│   │   │   ├── preprocessing.py # Gene normalization and dedup
│   │   │   ├── enrichment.py    # Fisher's test and FDR correction
│   │   │   ├── statistics.py
│   │   │   └── ranking.py       # Ranking score computation
│   │   └── utils/
│   │       ├── validators.py    # Input validation
│   │       └── helpers.py       # General utilities
│   └── tests/
│       ├── test_preprocessing.py
│       ├── test_kegg_service.py
│       ├── test_statistics.py
│       ├── test_ranking.py
│       └── test_api_integration.py
├── frontend/                    # React + Vite application
├── data/
│   ├── sample_genes/            # Example gene sets
│   ├── cached/                  # KEGG response cache (auto-generated)
│   └── example_results/
├── docs/                        # Full documentation suite
└── scripts/
    └── generate_static_chart.py # Matplotlib chart generator
```

---

## Team

| Name | Registration |
|------|-------------|
| Madhan Kumar Kumaran | 23BCB0065 |
| Sanjay Jaishankar | 23BCB0078 |
| Sampanna Shalya | 23BCB0141 |

---

*KEGGPathRank is an academic project for educational purposes. KEGG data is accessed via the public REST API under KEGG's terms of use.*
