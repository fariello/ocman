# Validation results (run 20260707-004045)

- Baseline (S1): `PYTHONPATH=. pytest` -> 172 passed, 2 skipped.
- After S7 fixes: `PYTHONPATH=. pytest` -> **174 passed, 2 skipped** (+2: S2-E1 read-before-cap
  test, new TUI parity test; augmented TUI e2e test).
- Packaging: `python -m build --wheel` rebuilt; wheel now CONTAINS
  scripts/migrate_recovery_names.py (S6-C1 verified). `twine check` PASSED.
- `ocman --help`: --force text now notes the filter/--compact size-cap override (S5-U1 verified).
- Secrets: gitleaks (tree + 229 commits) "no leaks found"; built-in scanner candidates triaged as
  false positives (session ids, recovery timestamps).
