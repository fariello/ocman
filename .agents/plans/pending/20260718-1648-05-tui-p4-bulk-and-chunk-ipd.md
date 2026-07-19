# IPD: TUI parity Phase 4 - bulk actions, db clean duration/scope, chunking

- Date: 2026-07-18
- Concern: functionality (CLI<->TUI parity), ui-ux
- Scope: sidebar multi-select + batch delete/export in `ocman_tui/`; the Database Admin
  prune UI (duration + scope + extracts); the recovery controls (chunk option).
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8
- Set: tui-parity
- Order: 4

## Workflow history

- 2026-07-18 created from the tui-parity umbrella (its_direct/pt3-claude-opus-4.8): the
  bulk + large-session phase, split out for focused review.
- 2026-07-18 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-001 (batch extracts via _write_delete_extracts), PR-002 (batch delete MUST confirm),
  PR-003 (duration->days via parse_duration_to_days), PR-004 (chunk in the hand-rolled write
  path), PR-005 (execution contract), PR-006 (multi-select UX resolved) fixed.
  GO - PENDING HUMAN APPROVAL.

## Goal

Give the TUI the CLI's bulk and large-session ergonomics: act on many sessions at once
(consolidated batch delete/export), prune by duration and project scope (not just integer
days), and split oversized sessions into parts (`--chunk`) instead of only truncating.

## Project conventions discovered (Step 0)

- Conventions as in the umbrella (no dashes, path-scoped commits, worker threads, tabs).
- Reuse points (verified against source 2026-07-18):
  - `db_delete_sessions_batch(session_ids, *, dry_run, force, verbosity,
    remove_project_ids=None)` (`ocman/cli.py`). It has NO `extracts` param (resolves
    OQ-P4-1) and, per its own docstring, "does NOT print a per-session preview or confirm;
    the caller is responsible for the single `confirm_destructive` preview." It performs ONE
    backup / transaction / VACUUM / metrics write / report. So the TUI MUST (a) confirm
    before calling it (PR-002) and (b) write extracts via the Phase 1
    `_write_delete_extracts(session_ids, expand_descendants=True)` BEFORE the batch, gated on
    the delete modal's extract checkbox (PR-001).
  - `bundle_session_data(...)` for per-session `.ocbox` export (already used by the existing
    ExportSessionModal).
  - `db_run_cleanup(days: float, project_id, project_dir, dry_run, force, clean_orphans,
    verbosity, assume_yes=False, extracts=None, extract_output_dir=None)`. Takes a numeric
    `days` (fractional OK), plus separate `project_id`/`project_dir` for scope, and
    `extracts`. The TUI parses a duration STRING to days via
    `parse_duration_to_days(text) -> float` (`ocman/cli.py:4894`; accepts 2h/5d/6w/6mo/1y,
    "30 days", or a bare number) then passes `days=` (PR-003).
  - `chunk_turns(turns, *, max_interactions: int, max_lines: int) -> list[list[Turn]]`
    (`ocman/cli.py:2590`) and `part_recovery_name(session_id, dt, kind, idx, total)` for the
    `.part-NNofMM` filenames; per-part caps from config `chunk_max_interactions` /
    `chunk_max_lines`.
- Current TUI: sidebar is single-select (`on_tree_node_selected`, `app.py:1027`); prune UI
  uses an integer retention-days input (`widgets/database.py:236,358`); the recovery-file
  buttons render one file each via a HAND-ROLLED path (`app.py:1324-1344`,
  `render_transcript`/`render_restart_context`/`render_compact_prompt` + `write_text`), NOT
  `recover_from_export`. Chunking must therefore be added in that hand-rolled path (PR-004).

## Findings (from the umbrella)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| T-06 | Medium | Medium | PU | batch | multi-session actions absent (single-select) | `app.py` sidebar select |
| T-07 | Medium | Low | PU | db-clean | integer-days only; no duration/scope/extracts | `widgets/database.py` |
| T-08 | Medium | Low | PU | chunk | `--chunk` not offered; TUI only truncates | recovery controls |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | T-06 | Add multi-select to the sidebar: maintain a running set of selected SESSION ids on the existing `Tree` (toggle on select/space; visible highlight or a selected-count label). Preserve single-select behavior when the set is empty/one. Fall back to a dedicated checklist widget ONLY if the Tree cannot express multi-select cleanly (PR-006). Add a "batch actions" affordance enabled when >=1 selected. | `ocman_tui/widgets/sidebar.py`, `ocman_tui/app.py` | Medium | TUI test: select 2 sessions; the selection set reflects both. |
| 2 | T-06, PR-002, PR-001 | Batch DELETE: MUST show a confirmation first (reuse the Phase 1 `DeletionSafetyModal` pattern or an equivalent multi-session confirm carrying the "write recovery extracts first" checkbox), because `db_delete_sessions_batch` does NOT confirm. On confirm: if extracts checked, call `_write_delete_extracts(selected_ids, expand_descendants=True)` in the worker BEFORE the batch, then `db_delete_sessions_batch(selected_ids, dry_run=False, force=True, verbosity=0)`. One consolidated backup/transaction/VACUUM/report (inherited). Refresh + clear selection after. | `ocman_tui/app.py` | Medium | TUI test: select 2 sessions, confirm, both are deleted in ONE pass; with extracts checked, recovery files are written first; cancelling deletes nothing. |
| 3 | T-06 | Batch EXPORT: write one `.ocbox` per selected session via `bundle_session_data` (to a chosen dir). A single combined bundle is out of scope (see Scope check). | `ocman_tui/app.py` | Low | TUI test: exporting 2 selected sessions produces 2 `.ocbox` files. |
| 4 | T-07, PR-003 | Prune UI: accept a duration STRING (parsed via `parse_duration_to_days` into fractional days) in addition to the integer-days input; add an optional project scope (resolve to `project_dir`/`project_id`) and the extract toggle. Call `db_run_cleanup(days=<parsed>, project_id=<scope or None>, project_dir=<scope or None>, dry_run=..., force=..., clean_orphans=..., verbosity=0, assume_yes=True, extracts=<toggle>)`. Keep integer-days as a shortcut. Invalid duration -> a clear error, no prune. | `ocman_tui/widgets/database.py`, `core.py` | Low | TUI test: "6w" maps to ~42 days and prunes the right window; a project scope limits to that project; extracts honored; a bad duration string errors without pruning. |
| 5 | T-08, PR-004 | Recovery controls: add a "Split into parts (chunk)" checkbox. When checked, in the existing hand-rolled write path (`app.py:1324-1344`) split the filtered turns with `chunk_turns(turns, max_interactions=<cfg chunk_max_interactions>, max_lines=<cfg chunk_max_lines>)` and write each part with `part_recovery_name(sid, now, kind, idx, total)` (transcript/restart/prompt per part). Nothing dropped. When unchecked, current single-file behavior is unchanged. | `ocman_tui/app.py`, `core.py` | Low | TUI test: with chunk on, a large session yields multiple `.part-NNofMM` files and the union of parts covers all turns. |

## Deferred / out of scope

- A single COMBINED multi-session `.ocbox` bundle: not built this phase (per-session
  bundles are the parity baseline; combined has no CLI counterpart to match). Not a Fix-Bar
  deferral, just an explicit non-goal to avoid scope creep.

## Scope check

- Over-scope: do NOT build a combined bundle or a new batch-only screen; reuse the existing
  export/delete/prune mechanisms with a selection set.
- Under-scope (now fixed): batch-delete confirmation (PR-002) and batch-delete extracts
  (PR-001) are added as explicit Step 2 requirements with tests.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE THE ACTUAL runner output
  (never a claimed pass).
- TUI `run_test()` tests: (a) multi-select set reflects 2 chosen sessions; (b) batch delete
  after confirm removes both in one pass; (c) batch delete with extracts checked writes
  recovery files first; (d) cancelling the confirm deletes nothing; (e) batch export makes
  one `.ocbox` per session; (f) duration prune ("6w") + project scope + extracts; (g) bad
  duration string errors without pruning; (h) chunk writes multiple `.part-NNofMM` files
  covering all turns.
- Parity spot-checks vs the CLI equivalents (`session delete` batch, `db clean --older-than`,
  `recover --chunk`).

## Spec / documentation sync

Update the README/ARCHITECTURE TUI section (consolidated pass at the end of the parity
effort) and add a CHANGELOG entry for Phase 4.

## Open questions

- OQ-P4-1: RESOLVED (this review) - `db_delete_sessions_batch` has NO `extracts` param;
  the TUI calls `_write_delete_extracts(...)` before the batch (Step 2).
- OQ-P4-2: RESOLVED (this review) - use a running selection set on the existing `Tree`
  (highlight + count), falling back to a checklist widget only if the Tree cannot express
  multi-select; this is an implementation choice, not a human decision.

## Approval and execution gate

This IPD is a proposal and is NOT auto-executed. Execution contract:

- Open questions: none (OQ-P4-1 and OQ-P4-2 resolved above).
- Scope fence: ONLY sidebar multi-select + batch delete/export, the prune-UI duration/scope/
  extracts, and the chunk option in the recovery controls. Do NOT add a combined bundle, a
  new batch-only screen, or change the CLI. Reuse the Phase 1 delete-confirm + extract
  machinery. No new runtime dependencies.
- Honesty rule (hard MUST): paste the ACTUAL `pytest -q` output in the execution report;
  never claim a pass you did not run.
- Commits: path-scoped, NEVER push, NEVER tag.
- Lifecycle: on completion set `Status: executed` and `git mv` this IPD to
  `.agents/plans/executed/` (verify no pending/executed duplicate).

Next: human approval sets `Status: approved`; then execute per the above.
