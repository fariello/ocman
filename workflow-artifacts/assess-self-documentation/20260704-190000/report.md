# Assessment run report - self-documentation (clean-backups preview)

- Date / run ID: 20260704-190000 (invoked 2026-07-04 18:49)
- Concern: self-documentation ("prompts that teach") + UI/UX, on a destructive command
- Scope: NARROWED to the `ocman --clean-backups` confirmation output
- IPD written: .agents/plans/pending/2026-07-04-assess-self-documentation-clean-backups-preview.md
- Verdict: **needs work** — the confirmation lists only what will be deleted, so the user cannot see what
  survives, and there is no special warning when the purge removes ALL backups.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| CB-2 | High | Low | stakeholder / QA | No forceful warning when the purge deletes ALL backups (100% of rollback safety) |
| CB-1 | Medium | Low | novice / UI-UX | Only doomed backups listed; user can't tell what survives before confirming |
| CB-3 | Medium | Low | QA | "older than N days" header + "Created:" (really st_mtime) can mislead |
| CB-5 | Low | Low | UI-UX | Column alignment breaks when ANSI color tags are added |
| CB-8 | Low | Low | accessibility | Must not rely on color alone |

(Full list incl. CB-4/CB-6/CB-7 in `findings.csv`.)

## Proposed plan (summary)

1. Collect both `to_delete` and `to_keep` in one pass (size computed once).
2. Render ALL backups with a leading `DELETE` (red) / `KEEP` (green) column; pad plain text before color;
   words carry the meaning (color-independent).
3. Summarize KEEP rows past a threshold (full under `-v`) so DELETE rows stay visible at scale.
4. If `kept == 0` and there is >= 1 backup, print a prominent red "this deletes ALL N backups — no rollback
   backups will remain" warning; else the normal "N to delete, M kept" summary.
5. Header shows the concrete cutoff timestamp; relabel per-row "Created" → "Modified".
6. Same annotated view + warning in dry-run; unchanged typed-`yes` confirmation on the real path.
7. README + CHANGELOG.

## Deferred (with reason)

- Applying the same KEEP/DELETE treatment to the session age-based `--clean` prompt (`db_run_cleanup`): out
  of scope for this request (a separate, analogous command). Recommended as a follow-up.

## Out-of-repo / organizational notes

- None. Pure CLI output change; no new dependency; the set of deleted items and the cutoff math are unchanged.

## Next step

Review the IPD (optionally run `plan-review`) and approve before execution. This workflow did not execute the
plan and changed no application code. Three open questions (KEEP threshold, sort grouping, whether to extend
to `--clean`).
