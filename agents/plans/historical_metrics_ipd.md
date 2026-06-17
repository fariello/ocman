# Implementation Plan Document (IPD) - Historical Deletion Metrics Sidecar

This document details the design and implementation plan to persist cumulative metrics of deleted database records (projects, sessions, subagents, messages, token counts, and API costs) in a sidecar JSON file, allowing `ocman info` to display both active and historical usage metrics.

---

## 1. Problem Statement
When running `ocman --clean` or `ocman --delete`, sessions and messages are permanently purged from `opencode.db` to reclaim disk space. Consequently, historical usage details (such as total LLM tokens used, total API cost, and total subagents spawned) are lost. The `ocman info` command can only query current/active database states.

---

## 2. Design & Architecture

We will implement a **Sidecar JSON Ledger** located at:
`~/.local/share/opencode/ocman_history.json`

### Why JSON Sidecar?
- **Isolation**: Prevents any changes/risks to the core `opencode.db` schema.
- **Persistence**: Survives database recreations or rebuild scripts (e.g. `rebuild_opencode.sh`).
- **Simplicity**: No database locking issues or complex SQLite schema upgrades.

### Schema of `ocman_history.json`
```json
{
  "cumulative": {
    "projects_deleted": 0,
    "sessions_deleted": 0,
    "subagents_deleted": 0,
    "messages_deleted": 0,
    "cost_deleted": 0.0,
    "tokens_input_deleted": 0,
    "tokens_output_deleted": 0
  },
  "runs": [
    {
      "timestamp": "2026-06-17 19:00:00",
      "reason": "clean" or "delete",
      "sessions_count": 12,
      "subagents_count": 3,
      "messages_count": 412,
      "cost": 0.3542,
      "tokens_input": 12000,
      "tokens_output": 5400
    }
  ]
}
```

---

## 3. Proposed Changes

### Component 1: `ocman.py` (Core Library)

#### [MODIFY] [ocman.py](file:///home/gfariello/VC/ocman/ocman.py)

1.  **Define History Path and Helper Functions**:
    - Add `OPENCODE_HISTORY_PATH = Path.home() / ".local" / "share" / "opencode" / "ocman_history.json"`.
    - Create `_load_history()`: Safely loads the JSON structure, returning default template if missing or corrupted.
    - Create `_save_history(data)`: Atomically writes history back to the JSON file using a temp file write-and-rename pattern.
    - Create `record_deletion_run(reason, session_ids, conn)`:
      - Connects to SQLite and queries aggregates for `session_ids` before they are deleted:
        - `cost` sum
        - `tokens_input` sum
        - `tokens_output` sum
        - Total sessions count (`COUNT(*)`)
        - Subagent count (`COUNT(*) WHERE parent_id IS NOT NULL AND parent_id != ''`)
        - Messages count (`SELECT COUNT(*) FROM message WHERE session_id IN (...)`)
      - Loads the ledger, increments `cumulative` fields, appends a run log under `runs`, and saves.

2.  **Integrate Deletion hooks**:
    - Inside `db_delete_session_recursive()`:
      - Before executing the delete transaction, query the aggregates.
      - Upon successful commit of the transaction, invoke `record_deletion_run("delete", session_ids, conn)`.
    - Inside `db_run_cleanup()`:
      - Before executing the delete transaction, query the aggregates for `target_session_ids`.
      - Upon successful commit of the transaction, invoke `record_deletion_run("clean", target_session_ids, conn)`.

3.  **Update `db_show_info()`**:
    - Load the sidecar JSON.
    - Sum the active database metrics with the historical `cumulative` metrics from the sidecar.
    - Format and present the output to show:
      - Active, Historical, and Total sums.

---

### Component 2: Automated Tests (`tests/`)

#### [MODIFY] [test_ocman.py](file:///home/gfariello/VC/ocman/tests/test_ocman.py)
- Create unit tests for historical logging:
  - Mock history JSON file path.
  - Assert that calling `db_delete_session_recursive()` correctly updates the history ledger.
  - Assert that calling `db_run_cleanup()` correctly logs the cleanup metrics.
  - Verify that `db_show_info` correctly aggregates active and historical usage metrics.

---

## 4. Verification Plan

### Automated Tests
- Run the test suite:
  ```bash
  PYTHONPATH=. pytest -v
  ```

### Manual Verification
1.  Verify the current status:
    ```bash
    ocman info
    ```
2.  Run a cleanup or session deletion (e.g. `ocman --session X --delete` or `ocman --clean --days 30`).
3.  Check that `~/.local/share/opencode/ocman_history.json` was created and contains correct metrics.
4.  Run `ocman info` again and verify it displays the updated totals (Active + Historical).
