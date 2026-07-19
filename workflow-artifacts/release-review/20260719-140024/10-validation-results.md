# Validation results

## Full test suite (regression gate) - Section 3
Command: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`
Result: **407 passed, 2 skipped in 106.80s.**
- The 2 skips are `tests/test_perf.py` benchmarks, gated on `OCMAN_BENCHMARK=1` (informational).
- Test inventory: test_ocman.py 220, test_tui.py 32, test_config_backup_restore.py 16,
  test_core.py 6, test_perf.py 2 (276 test functions).

## New-feature regression coverage (this release cycle)
Each shipped feature carries dedicated tests (43 matched by name):
- extract-on-delete (CLI + TUI), gather_spend + spend JSON, storage doctor/reclaim
  (render+totals, checkpoint+VACUUM, refuse-while-running, no-snapshot-control),
  running (render+banner, fail-loud), batch multi-select delete/export, db-clean
  duration/scope, chunk `.part-NNofMM`, clear-history, config preserve-unmanaged-keys,
  db_not_found hint, unexpected-exception traceback guard, bare-word help.

## Packaging / build - deferred to Section 6.

## Section 7 (post-implementation) re-validation
- `ocman -V` -> `ocman 1.2.0`.
- `gitleaks detect` (353 commits) -> **no leaks found** (baseline effective).
- Full suite re-run: **407 passed, 2 skipped** (unchanged; bump/CHANGELOG/baseline are
  non-behavioral).
- `python -m build --wheel` -> **ocman-1.2.0-py3-none-any.whl** built cleanly.
