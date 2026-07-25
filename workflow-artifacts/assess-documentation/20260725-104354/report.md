# Assessment run report - documentation (whole project, README primary)

- Date / run ID: 20260725-104354
- Concern: documentation
- Scope: whole project; README.md primary, CHANGELOG.md cross-check; verified vs ocman/cli.py
- IPD written: .agents/plans/pending/20260725-1043-01-assess-documentation.md
- Verdict: adequate for documentation (accurate and current; one High accuracy fix + minor gaps)

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| AD-01 | High | Low | engineer,novice | README `ocman kill [PATTERN]` is stale; shipped command is `PID\|PATTERN` (all-digits = PID) with an enriched confirm preview |
| AD-02 | Medium | Low | engineer | Env-var table claims `OCMAN_CONFIG_PATH` overrides the config path, but it is a hardcoded constant never read from the environment |
| AD-03 | Medium | Low | novice,engineer | `ocman spend` is listed under the `history` table but is a top-level verb (no `ocman history spend`) |
| AD-04 | Low | Low | engineer | `lr`/`running` `--long` (Session column) undocumented |
| AD-05 | Low | Low | novice | `session export` shown session-only; project export only via top-level `ocman export project` |
| AD-06 | Low | Low | engineer | CHANGELOG `[Unreleased]` empty despite post-1.3.0 kill-by-PID/preview work in code |
| AD-07 | Low | Low | novice | No consolidated "Platforms" statement (Linux-only features + Linux-only pysqlite3-binary) |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)
1. Fix the `kill` README row to `[PID|PATTERN]` + one sentence on PID + the enriched preview (AD-01).
2. Correct the env-var table: remove the false `OCMAN_CONFIG_PATH` override row (AD-02).
3. Move `ocman spend` from the history table to top-level verbs (AD-03).
4. Document `lr --long` (AD-04); point `session export` at top-level project export (AD-05).
5. Add an `[Unreleased]` CHANGELOG entry for kill-by-PID + enriched preview (AD-06).
6. Add a short "Platforms" note to Known Limitations (AD-07).

## Deferred (with reason)
- None deferred on Remediation-Risk grounds (all fixes are Low risk). The CODE alternative for
  AD-02 (implement an `OCMAN_CONFIG_PATH` env override) is intentionally out of scope for a docs
  plan; it is a behavior change needing its own decision + tests, recorded as an open question. The
  docs-side correction is proposed and is sufficient to remove the inaccuracy.

## Out-of-repo / organizational notes (if any)
- None.

## Next step
Review the IPD (optionally run the `plan-review` workflow on it) and approve before execution. This
workflow does not execute the plan.
