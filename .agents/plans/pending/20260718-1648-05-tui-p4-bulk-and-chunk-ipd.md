# IPD: TUI parity Phase 4 - bulk actions, db clean duration/scope, chunking

- Date: 2026-07-18
- Concern: functionality (CLI<->TUI parity), ui-ux
- Scope: sidebar multi-select + batch delete/export in `ocman_tui/`; the Database Admin
  prune UI (duration + scope + extracts); the recovery controls (chunk option).
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8
- Set: tui-parity
- Order: 4

## Workflow history

- 2026-07-18 created from the tui-parity umbrella (its_direct/pt3-claude-opus-4.8): the
  bulk + large-session phase, split out for focused review.

## Goal

Give the TUI the CLI's bulk and large-session ergonomics: act on many sessions at once
(consolidated batch delete/export), prune by duration and project scope (not just integer
days), and split oversized sessions into parts (`--chunk`) instead of only truncating.

## Project conventions discovered (Step 0)

- Conventions as in the umbrella (no dashes, path-scoped commits, worker threads, tabs).
- Reuse points: `db_delete_sessions_batch(session_ids, *, dry_run, force, verbosity,
  remove_project_ids=..., extracts=?)` (confirm whether the batch path takes `extracts`; if
  not, extraction runs via the Phase 1 `_write_delete_extracts` helper before the batch);
  `bundle_session_data` for per-session export; `db_run_cleanup(..., project_dir=...,
  extracts=...)` for age prune with scope + extracts; the duration parser used by
  `_add_clean_opts` (compact forms 2h/5d/6w/6mo/1y and "30 days"); `chunk_turns(...)` and
  the chunk sizing config keys `chunk_max_interactions`/`chunk_max_lines`.
- Current TUI: sidebar is single-select (`on_tree_node_selected`); prune UI uses an
  integer retention-days input (`widgets/database.py`); recovery controls only truncate.

## Findings (from the umbrella)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| T-06 | Medium | Medium | PU | batch | multi-session actions absent (single-select) | `app.py` sidebar select |
| T-07 | Medium | Low | PU | db-clean | integer-days only; no duration/scope/extracts | `widgets/database.py` |
| T-08 | Medium | Low | PU | chunk | `--chunk` not offered; TUI only truncates | recovery controls |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | T-06 | Add multi-select to the sidebar (Textual `Tree` node checkboxes or a selection set) and a batch-actions affordance. Batch delete routes through `db_delete_sessions_batch` (honoring the Phase 1 extract toggle); batch export writes one `.ocbox` per selected session (or a combined bundle if simple). Single-select behavior preserved. | `ocman_tui/widgets/sidebar.py`, `ocman_tui/app.py` | Medium | TUI test: select 2 sessions, batch delete removes both in one pass; extract toggle honored. |
| 2 | T-07 | Prune UI: accept a duration string (parsed with the same forms as `--older-than`) in addition to integer days; add an optional project scope and the extract toggle. Map to `db_run_cleanup(days/project_dir/extracts=...)`. Keep integer-days as a shortcut. | `ocman_tui/widgets/database.py`, `core.py` | Low | TUI test: "6w" prunes the right window; project scope limits to that project; extracts honored. |
| 3 | T-08 | Recovery controls: add a "Split into parts (chunk)" option alongside truncation. When chosen, produce `.part-NNofMM` files via the chunk path with the configured per-part caps. | `ocman_tui/app.py` | Low | TUI test: chunk produces multiple `.part-NNofMM` files; nothing dropped. |

## Deferred / out of scope

None for this phase.

## Scope check

- Over-scope: batch export as a single combined bundle is optional; per-session bundles are
  the parity baseline. Keep it simple; add combined only if trivial.
- Under-scope: none.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` (paste real output).
- TUI tests for multi-select batch delete, duration/scope prune, and chunk output; parity
  spot-checks vs the CLI equivalents.

## Spec / documentation sync

Update the README/ARCHITECTURE TUI section (consolidated pass) and CHANGELOG for Phase 4.

## Open questions

- OQ-P4-1: does `db_delete_sessions_batch` accept `extracts`, or should the TUI call the
  Phase 1 `_write_delete_extracts` helper first? Confirm at execution.
- OQ-P4-2: multi-select UX in Textual `Tree` (node highlighting + a running selection set)
  vs a separate checklist widget. Decide during execution for the least-friction option.

## Approval and execution gate

Run `plan-review`, then on approval execute, validate, and move to `executed/`.
