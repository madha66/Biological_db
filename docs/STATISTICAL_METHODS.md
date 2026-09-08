# Statistical Methods

## 1. Pathway Representation Score

The pathway representation score measures what fraction of the user's input gene set overlaps with a given KEGG pathway.

### Formula

```
Pathway Score = a / n
```

Where:
- **a** = number of valid input genes that map to the pathway
- **n** = total number of valid input genes

### Interpretation

- A score of **1.0** means every valid input gene maps to this pathway.
- A score of **0.1** means 10% of the input genes are in this pathway.
- This is a descriptive statistic only — it does not account for pathway size or chance overlap.

> **Important:** A high representation score alone does not imply statistical significance. A very large pathway (e.g., "Metabolic pathways" with 1,500+ genes) may contain many of your input genes simply because it covers a large fraction of the genome, not because your genes are specifically enriched in it.

---

## 2. Fisher's Exact Test

### Purpose

Fisher's exact test evaluates whether the overlap between the user's input genes and a KEGG pathway is greater than would be expected by chance, given the sizes of the gene set, the pathway, and the background universe.

### Contingency Table

For each pathway, we construct a 2×2 contingency table:

```
                      In pathway    Not in pathway    Total
Input genes              a               b            a + b = n
Background genes         c               d            c + d
Total                   a + c           b + d          N
```

Where:
- **a** = number of valid input genes mapped to this pathway
- **b** = number of valid input genes NOT mapped to this pathway = n − a
- **c** = number of background-universe genes (excluding input genes) mapped to this pathway = K − a
- **d** = number of background-universe genes (excluding input genes) NOT mapped to this pathway = N − n − c
- **n** = total number of valid input genes (a + b)
- **K** = total number of genes in the pathway in KEGG (a + c)
- **N** = total number of genes in the background universe

### Test Configuration

- **Test**: `scipy.stats.fisher_exact(table, alternative="greater")`
- **Hypothesis**: One-sided test for overrepresentation (testing whether the input genes are enriched in the pathway beyond chance)
- **Null hypothesis (H₀)**: The input genes are not enriched in the pathway (the observed overlap is consistent with random selection)
- **Alternative hypothesis (H₁)**: The input genes are overrepresented in the pathway

### Worked Example

Suppose:
- 6 valid input genes (n = 6)
- 3 of them map to the "p53 signaling pathway" (a = 3)
- The p53 signaling pathway has 72 genes total in KEGG (K = 72)
- The background universe has 7,500 genes (N = 7,500)

```
a = 3
b = 6 - 3 = 3
c = 72 - 3 = 69
d = 7500 - 6 - 69 = 7425
```

```
           In pathway    Not in pathway
Input:        3               3
Background:   69             7425
```

Fisher's exact test p-value ≈ 0.00014 (highly significant).

### Background Universe

The background universe is defined as: **all genes annotated to at least one KEGG pathway for the selected organism**. This is retrieved via the KEGG `/link/pathway/{organism}` endpoint.

> **Note:** This is an approximation. The true biological "gene universe" would be all genes in the genome. However, KEGG only annotates a subset of genes (those with known pathway associations). This approximation is standard in pathway enrichment tools. See `LIMITATIONS.md` for details on its implications.

---

## 3. Multiple Testing Correction (Benjamini–Hochberg FDR)

### Problem

When testing many pathways simultaneously, the probability of obtaining at least one false positive increases dramatically. If you test 100 pathways at α = 0.05, you'd expect ~5 false positives even if no pathway is truly enriched.

### Solution: False Discovery Rate Control

The Benjamini–Hochberg (BH) procedure controls the **False Discovery Rate (FDR)** — the expected proportion of false discoveries among the pathways called significant.

### Procedure

1. Order the m raw p-values from smallest to largest: p₍₁₎ ≤ p₍₂₎ ≤ ... ≤ p₍ₘ₎
2. For each p-value at rank i, compute the adjusted p-value: `p_adj₍ᵢ₎ = min(p₍ᵢ₎ × m/i, 1)`
3. Enforce monotonicity: working backwards from p₍ₘ₎, set each p_adj₍ᵢ₎ = min(p_adj₍ᵢ₎, p_adj₍ᵢ₊₁₎)

### Implementation

```python
from statsmodels.stats.multitest import multipletests
reject, adjusted_pvals, _, _ = multipletests(raw_pvals, method="fdr_bh")
```

### Interpretation

- An adjusted p-value of 0.03 means: among all pathways with adjusted p-value ≤ 0.03, we expect at most 3% to be false discoveries.
- We use a significance threshold of adjusted p < 0.05 by default.
- Adjusted p-values are always ≥ the corresponding raw p-values.

---

## 4. Responsible Interpretation

### What the results show
- Which pathways are **significantly enriched** in the submitted gene set.
- The **degree of representation** (what fraction of input genes overlap with each pathway).

### What the results do NOT show
- **Causation**: Enrichment does not mean a pathway "causes" any condition.
- **Biological mechanism**: The analysis identifies statistical associations, not functional relationships.
- **Completeness**: KEGG annotations may be incomplete; absence of enrichment does not mean absence of involvement.

### Representation vs. Enrichment

| Scenario | Representation | Enrichment | Interpretation |
|----------|---------------|------------|----------------|
| Large pathway, many genes overlap | High | May be low | High overlap may be due to pathway size, not specificity |
| Small pathway, few genes overlap | Low | May be high | Even a few genes in a small pathway can be very significant |
| Medium pathway, proportional overlap | Medium | Not significant | Overlap is consistent with chance |
| Small pathway, many genes overlap | High | High | Strong evidence of association |
