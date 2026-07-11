# Commit Log

- **Run ID**: 20260617-193252

The following local commit was made to track the changes implemented in this run:

## Commit Details

- **Commit Hash**: 8f08a6afc2099e3229a59c96a8f62a1da1a3cfd3
- **Author**: Gabriele Fariello <gabriele.fariello@gmail.com>
- **Date**: 2026-06-17T19:44:15+02:00
- **Branch**: main
- **Commit Message**:
  ```text
  release-review[20260617-193252]: Implement unified ocman TUI, refactor to async background workers, immediate temp file cleanup, fixed duplicate sidebar nodes, implemented CLI history resetting, updated pyproject package name, updated GHA matrix, and removed obsolete files. Refs 20260617-193252-S2-A1, 20260617-193252-S2-A2, 20260617-193252-S3-A1, 20260617-193252-S4-A1, 20260617-193252-S4-A2, 20260617-193252-S5-A1, 20260617-193252-S5-A2, 20260617-193252-S6-A1, 20260617-193252-S6-A2.
  ```

## Files Changed

| File Path | Action | Description | Refs |
|---|---|---|---|
| [ocman_tui/widgets/database.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/database.py) | Modified | Refactored prune operations to background workers, thread-safe logger. | `20260617-193252-S2-A1` |
| [ocman_tui/app.py](file:///home/gfariello/VC/ocman/ocman_tui/app.py) | Modified | Refactored deletion to background worker, unlink temp file immediately. | `20260617-193252-S2-A1`, `20260617-193252-S2-A2` |
| [ocman_tui/widgets/sidebar.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/sidebar.py) | Modified | Prevent duplicate nested nodes in Tree view. | `20260617-193252-S5-A1` |
| [ocman.py](file:///home/gfariello/VC/ocman/ocman.py) | Modified | Fully implemented CLI history resetting `--clear-history`. | `20260617-193252-S5-A2` |
| [pyproject.toml](file:///home/gfariello/VC/ocman/pyproject.toml) | Modified | Updated name to `ocman` (retired legacy orsession name). | `20260617-193252-S6-A1` |
| [.github/workflows/ci.yml](file:///home/gfariello/VC/ocman/.github/workflows/ci.yml) | Modified | Added Python 3.14 to CI matrix. | `20260617-193252-S6-A2` |
| [tests/test_tui.py](file:///home/gfariello/VC/ocman/tests/test_tui.py) | Modified | Added unit tests for deletion and pruning background workers. | `20260617-193252-S3-A1` |
| [README.md](file:///home/gfariello/VC/ocman/README.md) | Modified | Updated requirements and usage instructions (no standalone `orsession`). | `20260617-193252-S4-A1` |
| [SPEC-orsession.md](file:///home/gfariello/VC/ocman/SPEC-orsession.md) | Deleted | Removed obsolete specification documentation. | `20260617-193252-S4-A2` |
| [opencode_db_cleanup_handoff_for_claude.md](file:///home/gfariello/VC/ocman/opencode_db_cleanup_handoff_for_claude.md) | Deleted | Removed stale handoff document. | `20260617-193252-S4-A2` |
| [scripts/check_orsession.sh](file:///home/gfariello/VC/ocman/scripts/check_orsession.sh) | Deleted | Removed diagnostics script for retired orsession. | `20260617-193252-S4-A2` |

## Validation Summary

All 20 unit tests passed successfully via `PYTHONPATH=. pytest -v` on Python 3.14.4 before committing.
