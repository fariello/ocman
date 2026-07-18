# IPD: TUI parity Phase 2 - storage checkup (doctor view) + guarded reclaim

- Date: 2026-07-18
- Concern: functionality (CLI<->TUI parity), ui-ux + safety
- Scope: a new top-level "Storage" tab in `ocman_tui/` presenting a read-only doctor view
  and guarded reclaim actions; supporting helpers as needed. CLI logic is reused, not
  reimplemented.
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8
- Set: tui-parity
- Order: 2

## Workflow history

- 2026-07-18 created from the tui-parity umbrella (its_direct/pt3-claude-opus-4.8):
  the doctor+reclaim phase, split out for focused review.
- 2026-07-18 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-001..PR-006 fixed; GO - PENDING HUMAN APPROVAL. (Details in the gate section below.)

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
- Reuse points in `ocman/cli.py` (verified against source 2026-07-18):
  - `discover_storage_locations(db_path) -> dict` (the `loc` dict).
  - `run_doctor_checks(loc, *, retention_days=None, running=None, progress=None, fast=False,
    deep=False) -> list[dict]`. Each record is built by `_check_record` and has EXACTLY
    these keys: `key`, `title`, `status`, `size_bytes` (int), `count` (int), `detail`,
    `fix_cmd` (the suggested `ocman ...` command or None), `issue_url` (or None), `bucket`
    in {`now`, `optin`, `report`}. `progress(label)` is called before each check.
  - `_doctor_tag(status) -> str` for the styled 5-char status tag; status constants
    `DOCTOR_OK/INFO/NOTICE/WARN/DEBUG/ERROR/UNKNOWN`.
  - `db_family_open_by_live_pid(db_path) -> bool` (is OpenCode holding the DB open).
  - Reclaim functions (all print to stdout; all return None):
    `reclaim_checkpoint_vacuum(loc, *, dry_run, while_running, assume_yes, verbosity)`;
    `reclaim_temp(loc, *, dry_run, force, min_age_hours, assume_yes, verbosity)`;
    `reclaim_parts(loc, *, dry_run, while_running, assume_yes, ...)`;
    `reclaim_backups_dir(raw_path, loc, *, dry_run, assume_yes, min_age_hours, verbosity)`.
    `min_age_hours` comes from config `reclaim_tmp_min_age_hours` (default 24) for temp and
    from the appropriate retention for backups; pass it explicitly.
  - NOTE: `reclaim_snapshots(...)` exists but is EXCLUDED from the TUI (umbrella OQ-2).

## Findings (from the umbrella)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| T-02 | High | Medium | STK/PU | doctor | read-only storage checkup absent from TUI | no ref in `ocman_tui/`; CLI `run_doctor_checks`/`cli_doctor` |
| T-03 | High | Med-High | STK/PU | reclaim | guarded disk reclamation absent from TUI | no ref in `ocman_tui/`; CLI `cli_reclaim`/`reclaim_*` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | T-02 | Add a new top-level "Storage" `TabPane`. On open / a Refresh button, run `run_doctor_checks(loc, running=db_family_open_by_live_pid(...), progress=<notify>)` in a worker thread; render a read-only `DataTable`: Status (styled via `_doctor_tag(r["status"])`), Title (`title`), Detail (`detail`), Size (`size_bytes`), Count (`count`), and the suggested fix (`fix_cmd`) when present. Show the three reclaim-bucket totals summed from records by `bucket` (now / optin / report), matching the CLI summary. | `ocman_tui/app.py` (+ `widgets/storage.py`), `ocman_tui/core.py` | Medium | TUI test: with a seeded DB the doctor table renders rows and the per-bucket totals equal the sums from `run_doctor_checks` on the same DB. |
| 2 | T-03 | Add a "Reclaim" area to the Storage tab: a primary "Checkpoint + VACUUM" button plus opt-in buttons for `--reclaim-temp`, `--reclaim-parts`, and a "prune backups dir" (path input). Each opens a confirm modal (preview of what will be freed), then runs the matching `reclaim_*` function in a worker thread with `assume_yes=True` (the modal IS the confirmation), passing `min_age_hours` (from config `reclaim_tmp_min_age_hours`) to `reclaim_temp`/`reclaim_backups_dir`, and `while_running` from a checkbox (default OFF). Refuse-while-open and backup-first are inherited from the reclaim functions. After a run, re-run doctor to refresh. | `ocman_tui/app.py`/`widgets/storage.py`, `ocman_tui/core.py` | Med-High | TUI test: checkpoint+VACUUM rewrites the DB and refreshes the view; a reclaim-temp run removes only eligible own-user temp files; the guarded refuse-while-running path is exercised and surfaces the refusal (see Step 4). |
| 3 | T-03/OQ-2 | Show a short, static note in the Reclaim area: the snapshot-force mode is intentionally CLI-only; to use it run `ocman reclaim --force-snapshots ...` and/or `ocman doctor` on the command line. No snapshot button in the TUI. | `ocman_tui/app.py`/`widgets/storage.py` | Low | negative TUI test: no snapshot-force control exists in the Storage tab; the pointer note is present. |
| 4 | PR-003/PR-004 | Capture the reclaim functions' stdout (a `contextlib.redirect_stdout` around the worker call) and surface it in a Storage log pane / notify, so the guarded refuse-while-running message and the freed-bytes result are always visible in the UI (never swallowed). Do NOT refactor the reclaim functions unless capture proves unreliable (fallback: have them return a small result and print in a CLI wrapper). On a refuse-while-running result, the UI MUST NOT report success. | `ocman_tui/app.py`/`widgets/storage.py` | Medium | TUI test: with OpenCode simulated as holding the DB open, the reclaim action reports the refusal (not success) and makes no change. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| T-03 (snapshot-force only) | Med-High | Safety | Can break OpenCode undo/revert; maintainer chose CLI-only (OQ-2). | Keep CLI-only; TUI shows the pointer note. |

## Scope check

- Over-scope: none. The view mirrors existing CLI capability; no new diagnostics invented.
- Under-scope: none for this phase (spend/running are Phase 3).

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE THE ACTUAL runner
  output (never a claimed pass).
- TUI `run_test()` tests for: (a) doctor table renders and per-bucket totals equal the sums
  from `run_doctor_checks` on the same seeded DB; (b) checkpoint+VACUUM action rewrites the
  DB and refreshes; (c) reclaim-temp removes only eligible own-user temp files; (d) the
  refuse-while-running path reports the refusal and makes NO change; (e) negative test: no
  snapshot-force control exists in the Storage tab.
- Parity spot-check: TUI doctor rows vs `ocman doctor` on the same DB.

## Spec / documentation sync

Add the "Storage" tab to the README/ARCHITECTURE TUI section (done in the consolidated
docs pass at the end of the parity effort) and a CHANGELOG entry for Phase 2.

## Open questions

- OQ-P2-1: RESOLVED (this review) - capture reclaim stdout via `contextlib.redirect_stdout`
  and surface it in the Storage log/notify; refactor the reclaim functions to return results
  ONLY as a fallback if capture proves unreliable. The refuse-while-running message MUST
  reach the UI either way (tested in Step 4 / validation d).
- OQ-P2-2: doctor `--deep` (superseded-parts estimate, ~seconds) - offer a "deep scan"
  toggle in the TUI, or always run the default (non-deep) scan? Leaning: default scan with
  an optional "deep" checkbox. Non-blocking; decide at execution.

## Approval and execution gate

This IPD is a proposal and is NOT auto-executed. Execution contract:

- Open questions: OQ-P2-1 resolved (above); OQ-P2-2 is non-blocking (default-scan is safe).
- Scope fence: ONLY the Storage tab (doctor view + safe reclaim actions) and the minimal
  `core.py` re-exports. Do NOT touch other tabs, the CLI reclaim/doctor logic, or add the
  snapshot-force path. No new runtime dependencies.
- Honesty rule (hard MUST): paste the ACTUAL `pytest -q` output in the execution report;
  never claim a pass you did not run.
- Commits: path-scoped (`git commit -m msg -- <paths>` or staged-index commit), NEVER push,
  NEVER tag.
- Lifecycle: on completion set `Status: executed` and `git mv` this IPD to
  `.agents/plans/executed/` (verify no pending/executed duplicate).

Next: human approval sets `Status: approved`; then execute per the above.
