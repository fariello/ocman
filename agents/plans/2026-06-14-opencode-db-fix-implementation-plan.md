# OpenCode Database Cleanup Consolidation Plan

Consolidate all database cleanup functionality into the main Python CLI tool (`opencode_recover_session.py`). This removes the need for the separate `clean_opencode.sh` script and provides a safer, cross-platform, project-filterable cleanup mechanism.

## User Review Required

> [!IMPORTANT]
> - Deleting a session recursively deletes all child/descendant sessions as well.
> - Cleanup can be limited to a specific project directory using `--project` or auto-detected CWD.
> - A backup directory `~/.local/share/opencode/backups/opencode-db-cleanup-YYYYMMDD-HHMMSS/` is automatically created before any database modifications.
> - Redundant shell script `clean_opencode.sh` will be deleted from the repository.

## Proposed Changes

### OpenCode Session Recovery CLI

#### [MODIFY] [opencode_recover_session.py](file:///home/gfariello/VC/opencode-recover/opencode_recover_session.py)
- **Add new CLI arguments**:
  - `--clean`: Run the age-based session cleanup workflow.
  - `--days <N>`: Retention window in days (default: 5).
  - `--clean-orphans`: Run the orphan cleanup workflow to purge dangling database records.
  - `--dry-run`: Read-only preview of what would be deleted.
  - `--force`: Bypass process checks (e.g. if `opencode --continue` is running).
- **Implement cleanup logic**:
  - **Age-based Cleanup (`--clean`)**:
    - Resolve project filter if `--project` is provided or auto-detected from CWD.
    - Query root sessions older than `--days` matching the project filter.
    - Traverse descendants recursively using a CTE.
    - Gather counts of database rows and `session_diff` JSON files to delete.
  - **Orphan Cleanup (`--clean-orphans`)**:
    - Scan for dangling rows in `event`, `part`, `message`, `session_message`, `session_input`, `session_share`, `session_context_epoch`, `todo`, `event_sequence` where the `session_id`/`aggregate_id` does not exist in the `session` table.
  - **Execution & Safety**:
    - Display detailed summary of rows and files to be deleted.
    - Perform a timestamped backup of the database family (`.db`, `-wal`, `-shm`) under `~/.local/share/opencode/backups/`.
    - Run deletions in a single SQLite transaction.
    - Delete corresponding `session_diff/<id>.json` files from disk.
    - Run `VACUUM;` to reclaim disk space.
    - Output post-cleanup metrics and clear rollback instructions.

#### [DELETE] [clean_opencode.sh](file:///home/gfariello/VC/opencode-recover/clean_opencode.sh)
- Remove the redundant shell cleanup script from the repository.

## Verification Plan

### Automated & Manual Verification
1. Run `python3 opencode_recover_session.py --clean --days 30 --dry-run` to preview age-based cleanup.
2. Run `python3 opencode_recover_session.py --clean-orphans --dry-run` to preview orphan cleanup.
3. Stop any active `opencode` processes and run a real cleanup to verify file size reduction and backup creation.
4. Verify the database size on disk shrinks post-cleanup.
