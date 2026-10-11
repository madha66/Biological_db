# PathWeave — Methodological & Architectural Limitations Assessment

This document details critical methodological and technical limitations identified during the comprehensive audit of PathWeave. These findings must be considered when interpreting pathway enrichment rankings and drafting academic report sections.

---

## 1. KEGG Identifier Discrepancy in Live vs Bundled Pathways
- **Observed Implementation**: The live KEGG REST client (`backend/app/kegg/client.py`) fetches `/link/hsa/pathway`, which pairs pathway IDs with numeric NCBI Entrez gene identifiers (e.g., `hsa:7157`, `hsa:10327`).
- **Query Format**: In contrast, `sample_interactions.csv` and submitted seed inputs use standard HGNC gene symbols (e.g., `TP53`, `PTEN`, `AKT1`).
- **Impact**: No gene identifier translation table is applied inside `pipeline.py`. To allow matches, `get_full_pathway_data()` merges the ~20 curated pathways from `_DEMO_PATHWAYS['hsa']`. Consequently, in live mode, **only the 20 pathways in `_DEMO_PATHWAYS` can ever match gene symbols**. All remaining ~350 KEGG pathways have 0 symbol overlap and are excluded by `min_overlap=2`.

## 2. Asymmetric Null Model Comparison (Apples-to-Oranges Sampling)
- **Observed Implementation**: In `run_null_model()`, each null iteration randomly samples `n_seed` genes (e.g., 5 genes) from `all_genes` with uniform weight 1.0, and scores pathways directly without RNA network expansion.
- **Comparison**: The observed top pathway score is computed after 2-hop RNA neighborhood expansion (yielding 23 weighted genes with weights up to 3.0).
- **Impact**: A random set of 5 genes will rarely achieve an overlap count >= 2, whereas 23 genes readily overlap cancer pathways. This systematic input size asymmetry artificially inflates the apparent significance of the observed score and produces empirical p-values near 0.0.

## 3. Fixed Statistical Universe Background
- **Observed Implementation**: `get_background_size('hsa')` returns a fixed constant of `7500`.
- **Impact**: The actual protein-coding genome comprises ~20,000 genes, while KEGG human pathway annotations cover ~8,000–8,500 distinct genes. Using an arbitrary fixed universe rather than the dynamically verified union of all annotated pathway genes introduces bias into cell `d` of Fisher's exact contingency table.

## 4. Min-Max Normalization Dependence in Composite Scoring
- **Observed Implementation**: In `scorer.py`, composite score components (-log10 FDR, log2 OR, coverage, evidence strength) are normalized using `(x - min) / (max - min)` across the set of tested pathways.
- **Impact**: The composite score is strictly relative to the specific cohort of pathways passing the `min_overlap` filter in that single run. Adding or removing a pathway alters the minimum and maximum values, shifting all composite scores. The composite score is a heuristic ranking index, **not a calibrated statistical probability**.

## 5. First-Match Precedence and Hardcoded Threshold in Inflammation Tagging
- **Observed Implementation**: In `tag_pathway()`, categories are evaluated sequentially according to dictionary order in `inflammation_tags.json` (`infection` -> `autoimmunity` -> `metabolic` -> `cancer` -> `tissue_damage`).
- **Impact**: A pathway that biologically overlaps multiple categories (e.g., `hsa04940` in autoimmunity and metabolic, or angiogenesis-related pathways) is unconditionally assigned to whichever category appears first in the file.
- **Hardcoded Threshold**: `summarise_inflammation()` enforces `if r.fdr <= 0.05:`, ignoring any custom `opts.fdr_threshold` provided by the user in the API request.

## 6. Bundled Interaction Dataset Provenance
- **Observed Implementation**: The bundled dataset `data/sample_interactions.csv` consists of 110 hand-curated interaction records across 27 RNAs and 41 genes.
- **Impact**: It is a demonstration fixture, not an exhaustive whole-genome regulatory database. Unrepresented seed genes (such as `BRCA1` and `EGFR`) have 0 interactions in the file, producing 0 RNA connections despite extensive real-world literature.