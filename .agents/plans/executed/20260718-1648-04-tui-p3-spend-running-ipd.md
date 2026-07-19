# IPD: TUI parity Phase 3 - reporting views (spend + running)

- Date: 2026-07-18
- Concern: functionality (CLI<->TUI parity), ui-ux
- Scope: two new read-only top-level tabs in `ocman_tui/` - "Spend" and "Running".
- Status: executed
- Approval: approved by maintainer 2026-07-18
- Author: its_direct/pt3-claude-opus-4.8
- Set: tui-parity
- Order: 3

## Workflow history

- 2026-07-18 created from the tui-parity umbrella (its_direct/pt3-claude-opus-4.8): the
  read-only reporting phase, split out for focused review.
- 2026-07-18 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-001 (running fail-loud state), PR-002 (gather_spend required, not optional),
  PR-003 (spend --json byte-identical anti-regression), PR-004 (execution contract),
  PR-005 (empty/error states) fixed. GO - PENDING HUMAN APPROVAL.
- 2026-07-18 executed (its_direct/pt3-claude-opus-4.8): extracted `gather_spend()` (CLI
  spend text/JSON unchanged); added `ocman_tui/widgets/spend.py` (Spend tab) and
  `ocman_tui/widgets/running.py` (Running tab, fail-loud on RunningDetectionError) as new
  top-level tabs; core.py re-exports. 5 net-new tests (gather_spend shape, spend table +
  historical toggle, running render+banner, running fail-loud). Full suite: 392 passed,
  2 skipped.

## Goal

Surface the CLI's `spend` and `list running` reports in the TUI so a UI user can see LLM
cost/token spend (including historical/deleted spend) and running/insecure OpenCode
instances. Both are read-only/observe-only.

## Project conventions discovered (Step 0)

- Guiding principles + conventions as in the umbrella and Phase 2 (no dashes, path-scoped
  commits, worker threads, new top-level tabs).
- Reuse points (verified against source 2026-07-18):
  - `cli_spend(project=None, *, sessions=False, historical=False, json_output=False)`
    (`ocman/cli.py:11908`) builds its data INLINE (`proj_rows`, `live_total/in/out/cache`,
    and the `hist_*` cumulative-ledger totals) and only prints or emits JSON. There is NO
    data-returning core today, so one MUST be extracted (see Step 1). The JSON branch
    (`ocman/cli.py:11978-11990`) is the canonical shape to mirror: `scope`, `projects[]`
    (each `{id, directory, cost, tokens_input, tokens_output, tokens_cache_read}`),
    `live_total`, `live_tokens`, `historical_total`, `historical_tokens`, `grand_total`,
    `grand_tokens`. Historical spend is GLOBAL (the deletion ledger has no project_id), so
    it is a single line, never fabricated per project.
  - `detect_running_instances(*, all_users=False, probe=False, verbosity=0) -> list[dict]`
    (`ocman/cli.py:7964`). Each instance dict: `pid, ppid, user, elapsed, started, cwd,
    project, cmdline, kind (serve|web|tui|tui+server), listeners[], auth
    (secured|unsecured|unknown), vulnerable (bool), exposed (bool = non-loopback),
    session {id/ids, provenance}`. It RAISES `RunningDetectionError` (`ocman/cli.py:7866`)
    when it cannot reliably enumerate (Windows, or `ss` unavailable) - the caller MUST fail
    loud and never render an empty "all clear" (see PR-001). `cli_list_running`
    (`ocman/cli.py:11799`) is the CLI presenter (do not reuse its printing; reuse the
    detector + the `vulnerable`/`exposed`/`auth` flags).
  - Already re-exported in `core.py`: `db_list_projects`. To add for this phase:
    `db_list_sessions`, `db_find_project`, `_load_history`, `detect_running_instances`,
    `RunningDetectionError`, and the new spend helper (Step 1).

## Findings (from the umbrella)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| T-04 | Medium | Medium | PU | spend | spend / --historical absent from TUI | CLI `cli_spend` |
| T-05 | Medium | Medium | PU/STK | running | list running + insecure-server flag absent | CLI `cli_list_running` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | T-04, PR-002 | Extract a data-returning helper `gather_spend(*, historical: bool) -> dict` from `cli_spend`, returning EXACTLY the per-project JSON shape (`projects[]`, `live_total`, `live_tokens`, `historical_total`, `historical_tokens`, `grand_total`, `grand_tokens`). Refactor `cli_spend`'s default (per-project) branch to render from the helper so the printed and `--json` output are unchanged. The per-session drill-down branch is out of scope for the TUI tab and may stay as-is. | `ocman/cli.py` | Medium | `spend --json` output is byte-identical before/after (PR-003 test); `spend` (text) output unchanged. |
| 2 | T-04 | Add a read-only "Spend" tab (`widgets/spend.py`): per-project `DataTable` (Project, Cost, Tokens In, Tokens Out, Cache) fed by `gather_spend()` in a worker thread, a live-total line, a "Include historical (deleted) spend" checkbox that re-renders with `historical=True` (adds the global historical + grand-total lines), and a Refresh. Empty state when there are no projects. | `ocman_tui/app.py`, `ocman_tui/widgets/spend.py`, `core.py` | Medium | TUI test: table rows/totals match `gather_spend()` on a seeded DB; the historical toggle adds the ledger's deleted spend. |
| 3 | T-05 | Add a read-only "Running" tab (`widgets/running.py`): call `detect_running_instances(all_users=...)` in a worker thread; render pid/user/uptime/kind/listener/auth/project; flag `vulnerable`/`exposed` instances with a prominent red security banner; Refresh button and an "all users" toggle. Observe-only; never mutates. | `ocman_tui/app.py`, `ocman_tui/widgets/running.py`, `core.py` | Medium | TUI test (mocked detector): rows render; a `vulnerable`/`exposed` instance triggers the banner; refresh re-queries. |
| 4 | PR-001 | The Running tab MUST honor the fail-loud contract: catch `RunningDetectionError` and show a loud "detection unreliable - this is NOT an all-clear" state (never an empty table that reads as 'nothing running'). | `ocman_tui/widgets/running.py` | Low | TUI test: with the detector patched to raise `RunningDetectionError`, the tab shows the unreliable-detection message and NOT an empty/clear table. |

## Deferred / out of scope

- The `spend --sessions` per-session drill-down is not surfaced as its own TUI view this
  phase (the per-project tab is the parity baseline; per-session detail is already visible
  in the existing session views). Not a deferral under the Fix Bar; it is simply not part
  of this phase's scope and is noted to avoid scope creep.

## Scope check

- Over-scope: none (mirrors CLI reporting). Do NOT reimplement `cli_list_running`'s printing
  or the per-session spend drill-down in the TUI.
- Under-scope (now fixed): the fail-loud running state (PR-001) and empty/error states
  (PR-005) are added as explicit steps/validation.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE THE ACTUAL runner output
  (never a claimed pass).
- PR-003 anti-regression: assert `spend --json` output is byte-identical before/after the
  Step 1 refactor (the JSON is a public serialized format).
- TUI `run_test()` tests: (a) spend table rows/totals match `gather_spend()` on a seeded DB;
  (b) historical toggle adds the ledger totals; (c) running tab renders instances and raises
  the banner for a vulnerable/exposed one (mocked detector); (d) running tab shows the loud
  unreliable-detection state when the detector raises `RunningDetectionError`.
- Empty states: spend tab with zero projects; running tab with zero instances (a plain
  "none found", distinct from the error state).

## Spec / documentation sync

Add "Spend" and "Running" tabs to the README/ARCHITECTURE TUI section (consolidated docs
pass at the end of the parity effort) and a CHANGELOG entry for Phase 3.

## Open questions

- OQ-P3-1: RESOLVED (this review) - `cli_spend` has NO data-returning core (it builds data
  inline and only prints/emits), so extracting `gather_spend()` is REQUIRED, not optional
  (Step 1). No open questions remain.

## Approval and execution gate

This IPD is a proposal and is NOT auto-executed. Execution contract:

- Open questions: none (OQ-P3-1 resolved above).
- Scope fence: ONLY the new Spend and Running tabs, the `gather_spend()` extraction (no
  change to `spend` text/JSON output), and the minimal `core.py` re-exports. Do NOT touch
  other tabs, the running detector logic, or add mutation. No new runtime dependencies.
- Honesty rule (hard MUST): paste the ACTUAL `pytest -q` output in the execution report;
  never claim a pass you did not run.
- Commits: path-scoped, NEVER push, NEVER tag.
- Lifecycle: on completion set `Status: executed` and `git mv` this IPD to
  `.agents/plans/executed/` (verify no pending/executed duplicate).

Next: human approval sets `Status: approved`; then execute per the above.
