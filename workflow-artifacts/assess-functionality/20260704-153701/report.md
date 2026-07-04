# Assessment run report - functionality (disk-usage reporting)

- Date / run ID: 20260704-153701
- Concern: functionality completeness
- Scope: NARROWED (user request) to disk-usage reporting — per-project on-disk usage and
  backups directory usage
- IPD written: .agents/plans/pending/2026-07-04-assess-functionality-disk-usage.md
- Verdict: **needs work** for this specific capability — `ocman info` reports DB-family and
  a global session-diff total but omits backups usage and any per-project breakdown, both
  of which the user reasonably expects. One honest constraint (per-project DB bytes are not
  measurable from a shared SQLite file) shapes the design.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| FUNC-1 | Medium | Low | stakeholder / power user | No backup-dir usage report (real case: 7.3 GB unseen) |
| FUNC-2 | Medium | Low | power user | No per-project breakdown; session-diff bytes are exactly attributable via project_id |
| FUNC-3 | High | Medium-High (functionality) | QA | Per-project DB *bytes* not measurable (shared SQLite) — must not present an estimate as exact |
| FUNC-4 | Low | Low | novice | Discoverability of the new info |
| FUNC-5 | Low | Low | power user | TUI parity (follow-up) |

(Full list in `findings.csv`.)

## Proposed plan (summary)

1. `dir_usage()` recursive size helper.
2. Add a "Backups (Disk Storage)" section to `ocman info` (total size, count, oldest/newest).
3. Add `ocman info --by-project`: exact per-project session-diff bytes + session/message/
   token counts, sorted by size; explicitly NO per-project DB bytes.
4. Document in README + `--help`; optional `disk`/`du` NL alias.
5. CHANGELOG entry.

## Deferred (with reason)

- FUNC-3 (per-project DB *bytes*): Remediation Risk **Medium-High** on **functionality** —
  not directly measurable from a shared SQLite file; any figure is an estimate and would
  mislead (honest-docs). Report exact session-diff bytes + row/token counts instead.
- FUNC-5 (TUI parity): deferred to a follow-up; CLI first.

## Out-of-repo / organizational notes

- The user's environment already shows the value: 7.3 GB backups + 2.8 GB DB. Backups are
  dominated by `opencode-db-cleanup-*` dirs (each a full DB copy) — the proposed backups
  section will make this visible and actionable (pair with `--clean-backups`).

## Next step

Review the IPD (optionally run `plan-review`) and approve before execution. This workflow
did not execute the plan and changed no application code.
