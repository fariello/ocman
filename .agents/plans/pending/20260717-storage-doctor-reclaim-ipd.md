# IPD: `ocman doctor` + `ocman reclaim` (OpenCode storage diagnosis and cleanup)

- Date: 2026-07-17
- Concern: usability / disk reclamation (OpenCode leaves large data behind)
- Scope: add a read-only `ocman doctor` that runs a FULL environment checkup (known
  OpenCode storage problems AND ocman's own housekeeping: orphaned tables/rows, orphaned
  session-diff files, DB integrity, backup inventory + stale-backup suggestions, temp
  leftovers), each with measured sizes/counts and a concrete recommended `ocman` fix
  command (and upstream issue link where relevant); and a guarded `ocman reclaim` that
  CLEANS the safe categories (with previews + confirmation), reusing ocman's existing
  sizing, orphan-detection, delete/VACUUM, backup, and running-guard machinery.
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-17 draft (its_direct/pt3-claude-opus-4.8): created at maintainer request
  after a user report (Reddit: ~100GB consumed) citing seven upstream OpenCode issues.
  Fetched and verified all seven issues; surveyed ocman's existing disk/DB/backup
  machinery (see Evidence). Maintainer decisions: (1) two commands, `doctor`
  (diagnose) + `reclaim` (fix); (2) event-table compaction OFF by default, explicit
  opt-in flag; (3) temp-file cleanup covers BOTH globs, PID-aware; (4) path discovery
  derives from db_path + honors XDG/TMPDIR + reports other large opencode dirs, and
  INTERACTIVELY offers to search / ask where; (5) snapshots are report-only by default
  but deletable behind a scary `--force-snapshots` flag; (6) `doctor` uses a read-only
  DB connection.
- 2026-07-17 scope expansion (maintainer): `doctor` is a FULL environment checkup, not
  just an OpenCode-bug scanner. It also checks ocman's own housekeeping: orphaned
  relational rows (reusing the `SESSION_RELATIONAL_TABLES` NOT-EXISTS predicate),
  orphaned session-diff files, sessions with dangling `project_id`, DB integrity, a
  backup inventory with a stale-backup deletion suggestion, and an old-session cleanup
  opportunity. Each check recommends the concrete `ocman` fix command, making `doctor`
  the guided front door to `db clean` / `db clean-orphans` / `backup clean` / `reclaim`.
  Restructured D-2 as a testable list of read-only CHECKS.

## Goal

Make ocman the tool that finds and safely reclaims the disk OpenCode leaves behind.

- `ocman doctor`: READ-ONLY FULL CHECKUP. Runs a suite of health checks over the
  OpenCode environment AND ocman's own footprint, printing for each: a status
  (OK / NOTICE / WARN), a measured size/count, a one-line explanation, the recommended
  `ocman` command to fix it, and an upstream issue link where the cause is an OpenCode
  bug. Ends with a summary (counts of OK/NOTICE/WARN, total reclaimable bytes). Never
  mutates anything (read-only DB connection), so it is safe even while OpenCode runs.
  The checks include, at minimum:
    - DB size + WAL/SHM family size (and runaway-WAL WARN); `event`-table bloat
      (message.updated snapshots); compacted-part output bytes.
    - Orphaned ROWS: for each session-scoped relational table, rows with no matching
      session; sessions whose `project_id` has no project row; orphaned session-diff
      FILES on disk with no session. (These map to `ocman db clean-orphans`.)
    - DB integrity (`PRAGMA quick_check`/`integrity_check`), reported as a check.
    - Backup inventory: count, total size, oldest/newest of ocman's OWN backups, with a
      stale-backup suggestion (e.g. "12 backups older than 30d reclaim 4.2 GB: run
      `ocman backup clean --older-than 30d`"); plus any large opencode-owned backup dir
      found by discovery, report-only.
    - Temp leftovers: `$TMPDIR/opencode-wal-*.db`, `/tmp/.*.so`.
    - Snapshots: size, report-only.
    - Age-based session cleanup opportunity: sessions older than the retention window
      (maps to `ocman db clean --older-than ...`), report-only count/size estimate.
  Each check names the ocman command that fixes it, so `doctor` is the guided front
  door to the existing `db clean` / `db clean-orphans` / `backup clean` / `reclaim`.
- `ocman reclaim`: performs the guarded cleanup of the SAFE categories (temp files, WAL
  checkpoint, stale backups), with `DestructivePreview` + typed confirmation, behind the
  running-OpenCode guard. The high-value-but-internal DB event-table compaction is
  opt-in (`--compact-events`). Git snapshots are report-only unless `--force-snapshots`.

## Background: the seven issues, mapped to what ocman can do (Evidence)

Verified from the upstream issues (fetched 2026-07-17) and ocman source
(`ocman/cli.py`). Categories by safety:

SAFE to clean externally:
- #36831 orphaned `$TMPDIR/opencode-wal-*.db` (~1.4GB each, one per session, never
  removed; reporter hit 268GB/200 files). Clean: keep the newest/active, delete older.
- #28089 leaked `/tmp/.*.so` JIT shared objects (~4.5MB each; reporter hit 728GB). Clean
  by age, but MUST skip any file still mmap'd by a live OpenCode process.
- #37495 runaway `opencode.db-wal` while running + stale `opencode.db.bak.*`. Clean:
  offline `PRAGMA wal_checkpoint(TRUNCATE)` (only when OpenCode is stopped) + delete
  stale `.bak.*`.
- #31526 `auto_vacuum=0`, freed pages never reclaimed. Clean: `VACUUM` when idle (ocman
  already VACUUMs after deletes; expose a standalone reclaim).
- The Reddit 88GB `~/backups/opencode/`: report (it is opencode's own backup dir, not
  ocman's) and, per D-3, offer to clean when the user points ocman at it.

PARTIAL (opt-in, mutates OpenCode's DB rows):
- #33356 `event` table dominated by full-snapshot `message.updated.1` (87% of a 13.7GB
  DB). VACUUM does NOT help (live data, freelist ~0). Fix = keep only the latest
  `message.updated` event per message and delete superseded ones. Opt-in
  `--compact-events`.
- #16101 compacted `part` output never cleared (`ToolStateCompleted` parts keep large
  `output`/`attachments` after `time.compacted` is set). Opt-in null-out of those
  fields for already-compacted parts, past a retention window.

REPORT-ONLY (unsafe to auto-clean):
- #36093 git snapshot objects referenced by live DB session hashes; blind prune breaks
  revert/undo. Report size + loud warning; delete only behind `--force-snapshots`
  (multi-confirm).

### ocman machinery to REUSE (do not duplicate)
- Sizing: `dir_usage` (`cli.py:10824`), `human_size_local` (`cli.py:10866`),
  `get_file_size_local` (`cli.py:10860`), `_per_project_disk_usage` (`cli.py:11519`),
  `fmt_int`/`fmt_cost` (`cli.py:4591/4604`).
- DB size/WAL/SHM family reporting: the `db_show_info` logic at `cli.py:11637-11652`.
- Delete + VACUUM engine + pre-op `opencode-db-cleanup-*` backup + integrity-check +
  `confirm_destructive` + rollback: `db_run_cleanup` (`cli.py:10451`),
  `db_delete_*` (`cli.py:7920/8226/8425`), `DestructivePreview`/`confirm_destructive`.
- Backup pruning: `cli_clean_backups` (`cli.py:12328`) - name-prefix matched.
- Running guard: `require_safe_to_mutate` (`cli.py:7662`); PID/`/proc` detection from
  `detect_running_opencode` / the `list running` enumerator (own-UID, `/proc/<pid>`),
  reused for the mmap/PID-aware temp reap.
- sqlite loader: `_get_sqlite` (`cli.py:4043`).

### Gaps this IPD must fill (confirmed absent today)
- No `PRAGMA wal_checkpoint` anywhere.
- No read-only DB connection mode anywhere (all `sqlite3.connect(path)` RW).
- No temp-file reclamation.
- Hardcoded `~/.local/share/opencode`; `$XDG_DATA_HOME` not honored;
  `OPENCODE_STORAGE_DIR` hardcoded to `Path.home()` not derived from `db_path`
  (`cli.py:392`).

## Design

### D-1 Storage-location discovery
Add a `discover_storage_locations()` helper returning a structured set of paths:
- Data dir = parent of the configured `db_path` (so `--db` and config are honored);
  additionally honor `$XDG_DATA_HOME` when `db_path` is at its default.
- DB family: `db_path`, `<db>-wal`, `<db>-shm`, `<db>.bak.*`.
- ocman backup dir (`default_backup_dir`).
- Temp globs: `$TMPDIR/opencode-wal-*.db` and `/tmp/.*.so` (respect `tempfile.gettempdir()`).
- Snapshot dirs (per-project/worktree gitdirs) for report-only sizing.
- Interactive extra-scan (D-1a): on a TTY, `doctor` OFFERS to also search common
  locations (e.g. `~/backups/opencode`, `$HOME` shallow scan for large `opencode*`
  dirs) and to ASK the user for an additional path to measure. Non-interactive: skip the
  offer, scan only the derived/known set. No deletion happens outside the SAFE set
  regardless of what discovery finds (discovery widens REPORTING, not auto-clean).

### D-2 `ocman doctor` (read-only full checkup)

- Add `db_connect_readonly(path)` using SQLite URI `file:<path>?mode=ro&immutable=1`
  (via `_get_sqlite`), so diagnosis provably cannot write and is safe even while
  OpenCode runs. If the DB is missing/locked, degrade to file-size-only reporting for
  the DB checks (still run the filesystem checks).

- Structure as a list of CHECKS. Each check is a small function returning a result
  record: `{key, title, status (ok|notice|warn), size_bytes, count, detail, fix_cmd,
  issue_url|None}`. `cli_doctor` runs them all, renders the table, prints the summary.
  This makes each check independently testable and easy to extend.

- The check set (reusing existing detection; NO duplicated logic where a helper exists):
  1. `db_size` - DB + WAL + SHM family (reuse `db_show_info` logic `cli.py:11637-11652`);
     WARN if WAL is large relative to the DB (runaway-WAL, #37495).
  2. `db_integrity` - read-only `PRAGMA quick_check` (WARN on any result != "ok").
  3. `event_bloat` - `SUM(length(data))` on `event` grouped by `type`; surface
     `message.updated.*` total + estimated superseded waste (kept-latest-per-message).
     NOTICE with the `--compact-events` recommendation + issue #33356.
  4. `compacted_parts` - bytes in `output`/`attachments` of `ToolStateCompleted` `part`
     rows whose message is `time.compacted`; NOTICE + `reclaim --reclaim-parts` + #16101.
  5. `orphan_rows` - for each `(table, col)` in `SESSION_RELATIONAL_TABLES`
     (`cli.py:399`, excluding `session`), read-only `COUNT(*) ... WHERE NOT EXISTS
     (SELECT 1 FROM session s WHERE s.id = {table}.{col})` (the exact predicate
     `db_run_cleanup` deletes with, `cli.py:10744-10749`); also count sessions whose
     `project_id` has no `project` row. WARN if any > 0; fix = `ocman db clean-orphans`.
  6. `orphan_diff_files` - session-diff `*.json` under the storage dir with no matching
     session row (reuse the orphan-diff logic from `db_run_cleanup` `cli.py:10650-10667`);
     fix = `ocman db clean-orphans`.
  7. `old_sessions` - COUNT + rough size of root sessions older than the retention
     window (`default_retention_days`); NOTICE; fix = `ocman db clean --older-than ...`.
  8. `ocman_backups` - inventory of ocman's OWN backups (reuse `dir_usage` + the
     `db_show_info` backups block `cli.py:11862-11894`): count, total size,
     oldest/newest; if backups older than a threshold exist, NOTICE with the reclaimable
     size + `ocman backup clean --older-than Nd`.
  9. `foreign_backups` - any large opencode-owned backup dir discovered in D-1 (e.g.
     `~/backups/opencode`): report-only WARN with size; no ocman fix command (advise
     manual review), since ocman does not own it.
  10. `temp_wal` - `$TMPDIR/opencode-wal-*.db` count/size; NOTICE + `ocman reclaim` + #36831.
  11. `temp_so` - `/tmp/.*.so` count/size (age-filtered); NOTICE + `ocman reclaim` + #28089.
  12. `snapshots` - snapshot dir size; report-only NOTICE + #36093 (never a safe fix).

- Output: a vistab table (reuse the session-header styling: `round-header`, `padding=0`,
  bold header, color-gated). Columns: `Check`, `Status`, `Size/Count`, `Recommended fix`.
  A `Status` of WARN is shown in bold red, NOTICE in yellow, OK plain (honoring
  NO_COLOR). Beneath the table: a details block per non-OK check (the one-line
  explanation + issue URL). Footer summary: `N OK / M notices / K warnings`, and totals
  for reclaimable-now vs. opt-in vs. report-only bytes.
- `--json` via `emit_json("doctor", {...})` emitting the list of check records
  (stable, additive schema).
- `doctor` NEVER mutates and is NOT behind the running guard (read-only, safe anytime).
- Verbosity: `-v` adds per-project event/part breakdowns and lists the specific
  orphaned tables/files; the default view stays a concise one-row-per-check summary.

### D-3 `ocman reclaim` (guarded cleanup)
Default run cleans ONLY the SAFE categories, each with its own preview + confirm:
- Temp WAL DBs: delete `$TMPDIR/opencode-wal-*.db` except the most-recently-modified
  (assumed active); PID-aware skip if a live OpenCode holds it open.
- Leaked `.so`: delete `/tmp/.*.so` older than an age threshold, SKIPPING any file
  currently mmap'd by a live OpenCode PID (read `/proc/<pid>/maps` for owned PIDs; on
  non-Linux, fall back to age-only + require `--force`). Default age threshold
  configurable (`reclaim_tmp_min_age_hours`, default 24).
- WAL checkpoint + `VACUUM`: only when OpenCode is NOT running (via
  `require_safe_to_mutate`); run `PRAGMA wal_checkpoint(TRUNCATE)` then `VACUUM` on a
  writable connection, after the standard `opencode-db-cleanup-*` backup.
- Stale backups: reuse `cli_clean_backups` for ocman's own; for opencode's own backup
  dir found in D-1, only prune when the user explicitly points reclaim at it
  (`--backups-dir PATH`) with a preview.

Opt-in categories (each its own flag, each guarded + backed up + typed-confirm):
- `--compact-events`: keep only the latest `message.updated` event per message
  (`aggregate_id`, message id/seq per the issue), delete superseded rows, then VACUUM.
  Loud explanation that this trims OpenCode's replay log.
- `--reclaim-parts`: null `output`/`attachments` on `ToolStateCompleted` `part` rows
  whose message has `time.compacted` set and is older than a retention window.

Report-only unless forced:
- Snapshots: never touched by default. `--force-snapshots` enables deletion behind a
  multi-line RED warning + a typed confirmation distinct from the normal one (it can
  break revert/undo because ocman cannot compute DB reachability); it prunes only the
  snapshot dir the user names, never guesses.

All destructive paths: `require_safe_to_mutate` first, `DestructivePreview` +
`confirm_destructive` (honor `-y`/`--yes` for the ordinary confirm only, NOT for
`--force-snapshots`), pre-op backup where a DB write is involved, and honor `--dry-run`.

### D-4 Safety invariants
- `doctor` cannot write (read-only connection; asserted by a test that a
  running-OpenCode scenario still lets `doctor` run and produces no mutation).
- No temp file that is open/mmap'd by a live OpenCode process is ever deleted.
- No DB write (checkpoint/VACUUM/compact/reclaim-parts) happens while OpenCode runs
  unless `--while-running` is explicitly given (reuse the existing guard semantics).
- Snapshots are never deleted without `--force-snapshots` + its own typed confirm.
- `--dry-run` on `reclaim` performs zero deletions/writes and prints exactly what would
  be removed with sizes.

### D-5 CLI surface
- `ocman doctor [-v] [--json]` (read-only; no guard). `-v` expands per-project /
  per-table detail; `--json` emits the check records.
- `ocman reclaim [--dry-run] [-y/--yes] [--while-running] [--compact-events]
  [--reclaim-parts] [--force-snapshots] [--backups-dir PATH]
  [--tmp-min-age-hours N]`.
- Config keys (via DEFAULT_CONFIG + CONFIG_TEMPLATE, following `filter_max_bytes`):
  `reclaim_tmp_min_age_hours` (default 24), `reclaim_parts_retention_days` (default 30).
- Normalizer + defaults entries for the new flags; handlers dispatch to
  `cli_doctor(args)` / `cli_reclaim(args)`.

## Test plan

Unit / offline (seed a temp DB + fake temp files under a tmp HOME, the established
`Path.home()` monkeypatch pattern):
- discovery: derives data dir from `db_path`; honors `$XDG_DATA_HOME`/`$TMPDIR`;
  collects the DB family + temp globs; non-interactive skips the extra-scan offer.
- `db_connect_readonly`: a write attempt raises (proves read-only); missing DB degrades
  to size-only without crashing.
- doctor: on a seeded DB with a bloated `event` table (fake `message.updated` rows) the
  report shows the event-table check, its size, the correct issue number/URL, and the
  reclaimable/opt-in/report-only split; `--json` envelope shape is stable.
- doctor orphan checks: seed orphaned relational rows (a `part`/`message` with a
  session_id absent from `session`), a session with a dangling `project_id`, and an
  orphaned session-diff `*.json`; assert `doctor` flags each with a WARN and recommends
  `ocman db clean-orphans` (and that it did NOT delete them - read-only).
- doctor backup check: seed a few `opencode-backup-*.zip`/`opencode-db-cleanup-*` under
  the sandbox backup dir with old mtimes; assert the backups check reports count/size,
  oldest/newest, and suggests `ocman backup clean --older-than`.
- doctor integrity + db_size checks render without a DB present (degrade gracefully to
  filesystem-only) and with a healthy seeded DB (status OK).
- doctor-while-running: with detection forced to "some", `doctor` still runs and writes
  nothing (guard-neutralizer opt-out marker as in the mutation-guard tests).
- each check is unit-testable in isolation (call the check fn against a seeded
  read-only DB / temp tree and assert its result record).
- reclaim temp WAL: keeps the newest `opencode-wal-*.db`, deletes older; `--dry-run`
  deletes nothing.
- reclaim `.so` PID-aware: a `.so` "mapped" by a fake live PID is skipped; an old
  unmapped one is deleted; `--dry-run` no-ops.
- reclaim checkpoint/VACUUM: refuses while running (guard), proceeds with
  `--while-running`; asserts a backup dir was created and VACUUM ran once.
- `--compact-events`: seeded superseded `message.updated` rows -> only the latest per
  message remains; a pre-op backup exists; VACUUM ran; OFF without the flag (default
  reclaim leaves `event` untouched).
- `--reclaim-parts`: only compacted parts past the retention window get `output`/
  `attachments` nulled; non-compacted parts untouched.
- snapshots: default run never deletes snapshot dirs; `--force-snapshots` requires the
  distinct typed confirm; `-y` does NOT bypass it.

Run: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and paste real output.

## Docs
- README: new `doctor` / `reclaim` command reference rows + a "Health checkup and
  reclaiming disk" section. Describe `doctor` as a full read-only checkup (DB size/WAL,
  integrity, event/part bloat, orphaned rows/files, backup inventory + stale-backup
  suggestion, old-session cleanup opportunity, temp leftovers, snapshots), each with the
  recommended `ocman` fix command; then `reclaim` for the safe/opt-in cleanup, with the
  safe/opt-in/report-only split and the issue links.
- ARCHITECTURE: a subsection on the read-only diagnosis connection, discovery, the
  reuse of `db_run_cleanup`/backup/guard machinery, and the PID-aware temp reap.
- CHANGELOG: Added entry.
- CONFIG_TEMPLATE: doc-comments for the two new keys.

## Risks and non-goals
- Risk: deleting a temp file OpenCode still needs. Mitigated by keep-newest + PID/mmap
  skip + age threshold + `--dry-run`.
- Risk: `--compact-events` alters OpenCode's replay log. Mitigated by OFF-by-default +
  backup + typed confirm + loud explanation; VACUUM reclaims the freed pages.
- Risk: snapshot deletion breaks revert/undo. Mitigated by report-only default +
  `--force-snapshots` scary confirm; ocman never guesses which snapshot dir.
- Risk: non-Linux lacks `/proc` mmap introspection. Mitigated: `.so` reap falls back to
  age-only and requires `--force` there; documented.
- Non-goal: fixing OpenCode itself (these are upstream bugs; ocman mitigates the
  symptoms). Each report row links the upstream issue so users can track the real fix.
- Non-goal: computing git-snapshot reachability (only OpenCode can do that safely).
- Non-goal: changing the TUI.

## Open questions
- O-1 (decide at execution, non-blocking): exact `doctor` category ordering and whether
  to show per-project event/part breakdowns or just totals (leaning: totals in the main
  table, per-project only under `-v`).
- O-2 (decide at execution, non-blocking): whether `reclaim` with no flags on a clean
  system prints "nothing to reclaim" vs. a short green all-clear.

## Execution contract (gate)
An executing agent MUST:
- Treat D-1..D-5 decisions as resolved; O-1/O-2 are execution-time niceties recorded in
  the Workflow history. Invent no other scope. TUI untouched. `doctor` stays read-only.
- Independently RE-VERIFY the upstream issue claims and the reused `cli.py` line
  references before relying on them; the issue reports are external input.
- NEVER delete a temp file mmap'd/held by a live OpenCode process; NEVER write to the DB
  while OpenCode runs without `--while-running`; NEVER delete snapshots without
  `--force-snapshots` + its distinct confirm.
- Honesty rule (hard MUST): paste the ACTUAL
  `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` output; never claim a pass not
  run.
- Commit path-scoped (`git commit -m msg -- <paths>`), NEVER `-A`/`-a`, NEVER push,
  NEVER tag.
- On completion set `Status: EXECUTED`, add a Workflow-history execution line, and
  `git mv` this IPD pending -> executed (verify no dup via `git ls-tree HEAD`).
