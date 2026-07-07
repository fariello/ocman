# 06-commands

(run 20260707-004045)

## Section 2
- scan_secrets.py -> secrets-scan.json: 1587 candidates, all low/medium, 0 high. High-entropy =
  session ids; "credit-card" mediums = 2026... recovery timestamps (false positives).
- gitleaks detect (tree + 229 commits): "no leaks found" (authoritative).
- PYTHONPATH=. pytest: 172 passed, 2 skipped.

## Section 6
- python -m build --wheel: built ocman-1.1.0-py3-none-any.whl. Wheel contents: ocman.py +
  ocman_tui/* only; scripts/migrate_recovery_names.py ABSENT (=> C1).
- twine check dist/ocman-1.1.0*: PASSED.
