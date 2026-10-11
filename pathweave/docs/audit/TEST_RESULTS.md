# PathWeave — Automated Testing & Software Verification Report

## 1. Test Execution Summary

- **Date & Time**: 2026-10-11T21:39:27+05:30
- **Operating Environment**: Windows 11 (win32), Python 3.13.14, pytest 8.3.4, pluggy 1.6.0
- **Test Command**: `python -m pytest tests -v --tb=short` (executed from `backend/`)
- **Exit Code**: `0` (Success)
- **Log Location**: `docs/audit/logs/test_run.log`
- **Total Test Cases Executed**: 48
- **Results**: **48 passed, 0 failed, 0 skipped, 0 errored** (Execution duration: 14.48s)

---

## 2. Test Breakdown by Module

| Test Module | Total Tests | Passed | Failed | Skipped | Scope & Focus |
|---|---|---|---|---|---|
| `tests/test_audit_validation.py` | 5 | 5 | 0 | 0 | Contingency table consistency, SciPy Fisher equivalence, null model determinism, p-value boundaries, FDR threshold filtering |
| `tests/test_cross_validation.py` | 6 | 6 | 0 | 0 | Reactome and QuickGO lookups for TP53/BRCA1, external API failure tolerance, normalized cross-database pathway matching |
| `tests/test_ensembl_transcripts.py` | 7 | 7 | 0 | 0 | Ensembl transcript expansion, Ensembl gene ID resolution, HTTP 500 retry logic, partial failure isolation |
| `tests/test_kegg_identifiers.py` | 6 | 6 | 0 | 0 | KEGG organism entry parsing, gene symbol resolution (`TP53` -> `hsa:7157`), pathway link retrieval, disease link parsing |
| `tests/test_rna_network.py` | 6 | 6 | 0 | 0 | Mixed input type separation, miRNA target normalization, lncRNA target absence handling, STRING PPI deduplication, connected-component clustering |
| `tests/test_scoring.py` | 18 | 18 | 0 | 0 | Gene weighting formula with single/multiple/mixed RNAs, seed gene weight preservation, Jaccard similarity metrics, Fisher scoring, BH-FDR correction, redundancy merging |
| **Total Backend Test Suite** | **48** | **48** | **0** | **0** | **100% Pass Rate** |

---

## 3. Individual Test Case Inventory

### `tests/test_audit_validation.py` (Added During Comprehensive Audit)
1. `test_contingency_table_consistency` — PASSED: Verifies that cells `a`, `b`, `c`, `d` are all non-negative, `a + b == len(query_genes)`, `a + c == pathway_size`, and `a + b + c + d == background_size`.
2. `test_fisher_exact_matches_scipy` — PASSED: Confirms that `score_pathways` Fisher p-value matches `scipy.stats.fisher_exact` to machine precision (< 1e-12).
3. `test_null_model_deterministic_sampling` — PASSED: Confirms that repeated runs with identical random seed produce byte-for-byte identical null distributions.
4. `test_empirical_pvalue_boundary_and_zero_prevention` — PASSED: Evaluates proportion calculations and documents behavior when observed score exceeds all nulls.
5. `test_fdr_threshold_filtering_consistency` — PASSED: Confirms that strict vs lenient FDR thresholds filter monotonically.

### `tests/test_cross_validation.py`
6. `test_tp53_reactome_lookup` — PASSED
7. `test_brca1_reactome_lookup` — PASSED
8. `test_tp53_go_lookup` — PASSED
9. `test_brca1_go_lookup` — PASSED
10. `test_external_api_failure_is_reported` — PASSED
11. `test_cross_database_matching_is_transparent` — PASSED

### `tests/test_ensembl_transcripts.py`
12. `test_known_gene_transcripts[TP53-ENSG00000141510-ENST00000269305]` — PASSED
13. `test_known_gene_transcripts[BRCA1-ENSG00000012048-ENST00000357654]` — PASSED
14. `test_known_gene_transcripts[BRCA2-ENSG00000139618-ENST00000380152]` — PASSED
15. `test_invalid_gene_warns` — PASSED
16. `test_tp53_transient_http_500_then_success` — PASSED
17. `test_tp53_persistent_http_500_warns` — PASSED
18. `test_partial_failure_preserves_successes` — PASSED

### `tests/test_kegg_identifiers.py`
19. `test_parse_gene_identifier` — PASSED
20. `test_resolve_tp53_identifier` — PASSED
21. `test_gene_pathway_lookup_uses_resolved_entry[TP53-hsa:7157]` — PASSED
22. `test_gene_pathway_lookup_uses_resolved_entry[BRCA1-hsa:672]` — PASSED
23. `test_invalid_gene_warns` — PASSED
24. `test_kegg_disease_links_parse_ds_entries` — PASSED

### `tests/test_rna_network.py`
25. `test_mixed_input_resolution_never_treats_rnas_as_genes` — PASSED
26. `test_mirna_relationships_are_normalized` — PASSED
27. `test_lncrna_resolution_reports_missing_curated_targets` — PASSED
28. `test_external_failure_isolated_for_string` — PASSED
29. `test_string_interactions_and_network_edges_are_deduplicated` — PASSED
30. `test_network_clustering_and_shared_unique_associations` — PASSED

### `tests/test_scoring.py`
31. `test_gene_weight_validated_single_rna` — PASSED
32. `test_gene_weight_predicted_single_rna` — PASSED
33. `test_gene_weight_two_validated_rnas` — PASSED
34. `test_gene_weight_mixed_evidence` — PASSED
35. `test_seed_gene_gets_weight_one` — PASSED
36. `test_four_rnas_weight` — PASSED
37. `test_jaccard_identical` — PASSED
38. `test_jaccard_disjoint` — PASSED
39. `test_jaccard_partial` — PASSED
40. `test_jaccard_empty` — PASSED
41. `test_score_pathways_high_overlap` — PASSED
42. `test_score_pathways_min_overlap_filter` — PASSED
43. `test_score_pathways_coverage` — PASSED
44. `test_score_pathways_multiple_fdr` — PASSED
45. `test_merge_identical_pathways` — PASSED
46. `test_merge_disjoint_pathways` — PASSED
47. `test_merge_partial_overlap_above_threshold` — PASSED
48. `test_merge_partial_overlap_below_threshold` — PASSED

---

## 4. Frontend Production Build Verification

- **Command**: `npm run build` (executed from `frontend/`)
- **Environment**: Node.js `v24.18.0`, npm `11.16.0`, Vite `v8.3.2`, TypeScript `5.x`
- **Exit Code**: `0` (Success)
- **Duration**: `3.10s`
- **Output Artifacts**:
  - `dist/index.html` (1.06 kB)
  - `dist/assets/index-icxgZS2V.css` (27.30 kB)
  - `dist/assets/cytoscape.esm-D6xx22XN.js` (434.86 kB)
  - `dist/assets/index-BudZZ0s_.js` (972.34 kB)
- **Status**: Production build succeeds cleanly without TypeScript compilation errors. Vite reports a non-blocking chunk-size advisory on `index-BudZZ0s_.js` exceeding 500 kB.

---

## 5. Test Classification & Coverage Distinction

1. **Unit Tests (42 tests)**:
   - Gene weighting math, contingency tables, Fisher's exact tests, BH-FDR correction, Jaccard clustering, RNA identifier normalization, mock network clustering.
2. **Integration / Fault Tolerance Tests (6 tests)**:
   - External service retry logic (Ensembl HTTP 500 retry), partial API failure isolation (QuickGO, Reactome, STRING API errors handled gracefully with warning strings rather than exceptions).
3. **Live External API Tests**:
   - Not run inside the automated pytest suite (tests use unittest.mock / httpx MockTransport to guarantee deterministic CI execution). Live API connectivity was verified independently during audit execution (Section 4).
4. **End-to-End Build**:
   - Confirmed through full backend FastAPI startup verification and frontend production build compilation.
