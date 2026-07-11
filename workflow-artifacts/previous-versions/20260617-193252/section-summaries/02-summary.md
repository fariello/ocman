# Section 2 Summary - Quality, Security, and Edge Cases

- **Run ID**: 20260617-193252

## Highest-Priority Findings

### 20260617-193252-S2-E1: Blocking DB Operations in Event Loop
- **Severity**: Medium (Usability / Concurrency)
- **Affected Area**: `ocman_tui/widgets/database.py` and `ocman_tui/app.py`
- **Evidence**: `run_prune_operation()` in `database.py` and `confirm_and_delete_session()` in `app.py` call synchronous database routines (`db_run_cleanup` and `db_delete_session_recursive` which executes SQL transactions and `VACUUM`) on the main thread.
- **Impact**: For large databases, prune operations or recursive deletions can lock/freeze the Textual TUI interface for several seconds, disabling clock updates, navigations, and responsiveness.
- **Recommended Fix**: Execute these heavy operations inside background worker threads using `threading.Thread` and update status displays and progress indicators via `self.call_from_thread`.

### 20260617-193252-S2-E2: Temp Export File Leakage
- **Severity**: Low (Resource Handling)
- **Affected Area**: `ocman_tui/app.py` background `export_worker`
- **Evidence**: Each session selection calls `write_export_to_temp` which dumps a session export JSON into `self.temp_dir`. The files are only deleted on application unmount.
- **Impact**: If a user navigates through many sessions in a single TUI run, large temporary JSON files accumulate in `/tmp` occupying disk space unnecessarily.
- **Recommended Fix**: Unlink the temporary export file as soon as it has been loaded and parsed into memory inside the worker thread.

---

## Action Plan

### 20260617-193252-S2-A1: background Threading for DB Operations
- **Source Finding**: `20260617-193252-S2-E1`
- **Target**: Refactor TUI database cleans and deletions to run in background worker threads.

### 20260617-193252-S2-A2: Immediate Temp Export Unlinking
- **Source Finding**: `20260617-193252-S2-E2`
- **Target**: Unlink the JSON export file immediately after parsing it in `export_worker`.
