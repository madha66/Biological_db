# Ranking Algorithm

## Formula

```
Ranking Score = Pathway Score × -log₁₀(Adjusted p-value)
```

Where:
- **Pathway Score** = (Input genes in pathway) / (Total valid input genes) — ranges from 0 to 1
- **Adjusted p-value** = Benjamini–Hochberg FDR-corrected p-value from Fisher's exact test
- **-log₁₀(Adjusted p-value)** transforms the p-value into a positive score where smaller (more significant) p-values yield higher scores

The adjusted p-value is floored at **ε = 10⁻³⁰⁰** to avoid `-log₁₀(0)`.

## Why This Formula?

1. **Representation alone is insufficient**: A pathway that contains many genes (e.g., "Metabolic pathways") may overlap with many input genes purely by chance, without being biologically interesting.

2. **Statistical significance alone is insufficient**: A pathway might be statistically enriched with just 1 gene if that pathway is very small — but a pathway with only 1 contributing gene may not be practically informative.

3. **The product balances both**: By multiplying representation × significance, the ranking naturally favors pathways that are both well-represented in the input gene set AND statistically enriched beyond chance.

4. **-log₁₀ scaling**: The log transform converts multiplicative differences in p-values to additive differences. A p-value of 10⁻⁶ is scored twice as high as 10⁻³, reflecting the substantial difference in statistical evidence.

5. **Determinism**: Given the same input genes, organism, and KEGG database state, the ranking will always produce the same result. Ties (identical ranking scores) are broken by input gene count (higher count ranked first).

## Implementation

The ranking score is computed in `backend/app/analysis/ranking.py`:

```python
def compute_ranking_score(pathway_score: float, adjusted_p_value: float) -> float:
    clamped_p = max(adjusted_p_value, PVALUE_EPSILON)  # Floor at 1e-300
    neg_log_p = -math.log10(clamped_p)
    return round(pathway_score * neg_log_p, 6)
```

## Worked Numeric Example

### Input
- **Total valid input genes**: 6 (TP53, BRCA1, EGFR, AKT1, PTEN, MYC)
- **Organism**: Human (hsa)
- **Background universe**: 7,500 genes

### Pathway A: "p53 signaling pathway"
- Input genes in pathway: **3** (TP53, BRCA1, PTEN)
- Pathway score: 3/6 = **0.5000**
- Fisher's raw p-value: 0.00014
- Adjusted p-value: **0.00042**
- -log₁₀(0.00042) = **3.3768**
- **Ranking Score** = 0.5000 × 3.3768 = **1.6884**

### Pathway B: "MAPK signaling pathway"
- Input genes in pathway: **2** (EGFR, MYC)
- Pathway score: 2/6 = **0.3333**
- Fisher's raw p-value: 0.12
- Adjusted p-value: **0.18**
- -log₁₀(0.18) = **0.7447**
- **Ranking Score** = 0.3333 × 0.7447 = **0.2482**

### Pathway C: "Metabolic pathways" (very large pathway)
- Input genes in pathway: **4** (TP53, EGFR, AKT1, PTEN)
- Pathway score: 4/6 = **0.6667**
- Fisher's raw p-value: 0.45 (not significant — large pathway, overlap is expected by chance)
- Adjusted p-value: **0.55**
- -log₁₀(0.55) = **0.2596**
- **Ranking Score** = 0.6667 × 0.2596 = **0.1731**

### Final Ranking

| Rank | Pathway | Input Genes | Pathway Score | Adj. p-value | Ranking Score |
|------|---------|------------|---------------|-------------|---------------|
| 1 | p53 signaling pathway | 3 | 0.5000 | 0.00042 | **1.6884** |
| 2 | MAPK signaling pathway | 2 | 0.3333 | 0.18 | **0.2482** |
| 3 | Metabolic pathways | 4 | 0.6667 | 0.55 | **0.1731** |

**Key insight**: Pathway C has the highest representation score (0.667) but the lowest ranking score (0.173) because it is not statistically enriched. Pathway A ranks highest because it has both substantial representation AND strong statistical significance.

## Edge Cases

- **Adjusted p-value = 1.0**: -log₁₀(1) = 0, so Ranking Score = 0. These pathways are not enriched.
- **Very small p-values**: Floored at ε = 10⁻³⁰⁰ to prevent numerical overflow.
- **Pathway Score = 0**: Impossible in practice — a pathway only enters the analysis if at least one input gene maps to it.
