# IPD: Per-project historical spend accounting and reporting

- Date: 2026-08-28
- Concern: functionality + reporting accuracy. When all sessions for a repository are deleted, `ocman spend /path/to/repo` reports $0.00 with 0 sessions, losing track of historical LLM spend incurred on that project.
- Scope: `ocman/cli.py` (`gather_deletion_metrics`, `save_deletion_metrics`, `_load_history`, `_get_project_history`, `cli_spend`, `gather_spend`), `tests/test_ocman.py`, `README.md`.
- Status: executed
- Target version: rides the current in-flight line.
- Approval: maintainer requested 2026-08-28.

## Workflow history
- 2026-08-28: maintainer reported that `ocman spend ~/VC/agent-workflows` returns $0.00 when all sessions are deleted even though cost was incurred. Filed GitHub Issue #2.
- 2026-08-28 execution: enhance deletion metrics gathering and historical ledger to retain per-project cost and token attribution, update `cli_spend` to report historical spend for project-level queries, update `gather_spend` for zero-session projects under `--historical`, update tests and documentation.

## Evidence
- `cli_spend` (`cli.py:13567`) inspects active sessions from `db_list_sessions(proj_id)` only. If all sessions for a project are deleted, `rows` is empty and returns `$0.00`.
- The `if project or sessions:` branch in `cli_spend` ignores the `historical` flag and does not read the history ledger.
- `gather_deletion_metrics` (`cli.py:12645`) aggregates cost globally across deleted session IDs without recording `project_id`, `worktree`, or per-project sub-totals.
- `_load_history` and `save_deletion_metrics` (`cli.py:12402`, `12756`) store deleted costs into global `cumulative.cost_deleted` only.
- `db_list_projects` (`cli.py:4204`) filters `HAVING session_count > 0`, omitting projects with 0 live sessions from global spend listings.

## Design decisions
- History ledger format: Extend `cumulative` in `ocman_history.json` with an optional `by_project` mapping `{project_id: {"project_id": str, "worktree": str, "cost_deleted": float, "tokens_input_deleted": int, "tokens_output_deleted": int, "tokens_cache_read_deleted": int, "sessions_deleted": int}}`.
- Deletion metrics capture: In `gather_deletion_metrics`, join `session` with `project` to extract `project_id`, `worktree`, per-session costs and token split, and build `stats["by_project"]`.
- Project history lookup: Introduce `_get_project_history(target_id_or_path)` which matches projects in `cumulative["by_project"]` by exact ID, exact worktree, resolved/normalized path, or directory name.
- Project spend command (`ocman spend <project>`):
  - When live sessions exist: show live table and total. If historical spend exists, show note or `--historical` breakdown.
  - When 0 live sessions exist but historical spend exists: display 0 live sessions, historical cost/tokens breakdown, and grand total so cost is not reported as $0.
  - Support `--historical` and `--json` envelopes for project-scoped queries.
- Global spend command (`ocman spend --historical`): Include projects with 0 live sessions if they have historical spend recorded in the ledger.

## Detailed Implementation Checklist (TODO)
- [x] C1 Update `gather_deletion_metrics` in `ocman/cli.py` to join `project` and capture `project_id`, `worktree`, and build `by_project` metrics.
- [x] C2 Update `save_deletion_metrics` and `_load_history` in `ocman/cli.py` to persist and maintain `cumulative["by_project"]`.
- [x] C3 Add `_get_project_history()` helper in `ocman/cli.py` to resolve project historical data by ID or path.
- [x] C4 Update `cli_spend()` in `ocman/cli.py` to support historical spend display and `--historical` for project queries.
- [x] C5 Update `gather_spend()` in `ocman/cli.py` to account for projects with 0 live sessions when `historical=True`.
- [x] C6 Update `README.md` spend documentation if needed.
- [x] C7 Add comprehensive unit tests in `tests/test_ocman.py` for per-project deletion metrics and historical spend reporting.
- [x] C8 Run full test suite and paste actual output.
- [x] C9 Move IPD to `executed/` and update status upon verification.

## Execution record
- Full test run output:
```
======================= 493 passed, 2 skipped in 47.31s ========================
======================== 79 passed in 120.16s (0:02:00) ========================
======================= 572 passed, 2 skipped in 167.47s =======================
```
