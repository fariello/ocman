# IPD: TUI parity Phase 3 - reporting views (spend + running)

- Date: 2026-07-18
- Concern: functionality (CLI<->TUI parity), ui-ux
- Scope: two new read-only top-level tabs in `ocman_tui/` - "Spend" and "Running".
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8
- Set: tui-parity
- Order: 3

## Workflow history

- 2026-07-18 created from the tui-parity umbrella (its_direct/pt3-claude-opus-4.8): the
  read-only reporting phase, split out for focused review.

## Goal

Surface the CLI's `spend` and `list running` reports in the TUI so a UI user can see LLM
cost/token spend (including historical/deleted spend) and running/insecure OpenCode
instances. Both are read-only/observe-only.

## Project conventions discovered (Step 0)

- Guiding principles + conventions as in the umbrella and Phase 2 (no dashes, path-scoped
  commits, worker threads, new top-level tabs).
- Reuse points: `cli_spend(project=None, *, sessions=False, historical=False, json_output=...)`
  currently prints/emits; the underlying per-project + historical aggregation logic in
  `ocman/cli.py` should be reused (extract a data-returning helper if `cli_spend` only
  prints). `cli_list_running(*, all_users=False, probe=False, json_output=...)` and its
  `detect_running_instances(...)` / `_auth_cell` helpers produce the running rows and the
  insecure-server flag.

## Findings (from the umbrella)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| T-04 | Medium | Medium | PU | spend | spend / --historical absent from TUI | CLI `cli_spend` |
| T-05 | Medium | Medium | PU/STK | running | list running + insecure-server flag absent | CLI `cli_list_running` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | T-04 | If needed, extract a data-returning helper from `cli_spend` (e.g. `gather_spend(...) -> dict`) so both the CLI and TUI render the same numbers without duplicating aggregation. No CLI behavior change. | `ocman/cli.py` | Medium | CLI `spend` output unchanged; helper returns the same totals. |
| 2 | T-04 | Add a read-only "Spend" tab: per-project table (cost + split tokens) with a "Include historical (deleted) spend" toggle mapping to `historical=True`, and a refresh. | `ocman_tui/app.py`/`widgets/spend.py`, `core.py` | Medium | TUI test: spend table rows/totals match the helper on a seeded DB; historical toggle adds deleted spend. |
| 3 | T-05 | Add a read-only "Running" tab: list running OpenCode instances (pid/user/uptime/kind/dir/project/session), flag insecure control servers (unauthenticated / non-loopback) prominently (red), with a manual Refresh and an "all users" toggle. Observe-only; never mutates. | `ocman_tui/app.py`/`widgets/running.py`, `core.py` | Medium | TUI test (mocked detector): rows render; an insecure instance is flagged; refresh re-queries. |

## Deferred / out of scope

None for this phase.

## Scope check

- Over-scope: none (mirrors CLI). Under-scope: none.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` (paste real output).
- TUI tests with a seeded DB / mocked running-detector; parity spot-check vs `ocman spend`
  and `ocman list running --json`.

## Spec / documentation sync

Add "Spend" and "Running" tabs to the README/ARCHITECTURE TUI section (consolidated docs
pass) and a CHANGELOG entry for Phase 3.

## Open questions

- OQ-P3-1: does `cli_spend` already have a data-returning core, or must one be extracted?
  Confirm at execution; prefer extracting a helper over duplicating aggregation.

## Approval and execution gate

Run `plan-review`, then on approval execute, validate, and move to `executed/`.
