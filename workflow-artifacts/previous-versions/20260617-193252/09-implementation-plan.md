# Consolidated Implementation Plan

- **Run ID**: 20260617-193252
- **HEAD Commit**: f823aa6e6f9308fe3b0765a4d9d0775a36c90056

This plan outlines the changes to be implemented during the execution phase (Section 7).

---

## 1. Concurrency and Resource Improvements (Section 2 Actions)

### 20260617-193252-S2-A1: background Threading for Database Operations
- **Files**:
  - [ocman_tui/widgets/database.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/database.py)
  - [ocman_tui/app.py](file:///home/gfariello/VC/ocman/ocman_tui/app.py)
- **Change**:
  - In `DatabaseAdminWidget.run_prune_operation`, spawn `db_run_cleanup` inside a Textual background worker using `self.run_worker`. Redirect stdout to a string/rich log dynamically, and notify completion upon exit.
  - In `OrsessionApp.confirm_and_delete_session` (handle_confirmation), run the `db_delete_session_recursive` inside a background worker, refresh data and notify on the main thread when done.
- **Verification**: Run the TUI and check that the interface does not freeze or block during prunes or deletes.

### 20260617-193252-S2-A2: Immediate Temp Export Unlinking
- **Files**:
  - [ocman_tui/app.py](file:///home/gfariello/VC/ocman/ocman_tui/app.py)
- **Change**:
  - In the `export_worker` thread or callback, unlink the temporary JSON file immediately after `load_export_file` has successfully parsed it.
- **Verification**: Verify that temporary files do not accumulate in `/tmp` when switching sessions in the TUI.

---

## 2. Test Suite Expansion (Section 3 Actions)

### 20260617-193252-S3-A1: Implement Async TUI Worker Tests
- **Files**:
  - [tests/test_tui.py](file:///home/gfariello/VC/ocman/tests/test_tui.py)
- **Change**:
  - Add test cases that simulate clicking the database prune button and session delete button. Use Textual's test pilot framework to verify that background threads execute successfully without throwing errors.
- **Verification**: `PYTHONPATH=. pytest -v`

---

## 3. Documentation Updates (Section 4 Actions)

### 20260617-193252-S4-A1: Update `README.md`
- **Files**:
  - [README.md](file:///home/gfariello/VC/ocman/README.md)
- **Change**:
  - Update instructions, replacing legacy `orsession` references with `ocman ui` and `ocman gui`. Update the installation instructions to show how dependencies are handled.
- **Verification**: Read the file to ensure layout and contents are clear.

### 20260617-193252-S4-A2: Delete Stale/Obsolete Files
- **Files**:
  - [SPEC-orsession.md](file:///home/gfariello/VC/ocman/SPEC-orsession.md) [DELETE]
  - [opencode_db_cleanup_handoff_for_claude.md](file:///home/gfariello/VC/ocman/opencode_db_cleanup_handoff_for_claude.md) [DELETE]
  - [scripts/check_orsession.sh](file:///home/gfariello/VC/ocman/scripts/check_orsession.sh) [DELETE]
- **Verification**: `git rm` files and check status.

---

## 4. Usability Improvements (Section 5 Actions)

### 20260617-193252-S5-A1: Fix Duplicate Sidebar Nodes
- **Files**:
  - [ocman_tui/widgets/sidebar.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/sidebar.py)
- **Change**:
  - Add `s["id"] not in session_map` before nesting a node, or remove resolved items from the loop to prevent duplicate session tree nodes.
- **Verification**: Open TUI and check that child/subagent sessions are listed only once under their parent session.

### 20260617-193252-S5-A2: Implement CLI `--clear-history`
- **Files**:
  - [ocman.py](file:///home/gfariello/VC/ocman/ocman.py)
- **Change**:
  - Replace the placeholder print statement for `--clear-history` with code that resets the history file structure and saves it.
- **Verification**: Run `ocman --clear-history` and verify `ocman_history.json` content.

---

## 5. Packaging and CI Alignment (Section 6 Actions)

### 20260617-193252-S6-A1: Update `pyproject.toml`
- **Files**:
  - [pyproject.toml](file:///home/gfariello/VC/ocman/pyproject.toml)
- **Change**:
  - Change project name to `ocman`.
- **Verification**: Run `pip install .` and verify the package name.

### 20260617-193252-S6-A2: Update CI Python Version Matrix
- **Files**:
  - [.github/workflows/ci.yml](file:///home/gfariello/VC/ocman/.github/workflows/ci.yml)
- **Change**:
  - Add `"3.14"` to matrix.
- **Verification**: Check yml syntax validity.

---

## Verification Plan

### Automated Tests
- Run `PYTHONPATH=. pytest -v` on Python 3.14 to ensure all 18 baseline tests and new async TUI worker tests pass.

### Manual Verification
- Launch TUI via `python3 ocman.py ui` or `gui`.
- Navigate sidebar, check tree structure (no duplicates).
- Trigger database prune and deletion, verify UI responsiveness (clock updates, navigation continues).
- Verify unlinked temp files in `/tmp`.
