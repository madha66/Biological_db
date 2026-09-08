# Methodology

## Overview

KEGGPathRank implements a complete pathway enrichment analysis pipeline that takes a set of gene identifiers as input and produces a statistically ranked list of biologically relevant KEGG pathways.

## Step-by-Step Pipeline

### Step 1: Gene Collection

The user provides a set of gene symbols (e.g., TP53, BRCA1, EGFR) through the web interface. The system accepts flexible input formats: comma-separated, space-separated, newline-separated, or any combination.

### Step 2: Input Preprocessing

1. **Tokenization**: The raw input string is split on commas, spaces, newlines, tabs, and semicolons.
2. **Trimming**: Leading and trailing whitespace is removed from each token.
3. **Deduplication**: Case-insensitive deduplication is applied (e.g., "TP53" and "tp53" are treated as the same gene). The first occurrence's casing is preserved for display.
4. **Syntactic validation**: Tokens are checked against a pattern for plausible gene symbols. Purely punctuation or empty tokens are discarded.

### Step 3: KEGG Gene Identification

Each preprocessed gene symbol is resolved to a KEGG gene ID using the KEGG REST API:
- **Endpoint**: `GET /find/{organism}/{gene_symbol}`
- **Process**: The API returns matching genes with descriptions. The system looks for an exact symbol match in the description field.
- **Outcome**: Each gene is classified as either "valid" (successfully mapped to a KEGG gene ID) or "unmapped" (no matching KEGG entry).

The analysis proceeds with valid genes only. Unmapped genes are reported to the user but do not block the analysis.

### Step 4: KEGG Pathway Mapping

For each valid gene (now identified by its KEGG gene ID), the system queries KEGG for all associated pathways:
- **Endpoint**: `GET /link/pathway/{kegg_gene_id}`
- **Process**: Returns all pathway IDs linked to the gene. Global/reference maps (IDs starting with "map") are filtered out; only organism-specific pathways are retained.
- **Outcome**: A bidirectional mapping is constructed: gene→pathways and pathway→genes.

### Step 5: Pathway Aggregation

For each pathway discovered in Step 4:
- Count how many of the user's valid input genes map to it.
- Retrieve pathway metadata (name, total gene count) from KEGG.
- Build the data structures needed for statistical analysis.

### Step 6: Pathway Representation Score

For each pathway:

```
Pathway Score = (Number of input genes in pathway) / (Total valid input genes)
```

This score (0 to 1) measures what fraction of the user's gene set is captured by the pathway. It is a descriptive statistic, not a significance test.

### Step 7: Statistical Enrichment — Fisher's Exact Test

For each pathway, a 2×2 contingency table is constructed:

|                    | In pathway | Not in pathway |
|--------------------|-----------|----------------|
| **Input genes**     | a         | b              |
| **Background genes**| c         | d              |

Where:
- **a** = input genes mapped to this pathway
- **b** = input genes NOT mapped to this pathway = (total valid input genes) − a
- **c** = background genes in this pathway (excluding input genes) = (total pathway genes) − a
- **d** = background genes NOT in this pathway (excluding input genes) = (universe size) − (total valid input genes) − c

Fisher's exact test is applied with `alternative="greater"` (one-sided, testing for overrepresentation). This evaluates whether the input genes are found in the pathway more often than expected by chance.

The **background universe** is defined as all genes recognized by KEGG for the selected organism across all annotated pathways (see Limitations).

### Step 8: Multiple Testing Correction (Benjamini–Hochberg FDR)

Testing many pathways simultaneously inflates the false-positive rate. The Benjamini–Hochberg procedure controls the False Discovery Rate (FDR) — the expected proportion of false discoveries among pathways called significant.

All raw p-values from Step 7 are corrected using `statsmodels.stats.multitest.multipletests(pvals, method="fdr_bh")`. Adjusted p-values are reported throughout the results.

### Step 9: Pathway Ranking

Each pathway receives a final ranking score:

```
Ranking Score = Pathway Score × -log₁₀(Adjusted p-value)
```

- The adjusted p-value is floored at ε = 10⁻³⁰⁰ to prevent log(0).
- Pathways are sorted by ranking score in descending order.
- Ties are broken by input gene count (more genes ranked higher).

This formula rewards pathways that are both well-represented in the input gene set AND statistically enriched beyond chance.

### Step 10: Visualization & Results

Results are presented in a web dashboard with:
- **Summary statistics**: Gene counts, pathway counts, significance counts.
- **Horizontal bar chart**: Top-ranked pathways, color-coded by significance level.
- **Sortable table**: All tested pathways with full statistics.
- **Drill-down details**: Click any pathway to see contributing genes and KEGG links.

All result descriptions use language like "significantly enriched" or "associated with" — never causal language.
