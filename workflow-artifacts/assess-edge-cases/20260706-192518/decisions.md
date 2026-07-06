# Decisions and assumptions - assess-edge-cases (filter + naming + migration) run 20260706-192518

## Concern and scope
- Concern: edge-cases. Lens: `.agents/workflows/assess/lenses/edge-cases.md`.
- Scope narrowed (pre-release, per user's assessment sequence) to the new 1.1.0 surface:
  `canonical_recovery_name`/`parse_recovery_name`, `cli_filter`, `scripts/migrate_recovery_names.py`.
  Not a whole-project pass.

## Project conventions discovered
- Principles from `ARCHITECTURE.md` + universal fallback (self-documenting, KISS, honest docs,
  configurable-over-hardcoded).
- IPD lifecycle `.agents/plans/pending/` -> `executed/`; run records under
  `workflow-artifacts/assess-<concern>/<RUN_ID>/` (committed, out of review scope).
- Scope exclusions honored: did not assess `.agents/workflows/` or `workflow-artifacts/`.

## Key decisions / assumptions
- **Verdict "adequate," not "needs work":** every finding is safe-by-default - none corrupts data
  or crashes on a normal path. EC-1 (the only Medium) is a *graceful-handling* gap, not a
  correctness/data-loss bug (the migration already preserves both files). The rest are low-severity
  input-validation/robustness polish.
- **Minute-precision is intentional and kept.** EC-1's collision is inherent to the user's chosen
  `YYYYMMDD-HHMM` scheme. Reverting to seconds was DEFERRED (Medium-High on functionality): it
  reverses a deliberate decision + its tests/docs and still would not fully avoid collisions. The
  fix is to handle the collision gracefully in the migration, not to change the scheme.
- **EC-6 is not worth code:** real opencode session ids are `ses_<base62>`, never a bare 8-digit
  string, so the date-only mis-split is unreachable; canonical names round-trip correctly. Proposed
  a doc comment + a behavior-pinning test only.
- **Findings verified by repro,** not inferred: same-minute migration collision, empty-input send,
  whitespace-scope acceptance, bogus-kind acceptance, case-sensitive suffix, 8-digit-sid mis-split,
  and the (positive) invalid-date -> dt=None fallback were all reproduced directly.
- **Execution coupling:** EC-2/EC-3 edit the same `cli_filter` block as the pending security IPD's
  size-cap/secret-scan changes; recommended executing the two IPDs together to avoid double edits.

## What was intentionally NOT proposed and why (Remediation-Risk axis)
- Seconds-precision canonical names (Functionality, Medium-High) - see above.
- Content-hash or numeric-counter disambiguation suffixes on canonical names (Complexity) - would
  complicate a deliberately simple naming scheme; the migration skip-with-explanation suffices.

## Open questions for the user (also in the IPD)
1. EC-1: skip-with-explanation (proposed) vs. auto-disambiguate same-minute collisions (e.g. `-2`)?
2. EC-5: confirm you want case-insensitive suffix matching (macOS safety) though ocman is
   Linux-primary (one-line, zero-risk).
