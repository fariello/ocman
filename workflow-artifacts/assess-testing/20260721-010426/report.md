# Assessment - testing (whole test suite)

Verdict: **adequate** for testing (strong on critical paths; targeted gaps worth closing).
IPD written: `.agents/plans/pending/20260721-0111-01-assess-testing.md`

Evidence: 452 passed, 2 skipped (verified via pytest); 70% statement coverage
(coverage 7.15.0, source=ocman,ocman_tui); cli.py 71%, TUI 53-65%.

## Top findings
| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| T-01 | Medium | Low | testing | No coverage measurement (no config; CI runs bare pytest) - regressions invisible |
| T-02 | Medium | Low | QA/QC | ~10 TUI tests assert modal presence after ONE pause (no poll) - the flake class that forced reruns |
| T-03 | Medium | Low | testing | Uncovered ERROR/rollback branches in destructive/transfer fns (_execute_move, import, deletes, restore) |
| T-04 | Low | Low | software eng | Remote-move/git-decision code hard to test; needs a pure testable seam |
| T-05 | Low | Low | testing | TUI weakest-covered (database.py 53%, app.py 65%) |
| T-06 | Low | Low | QA/QC | Perf tests skip-by-default; never run in CI |
| T-07 | - | - | testing | POSITIVE: strong critical-path/security/portability coverage; meaningful assertions |

## Proposed plan (summary)
1. Shared `await_screen(...)` poll helper; replace bare modal-mount asserts in test_tui.py (T-02).
2. Add coverage config + pytest-cov dev dep; document `pytest --cov` (T-01).
3. Optional non-gating coverage step in CI (T-01).
4. Negative/rollback tests for the uncovered error branches of import/delete/move/restore, mutation-checked (T-03).
5. Extract a pure testable seam from _gather_git_decisions; unit-test the branch logic (T-04).
6. (Lower) Focused TUI worker/error-path tests; make one perf check CI-runnable report-only (T-05, T-06).

## Deferred (with reason)
- Hard coverage-% CI gate: Remediation Risk Medium-High on functionality/usability (brittle
  thresholds cause false failures / ratchet fights). Sequence measurement+visibility first.
- Blanket "raise coverage to N%": wont-do per the lens (chase behavior, not a number).

Next step: review the IPD (optionally run plan-review on it) and approve before execution.
This workflow does not execute the plan.
