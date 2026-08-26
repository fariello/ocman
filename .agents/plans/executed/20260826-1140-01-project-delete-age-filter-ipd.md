# IPD: `ocman project delete PROJECT --age AGE` session filtering

- Date: 2026-08-26
- Concern: capability + CLI ergonomics. Currently `ocman project delete PROJECT` recursively
  deletes the entire project record and all its sessions. The user wants `ocman project delete
  PROJECT --age AGE` to only delete sessions in the PROJECT that are older than AGE (e.g. 1h, 3d,
  5w, 9m, 1y), while preserving the project itself and any newer sessions.
- Scope: `ocman/cli.py` (`parse_duration_to_days` unit extension for `m`, `build_parser` `--age`
  flag on `project delete`, `_normalize` parsing, `db_delete_project_recursive` age cutoff support,
  `main` and `_run_pending_manifest_items` wiring), `tests/test_ocman.py`, `README.md`.
- Status: executed
- Target version: rides the current in-flight line.
- Approval: maintainer requested 2026-08-26.

## Workflow history
- 2026-08-26: maintainer requested adding `--age AGE` filtering to `ocman project delete PROJECT`
  supporting compact units (1h, 3d, 5w, 9m, 1y) to only delete sessions older than AGE.
- 2026-08-26 execution: added `m` unit to duration parser, added `--age` / `--older-than` flag
  to `project delete` parser, normalized age to days, added age cutoff filtering to
  `db_delete_project_recursive` that skips project row deletion when filtering by age, updated
  `README.md`, added unit and integration tests covering parser, age filtering, dry-run, negative
  error handling, and pending actions replay.

## Evidence
- `parse_duration_to_days` (`cli.py:4996`) parses duration strings into fractional days.
  Added `m` as an alias for `mo` (30.0 days) to enable standard monthly age expressions like `9m`.
- `db_delete_project_recursive` (`cli.py:9324`) queries sessions using `session_tree` CTE.
  When `days` is provided, the root query filters `WHERE project_id = ? AND time_created < ?`
  with cutoff epoch milliseconds, deletes matching session rows and disk files, and skips
  deleting the `project` table row.
- When `session_ids` matching the age cutoff is empty, `db_delete_project_recursive` prints a
  clear message ("No sessions found in project ... older than ...") and returns without changes.

## Design decisions
- Flag name: `--age` (with alias `--older-than` for parity with `db clean`).
- Project row preservation: when `--age` is specified, only matching sessions are deleted. The
  project row itself is NEVER deleted when `--age` is active, even if all current sessions match.
- Units supported: `h` (hours), `d` (days), `w` (weeks), `m` / `mo` (months, ~30d), `y` (years, ~365d),
  bare numbers (treated as days), or spelled-out units (e.g. "30 days").
- Pending actions: `--pend` on `project delete` preserves the `--age` / `days` argument when
  saving to `.agents/pending.json` and passes it through upon `ocman pending run`.

## Detailed Implementation Checklist (TODO)
- [x] C1 Support `m` (month) in `_DURATION_UNIT_DAYS` and `_DURATION_COMPACT_RE` in `ocman/cli.py`.
- [x] C2 Add `--age` / `--older-than` flag to `p_project.delete` subparser in `build_parser()` in `ocman/cli.py`.
- [x] C3 In `_normalize()`, parse `g("age")` via `parse_duration_to_days()` and store in `out["days"]` / `out["age"]`.
- [x] C4 Update `db_delete_project_recursive` to accept `days: float | None = None`. When `days` is set, filter `time_created < cutoff_time`, skip deleting the project row, and report session cleanup accurately.
- [x] C5 Wire `days` through `main()` and `_run_pending_manifest_items()` for `project-delete`.
- [x] C6 Update `README.md` project delete documentation.
- [x] C7 Add comprehensive unit and integration tests in `tests/test_ocman.py`.
- [x] C8 Run full test suite and paste actual output.
- [x] C9 Move IPD to `executed/` upon verification.

## Execution record
- Full test run output:
```
============================= 320 passed in 38.21s =============================
```
