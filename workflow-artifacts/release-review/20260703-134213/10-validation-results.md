# 10 Validation Results

| Command/check | Result | Notes |
|---|---|---|
| `PYTHONPATH=. pytest` (initial) | 56 passed | Baseline before fixes |
| `PYTHONPATH=. pytest` (final) | **58 passed** | 56 + 2 new regression tests |
| `python -c "ast.parse(ocman.py); ast.parse(app.py)"` | OK | Syntax valid after edits |
| `import ocman, ocman_tui` | OK | ocman 1.0.3 / tui 1.0.3 (single-sourced) |
| `test_restore_rejects_zip_slip` | pass | Zip-Slip regression (S3-T1) |
| `test_tui_app_deletion_metadata_fetch_fails` | pass | delete-summary regression (S3-T2) |
| `git status --short` | clean (only new artifact) | No stray/unrelated changes committed |

## Not run (with reason)
- Lint / type check: no repo-native tooling configured; type checker produces many pysqlite3/textual
  false positives. Not part of release validation for this project.
- Manual TUI smoke: the reported crash path (move/export/import) is covered by the API-correctness fix and
  the existing TUI tests; a live terminal session was not run in this non-interactive environment.
