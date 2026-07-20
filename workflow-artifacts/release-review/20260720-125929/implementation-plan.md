# Implementation Plan (Section 7)

Consolidated from Sections 1-6. This is a delta re-review; the audit found the delta correct
and the package release-ready, so the implementation set is small.

## Findings summary

| ID | Type | Sev | RR | Status after audit | Disposition |
|---|---|---|---|---|---|
| S1-CI1 / S6-CI1 | CI | Low | Low | identified | FIX now (restore fail-fast) |
| S2-B1 | B | Med | Low | completed (already fixed in 4cfcd18) | verify only |
| S2-S1 | S | Low | Low | not_applicable (synthetic fixtures, baselined) | no action |
| S3-T1 | T | Low | Low | completed | no action |
| S4-D1 | D | Low | Low | completed | no action |
| S4-D2 | D | Low | Low | identified | FIX now (changelog date) |
| S5 (principles/cold-start/TODO) | - | - | - | PASS/STRONG/clean | no action |
| S6-P1 | P | Med | Low | completed | no action |

## Actions to implement in Section 7

### A1 (from S1-CI1 / S6-CI1): Restore CI fail-fast to default

- Change: in `.github/workflows/ci.yml`, remove the temporary `fail-fast: false` override and
  its explanatory comment, returning the matrix to the default (fail-fast: true).
- Remediation Risk: Low. It only changes CI scheduling behavior on a failure; it does not
  affect what is tested. The matrix is currently green (15/15), which is the documented
  precondition for restoring it (DECISIONS.md).
- Validation: push triggers CI; confirm all cells stay green. (Push/CI is a remote action;
  under this run it will be part of the Section 9 release execution / or committed locally and
  pushed only on the user's push approval per the run's push policy.)

### A2 (from S4-D2): Correct the CHANGELOG [1.2.0] release date

- Change: update `## [1.2.0] - 2026-07-19` to the actual finalization date `2026-07-20`.
- Remediation Risk: Low. Cosmetic changelog accuracy; no functional impact.
- Validation: visual; no test impact.

## Explicitly NOT changing

- The macOS firmlink fix (S2-B1) and vistab floor (S6-P1): already implemented and verified;
  no further change.
- The synthetic secret fixtures (S2-S1): confirmed false positives, already baselined; no
  history rewrite (disruptive, no security benefit).
- No lint/type-check CI added (scope creep). No new features. No refactors.
- The DECISIONS.md fail-fast entry says restore "once green"; after A1 lands and CI confirms
  green, that follow-up is satisfied (the entry is historical/append-only and stays as record).

## Order

1. A2 (CHANGELOG date) - local, no side effects.
2. A1 (ci.yml fail-fast restore) - local commit; CI re-run happens on push.
3. Full local test suite re-run (regression guard) after edits.
