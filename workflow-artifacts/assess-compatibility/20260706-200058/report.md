# Assessment run report - compatibility (recovery naming, filter, TUI, cross-platform)

- Date / run ID: 20260706-200058
- Concern: compatibility (resolved from the misspelling "compatability")
- Scope: 1.1.0 surface + interop - naming helpers, `cli_filter`, migration script, CLI + TUI
  recovery writers, supported platform matrix.
- IPD written: `.agents/plans/pending/20260706-assess-compatibility-filter-and-naming.md`
- Verdict: **needs work** for compatibility (two Medium consistency defects the 1.1.0 rename
  widened - CLI/TUI naming divergence and a stale naming-contract lookup - plus a macOS FS gap;
  backward read-compat and Windows filename safety are OK)

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| COMP-1 | Medium | Low-Medium | power user / stakeholder | CLI writes canonical `YYYYMMDD-HHMM-<full_sid>.<kind>.md`; TUI still writes `opencode-recovery-<sid[:8]>-<YYYYMMDD-HHMMSS>.<kind>.md` + `.compact-prompt.md`. 1.1.0 widened a pre-existing divergence; migration doesn't normalize TUI output. |
| COMP-2 | Medium | Low | software eng / power user | Compact-prompt written as `*.prompt.md` but the CLI compaction picker looks for `*.compact-prompt.md` (ocman.py:8907) - works only by the `generated_paths[-1]` fallback; TUI + a docstring still say `.compact-prompt.md`. |
| COMP-3 | Medium | Low | operator | `parse_recovery_name` suffix match is case-sensitive; on macOS (supported CI target) a `*.RESTART.MD` legacy file is silently un-migrated. (Same root as edge-cases EC-5.) |
| COMP-4 | Low | Low | operator | (Positive) canonical names are Windows-safe (`safe_filename` allow-list; no `:`); no reserved-name guard but unreachable for `ses_` ids. |
| COMP-5 | Low | Low | operator / stakeholder | New config keys (`filter_max_bytes`, `filter_secret_scan`) from sibling IPDs must default safely so old `ocman.toml` keeps working. |
| COMP-6 | Low | Low | software eng | (Positive) `parse_recovery_name` reads both legacy on-disk forms + canonical -> old files stay readable/migratable. Pin with a test. |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

1. COMP-1/2: unify TUI naming with the CLI via `canonical_recovery_name` (full sid, `.prompt.md`,
   fix the button label).
2. COMP-2: fix the stale `.compact-prompt.md` lookup (-> `.prompt.md`) + the docstring.
3. COMP-3: adopt the edge-cases case-insensitive parse fix (shared, execute once).
4. COMP-5: safe defaults for the new config keys; old `ocman.toml` loads unchanged.
5. COMP-4/6: regression tests (Windows-valid names; backward-read of legacy forms).

## Deferred (with reason)

- Windows reserved-device-name (CON/PRN/NUL) sanitizer in `safe_filename`: Remediation Risk
  Medium-High on **complexity** - a correct per-component, extension-aware reserved-name filter is
  disproportionate given `ses_` ids can never equal a reserved name and the risk is implausible /
  non-destructive. (Effort/time is not the reason.)

## Out-of-repo / organizational notes

- None. The CI matrix (ubuntu/macos/windows x 3.10-3.14) is the compatibility oracle; proposed
  tests run there.

## Next step

Review the IPD (optionally run `plan-review`) and approve before execution. Execute together with
the sibling security + edge-cases IPDs (overlapping code). This workflow does not execute the plan.
