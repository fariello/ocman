# assess testing - decisions & assumptions

- Concern: `tests` -> resolved to the `testing` lens (closest match; `tests`->testing).
- Scope: the whole test suite (argument was `tests`); assessed tests/*.py against ocman/ + ocman_tui/.
- Project conventions: universal fallback principles (no GUIDING_PRINCIPLES.md). Plans lifecycle
  `.agents/plans/pending/` -> `executed/`; IPD name `YYYYMMDD-HHMM-NN-<slug>.md`; Status born `to-review`.
  No em/en dashes in authored prose. Path-scoped commits, never push.
- Test stack: pytest + anyio (dev extra); command `PYTHONPATH=. pytest`; CI matrix ubuntu/macos/windows x py3.10-3.14 runs bare `pytest` (no coverage). conftest neutralizes the running-OpenCode guard by default and skips Linux-only detector tests off-Linux.

## Verdict basis (evidence, not self-report)
- Ran the suite: 452 passed, 2 skipped (2 = OCMAN_BENCHMARK-gated perf).
- Measured coverage (coverage 7.15.0, --source=ocman,ocman_tui): 70% overall; cli.py 71%; TUI 53-65%.
- Mapped cli.py missing lines to functions to find the real gaps (see evidence.md).

## What was intentionally NOT proposed (and why)
- A hard coverage % gate in CI: NOT proposed as a first step. Remediation Risk on the
  functionality/usability axis: a brittle threshold causes false CI failures and ratchet
  fights; propose measurement + visibility first, gate later if wanted. (T-01 stays measurement-only.)
- A blanket "raise coverage to N%" push: rejected per the lens (chase behavior, not a number).
  Proposed targeted tests for the highest-risk uncovered branches instead.
- Rewriting the TUI test approach wholesale: only the flake-prone mount-assert pattern (T-02)
  is proposed for a shared helper; broader TUI coverage (T-05) is Low priority, targeted.

## Assumptions
- The 468 missed lines in `_run_main` are mostly the large command-dispatch tail (rare/error
  branches), not an untested feature; not treated as a single high finding.
- coverage numbers are from a Linux py3.14 run; off-Linux detector paths are skipped there, so
  their coverage is understated (acceptable; those paths ARE covered on Linux CI cells).

## Open questions for the user
- Do you want coverage merely VISIBLE (report artifact / CI log) or eventually GATED at a floor?
- Priority order among T-02 (flake hardening), T-03 (destructive error-path tests), T-05 (TUI)?
