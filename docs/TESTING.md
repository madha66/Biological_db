# Testing Strategy and Test Suite

KEGGPathRank includes an automated test suite covering unit, statistical, edge-case, and integration scenarios.

---

## Test Organization

The tests are located in `backend/tests/`:

| File | Scope | Key Assertions |
|------|-------|----------------|
| `test_preprocessing.py` | Gene Normalization | Trimming, uppercase conversion, duplicate removal, invalid delimiter handling, empty list rejection. |
| `test_kegg_service.py` | KEGG API Client & Cache | Request retries, exponential backoff, URL construction, organism mapping, caching mechanics, network error handling. |
| `test_statistics.py` | Enrichment & Multiple Testing | 2×2 contingency table construction, Fisher's exact test (one-sided `greater`), Benjamini–Hochberg FDR monotonicity and edge cases (all $p=0$, all $p=1$, empty). |
| `test_ranking.py` | Ranking Formula | Ranking score computation ($S = \text{Score} \times -\log_{10}(p_{\text{adj}})$), sorting order, tie-breaking, extreme values handling. |
| `test_api_integration.py` | End-to-End FastAPI Routes | `/api/health`, `/api/organisms`, `/api/analyze`, `/api/pathway/{id}`, 400 bad requests, 404 missing pathways, 502 upstream errors. |

---

## Running the Test Suite

Execute pytest across all test files:

```bash
# Windows PowerShell
$env:PYTHONPATH = "backend"
python -m pytest backend/tests/ -v

# Linux / macOS
PYTHONPATH=backend pytest backend/tests/ -v
```

---

## Coverage and Reliability

- **Total Test Cases**: 44 automated tests.
- **Pass Rate**: 100% (44 / 44 passed).
- **Mocking**: External KEGG network calls in integration tests are mocked to enable fast, deterministic CI execution without depending on KEGG API availability or rate limits.
