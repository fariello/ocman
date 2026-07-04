# Decisions and assumptions - assess-self-documentation (clean-backups) run 20260704-190000

## Concern / scope
- Concern: self-documentation ("prompts that teach") + UI/UX. Lens: self-documentation.md.
- Scope: NARROWED by the user to `ocman --clean-backups` confirmation output.
- Lead personas: novice + UI/UX, with stakeholder/QA (destructive-op safety) and accessibility.

## Project conventions discovered
- `cli_clean_backups` (ocman.py:7224-7331) collects only `backups_to_delete`; color helpers exist
  (color_red/green/bold/yellow, 147-166); `human_size_local` for sizes.
- Destructive command → the change must increase visibility and preserve the typed-`yes` confirm + dry-run.
- Out of scope (framework): `.agents/workflows/`, `workflow-artifacts/`.

## Key decisions
- Verdict **needs work**.
- **CB-2 (all-backups warning) is the highest-value item** — deleting 100% of rollback safety deserves a
  forceful, distinct warning, not the same quiet prompt.
- **Accessibility (CB-8):** use the literal words DELETE/KEEP so meaning survives without color; color is an
  enhancement. Also fixes CB-5 (pad plain text before coloring).
- **At-scale readability (CB-6):** always show DELETE rows in full; summarize KEEP rows past a threshold
  (full under `-v`) so the actionable set isn't buried.
- **Honest labels (CB-3):** show the concrete cutoff timestamp; "Created" is actually `st_mtime` → "Modified".
- No change to WHICH items are deleted, the cutoff math, or the confirmation gate — output only.

## What was intentionally NOT proposed (and why)
- Extending the KEEP/DELETE view to the session `--clean` prompt (`db_run_cleanup`): separate command,
  out of the request's scope; recommended as a follow-up (open Q3).
- Interactive per-item selection / a TUI picker: over-scope, not requested.

## Open questions for the user
1. KEEP-summarization threshold (20) + full under `-v`, or always list all KEEP rows?
2. Sort: DELETE-first grouping, or one combined chronological list with inline tags?
3. Apply the same treatment to the session age-based `--clean` confirmation too?

## Cross-cutting observation (other places the same pattern applies)
The "show the full outcome + warn forcefully on total/irreversible destruction" pattern generalizes to
ocman's other destructive confirmations. Surveyed (grounded in code), NOT part of this IPD's scope but
candidates for follow-up assess runs:
- `db_run_cleanup` age-based session `--clean` (ocman.py:6007-6079): lists rows/files to delete + typed-yes;
  same "what survives / are we deleting everything old" clarity gap. (Already flagged as open Q3.)
- `db_delete_session_recursive` (4666-4712) and `db_delete_project_recursive` (4920-4967): show what WILL be
  deleted (rows/files) but not the surrounding scope; a "deletes the entire project incl. N sessions" summary
  + irreversibility emphasis would help. TUI equivalents: DeletionSafetyModal / ProjectDeletionSafetyModal
  (app.py:136, 257) — already say "irreversible" but could show the KEEP/DELETE-style scope.
- `--restore` / RestoreBackupModal (app.py:67): overwrites current DB/config/storage — a "what will be
  overwritten / current state will be replaced (rollback ZIP saved at X)" preview would match the pattern.
- `--clear-history` (4257): wipes the activity ledger + totals — deserves an explicit "this erases all N runs
  and resets grand totals" confirmation.
- `--clean-orphans` prune (5964-6074): shows projects/sessions to purge; same all-or-partial clarity applies.
The unifying principle to extract: a shared "confirm destructive action" helper that (a) shows the full
before/after (keep vs remove), (b) forcefully flags total/irreversible loss, (c) is color-independent
(DELETE/KEEP words), and (d) preserves the typed-yes gate + dry-run. Recommend a small `assess-architecture`
pass to design that shared helper rather than re-implementing per-command.
