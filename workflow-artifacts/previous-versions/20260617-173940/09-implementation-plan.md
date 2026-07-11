# Implementation Plan - 20260617-173940

This plan outlines the implementation phase for hardening the `ocman` CLI and `orsession` TUI application.

## User Review Required

> [!IMPORTANT]
> - There are no breaking changes to the CLI arguments or TUI flows.
> - The standalone nature of `ocman.py` is fully preserved. It still requires zero third-party dependencies to run.
> - A new pytest-based testing suite is added under `tests/`. Running tests will require installing dev dependencies (`pytest`).
> - A simple GitHub Actions CI workflow is added under `.github/workflows/ci.yml` to run automated testing and lint check on pushes/PRs.

## Proposed Changes

### Database & Security Hardening (`ocman.py`)

#### [MODIFY] [ocman.py](file:///home/gfariello/VC/ocman/ocman.py)
- **SQLite Transactions**: Update `db_delete_session_recursive` and `db_run_cleanup` to wrap connections in `try...except...finally` blocks (or use Python's context manager). If any exception is raised during deletion or vacuuming, explicitly call `conn.rollback()`. Ensure `conn.close()` is always run in a `finally` block to prevent resource leaks.
- **Path Traversal Protection**: Sanitize the session ID input (`session_id`/`sid`) in the file-deletion routines (`files_to_delete`) to verify that the resolved path is located strictly within the expected `storage_dir` (`Path.resolve()` boundary checks).
- **Subprocess Export Timeout**: Add a timeout (e.g. 120s) to the `subprocess.run("opencode", "export", ...)` call in `ocman.py` to prevent infinite hangs.

### TUI Interval Cleanup (`orsession`)

#### [MODIFY] [app.py](file:///home/gfariello/VC/ocman/orsession/app.py)
- **Interval Timers**: Store the interval Timer object returned by `set_interval(...)` when kicking off background threads (export, compaction, pipeline). Call `timer.stop()` upon thread completion, error, or cancellation to release event loop cycles.

### Automated Testing (`tests/`)

#### [NEW] [test_core.py](file:///home/gfariello/VC/ocman/tests/test_core.py)
- Add unit tests for:
  - Configuration reference expansion (`expand_config_refs` with environment and file refs).
  - Model extraction and resolution (`extract_models_from_config`, `resolve_model`).
  - Turn extraction and consolidation (`extract_turns_from_export`, `consolidate_turns`).
  - Truncation algorithms (`truncate_turns_by_interactions`, `truncate_turns_by_lines`).

#### [NEW] [test_ocman.py](file:///home/gfariello/VC/ocman/tests/test_ocman.py)
- Add database-level testing using a mock/temporary in-memory SQLite database mimicking the `opencode.db` structure to verify:
  - `db_list_projects` and `db_list_sessions`.
  - Recursive sub-session descendant resolution.
  - Deletion count checks.
  - Safe ID sanitization.

### Continuous Integration (`.github/`)

#### [NEW] [ci.yml](file:///home/gfariello/VC/ocman/.github/workflows/ci.yml)
- Add GitHub Actions CI workflow checking code style/syntax and running `pytest` tests on python 3.10 through 3.14.

### Documentation & Deprecations

#### [MODIFY] [README.md](file:///home/gfariello/VC/ocman/README.md)
- Update the `All Arguments` table and add examples for database retention cleaning (`--days`, `--clean-orphans`, `--db`, `--dry-run`, `--force`, `--delete`).

#### [MODIFY] [rebuild_opencode.sh](file:///home/gfariello/VC/ocman/rebuild_opencode.sh)
- Add a deprecation banner/comment at the top suggesting the use of `ocman --clean` instead.

---

## Verification Plan

### Automated Tests
- Run `pytest` locally to verify that all newly introduced test cases pass:
  ```bash
  /home/gfariello/venv/p3.14/bin/pytest -v
  ```

### Manual Verification
- **TUI Verification**: Launch the TUI using `orsession` and verify that session detail browsing, export, and compaction function correctly and do not trigger hanging processes or deadlocks.
- **CLI Verification**: Run `ocman --clean --days 30 --dry-run` and `ocman --clean-orphans --dry-run` to verify dry-run outputs match database contents safely.
- **Security Check**: Verify that trying to delete a session ID with traversal characters (e.g. `../test`) throws an explicit validation error and refuses to delete anything.
