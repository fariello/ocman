# IPD: TUI parity Phase 1 - delete safety (extract-on-delete + working clear-history)

- Date: 2026-07-18
- Concern: functionality (CLI<->TUI parity), ui-ux + safety
- Scope: `ocman_tui/` delete confirmation modals and delete workers; the history-clear
  control; a small shared helper in `ocman/cli.py`.
- Status: executed
- Approval: approved by maintainer 2026-07-18 (extract default ON; implement history clear)
- Author: its_direct/pt3-claude-opus-4.8
- Set: tui-parity
- Order: 1

## Workflow history

- 2026-07-18 created from the tui-parity umbrella (its_direct/pt3-claude-opus-4.8): the
  safety-first phase, split out of the umbrella per maintainer direction.
- 2026-07-18 executed (commit 45eb8c4): implemented and tested; retro-documented as this
  per-phase IPD.

## Goal

Close the delete-safety gap so the TUI is not more destructive than the CLI, and remove a
dishonest "Planned" control. Before this phase, TUI deletes called `db_delete_*` with
`force=True, confirm=False` and wrote NO recovery extracts, even though the CLI now offers
extract-on-delete by default. The "Clear Historical Activity Log (Planned)" button was a
dead stub.

## Project conventions discovered (Step 0)

- Guiding principles: AGENTS.md + universal fallback. No em/en dashes in authored text.
- Plans: `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`.
- Contract: path-scoped commits, never push, paste REAL pytest output.
- Stack: Textual TUI in `ocman_tui/` importing core logic from `ocman/cli.py` via
  `ocman_tui/core.py`; worker-thread pattern for long ops; `ModalScreen` confirmations.

## Findings (from the umbrella)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| T-01 | High | Medium | PU/QA | delete-safety | extract-on-delete not wired into TUI; deletes force=True/confirm=False, no recovery files | `ocman_tui/app.py` delete workers; CLI `extract_sessions_before_delete` |
| T-14 | Low | Low | NOV | honesty | history clear is a dead "Planned" stub | `ocman_tui/app.py` (FutureTodoModal) |

## Proposed changes (as executed)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | T-01 | Add a default-ON "Write recovery extracts first" checkbox to `DeletionSafetyModal` and `ProjectDeletionSafetyModal`; dismiss payload changed from `bool` to `None`(cancel)/`{"extracts": bool}`(confirm). | `ocman_tui/app.py` | Medium | TUI test: delete writes 3 files when checked; none when unchecked. |
| 2 | T-01 | Session delete worker: new `_write_delete_extracts()` (expands the session subtree, reads DB directly via `extract_sessions_before_delete`, writes to the configured out-dir, best-effort in the worker thread). Project delete worker: pass `extracts=` into `db_delete_project_recursive`. | `ocman_tui/app.py`, `ocman_tui/core.py` | Medium | files appear in out-dir; delete still completes; DB-direct (no OpenCode launch). |
| 3 | T-14 | Replace the `FutureTodoModal` stub with a working `ClearHistoryModal` (typed-yes) that calls a new shared `clear_history_ledger()` (also used by `ocman history clear`), then clears the RichLog and refreshes. | `ocman/cli.py`, `ocman_tui/app.py` | Low | TUI test: ledger runs=[] and cumulative reset after confirm. |

## Deferred / out of scope

None for this phase.

## Required tests / validation (met)

- 3 new TUI tests (`tests/test_tui.py`): extract-on (files written), extract-off (no dir),
  clear-history (ledger wiped). Full suite at execution: 383 passed, 2 skipped.
- No em/en dashes introduced.

## Spec / documentation sync

CHANGELOG "Added" entry for Phase 1 landed in commit 45eb8c4. The consolidated README /
ARCHITECTURE TUI-section update is handled once at the end of the parity effort.

## Open questions

Resolved before execution: extract default ON (maintainer); implement history clear
(OQ-1); reclaim snapshot-force is a later phase's concern.

## Approval and execution gate

Executed. This IPD is the record of Phase 1 (commit 45eb8c4).
