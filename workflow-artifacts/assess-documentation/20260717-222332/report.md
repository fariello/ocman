# Assessment - documentation (whole project)

Verdict: needs work for documentation
IPD written: .agents/plans/pending/20260717-2223-01-assess-documentation.md

Documentation is broadly present and the CHANGELOG [Unreleased] is thorough and current,
but README.md and ARCHITECTURE.md carry several now-FALSE accuracy claims after the
recent feature wave, plus coverage gaps (undocumented flags, env vars, config keys). The
documentation lens prioritizes accuracy (highest harm) over completeness, so the plan
fixes the false claims first. All findings are low Remediation Risk (docs only), so all
are proposed for action; none deferred.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| D-01 | High | Low | novice | README "Zero external dependencies" is false; the CLI hard-imports vistab and has 4 core deps. |
| D-02 | High | Low | novice | "Standalone `ocman.py`" install mode references a file that does not exist (module is `ocman/cli.py`). |
| D-03 | High | Low | engineer | "Recovery options" table lists `--show-secrets`/`--expunge-secrets`/`-y`/`--force` as recover flags; they are compact-only (recover rejects them). |
| D-04 | High | Low | engineer | ARCHITECTURE says "standard library only for the CLI path" and names `ocman.py`; both false. |
| D-05 | Medium | Low | engineer | README config template: `filter_secret_scan` unquoted (invalid TOML) and wrong `default_out_dir` default. |
| D-06 | Medium | Low | engineer | 4 config keys undocumented in README (chunk_max_interactions/lines, reclaim_tmp_min_age_hours, reclaim_parts_retention_days). |
| D-07 | Medium | Low | novice/engineer | No env-vars section; OPENCODE_DB/XDG_DATA_HOME/OPENCODE_CONFIG_DIR undocumented. |
| D-08 | Medium | Low | engineer | Several real flags missing from README command tables. |
| D-09 | Medium | Low | engineer | ARCHITECTURE verb list omits spend/running/doctor/reclaim. |
| D-10 | Low | Low | novice | README overclaims `ocman help all` as the complete reference; it omits new commands. |
| D-11 | Low | Low | engineer | CHANGELOG reclaim entry omits two flags; batch-delete has no discrete entry. |

## Proposed plan (summary)

1. Kill the "zero-dependency / `ocman.py` standalone" install story; state real install + deps; fix ARCHITECTURE `ocman.py` -> `ocman/cli.py` and drop "standard library only" (D-01/D-02/D-04).
2. Correct the Recovery-options table to separate compact-only flags from shared recovery flags (D-03).
3. Fix the config template (quote `filter_secret_scan`; correct `default_out_dir`) (D-05).
4. Document the 4 missing config keys (D-06).
5. Add an Environment variables section (D-07).
6. Add the missing flags to the README command tables (D-08).
7. Update the ARCHITECTURE top-level verb list (D-09).
8. Soften/repair the `help all` claim, cross-ref self-documentation (D-10).
9. Tidy the CHANGELOG reclaim/batch-delete entries (D-11).

## Deferred (with reason)

None. Every finding is a low-Remediation-Risk documentation correction; nothing clears
the Medium-High bar that would justify deferral.

Next step: review the IPD (optionally run plan-review on it) and approve before
execution. This workflow does not execute the plan.
