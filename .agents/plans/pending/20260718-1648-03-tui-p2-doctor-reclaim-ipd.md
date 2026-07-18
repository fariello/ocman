# IPD: TUI parity Phase 2 - storage checkup (doctor view) + guarded reclaim

- Date: 2026-07-18
- Concern: functionality (CLI<->TUI parity), ui-ux + safety
- Scope: a new top-level "Storage" tab in `ocman_tui/` presenting a read-only doctor view
  and guarded reclaim actions; supporting helpers as needed. CLI logic is reused, not
  reimplemented.
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8
- Set: tui-parity
- Order: 2

## Workflow history

- 2026-07-18 created from the tui-parity umbrella (its_direct/pt3-claude-opus-4.8):
  the doctor+reclaim phase, split out for focused review.

## Goal

Bring ocman's headline "diagnose and repair storage" capability into the TUI: a read-only
`doctor` checkup and the guarded `reclaim` actions, so a UI user can see and reclaim disk
usage without dropping to the CLI. Reuse the CLI's `run_doctor_checks` and the
`reclaim_*` functions verbatim (they hold the guards); the TUI only presents and confirms.

## Project conventions discovered (Step 0)

- Guiding principles: AGENTS.md + universal fallback. No em/en dashes in authored text.
- Plans: `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`.
- Contract: path-scoped commits, never push, paste REAL pytest output.
- Stack: Textual TUI; long ops run in worker threads and marshal UI updates back with the
  `_shutting_down` guard; new views are new top-level tabs (umbrella OQ-6 decision).
- Reuse points in `ocman/cli.py`: `discover_storage_locations()`, `run_doctor_checks(loc,
  running=..., progress=..., fast=, deep=) -> list[dict]` (each record has `status`,
  `title`, `detail`, `size_bytes`, `bucket` in {now, optin, report}, optional `count`,
  `issue_url`, and the suggested-fix text); `_doctor_tag(status)`; the doctor status
  constants `DOCTOR_OK/INFO/NOTICE/WARN/DEBUG/ERROR/UNKNOWN`;
  `db_family_open_by_live_pid(db_path)`; reclaim functions
  `reclaim_checkpoint_vacuum(loc, *, dry_run, while_running, assume_yes, verbosity)`,
  `reclaim_temp(loc, *, dry_run, force, min_age_hours, ...)`,
  `reclaim_parts(loc, *, dry_run, while_running, assume_yes, ...)`,
  `reclaim_backups_dir(raw_path, loc, *, dry_run, assume_yes, ...)`. NOTE: `reclaim_snapshots`
  exists but is EXCLUDED from the TUI (umbrella OQ-2).

## Findings (from the umbrella)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| T-02 | High | Medium | STK/PU | doctor | read-only storage checkup absent from TUI | no ref in `ocman_tui/`; CLI `run_doctor_checks`/`cli_doctor` |
| T-03 | High | Med-High | STK/PU | reclaim | guarded disk reclamation absent from TUI | no ref in `ocman_tui/`; CLI `cli_reclaim`/`reclaim_*` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | T-02 | Add a new top-level "Storage" `TabPane`. On open / a Refresh button, run `run_doctor_checks(loc, running=..., progress=<notify>)` in a worker thread; render a read-only table (DataTable): Status tag (via `_doctor_tag` or an equivalent styled cell), Title, Detail, Size, Count. Show the three reclaim-bucket totals (now / opt-in / report-only) beneath, matching the CLI's summary. | `ocman_tui/app.py` (+ maybe a `widgets/storage.py`), `ocman_tui/core.py` | Medium | TUI test: with a seeded DB the doctor table renders rows and the bucket totals match `run_doctor_checks` on the same DB. |
| 2 | T-03 | Add a "Reclaim" area to the Storage tab: a primary "Checkpoint + VACUUM" button plus opt-in toggles/buttons for `--reclaim-temp`, `--reclaim-parts`, and a "prune backups dir" (path input). Each opens a confirm modal (preview of what will be freed), then runs the matching `reclaim_*` function in a worker thread with `assume_yes=True` (the modal IS the confirmation) and `while_running`/`force` mapped from a checkbox. Refuse-while-open behavior and backup-first are inherited from the reclaim functions; surface their messages via notify/log. After a run, re-run doctor to refresh. | `ocman_tui/app.py`/`widgets/storage.py`, `ocman_tui/core.py` | Med-High | TUI test: checkpoint+VACUUM shrinks/rewrites the DB and refreshes the view; a reclaim-temp run removes only eligible temp files; guarded refusal path is exercised. |
| 3 | T-03/OQ-2 | Show a short, static note in the Reclaim area: the snapshot-force mode is intentionally CLI-only; to use it run `ocman reclaim --force-snapshots ...` and/or `ocman doctor` on the command line. No snapshot button in the TUI. | `ocman_tui/app.py`/`widgets/storage.py` | Low | the note is present; no snapshot control exists. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| T-03 (snapshot-force only) | Med-High | Safety | Can break OpenCode undo/revert; maintainer chose CLI-only (OQ-2). | Keep CLI-only; TUI shows the pointer note. |

## Scope check

- Over-scope: none. The view mirrors existing CLI capability; no new diagnostics invented.
- Under-scope: none for this phase (spend/running are Phase 3).

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` (paste real output).
- TUI `run_test()` tests for: doctor table renders + bucket totals match; checkpoint+VACUUM
  action; reclaim-temp action (own-user temp only); the guarded-refusal path.
- Parity spot-check: TUI doctor rows vs `ocman doctor` on the same DB.
- Capturing reclaim function stdout: decide during execution whether to (a) capture via a
  context manager and show in a log pane, or (b) refactor the reclaim functions to return a
  small result and print in the CLI wrapper. Prefer (a) first (no CLI behavior change); fall
  back to (b) only if capture is unreliable. This is an open question below.

## Spec / documentation sync

Add the "Storage" tab to the README/ARCHITECTURE TUI section (done in the consolidated
docs pass at the end of the parity effort) and a CHANGELOG entry for Phase 2.

## Open questions

- OQ-P2-1: reclaim functions currently print to stdout. Capture their output for the TUI
  (context-manager redirect) or refactor them to return structured results? Leaning:
  capture first (no CLI change); refactor only if needed.
- OQ-P2-2: doctor `--deep` (superseded-parts estimate, ~seconds) - offer a "deep scan"
  toggle in the TUI, or always run the default (non-deep) scan? Leaning: default scan with
  an optional "deep" checkbox.

## Approval and execution gate

This IPD is a proposal. Run `plan-review` to harden it, then on human approval set
`Status: approved`, execute, run the validation, and move to `executed/`.
