# 10 Validation results

Authoritative invocation: `PYTHONPATH=. pytest` (README-documented; CI uses `PYTHONPATH: .`).

| Check | Command | Result | When |
|---|---|---|---|
| Full test suite | `PYTHONPATH=. pytest -q` | **126 passed, 2 skipped** | S2 |
| Syntax | `python -m py_compile ocman.py ocman_tui/app.py ocman_tui/core.py` | OK | S2 |
| Import | `PYTHONPATH=. python -c "import ocman"` | OK (v1.0.4) | S2 |
| CLI smoke | `ocman --version` / `--help` | `ocman 1.0.4`; help renders | S2 |
| Secrets/PII | `scan_secrets.py` (tree+history) + gitleaks + detect-secrets | 4432 candidates, all false positives | S2 |

## Delta test-coverage assessment (S3)
Strong. Covered: process lock (5 tests), `dir_usage`, `render_destructive_preview` (3), `cli_clean_backups`
(6: cancel/dry-run/keep-delete/all-deleted-warning), compacted-copy (11), disk `preprocess_argv` alias.
Gaps (all Low): `_per_project_disk_usage` (T1), focused `confirm_destructive`/`_project_for_cwd` (T2).

## Environment note (S3-R1)
`ocman` is installed **editable** here (points at this repo), so bare `pytest` resolves local source; CI uses
`PYTHONPATH=.`. Residual risk only for a fresh non-editable install; documented in README.

## The "2 skipped"
Opt-in perf benchmarks (`tests/test_perf.py`, gated by `OCMAN_BENCHMARK=1`). Intentional; never a CI gate.
