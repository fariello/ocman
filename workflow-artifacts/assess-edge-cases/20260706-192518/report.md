# Assessment run report - edge-cases (filter, canonical naming, migration script)

- Date / run ID: 20260706-192518
- Concern: edge-cases
- Scope: new 1.1.0 surface - `canonical_recovery_name`/`parse_recovery_name`, `cli_filter`,
  `scripts/migrate_recovery_names.py`.
- IPD written: `.agents/plans/pending/20260706-assess-edge-cases-filter-and-naming.md`
- Verdict: **adequate** for edge-cases (safe by default - no data-loss or crash-on-normal-path;
  one Medium graceful-handling gap and several low-severity input-validation/robustness items)

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| EC-1 | Medium | Low | QA / software eng | Minute-precision names: two legacy files differing only in seconds canonicalize to the same target; migration safely skips the second but with a terse, confusing message. |
| EC-2 | Low | Low | QA / novice | `filter` sends empty/whitespace-only input to the LLM instead of refusing early. |
| EC-3 | Low | Low | software eng | Whitespace-only `--scope` passes the "at least one scope" check (`if scope:`). |
| EC-4 | Low | Low | software eng | `canonical_recovery_name` accepts a bogus `kind` with no validation -> unparseable name. |
| EC-5 | Low | Low | QA | `parse_recovery_name` suffix match is case-sensitive; `*.RESTART.MD` unrecognized. |
| EC-6 | Low | Low | software eng | Legacy date-only name with an 8-digit-leading session id mis-splits (theoretical for real ids). |
| EC-7 | Low | Low | QA | (Positive) invalid embedded dates correctly yield `dt=None` -> safe mtime fallback; pin with a test. |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

1. EC-1: explanatory same-minute-collision message in the migration (keep safe skip) + doc the minute precision.
2. EC-2: refuse empty/whitespace input in `cli_filter` before the API call.
3. EC-3: `.strip()` `--scope` and treat all-whitespace as absent.
4. EC-4: validate `kind in RECOVERY_KINDS` in `canonical_recovery_name`.
5. EC-5: case-insensitive suffix match in `parse_recovery_name`.
6. EC-7: regression tests pinning invalid-date -> `dt=None`.

## Deferred (with reason)

- Raising canonical names back to **seconds** precision (to avoid EC-1 collisions): Remediation
  Risk Medium-High on **functionality** - it reverses the deliberate minute-precision decision and
  its tests/docs and still would not fully prevent collisions. The graceful migration handling is
  the correct fix instead. (Effort/time is not the reason.)
- EC-6 is not deferred-as-risky but simply not worth code (unreachable for real `ses_...` ids);
  documented + a behavior-pinning test.

## Out-of-repo / organizational notes

- None.

## Next step

Review the IPD (optionally run `plan-review`) and approve before execution. Prefer executing it
together with the pending security IPD since both edit the same `cli_filter` block. This workflow
does not execute the plan.
