# Assessment run report - self-documentation (whole project, CLI surface)

- Date / run ID: 20260725-214313
- Concern: self-documentation (in-product, learn-as-you-go clarity)
- Scope: whole project; `ocman/cli.py` CLI (help, naming, errors, first-run, discoverability);
  verified against the shipped `ocman` binary and source
- IPD written: .agents/plans/pending/20260725-2143-01-assess-self-documentation.md
- Verdict: adequate for self-documentation (genuinely strong; one High first-run/error-signal
  cluster + minor polish)

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| SD-01 | HIGH | Low | novice,ui/ux | Bare `ocman` prompts for a session; non-TTY stdin hits EOF -> "Unexpected error" -> exit 1 (crash on the most natural first command / in scripts) |
| SD-02 | HIGH | Low | novice | Help promises "(no args: lists sessions)" but no-args actually launches the interactive picker; the product misdescribes itself |
| SD-03 | MEDIUM | Low | novice,power | `db info` on a missing `--db` prints a soft warning + empty screen and exits 0, hiding the failure (the ideal `_db_not_found_error` exists but is unused) |
| SD-04 | MEDIUM | Low | power | `session search` empty exits 0 while the target-resolver's "No matches" exits 1; inconsistent signalling |
| SD-05 | MEDIUM | Low | novice,ui/ux | Per-command `-h` has no examples; examples live only in the top-level help / `help TOPIC` |
| SD-06 | MEDIUM | Low | novice | `filter` verb reads as "filter a list" but means "re-scope a recovery doc via the LLM" |
| SD-07 | LOW | Low | novice | `db rebase` help explains the jargon with the same jargon |
| SD-08 | LOW | Low | novice | `filter` option help ( -C / -oc / --scope ) is terse vs the identical recovery options |
| SD-09 | LOW | Low | novice | A few terminal empty-result `die()`s give no next-step |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)
1. No-args + non-TTY stdin: print the listing and exit 0 (only prompt at a TTY) (SD-01).
2. Correct the help line to match that behavior (SD-02).
3. Route `db info` missing-DB through `_db_not_found_error()` -> exit 1 (SD-03).
4. Make `session search` empty-result-exits-0 intent explicit (comment; behavior unchanged) (SD-04).
5. Add `epilog=` examples to high-traffic subcommands' `-h` (SD-05).
6. Add a `rescope` alias for `filter` (SD-06).
7. De-jargon `db rebase` help (SD-07); flesh out `filter` option help (SD-08); add next-steps to
   bare empty-result dies (SD-09).

## Deferred (with reason)
- Shell completion (argcomplete/static scripts): Remediation Risk Medium-High on COMPLEXITY (new
  dependency/packaging + per-shell install docs) for a self-documentation polish plan. Recommended
  as its own small IPD. Not an effort deferral.
- Broad verb re-naming beyond SD-06: usability risk (breaks muscle memory/scripts); help already
  distinguishes the commands and `doctor` routes users.

## Out-of-repo / organizational notes (if any)
- None.

## Next step
Review the IPD (optionally run `plan-review` on it) and approve before execution. This workflow
does not execute the plan.
