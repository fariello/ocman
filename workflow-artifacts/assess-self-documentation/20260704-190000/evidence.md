# Evidence - assess-self-documentation (clean-backups) run 20260704-190000

Read-only assessment. No code changed.

## Inspected (code)
- `cli_clean_backups` (ocman.py:7224-7331): scans `default_backup_dir.iterdir()`, matches names
  `opencode-backup-*`/`rollback-before-restore-*`/`opencode-db-cleanup-*`, and appends to
  **`backups_to_delete`** only those with `st_mtime < cutoff_time` (7253). It prints only that list
  (7263-7278: `Found N ... older than DAYS`, per-row `Size` + `Created:` from `st_mtime`), then
  `Total size to reclaim`, then a typed-`yes` prompt (7288). Kept backups are never collected or shown.
- Color helpers `color_red`/`color_green`/`color_bold`/`color_yellow` at ocman.py:147-166.
- The per-row f-string pads with `{name:<45}`/`{human_size_local(size):<10}` (7278) — padding on plain
  text; adding ANSI color would break alignment unless plain text is padded before coloring (CB-5).
- Cutoff timestamp is already computed (`cutoff_time = now - days*86400`, 7235) but not shown in the header.

## User-provided runtime evidence
- `ocman --clean-backups --days 0.1` listed 22 db-cleanup backups to purge (incl. a 4.43 GB and a 2.80 GB
  one), total 7.23 GB, with no indication of how many backups would remain — the motivating case for CB-1.
  If those 22 were all backups, the user would be wiping all rollback safety with no special warning (CB-2).

## Commands run
- `date`, `git status --short` (clean), `Read` of `cli_clean_backups`, `grep` for color helpers.

## Sampling / truncation notes
- Read the full `cli_clean_backups` function; did not re-read the whole file (targeted inspection).
