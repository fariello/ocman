# Lens: Bugs and correctness

Focus the assessment on defects in existing behavior: code that does the wrong thing,
produces incorrect output, or fails on a reachable path. Complements edge-cases
(untested limits) and testing (coverage) by hunting for outright incorrectness.

## Lead personas

QA engineer and software engineer, with the data-integrity view on anything that can
corrupt or lose data.

## Rubric

- **Logic errors:** wrong conditionals, off-by-one, inverted checks, incorrect
  operator/precedence, copy-paste mistakes, wrong variable, swapped arguments.
- **Contract violations:** functions that do not honor their documented behavior;
  return/throw inconsistencies; null/None handling; type confusion.
- **State & data integrity:** operations that can leave inconsistent or partial state;
  non-atomic multi-step writes; lost updates; the live-interaction / data-integrity
  surfaces from `../release-review/00-run-protocol.md` (resume/idempotency,
  overwrite-of-verified-output, spend accounting, wrong-process signaling).
- **Concurrency:** races, missing synchronization, TOCTOU, non-idempotent retries
  (cross-reference memory-resources/reliability).
- **Resource handling:** leaks, unclosed handles, use-after-close (cross-reference
  memory-resources).
- **Error handling:** swallowed errors, wrong error path, double responses, cleanup
  that does not run on failure.
- **Integration correctness:** wrong API usage, dialect/parameter mismatches, encoding
  bugs, timezone/locale bugs.
- **Regression risk:** recently changed code that looks behavior-altering.

## IPD emphasis

Verify each suspected bug by reading the actual code path (and, where cheap, a quick
reproduction), not by inference. Rate data-loss/corruption and auth/correctness on
reachable paths as Blocker/High. Propose a fix AND a regression test for each
confirmed bug. "Hard to test" is a prompt to extract a testable seam, not to skip the
test.
