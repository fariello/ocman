# Implementation Plan - Safely Moving Projects and Sessions in ocman

This document details the design and implementation plan for adding:
1. CLI commands to safely move projects/sessions (`ocman --move-project <project_id_or_path> --to <new_path>` and `ocman --move-session <session_id> --to <new_path>`).
2. Bulk path prefix rebasing via `ocman --rebase-paths --from <old_prefix> --to <new_prefix>`.
3. TUI integration via a specialized modal dialog to re-assign paths.
4. Auto-backup, pre-flight safety validations, and transaction isolation.

---

## User Review Required

> [!IMPORTANT]
> - **Missing Source Path Resolution**: If the source path does not exist on disk:
>   - **Interactive Mode**: We will display a clear explanation and prompt the user: `Source directory '{old_path}' does not exist on disk. Update database metadata only? [y/N]: `. If agreed, we perform a metadata-only database update.
>   - **Non-Interactive Mode**: We require an explicit `--metadata-only` flag. If missing, we fail with a clear error to prevent typos from executing database modifications silently.
> - **TUI Specialized Modal**: We will implement a custom `MoveProjectModal` overlay dialog in Textual TUI. When a project is selected, clicking a "Move/Update Path" button pops up this modal containing path input fields and a validation toggle (allowing physical move vs metadata-only re-assignment).
> - **Bulk Path Rebasing**: We introduce `--rebase-paths --from <old> --to <new>` as a metadata-only operation to fix database paths after system migrations (e.g. moving between different OS homes or partitions).

---

## Open Questions

- *None.* All design details have been aligned with the user feedback.

---

## Proposed Changes

### Configuration and DB Engines (`ocman.py`)

#### [MODIFY] [ocman.py](file:///home/gfariello/VC/ocman/ocman.py)

1. **Database Migration Logic**:
   - Create a `db_move_project_metadata(project_id: str, old_worktree: str, new_worktree: str) -> None` function.
     - Runs inside a single SQLite transaction.
     - Updates `project.worktree` to the `new_worktree`.
     - Updates all `session.directory` paths belonging to the project by replacing the `old_worktree` prefix with `new_worktree`.
   - Create a `db_move_session_metadata(session_id: str, old_dir: str, new_dir: str) -> None` function.
     - Updates `session.directory` to the `new_dir` for the session.
     - Recursively updates directories for all nested sub-sessions by substituting the `old_dir` prefix.
   - Create a `db_rebase_paths(old_prefix: str, new_prefix: str) -> dict[str, int]` function.
     - Iterates through the `project` and `session` tables and replaces matching prefix strings. Returns statistics on updated rows.

2. **Filesystem Move Logic**:
   - Define a helper `move_directory_structure(old_path: Path, new_path: Path) -> None`.
     - Validates that `old_path` is a directory and exists.
     - Validates that `new_path` does not exist (raising a validation error to prevent overwrites).
     - Uses `shutil.move` to perform atomic filesystem movement.

3. **Pre-flight Checks & Auto-Backup**:
   - Before executing any move operation, create a temporary rollback backup of the database (`~/.local/share/opencode/backups/rollback-before-move-<timestamp>.db`).
   - If filesystem movement or SQL updates raise any exception, automatically restore the backup database and clean up any partially-written directory at the destination.

4. **CLI Argument Parser integration**:
   - Add CLI arguments:
     - `--move-project <project_id_or_path>`
     - `--move-session <session_id>`
     - `--to <new_path>`
     - `--rebase-paths`
     - `--from <old_prefix>`
     - `--metadata-only`
   - Implement argument checks in `main()` to enforce parameters.

---

### TUI Integration (`ocman_tui/`)

#### [MODIFY] [app.py](file:///home/gfariello/VC/ocman/ocman_tui/app.py)

1. **Specialized Modal Dialog**:
   - Create `MoveProjectModal(ModalScreen)`:
     - Prompts the user with `Old Path (Read Only)`, `New Path (Input)`, and a checkbox `Perform physical directory move on disk`.
     - Performs target path validation upon submit.
     - Calls backend move functions inside a worker thread to keep TUI responsive.
     - Reloads TUI project lists upon completion.

#### [MODIFY] [database.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/database.py)

- Add a `Move/Update Path` button (`#btn-move-project`) next to the project actions section.
- Trigger `MoveProjectModal` when clicked.

---

## Verification Plan

### Automated Tests
We will add a new test file `tests/test_move.py` to verify:
1. **Metadata-only Project Move**: Mock database state and assert `project.worktree` and `session.directory` are updated correctly with path replacement.
2. **Physical Project Move**: Setup mock directory structures on disk, verify directories are moved, and database is updated.
3. **Collision Safety**: Verify that if the target directory already exists, the operation aborts and database is untouched.
4. **Interactive Prompts**: Mock TTY stdout/stdin to test interactive prompt fallback when directory is missing on disk.
5. **Rebase Operation**: Verify bulk prefix replacement across multiple projects and sessions.

### Manual Verification
1. Rename a test project directory on disk and run `ocman --move-project ~/old-path --to ~/new-path` in interactive CLI to verify metadata update prompts and database state synchronization.
2. Run `ocman ui` and verify that the "Move/Update Path" modal dialog behaves correctly.
