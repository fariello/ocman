# Evidence - assess-functionality (disk-usage) 20260704-153701

Read-only assessment. No code changed.

## Inspected (code)
- `db_show_info` (ocman.py:6455-6684): reports DB-family size (DB+WAL+SHM), DB stats,
  usage metrics, and a **global** session-diff total (6600-6611, printed 6680-6684).
  No backups section; no per-project breakdown.
- `default_backup_dir` config (ocman.py:230,260,268) and backup writers
  (`cli_backup`/delete/cleanup create `opencode-db-cleanup-*` dirs + `*.zip`).
- Session-diff path/naming: `OPENCODE_STORAGE_DIR/<session_id>.json` (ocman.py:345,5526);
  `session.project_id` provides exact per-project attribution.

## Inspected (environment, to confirm the value)
- `du -sh ~/.local/share/opencode/backups` → **7.3 G**.
- `ls -lh opencode.db*` → DB 2.8 G, -wal 2.1 M, -shm 32 K.
- `du -sh .../storage/session_diff` → 12 K.
- Backups dir listing: many `opencode-db-cleanup-YYYYMMDD-HHMMSS/` directories (each holds
  a full opencode.db copy) → explains the multi-GB total and the need for recursive sizing.

## Commands run
- `date`, `git status --short` (clean), `grep` for db_show_info / backup / session_diff
  references, `Read` of ocman.py:6455-6684, and the `du`/`ls` disk probes above.

## Sampling / truncation notes
- `db_show_info` read in full; backup dir listing truncated to first ~10 entries (many
  similar cleanup dirs). Findings unaffected.
