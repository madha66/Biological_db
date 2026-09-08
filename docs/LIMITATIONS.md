# Limitations and Methodological Considerations

## Overview

While KEGGPathRank provides robust, statistically grounded pathway enrichment and ranking from gene lists, several biological, computational, and data-source limitations must be understood to interpret the results accurately.

---

## 1. Background Gene Universe Definition

### The Challenge
Fisher's exact test requires defining the "background universe" of all testable genes ($N$). In ideal transcriptome-wide experiments (e.g., RNA-seq), $N$ represents all genes expressed above a detection threshold in the given tissue or cell type.

### KEGGPathRank Approach
In the absence of user-provided assay background files, KEGGPathRank defines $N$ as the union of all genes annotated in any KEGG pathway for the chosen organism (e.g., ~8,500 genes for *Homo sapiens*).

### Methodological Impact
- **Potential Bias**: Genes that participate in no known KEGG pathways are excluded from $N$.
- **Effect on p-values**: When $N$ is smaller than the true genome size (~20,000 protein-coding genes), Fisher's exact test p-values are conservative (less prone to false positives).

---

## 2. Dependency on KEGG Database Currency

- **Static Caching**: KEGGPathRank caches pathway definitions and mappings locally to ensure high responsiveness and respect KEGG API rate considerations.
- **Dynamic Updates**: KEGG continuously updates pathway maps, gene annotations, and cross-references. Pathway definitions may vary slightly depending on cache age.
- **Gene Symbol Aliases**: While official gene symbols are validated through the KEGG API, non-standard aliases, legacy symbols, or retired accession IDs may fail mapping.

---

## 3. Pathway Overlap and Gene Crosstalk

- Standard overrepresentation analysis (ORA) treats each pathway as an independent hypothesis.
- In reality, biological pathways share many common signaling components (e.g., *AKT1*, *TP53*, *MAPK1*).
- Multiple related pathways (e.g., *Pathways in cancer*, *PI3K-Akt signaling*, *Colorectal cancer*) may achieve high ranks concurrently due to overlapping gene members rather than distinct biological activation events.

---

## 4. Lack of Directionality and Quantitative Weights

- KEGGPathRank currently operates on discrete gene sets (presence/absence lists).
- It does not take into account fold-change magnitudes, up/down regulation directions, or post-translational modifications.
- Presence of a gene in a pathway does not indicate pathway activation or repression without downstream experimental validation.

---

## 5. Statistical Interpretation and Best Practices

| What KEGGPathRank Tells You | What KEGGPathRank Does NOT Tell You |
|-----------------------------|-------------------------------------|
| Statistical overrepresentation of submitted genes in curated pathways. | Causal mechanism or direction of pathway flux. |
| Relative ranking based on overlap density and statistical confidence. | Absolute biological necessity in a specific clinical context. |
| Potential cellular processes and disease mechanisms for follow-up. | A substitute for experimental verification (qPCR, Western, assays). |

---

## Summary of Design Decisions

1. **Deterministic Scoring**: No stochastic sampling or seed-dependent results.
2. **Benjamini–Hochberg Correction**: Applied across all tested pathways to control False Discovery Rate (FDR).
3. **Graceful Partial Mapping**: Invalid or unmapped symbols are transparently reported without halting the analysis pipeline.
