# Lens: Testing rigor and completeness

Focus the assessment on whether the project's tests give real confidence: do they
cover the critical behavior, protect against regressions, and reflect how the software
is actually used and fails?

## Lead personas

Testing/regression expert and QA engineer, with the software engineer on testability.

## Rubric

- **Coverage of what matters:** are the critical paths, public contracts, and
  high-risk code tested - not just easy code? Coverage of behavior, not just lines.
- **Test types present and appropriate:** unit, integration, contract, end-to-end,
  property-based, accessibility, load/perf - matched to the project type.
- **Negative & failure testing:** invalid inputs, error paths, rollback, the
  authorization matrix (role x resource, cross-tenant denial), timeouts/retries.
- **Edge & boundary cases** encoded as tests (cross-reference edge-cases lens).
- **Regression protection:** are recently changed and historically buggy areas pinned
  by tests? Characterization tests before risky refactors.
- **Production-equivalent fidelity:** integration tests run against the real
  dependency/dialect, not only a substitute that hides drift.
- **Test quality:** deterministic (no flakiness/sleeps/order dependence); meaningful
  assertions (not just "does not throw"); isolated; fast enough to run often;
  realistic fixtures/seeds that retain important edge scenarios.
- **Test-as-documentation:** tests communicate intended behavior.
- **CI execution:** the suite actually runs in CI and gates merges (cross-reference
  CI if assessed).

## IPD emphasis

Propose the highest-value missing tests first (critical paths, data-integrity/LIVE
behavior, recently changed code) rather than chasing a coverage number. For
hard-to-test code, propose the refactor that introduces a testable seam. Prefer
removing/replacing brittle or low-value tests over piling on more. Test additions are
low Remediation Risk; propose by default.
