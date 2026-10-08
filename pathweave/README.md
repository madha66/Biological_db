# PathWeave — Integrated Multi-RNA Pathway and Disease Association Explorer for Cancer Genomics

PathWeave is a university/research-oriented web application for exploring how
genes and regulatory RNAs relate to diseases, pathways, transcripts, and
protein interaction networks. It combines public biological services into one
typed FastAPI backend and a React frontend.

The project addresses a common cancer-genomics problem: evidence about a gene
or RNA is distributed across separate resources, each using different
identifiers and biological vocabularies. PathWeave resolves submitted inputs,
retrieves source-attributed associations, and presents the results as tables,
summaries, and an interactive typed network. External-service failures are
reported as warnings rather than being converted into fabricated associations.

## Key features

- Gene/mRNA, miRNA, lncRNA, and mixed input modes.
- KEGG gene identifier resolution, disease associations, and pathway links.
- Ensembl human transcript lookup with resolved Ensembl gene identifiers.
- Reactome pathway projection for resolved human Ensembl genes.
- Gene Ontology Biological Process annotations through QuickGO.
- Conservative cross-database validation using exact normalized names.
- STRING protein-protein interaction retrieval with a configurable score
  threshold in the request.
- A configurable miRNA relationship-service boundary.
- lncRNA identifier resolution through Ensembl and explicit handling when a
  curated relationship source is unavailable.
- Typed integrated networks containing genes, proteins, RNAs, diseases, and
  pathways.
- Interactive Cytoscape network visualization with pan, zoom, and node
  selection.
- Deterministic connected-component clustering.
- Shared and entity-specific disease/pathway association summaries.
- Warnings and partial results when individual public services fail.
- Existing seed-gene/pathway analysis, demo mode, routes, and export behavior.

## Current workflow

1. The user submits one or more identifiers and selects an input mode.
2. PathWeave detects and normalizes gene, miRNA, and lncRNA identifiers.
3. Gene inputs are resolved through KEGG; human genes are also resolved through
   Ensembl for transcript, Reactome, and GO work.
4. KEGG disease and pathway data is retrieved for resolved gene entries.
5. Ensembl transcripts, Reactome pathways, and GO Biological Process
   annotations are retrieved where applicable.
6. RNA relationship services are queried for miRNA and lncRNA inputs.
7. STRING is queried for protein interactions among resolved gene inputs.
8. Results are normalized into typed network nodes and edges.
9. The network is grouped into deterministic connected components.
10. Disease and pathway associations are compared across input entities to
    produce shared and unique summaries.
11. The frontend displays tables, warnings, summaries, clusters, and the
    interactive integrated network.

## Architecture

```text
backend/
  app/
    api/            FastAPI routes, Pydantic models, analysis orchestration
    kegg/           KEGG REST client and gene/pathway helpers
    rna/            RNA identifier normalization and RNA relationship services
    interactions/   STRING protein interaction client
    network/        Typed network construction, connected components, summaries
    providers/      Existing provider-related application code
    scoring/        Existing seed-gene/pathway scoring and analysis pipeline

frontend/
  src/
    api/            Typed HTTP client
    components/     Reusable interface and network components
    pages/          Analysis and result pages
    types/          TypeScript API and result models
```

The existing gene-analysis workflow remains separate from the disease-analysis
workflow. `POST /api/disease-analysis` calls the disease-analysis service,
which coordinates the existing KEGG, Ensembl, Reactome, and GO code together
with the RNA, STRING, and network modules.

## Data sources

| Source | Current contribution | Status |
|---|---|---|
| KEGG | Human/organism gene resolution, disease links, pathway links and names | Active |
| Ensembl REST | Gene symbol resolution, transcript expansion, human lncRNA identifier resolution, and gene cross-references | Active |
| Reactome AnalysisService | Pathway projection using resolved human Ensembl gene IDs | Active |
| QuickGO / Gene Ontology | Biological Process annotations and GO term names | Active |
| STRING | Human protein interaction network records and scores | Active |
| miRTarBase | miRNA target-service integration boundary | Configurable, not enabled by default |
| Curated lncRNA resources | No stable unauthenticated target/disease source is enabled | Not active |

The miRTarBase URL is read from `PATHWEAVE_MIRTARBASE_API_URL`. When it is
unset, PathWeave reports that the miRNA target service is not configured and
does not infer targets.

For lncRNAs, Ensembl can resolve an identifier and verify its annotation where
possible. A curated lncRNA target/disease database is not enabled by default,
so successful identifier resolution is reported separately from biological
relationship results.

DisGeNET, OMIM, COSMIC, LncRNADisease, miR2Disease, and similar resources are
not active data sources in the current implementation.

## Backend API

The FastAPI application exposes the following endpoints:

| Method and path | Purpose |
|---|---|
| `GET /health` | Basic service health response |
| `GET /api/organisms` | Supported organism metadata |
| `GET /api/genes/suggest?q=...` | Gene autocomplete suggestions |
| `POST /api/analyze` | Starts the existing seed-gene/pathway analysis job |
| `GET /api/jobs/{job_id}` | Polls an analysis job |
| `GET /api/demo` | Starts the existing offline/demo analysis |
| `GET /api/export/{job_id}?format=json\|csv` | Exports a completed existing analysis job |
| `POST /api/disease-analysis` | Runs integrated disease, pathway, RNA, interaction, and network analysis |
| `GET /api/diseases/search?q=...` | Searches the KEGG Disease catalogue |

### Disease-analysis request

`POST /api/disease-analysis` accepts the current `DiseaseAnalysisRequest`
model. `input_type` can be `gene`, `miRNA`, `lncRNA`, or `mixed`; organism
codes currently include `hsa`, `mmu`, and `rno`.

```json
{
  "inputs": ["TP53", "BRCA1", "BRCA2"],
  "input_type": "gene",
  "disease_query": "cancer",
  "organism": "hsa",
  "interaction_score": 0.4
}
```

The response includes resolved identifiers, input-resolution records, disease
associations, KEGG pathways, Reactome pathways, GO annotations, transcripts,
miRNA/lncRNA relationship results, STRING interactions, a typed network,
clusters, shared/unique summaries, and warnings.

## Installation and setup

### Backend

Python 3.12 was used for development and testing.

```powershell
cd pathweave\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the API from the `backend` directory:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

The API is then available at `http://127.0.0.1:8000`.

### Frontend

```powershell
cd pathweave\frontend
npm install
npm run dev
```

For a production build:

```powershell
npm run build
```

## Configuration

The current application uses one optional environment variable:

```powershell
$env:PATHWEAVE_MIRTARBASE_API_URL = "https://your-configured-endpoint"
```

`PATHWEAVE_MIRTARBASE_API_URL` enables the configurable miRNA relationship
client. It is empty by default. No API key, credential, or other environment
variable is required by the current source code. The STRING endpoint and
public KEGG, Ensembl, Reactome, and QuickGO endpoints are defined in code.

## Testing

From `backend`:

```powershell
python -m compileall -q app
python -m pytest -q
```

From `frontend`:

```powershell
npm run build
```

The current verified result is **43 backend tests passed**, and the frontend
production build passed. Vite prints a non-blocking chunk-size optimization
message because some generated bundles are larger than 500 kB.

The test suite mocks external services for normal unit tests. Live public
services can still be transiently unavailable during manual testing.

## Network model

The integrated network uses deduplicated typed nodes:

| Node type | Meaning |
|---|---|
| `gene` | Resolved or submitted gene input/target |
| `protein` | Protein endpoint returned by the interaction model |
| `miRNA` | Normalized miRNA input |
| `lncRNA` | lncRNA input resolved or normalized by the RNA service |
| `disease` | Disease identifier associated with an input |
| `pathway` | KEGG or other pathway identifier |

Implemented edge types include:

| Edge type | Meaning |
|---|---|
| `targets` | miRNA target-gene relationship |
| `regulates` | lncRNA-to-gene relationship when relationship data exists |
| `interacts_with` | STRING protein-protein interaction |
| `associated_with` | Entity-to-disease association |
| `participates_in` | Gene/entity participation in a pathway |

Edges retain source database, optional evidence, and optional score fields.
Duplicate edges are removed using their source, target, type, and source
database.

## Clustering

The current lightweight clustering implementation builds an undirected
adjacency graph and returns deterministic connected components. It does **not**
currently use Louvain or another community-detection algorithm. Each cluster
contains its members, node-type counts, major gene/protein members, and
associated disease/pathway summaries.

## Shared vs unique analysis

Disease and pathway names are collected per input entity. An association
supported by more than one input is represented as shared, with the supporting
inputs listed. Associations supported by only one input are placed in that
entity's unique results. Associations supported by all submitted entities are
marked with an `all inputs` scope; subset support is retained separately.

Cross-database pathway validation remains intentionally conservative. Names are
lowercased and normalized before exact matching. Similar-sounding concepts
with different names are not automatically treated as equivalent.

## Error handling and partial results

The analysis keeps successful results when an individual external service
fails. Warnings distinguish common cases such as:

- unresolved gene or RNA identifier;
- external source unavailable;
- request timeout or transient HTTP failure;
- no association returned by an available source;
- miRTarBase not configured;
- lncRNA identifier resolved without a curated relationship source.

The existing Ensembl client retries transient server failures. Other clients
use bounded timeouts and catch external request/parsing errors. A warning is
returned to the API and displayed by the frontend rather than silently
turning a failed request into a biological association.

## Scientific and technical limitations

- Public biological APIs can change, throttle, or become temporarily
  unavailable.
- miRTarBase has a configurable integration boundary, but no stable
  unauthenticated endpoint is configured by default.
- Ensembl lncRNA identifier resolution is available, but curated lncRNA
  target/disease relationships are not enabled by default.
- Clustering currently uses connected components, not Louvain or weighted
  community detection.
- KEGG/Reactome/GO cross-validation uses exact normalized-name matching; it is
  not a semantic equivalence engine.
- STRING and GO results may vary or partially fail during transient service
  incidents.
- Public-service result sizes and counts are live-data dependent and should
  not be treated as fixed fixtures.

## Future work

Potential future improvements, not current functionality:

- Configure and validate a stable miRTarBase integration.
- Add a curated lncRNA disease/target source.
- Add additional disease evidence databases with reliable public access.
- Add deterministic identifier-based or ontology-based pathway mappings.
- Add Louvain or another reproducible community-detection option.
- Add larger-scale caching and request batching.
- Improve network layouts and filtering for large graphs.
- Expand evidence scoring while preserving source provenance.

## Example use case

Submit `TP53`, `BRCA1`, and `BRCA2` with the disease filter `cancer`. The
current application can resolve KEGG and Ensembl identifiers, retrieve live
KEGG disease/pathway records, Ensembl transcripts, Reactome projections, GO
Biological Process annotations, STRING interactions, and a combined typed
network. The result page also shows warnings, clusters, shared/unique
associations, and conservative cross-database matches. Exact live counts are
not hardcoded because public source data and availability can change.

## Development and contribution

Develop features on a dedicated branch rather than directly on `main`.
Changes should preserve the existing gene-analysis and disease-analysis
workflows, keep source provenance, add focused mocked tests, and run the
backend compilation/tests plus frontend build before review.

## License

No license is currently specified in this repository.
