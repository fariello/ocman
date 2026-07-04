# Evidence - assess-architecture (destructive-confirm helper) 20260704-185633

Read-only assessment. No code changed.

## Inspected (code)
- Four typed-`yes` confirmation blocks (verified by reading):
  - `db_delete_session_recursive`: red "IRREVERSIBLE" at ocman.py:4702; `input("Type 'yes' to confirm
    deletion:")` + `!= "yes"` -> Cancelled, EOF/KeyboardInterrupt handled (4705-4714).
  - `db_delete_project_recursive`: `input("Type 'yes' to confirm project deletion:")` (4960-4967).
  - `db_run_cleanup` (clean/clean-orphans): `input("Type 'yes' to confirm database prune and vacuum:")` (6074-6079).
  - `cli_clean_backups`: `input(f"Type 'yes' to confirm deletion of these {n} backups:")` (7287-7295).
- Divergent styles elsewhere: move/metadata prompts `[y/N]`/`[Y/n]` (7442, 7526, 4542), config prompts (6873, 6892).
- `--clear-history` (7607-7624): resets cumulative totals + runs and `_save_history(default)` with **no
  confirmation** and no dry-run/force.
- TUI: `DeletionSafetyModal` (ocman_tui/app.py:136) and `ProjectDeletionSafetyModal` (257) implement their own
  async typed-`yes` confirmation, separate from the CLI code.
- Color helpers `color_red/green/bold/yellow` (147-166); `human_size_local` for sizes.
- Existing preview code each op hand-rolls: rows/files to delete (4666-4712, 4920-4967, 6007-6079),
  backups to delete (7262-7281). None show a keep-set or a total-loss warning.

## Cross-plan
- Pending `.agents/plans/pending/2026-07-04-assess-self-documentation-clean-backups-preview.md` proposes a
  bespoke KEEP/DELETE renderer for clean-backups — the direct motivation for extracting a shared abstraction
  (ARCH-3/ARCH-8) so it plugs in rather than diverges.

## Commands run
- `date`, `git status --short` (clean), `grep` for confirmation/input/clear-history sites, `Read` of the four
  confirm blocks + `--clear-history` + TUI modal class headers.

## Sampling / truncation notes
- Read the four confirmation blocks and `--clear-history` in full; TUI modals inspected at class/behavior level.
