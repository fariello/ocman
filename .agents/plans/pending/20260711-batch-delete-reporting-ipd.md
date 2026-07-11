# Implementation Plan - Batch delete reporting, per-batch VACUUM, empty-project cleanup

Status: PROPOSED (not yet executed)

Improves the UX of multi-session (and project-expanded) `ocman session delete`
and `ocman project delete`, based on a real run that deleted a whole project's
7 root sessions. The delete itself worked correctly; the reporting and
per-session repetition were the problem.

Evidence lines are `ocman/cli.py:<line>` verified on 2026-07-11 against the
post-restructure package layout (`ocman/cli.py`); re-verify before editing.

---

## Motivation (from a real run)

`ocman session delete /home/gfariello/VC/uri-ai-info` expands to the project's
sessions and loops `db_delete_session_recursive` once per session
(`ocman/cli.py:11296-11304`). That function prints, PER SESSION
(`ocman/cli.py:7284-7307`): a "Deletion complete!" block with database
size-before/after/reclaimed, a "database family backup" line, and a full
multi-line "Rollback instructions" stanza, and it runs a VACUUM. For a 7-session
delete this printed the whole stanza 7 times and VACUUMed 7 times.

Observed pain points:
1. No batch grand total: the user asked for a single "starting size, ending
   size, total delta" at the end.
2. Extreme repetition: backup + rollback instructions + size block repeated per
   session.
3. Repeated VACUUM: VACUUM ran once per session (slow on a multi-GB DB) instead
   of once for the whole batch.
4. `session delete <project>` leaves the now-empty `project` row behind, so
   running `ocman` from that directory no longer finds a project context (it
   falls back to `--list-projects`). Verified: after the run the uri-ai-info
   project row still exists with 0 sessions.

Not a bug: the sessions WERE deleted (verified 0 remaining under uri-ai-info);
the subsequent `list sessions` showed OTHER projects' sessions, which is correct.

---

## User Review Required

> [!IMPORTANT]
> - The single-session `session delete ID` and `project delete NAME` output
>   should stay essentially as today (one clean report). The change targets the
>   MULTI-target path (a spec list, or a project expansion) so it produces ONE
>   consolidated report instead of N.
> - One rollback backup and ONE VACUUM for the whole batch, not per session.
> - Add a batch grand total: starting DB size, ending DB size, total delta, plus
>   totals of sessions and rows deleted.
> - `session delete <project-expansion>` and `project delete` should, after
>   deleting the sessions, handle the now-empty project row (see the open
>   decision below).

---

## Design

### A. Separate "delete work" from "delete reporting/finalize"

`db_delete_session_recursive` currently does everything inline: delete rows,
create a backup, VACUUM, print the size/backup/rollback report
(`ocman/cli.py:7099`, report at `7284-7307`). Refactor so a batch can share one
backup, one VACUUM, and one report:

- Add a low-level `_delete_session_rows(session_id, *, conn, dry_run)` (or a
  `batch` flag) that deletes only the DB rows + on-disk diff files for one
  session inside an ALREADY-OPEN transaction, RETURNING a stats dict
  (rows-by-table, files removed, bytes) and printing at most a concise one-line
  progress note. It does NOT create a backup, VACUUM, or print the big report.
- Keep `db_delete_session_recursive(...)` as the single-session public entry:
  one backup, delete, one VACUUM, the existing full report (unchanged behavior,
  verified by existing tests).
- Add `db_delete_sessions_batch(session_ids, *, dry_run, force, verbosity)` that:
  1. resolves the full set and prints ONE preview (already done by the caller
     via `confirm_destructive`, `ocman/cli.py:11286-11293`);
  2. creates ONE rollback family backup;
  3. opens ONE transaction, calls `_delete_session_rows` per session,
     aggregating stats;
  4. commits, runs ONE VACUUM;
  5. prints ONE consolidated report (see B) with ONE rollback stanza.

### B. Consolidated batch report (the requested grand total)

After the batch, print once:
- `Sessions deleted:   N` (and subagents count if tracked)
- `Rows deleted:       <sum by table, or a single total>`
- `Files removed:      K (<bytes>)`
- `Database size before: <X>`
- `Database size after:  <Y> (after VACUUM)`
- `Total reclaimed:      <X - Y>` (DB delta) and `Total space reclaimed`
  (DB + files), matching the single-session vocabulary
- ONE `[!] safe backup ... / Rollback instructions:` stanza for the batch.

Measure size-before once (before the transaction) and size-after once (after the
single VACUUM), so the "total delta" is a true whole-batch number, not a sum of
per-session deltas.

### C. Per-batch VACUUM

VACUUM once after the whole batch commits, not per session. VACUUM is expensive
on a multi-GB DB; N VACUUMs was the main slowness. `db_run_cleanup` already
VACUUMs once for age-based cleanup; mirror that.

### D. Empty-project row after deleting a project's sessions

When the target was a PROJECT expansion (or `project delete`), after removing all
its sessions the `project` row is empty. Options (pick in review):
- (Recommended) If the delete originated from a project spec, also delete the
  now-empty `project` row (and `project_directory`/`workspace` rows) in the same
  transaction, so `ocman` in that directory behaves as if the project is gone.
  `project delete` arguably should already do this; confirm and align.
- Alternative: leave the row but tell the user it is now empty and how to remove
  it. Less surprising, but leaves a stale project.

Note: plain `session delete ID ID2` targeting sessions that happen to empty a
project is a grayer case; only auto-remove the project row when the user targeted
the PROJECT (expansion or `project delete`), not when they named individual
sessions. This must be explicit in the code and tested.

### E. Keep the destructive-confirm contract

The single batch preview + single typed confirm (with `-y`/`--yes` and
`--dry-run`) is already correct (`ocman/cli.py:11286-11293`, and the loop passes
`confirm=False`). Preserve it; the batch function must honor `dry_run` (report
what WOULD be deleted, size delta = 0, no VACUUM, no backup) and `-y`.

---

## Tests

- Batch delete of N sessions: exactly ONE backup created, ONE VACUUM run
  (assert via a counter/mock), ONE consolidated report with a grand total; the
  per-session big report/rollback stanza does NOT repeat N times.
- Grand total: size-before/after/delta reflect a single whole-batch measurement;
  rows/sessions/files totals equal the sum across the batch.
- `--dry-run` batch: nothing deleted, no VACUUM, no backup, report shows the
  would-delete set.
- Single-session `session delete ID` and `project delete NAME` reports are
  unchanged (characterization: pin current output shape before refactor).
- Project expansion delete removes the now-empty project row (per decision D);
  a plain multi-session delete that empties a project does NOT auto-remove it.
- Rollback: a mid-batch failure rolls back the whole transaction and restores the
  single backup (no partial deletion), matching the existing safety guarantee.

---

## Docs

- README + help: note that multi-target delete produces one consolidated report
  and one VACUUM; document the empty-project cleanup behavior chosen in D.
- ARCHITECTURE: record the `_delete_session_rows` / `db_delete_sessions_batch`
  seam and the single-backup/single-VACUUM batch model.

---

## Non-goals

- Changing single-session/single-project delete output beyond keeping it intact.
- Parallelizing deletes (sequential in one transaction is correct and safe).
- Undo beyond the existing single rollback backup.
