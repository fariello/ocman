# Implementation Plan - Batch delete reporting, per-batch VACUUM, empty-project cleanup

Status: PROPOSED (not yet executed)

Improves the UX of multi-session (and project-expanded) `ocman session delete`
and `ocman project delete`, based on a real run that deleted a whole project's
7 root sessions. The delete itself worked correctly; the reporting and
per-session repetition were the problem.

Evidence lines are `ocman/cli.py:<line>` re-verified during plan-review on
2026-07-11 against the current package layout (`ocman/cli.py`). Line numbers
drift; re-verify before editing.

---

## Motivation (from a real run)

`ocman session delete /home/gfariello/VC/uri-ai-info` expands to the project's
sessions and loops `db_delete_session_recursive` once per session (the batch loop
is at `ocman/cli.py:11304-11312`; the caller first prints ONE
`DestructivePreview` + single typed confirm at `11284-11301`).

`db_delete_session_recursive` (`ocman/cli.py:7095`) does the ENTIRE per-session
pipeline inline: it prints its OWN preview ("Recursively deleting the following
sessions" + "Rows that will be deleted", `7155-7190`), takes a database family
backup (`7212-7224`), opens a transaction and deletes (`7232-7253`), runs VACUUM
(`7267-7269`), records history via `save_deletion_metrics` (`7278`), and prints
the "Deletion complete!" size block + "Rollback instructions" stanza
(`7280-7303`). For a 7-session delete this repeats the per-session preview,
backup, VACUUM, metrics write, and rollback stanza SEVEN times.

Observed pain points:
1. No batch grand total: the user asked for a single "starting size, ending
   size, total delta" at the end.
2. Extreme repetition: per-session preview + backup + delete report + rollback
   instructions repeated once per session (the caller's single preview at
   `11284` does NOT suppress the per-session preview inside the function).
3. Repeated VACUUM: VACUUM ran once per session (slow on a multi-GB DB) instead
   of once for the whole batch.
4. Repeated history entries: `save_deletion_metrics("delete", ...)` (`7278`) is
   called once per session, so one batch produces N ledger entries instead of one.
5. `session delete <project>` leaves the now-empty `project` row behind, so
   running `ocman` from that directory no longer finds a project context (it
   falls back to the no-project screen). Verified: after the run the uri-ai-info
   project row still exists with 0 sessions.

Note on the backup dir: `backup_dir` uses `get_startup_timestamp_local()`
(process-start time, `7212`), so all N per-session backups already write into the
SAME timestamped directory (each overwrites the prior). Moving to one explicit
pre-batch backup is therefore also a correctness clarity win, not just cosmetic.

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

`db_delete_session_recursive` (`ocman/cli.py:7095`) currently does everything
inline for one session: preview (`7155-7190`), backup (`7212-7224`), transaction
+ delete (`7232-7253`), VACUUM (`7267-7269`), `save_deletion_metrics` (`7278`),
and the full size/backup/rollback report (`7280-7303`). Refactor so a batch can
share one preview-tail, one backup, one transaction, one VACUUM, one metrics
write, and one report:

- Add a low-level `_delete_session_rows(session_ids, *, conn)` that DELETEs the
  DB rows for the given session ids inside an ALREADY-OPEN transaction (reuse the
  chunked `SESSION_RELATIONAL_TABLES` delete at `7241-7245`) and returns
  per-table deleted counts. It does NOT print a preview, take a backup, VACUUM,
  write metrics, or print the report.
- Keep `db_delete_session_recursive(...)` as the single-session public entry with
  UNCHANGED external behavior (its own preview, backup, VACUUM, report). Existing
  tests pin this; do not alter its output (characterization first, rubric D).
- Add `db_delete_sessions_batch(session_ids, *, dry_run, force, verbosity)` that:
  1. does NOT re-print a per-session preview. The caller already printed ONE
     `DestructivePreview` + confirm (`ocman/cli.py:11284-11301`). The batch
     function must NOT call the per-session `db_delete_session_recursive`
     (which prints its own preview `7155-7190` and its own report); it drives
     `_delete_session_rows` directly.
  2. resolves the on-disk diff files for ALL session ids (reuse the traversal-safe
     resolution at `7168-7184`);
  3. runs the process-lock check ONCE (`check_opencode_process_lock`, `7109`);
  4. creates ONE rollback family backup (reuse `7212-7224`; the backup dir is
     already process-start-stamped so it is naturally one directory);
  5. opens ONE transaction, calls `_delete_session_rows` for the whole set (or
     chunked), aggregating deleted counts; commits;
  6. deletes the diff files; runs ONE VACUUM;
  7. aggregates metrics across the whole batch and calls `save_deletion_metrics`
     EXACTLY ONCE (not per session), so the history ledger gets one entry per
     batch (fixes pain point 4);
  8. prints ONE consolidated report (see B) with ONE rollback stanza.
- The `main()` `--delete` handler (`ocman/cli.py:11256-11315`) calls
  `db_delete_sessions_batch(...)` for the resolved set instead of looping
  `db_delete_session_recursive` per session (`11304-11312`). When exactly one
  session is targeted, either path is acceptable, but routing single-session
  deletes through the existing `db_delete_session_recursive` keeps its
  characterized output identical.

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
its sessions the `project` row is empty, so `ocman` run from that directory no
longer finds project context.

**Decision (resolved in plan-review):** delete the now-empty `project` row (and
its `project_directory` / `workspace` rows) in the SAME transaction, but ONLY
when the delete was targeted at the PROJECT (a project expansion, or
`project delete NAME`). This makes `ocman` behave as if the project is gone,
matching user expectation. Do this inside the one batch transaction so it is
atomic with the session deletes and covered by the single rollback backup.

Guard rails:
- A plain `session delete ID1 ID2` that names individual sessions which HAPPEN to
  empty a project MUST NOT auto-remove the project row (the user did not ask to
  delete the project). The batch API therefore needs an explicit
  `remove_empty_project: bool` (or the caller passes the resolved project id to
  delete) rather than inferring intent from "0 sessions remain".
- Determine emptiness by re-checking `SELECT COUNT(*) FROM session WHERE
  project_id = ?` inside the transaction after the session deletes (do not assume
  the batch covered every session; a concurrent session could exist). Only remove
  the project row if the count is 0.
- `project_directory`/`workspace` have `ON DELETE CASCADE` FKs to `project`, but
  the delete runs under `PRAGMA foreign_keys = OFF` (`7233`), so cascades will
  NOT fire; the batch MUST delete those project-scoped rows explicitly (reuse
  `PROJECT_RELATIONAL_TABLES` from the export work). Route each to a test.
- `project delete NAME` already calls `db_delete_project_recursive`
  (`ocman/cli.py:11246`, def at `7323`), a SEPARATE, complete function that
  deletes the project's sessions AND the `project`/`project_directory`/`workspace`
  rows via `PROJECT_RELATIONAL_TABLES` (`380-384`) with its own backup, VACUUM,
  and report. So the project-delete-with-row-removal behavior ALREADY EXISTS
  there; do not duplicate it.

  **Architecture guard (avoid a third delete path):** prefer routing a
  PROJECT-scoped `session delete <project>` expansion through the existing
  `db_delete_project_recursive` (which already does one backup / one VACUUM / one
  report for the whole project and removes the empty project row), rather than
  teaching the new `db_delete_sessions_batch` to also remove project rows. That
  keeps the empty-project-cleanup logic in exactly one place. Reserve
  `db_delete_sessions_batch` for TRUE multi-session sets that are NOT a whole
  project (an explicit list of ids, or a partial selection). Confirm how
  `resolve_and_expand_targets` distinguishes "user named a project" from "user
  named N sessions" so the `main()` handler (`11256-11315`) can dispatch:
  whole-project -> `db_delete_project_recursive`; otherwise ->
  `db_delete_sessions_batch` (no project-row removal). If that distinction is not
  cleanly available at the call site, surface it as an Open Question rather than
  guessing.

### E. Keep the destructive-confirm contract

The single batch preview + single typed confirm (with `-y`/`--yes` and
`--dry-run`) is already correct (`ocman/cli.py:11284-11301`, and the loop passes
`confirm=False`). Preserve it; the batch function must honor `dry_run` (report
what WOULD be deleted, size delta = 0, no VACUUM, no backup, no metrics write)
and `-y`. Because the batch drives `_delete_session_rows` directly (not the
per-session public function), the per-session preview/report at `7155-7190` /
`7280-7303` is naturally not emitted N times.

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

---

## Open Questions (raised in plan-review 2026-07-11)

- **Dispatch signal for "whole project" vs "N sessions".** Item D's
  architecture guard assumes the `main()` `--delete` handler can tell whether the
  user targeted a whole project (route to `db_delete_project_recursive`) or an
  explicit session set (route to `db_delete_sessions_batch`). `resolve_and_expand_targets`
  is called with `kinds={"session","project"}` and `allow_project_expansion=True`
  (`ocman/cli.py:11266-11273`); the executor must confirm the result exposes which
  input specs were projects (and whether the expansion covered ALL of a project's
  sessions) before wiring dispatch. If that signal is not cleanly available,
  Remediation Risk is Medium on functionality (mis-dispatch could remove a project
  row the user did not intend, or fail to), so resolve it in code review with a
  test rather than guessing here. This is a design confirmation, not a deferral of
  the fix.
