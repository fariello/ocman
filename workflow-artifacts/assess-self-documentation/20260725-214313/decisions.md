# Decisions and assumptions - assess self-documentation (20260725-214313)

## Concern / scope
- Concern: self-documentation (in-product learn-as-you-go clarity; distinct from the README
  `documentation` lens assessed earlier). Scope: whole project, the `ocman/cli.py` CLI surface.
- Verified against BOTH the shipped `ocman` binary (runtime exit codes and `-h`/error output) and
  the source, not inferred from names.

## Project conventions (Step 0)
- Lifecycle `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`; Status readiness.
- AGENTS.md prose rule (no em/en dashes). Python 3.10+ argparse CLI + Textual TUI, v1.3.0.
- Review-scope exclusions honored (`.agents/workflows/`, `workflow-artifacts/` not assessed).

## Key decisions
- Verdict: adequate. The CLI teaches unusually well (near-total help= coverage, task-grouped
  runnable examples, actionable no-match errors with Suggestions, help TOPIC system, graceful
  no-config fallback, best-in-class no-project onboarding). Findings are one High first-run/
  error-signal cluster + medium/low polish.
- Delegated a broad help/naming/error/first-run audit to an explore sub-agent, THEN the orchestrator
  re-verified the severe claims from the live binary before writing the IPD:
  - SD-01/02 CONFIRMED: bare `ocman </dev/null` exits 1 with "Unexpected error: EOF..." (the no-args
    path prompts `Select a session number` at cli.py:1697/16794; the help promise at cli.py:5634
    says it merely lists). My own first observation (a clean listing) was incomplete: I had missed
    the trailing prompt because my shell stdin looked interactive.
  - SD-03 CONFIRMED: `ocman --db /nope db info` exits 0 (soft warn cli.py:12894; ideal
    _db_not_found_error unused at cli.py:1214).
  - SD-04 CONFIRMED: `session search` empty exits 0 (cli.py:16345) vs resolver exit 1 (cli.py:5277).
  - CORRECTION: my earlier "invalid --older-than exits 0" was WRONG; it exits 2 (correct usage code)
    via _die_cli. The sub-agent caught this; I re-verified exit 2. So no finding there.

## What was intentionally NOT proposed (and why)
- Shell completion (argcomplete/static scripts): DEFERRED on the COMPLEXITY axis (Remediation Risk
  Medium-High): a new dependency + packaging surface + per-shell install docs, disproportionate for
  a self-documentation polish plan. Recommended as its own IPD. (findings.csv id SD-D1.)
- Broad verb re-naming beyond the SD-06 `rescope` alias: NOT proposed (usability axis) - renaming
  stable commands breaks users' muscle memory/scripts, and help already distinguishes them while
  `doctor` routes users to the right cleanup verb.
- SD-04 does NOT change the search empty-result exit code (kept at 0): changing it could break
  existing scripts; only the intent is made explicit.

## Assumptions (to confirm)
- SD-06: adding a `rescope` alias for `filter` is wanted (keeps `filter` working).
- SD-01: the intended no-args-AT-A-TTY behavior is the interactive picker; the plan keeps that and
  only changes the non-TTY path to a clean listing + exit 0.

## Open questions for the user
- Confirm SD-06 (add `rescope` alias) and SD-01 (keep the TTY picker) before executing steps 6/1.
