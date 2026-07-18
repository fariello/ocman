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
- Status: EXECUTED
- Approval: approved by maintainer 2026-07-17
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

- 2026-07-17 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED. Verified against cli.py + a live pysqlite3 read-only-connection probe. PR-001 (HIGH, FIXED): db_connect_readonly must be `mode=ro` NOT `immutable=1` (immutable yields stale/garbage reads while OpenCode writes; verified mode=ro blocks writes AND sees concurrent commits). PR-002 (HIGH, FIXED): OpenCode's real event/part/message schema is not in fixtures and only partly known from issues; every DB check must schema-probe and return unknown/skipped, never crash or false-OK. PR-003 (MEDIUM, FIXED): --compact-events/--reclaim-parts must use the VERIFIED grouping key/columns from opencode.repo-agent + source and FAIL CLOSED on unrecognized shape (a wrong key would DELETE the wrong event rows). PR-004 (MEDIUM, FIXED): old-session check must not report non-attributable per-session DB bytes (single shared file, cli.py:11902); report count + diff-file bytes only. PR-006 (MEDIUM, FIXED): --backups-dir/--force-snapshots delete in user-named dirs and must apply cli_clean_backups-grade path safety. Two asks queued to opencode.repo-agent (schema + layout) whose answers are a blocking dependency for the DB-mutating/path-deleting parts (gated), not for the review. Reused-mechanism refs verified (WAL/SHM family, backups block, orphan predicate + SESSION_RELATIONAL_TABLES, emit_json, own-UID /proc detection). Status -> reviewed.

- 2026-07-17 schema+layout verification (opencode.repo-agent, source-cited @ dev
  08fb47373 == v1.18.3; replies archived at
  `.agents/comms/shared/archive/20260717-2043-01/-02`): folded verified facts in and
  REVISED SCOPE (Status reset to to-review). Key corrections: (a) `event`-table GC
  (#33356) is UNSAFE (the event log is REPLAYED by V2 to rebuild state; deleting
  superseded rows risks corruption) -> `--compact-events` DELETE is REMOVED; replaced by
  a report-only `event_bloat` diagnosis. (b) `part.data.state.time.compacted` exists in
  schema but the agent found no code that SETS it or clears output -> `--reclaim-parts`
  is VERIFY-OR-SKIP: only act if the marker is empirically populated, else fail closed;
  use `json_set(data,'$.state.output','')` (never null the NOT NULL column). (c)
  `~/backups/opencode`, `$TMPDIR/opencode-wal-*.db`, `/tmp/*.so` are NOT OpenCode-owned
  (no source writes them; backups are a user job, temp files are Bun-runtime artifacts)
  -> report-only, delete temp only when stopped AND no live fd/mmap. (d) SAFE + confirmed:
  offline `wal_checkpoint(TRUNCATE)` + `VACUUM` (no auto_vacuum, no VACUUM in source,
  #31526). (e) Discovery: OpenCode honors `$XDG_DATA_HOME` + `OPENCODE_DB` +
  `OPENCODE_CONFIG_DIR` and uses `opencode-<channel>.db`; ocman must too. (f) Schema
  fingerprint = the `migration` table (no `user_version`). (g) "Running" = any live fd on
  the `.db`/`-wal`/`-shm` family (Desktop can add a second server process). Next: send
  the revised plan back to opencode.repo-agent to sanity-check, then /plan-review.

- 2026-07-17 revised-plan sanity-check (opencode.repo-agent, source-cited @ 08fb47373;
  reply archived `.agents/comms/shared/archive/20260717-2103-01`): VERDICT "looks right,
  conservative and safe." Upgraded `--reclaim-parts` from plausible to SAFE-by-construction:
  OpenCode sets `time.compacted` via the optional default-off `compaction.prune`
  (`session/compaction.ts:281`) and its request builder replaces a compacted part's output
  with a placeholder + drops attachments WITHOUT reading `state.output`/`attachments`
  (`session/message-v2.ts:293-296`) - so emptying `output` on disk changes nothing sent.
  Folded 5 non-blocking refinements: (1) event_bloat estimate labeled "would-be
  reclaimable upstream" (already); (2) `quick_check` non-ok while running = NOTICE/recheck,
  authoritative only when stopped; (3) resolve DB path vs data-dir subtrees INDEPENDENTLY
  (`OPENCODE_DB` may be absolute/outside data dir; `:memory:` -> no DB checks); (4) scope
  the `opencode*.db` glob to data-dir top level + exclude ocman backup prefixes; (5)
  `/tmp/*.so` origin still inferred - keep report-default + do an empirical `lsof` check
  before shipping the delete path. V2 `session_message` reclaim remains out of scope. All
  claims carry file:line for the executing agent to re-verify.

- 2026-07-17 /plan-review round 2 (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED (re-review of the re-scoped plan after the opencode.repo-agent verification rounds). Re-verified the ocman-side reuse refs against cli.py (db_show_info WAL/SHM 11640, SESSION_RELATIONAL_TABLES 399, orphan predicate 10748, backups block 11864, helpers dir_usage/human_size_local/emit_json/_get_sqlite/require_safe_to_mutate/_per_project_disk_usage all present). Findings: PR-007 (MEDIUM, FIXED) - the fd-on-DB-family "running" check does not exist yet (require_safe_to_mutate uses PROCESS enumeration); specified a new db_family_open_by_live_pid helper reusing the /proc own-UID scan, called alongside the guard. PR-008 (MEDIUM, FIXED) - tests need a schema-faithful event/part JSON fixture (real fixtures lack it); specified it. PR-009 (LOW, FIXED) - footer must split "ocman can reclaim now" vs opt-in vs report-only, never sum report-only into a headline reclaimable figure. PR-010 (LOW, FIXED) - RO helper must work on both sqlite backends + skip :memory:/missing. PR-011 (LOW, FIXED) - doctor reuses the global -v. opencode source citations (compaction.ts:281, message-v2.ts:293-296, global.ts, database.ts) are gated for the executing agent to re-verify (that repo is out of ocman's tree). Status -> reviewed.

- 2026-07-17 approved by maintainer; Status -> approved.
- 2026-07-17 EXECUTED (its_direct/pt3-claude-opus-4.8): implemented `ocman doctor` (read-only checkup) + `ocman reclaim` (guarded) in ocman/cli.py (~12520-end): discover_storage_locations, db_connect_readonly (mode=ro, both backends, skip :memory:/missing), db_family_open_by_live_pid (/proc own-UID fd scan), db_schema_fingerprint (migration table), 12 schema-defensive check_* functions + run_doctor_checks + cli_doctor (vistab round-header, 3-bucket footer, --json, global -v), _reclaim_guard_db_writes (dual guard), reclaim_checkpoint_vacuum, reclaim_parts (migration-gate + empirical time.compacted probe + json_set output-empty + retention + mandatory backup; event rows NEVER deleted), reclaim_temp (fd/mmap-aware, keep-newest), reclaim_backups_dir + reclaim_snapshots (path-safe), cli_reclaim; CLI subcommands + normalizer + config keys reclaim_tmp_min_age_hours(24)/reclaim_parts_retention_days(30). SAFETY INVARIANTS PERSONALLY VERIFIED in-code: no DELETE FROM event anywhere; doctor uses db_connect_readonly only; reclaim DB writes call both guards; reclaim_parts json_set (never null) + verify-or-skip; em-dash-clean. LIVE smoke test on this host: doctor reported real 6.27GB DB + 1.61GB /tmp/*.so (10 held-and-skipped) + 23 old sessions with the 3-bucket footer, schema fingerprint correctly UNKNOWN for the live DB's migration level (fail-safe); reclaim --dry-run correctly REFUSED (live fd holds the DB). Fixed the issue-URL host (sst -> anomalyco). Full suite: 366 passed, 2 skipped. Docs (README, ARCHITECTURE, CHANGELOG, CONFIG_TEMPLATE) updated. O-1/O-2 taken as: totals-in-main-table (per-project under -v); bare reclaim on a clean system prints the safe checkpoint+VACUUM outcome. attachments-clearing intentionally deferred. Status -> EXECUTED.

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
- `ocman reclaim`: performs the guarded cleanup of the SAFE categories, with
  `DestructivePreview` + typed confirmation, behind the running-OpenCode guard. The
  clearly-safe wins are offline `wal_checkpoint(TRUNCATE)` + `VACUUM` (space reclaim, no
  data-model risk) and guarded temp-file deletion. The DB `event`-table snapshot GC is
  NOT offered as a mutation (source-verified UNSAFE: the event log is replayed);
  `doctor` reports it instead. Compacted-part output reclaim is opt-in and VERIFY-OR-SKIP
  (`--reclaim-parts`). Git snapshots are report-only unless `--force-snapshots PATH`.

## Background: the seven issues, mapped to what ocman can do (Evidence)

Verified from the upstream issues (fetched 2026-07-17) and ocman source
(`ocman/cli.py`). Categories by safety:

SAFE to clean externally (source-confirmed):
- #37495/#31526 space reclaim: offline `PRAGMA wal_checkpoint(TRUNCATE)` then `VACUUM`
  on `opencode.db`, only when OpenCode is stopped + after a db/-wal/-shm backup.
  Source-confirmed safe (no auto_vacuum, no VACUUM in OpenCode; WAL mode). This is the
  primary, unambiguous DB win. NOTE: OpenCode writes NO `opencode.db.bak.*` itself
  (layout reply Q2), so there is no OpenCode-owned `.bak` family to prune.

RUNTIME-OWNED temp files (report-default, guarded delete; NOT OpenCode source):
- #36831 `$TMPDIR/opencode-wal-*.db` (~1.4GB each; reporter hit 268GB/200 files): layout
  reply Q4a found NO OpenCode source that writes this name; it is a SQLite-driver /
  bun:sqlite runtime artifact (origin inferred, not source-confirmed). Cannot identify
  "active vs stale" by name. So: REPORT by default; delete only when NO OpenCode process
  is running AND no live process holds the file open (fd check), behind a flag.
- #28089 `/tmp/*.so` (~4.5MB each; reporter hit 728GB): layout reply Q4b - these are
  Bun's extracted native/WASM libs (bun:sqlite, @parcel/watcher, Photon wasm), NOT
  OpenCode source, and are typically mmap'd by the live process. REPORT by default;
  delete only when stopped AND the file is not mmap'd/open by any live PID
  (`/proc/<pid>/maps` + `/proc/<pid>/fd`). Age threshold applies. Empirical
  `lsof`/`strace` confirmation recommended before ocman ever deletes these.
- The Reddit 88GB `~/backups/opencode/`: source-verified NOT OpenCode-owned (OpenCode
  writes no DB backups anywhere - no `VACUUM INTO`, no `.backup()`, no `copyFile` of the
  `.db`; layout reply Q2/Q3 + the `-2053-01` follow-up which re-verified repo-wide).
  Almost certainly a user cron/rsync/Timeshift job. ocman treats it as FOREIGN +
  REPORT-ONLY (never auto-delete): "large SQLite copies resembling OpenCode DB backups,
  not created by OpenCode; owner unknown - review manually." Deletion only if the user
  explicitly points reclaim at it (`--backups-dir PATH`) with full path-safety + preview.
  FORWARD-WATCH (follow-up): OpenCode has a latent `native.serialize()` / `client.export`
  capability with ZERO callers today (`database/sqlite.bun.ts:105,146`); a future release
  could start writing real DB snapshots, which WOULD change this ownership map. If ocman
  ever version-fingerprints OpenCode, treat "a new caller of that export/serialize
  appears" as the signal that OpenCode now makes its own DB backups.

REPORT-ONLY DB bloat (source-verified UNSAFE to auto-mutate):
- #33356 `event` table dominated by full-snapshot `message.updated` (87% of a 13.7GB
  DB). VACUUM does NOT help (live data, freelist ~0). The tempting fix (keep latest
  snapshot per message, delete the rest) is UNSAFE: `event` is the durable
  event-sourcing log V2 REPLAYS to rebuild state (schema reply Q1; `event.ts`
  durable/replay), so deleting rows risks corruption even though it does not cascade.
  ocman REPORTS this (size, per-type breakdown, issue link) and does NOT delete.

PARTIAL / opt-in (mutates OpenCode DB rows, verify-or-skip):
- #16101 compacted `part` output never cleared: `ToolStateCompleted` parts keep a large
  `data.state.output` string (+ `metadata`/`attachments`). The compaction marker is
  `data.state.time.compacted` (schema reply Q2), BUT the agent found no code that SETS
  it or clears output, so it may be absent in real data. `--reclaim-parts` therefore
  EMPIRICALLY probes whether the marker is populated; if not, it SKIPS (fail closed).
  When acting it rewrites `data` via `json_set(data,'$.state.output','')` (keeps valid
  JSON; never nulls the NOT NULL column), only for compacted parts past a retention
  window.

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
- ocman hardcodes `~/.local/share/opencode` and does NOT honor `$XDG_DATA_HOME` /
  `$OPENCODE_DB` / `opencode-<channel>.db`, whereas OpenCode DOES (layout Q1). ocman's
  discovery (D-1) must match OpenCode's resolution. `OPENCODE_STORAGE_DIR` is hardcoded
  to `Path.home()` not derived from `db_path` (`cli.py:392`).
- No `migration`-table schema fingerprinting (the correct gate; no `user_version`).

## Design

### D-1 Storage-location discovery
Add a `discover_storage_locations()` helper returning a structured set of paths.
Resolution mirrors OpenCode's own (layout reply Q1, `core/src/global.ts`):
- Resolve the DB path and the data-dir subtrees INDEPENDENTLY (verify reply Q5 note 3):
  an absolute `$OPENCODE_DB` may point OUTSIDE the data dir, and `$OPENCODE_DB=:memory:`
  has no file at all (skip the DB-file checks entirely in that case). Do NOT assume the
  DB and the snapshot/log/repos subtrees share a parent.
  - DB path: `$OPENCODE_DB` if set (absolute used verbatim; `:memory:` -> no DB checks);
    else the configured `db_path` (honors ocman's `--db`/config); else
    `<data>/opencode.db`.
  - Data dir (for subtrees + backups): `${XDG_DATA_HOME:-$HOME/.local/share}/opencode`.
    Honor `OPENCODE_CONFIG_DIR` for the config dir. (No `$OPENCODE_DATA` env exists.)
- DB family: the DB file (name may be `opencode.db` OR `opencode-<channel>.db`; detect
  by globbing `opencode*.db` at the DATA-DIR TOP LEVEL ONLY, and EXCLUDE ocman's own
  backup name prefixes like `opencode-db-cleanup-*` / `opencode-backup-*` so a backup is
  never misreported as the live DB - verify reply Q5 note 4), plus `<db>-wal`,
  `<db>-shm`. There is NO `<db>.bak.*` family (OpenCode writes none - layout Q2).
- Other OpenCode data-dir subtrees for reporting: `<data>/snapshot/**`, `<data>/log/**`,
  `<data>/repos/**`, `<data>/storage/**` (legacy session_diff), `<cache>/**`.
- ocman's OWN backup dir (`default_backup_dir`) - the only backups ocman owns/prunes.
- Runtime temp artifacts (report-default): `$TMPDIR/opencode-wal-*.db` and `/tmp/*.so`
  (respect `tempfile.gettempdir()`); plus OpenCode's own `<tmpdir>/opencode` scratch.
- Snapshot store: `<data>/snapshot/<project.id>/<hash>` bare git repos (layout Q5), for
  report-only sizing.
- Interactive extra-scan (D-1a): on a TTY, `doctor` OFFERS to also search common
  locations (e.g. `~/backups/opencode`, `$HOME` shallow scan for large `opencode*`
  dirs) and to ASK the user for an additional path to measure. Non-interactive: skip the
  offer, scan only the derived/known set. No deletion happens outside the SAFE set
  regardless of what discovery finds (discovery widens REPORTING, not auto-clean).

### D-2 `ocman doctor` (read-only full checkup)

- Add `db_connect_readonly(path)` using SQLite URI `file:<path>?mode=ro` (via
  `_get_sqlite`, `uri=True`), so diagnosis provably cannot write yet still reflects a
  concurrent writer's committed state, making it safe even while OpenCode runs. Do NOT
  use `immutable=1` (PR-001): `immutable` asserts the file will not change while open,
  which with a live OpenCode writer can return stale/garbage reads; verified that plain
  `mode=ro` both blocks writes and sees concurrent commits (`pysqlite3`, the active
  backend). Both `_get_sqlite()` backends (pysqlite3 and the stdlib `sqlite3` fallback)
  support `uri=True`; the helper must work on either (PR-010). If the DB is missing, is
  `:memory:` (no file), or the RO connect raises, degrade to file-size-only reporting for
  the DB checks (still run the filesystem checks) - never crash.

- Structure as a list of CHECKS. Each check is a small function returning a result
  record: `{key, title, status (ok|notice|warn), size_bytes, count, detail, fix_cmd,
  issue_url|None}`. `cli_doctor` runs them all, renders the table, prints the summary.
  This makes each check independently testable and easy to extend.

- SCHEMA-DEFENSIVE (PR-002): every DB-internal check MUST probe the schema before
  querying (via `PRAGMA table_info(<t>)` / `sqlite_master`) and return a distinct
  `unknown`/`skipped` status (NOT a crash and NOT a false `ok`) when the expected
  table/column/JSON shape is absent. OpenCode's real `event`/`part`/`message` schema is
  NOT represented in ocman's test fixtures and only partially known from the issue
  reports, so `doctor` must never assume a column exists. The exact shapes are being
  confirmed with `opencode.repo-agent` (see gate); until confirmed, treat the
  issue-derived shapes as tentative and code the probes so an unrecognized schema
  degrades to size-only reporting.

- The check set (reusing existing detection; NO duplicated logic where a helper exists):
  1. `db_size` - DB + WAL + SHM family (reuse `db_show_info` logic `cli.py:11637-11652`);
     WARN if WAL is large relative to the DB (runaway-WAL, #37495).
   2. `db_integrity` - read-only `PRAGMA quick_check`. If OpenCode is RUNNING (live fd),
      a single non-"ok" can be a transient mid-write artifact of reading a live WAL DB
      (verify reply Q5 note 2) -> report it as NOTICE ("recheck when OpenCode is
      stopped"), NOT a corruption WARN. When stopped, `quick_check` is authoritative -> a
      non-"ok" is a WARN.
   3. `event_bloat` - REPORT-ONLY. `SUM(length(data))` on `event` grouped by base
      `type` (split on the last `.`, or `LIKE 'message.updated.%'`); surface the
      `message.updated` total and estimated superseded waste (rows beyond the max-`seq`
      per `(aggregate_id, json_extract(data,'$.info.id'))`). NOTICE with issue #33356 and
      an explicit note that ocman will NOT delete these (replay-integrity risk); the fix
      is upstream. No reclaim command offered.
   4. `compacted_parts` - bytes in `data.state.output`/`metadata`/`attachments` of
      completed tool `part` rows whose `data.state.time.compacted` is present; NOTICE +
      `reclaim --reclaim-parts` + #16101. If NO part in the DB has `time.compacted`
      populated, report the potential bytes but mark the reclaim as "not currently
      actionable (marker unpopulated)".
  5. `orphan_rows` - for each `(table, col)` in `SESSION_RELATIONAL_TABLES`
     (`cli.py:399`, excluding `session`), read-only `COUNT(*) ... WHERE NOT EXISTS
     (SELECT 1 FROM session s WHERE s.id = {table}.{col})` (the exact predicate
     `db_run_cleanup` deletes with, `cli.py:10744-10749`); also count sessions whose
     `project_id` has no `project` row. WARN if any > 0; fix = `ocman db clean-orphans`.
  6. `orphan_diff_files` - session-diff `*.json` under the storage dir with no matching
     session row (reuse the orphan-diff logic from `db_run_cleanup` `cli.py:10650-10667`);
     fix = `ocman db clean-orphans`.
  7. `old_sessions` - COUNT of root sessions older than the retention window
     (`default_retention_days`) plus their attributable session-diff bytes on disk;
     NOTICE; fix = `ocman db clean --older-than ...`. Do NOT report a per-session DB byte
     "size" (the DB is a single shared file; bytes are not attributable per session -
     consistent with the existing note at `cli.py:11902`); label the DB portion as
     "reclaimed on VACUUM after delete", not a fixed number (PR-004).
  8. `ocman_backups` - inventory of ocman's OWN backups (reuse `dir_usage` + the
     `db_show_info` backups block `cli.py:11862-11894`): count, total size,
     oldest/newest; if backups older than a threshold exist, NOTICE with the reclaimable
     size + `ocman backup clean --older-than Nd`.
   9. `foreign_backups` - large SQLite copies resembling OpenCode DB backups OUTSIDE the
      data dir (e.g. `~/backups/opencode`, discovered in D-1): report-only WARN with
      size + "not created by OpenCode; owner unknown - review manually" (layout Q3). No
      auto-fix; deletable only via explicit `reclaim --backups-dir PATH`.
   10. `temp_wal` - `$TMPDIR/opencode-wal-*.db` count/size; report-only NOTICE + #36831,
       noting these are runtime/driver artifacts and reclaim needs OpenCode stopped + no
       live fd.
   11. `temp_so` - `/tmp/*.so` count/size (age-filtered) that are NOT mmap'd by a live
       OpenCode PID; report-only NOTICE + #28089 (Bun-extracted native libs).
   12. `snapshots` - `<data>/snapshot/**` size; report-only NOTICE + #36093 (never a safe
       auto-fix; DB references live hashes).

- Output: a vistab table (reuse the session-header styling: `round-header`, `padding=0`,
  bold header, color-gated). Columns: `Check`, `Status`, `Size/Count`, `Recommended fix`.
  A `Status` of WARN is shown in bold red, NOTICE in yellow, OK plain (honoring
  NO_COLOR). Beneath the table: a details block per non-OK check (the one-line
  explanation + issue URL). Footer summary: `N OK / M notices / K warnings`, and byte
  totals in THREE clearly-labeled buckets so the number is never misleading (PR-009):
  "ocman can reclaim now" (checkpoint+VACUUM + guarded temp + stale ocman backups),
  "opt-in" (`--reclaim-parts`), and "reported only, NOT ocman-reclaimable" (event bloat =
  upstream fix, foreign backups, snapshots). Never sum report-only bytes into a headline
  "reclaimable" figure.
- `--json` via `emit_json("doctor", {...})` emitting the list of check records
  (stable, additive schema).
- `doctor` NEVER mutates and is NOT behind the running guard (read-only, safe anytime).
- Verbosity: reuse the EXISTING global `-v/--verbose` (do not add a new flag, PR-011);
  at `-v`, `doctor` adds per-project event/part breakdowns and lists the specific
  orphaned tables/files; the default view stays a concise one-row-per-check summary.

### D-3 `ocman reclaim` (guarded cleanup)
A bare `reclaim` performs only the unambiguously-safe DB space reclaim (checkpoint +
VACUUM, guarded); everything riskier (temp-file deletion, part reclaim, backups,
snapshots) is behind an explicit flag. Each acting category has its own preview +
confirm:
- WAL checkpoint + `VACUUM` (the primary safe DB win): only when OpenCode is NOT running
  (guard below); run `PRAGMA wal_checkpoint(TRUNCATE)` then `VACUUM` on a writable
  connection, after the standard `opencode-db-cleanup-*` backup. Source-confirmed safe
  (schema Q5). No `--compact-events`: event-row deletion is NOT offered (UNSAFE; reported
  only, see D-2 check 3).
- Temp WAL DBs (`$TMPDIR/opencode-wal-*.db`): NOT deleted by default (report-only).
  Under an explicit flag, delete only when NO OpenCode process is running AND no live
  process holds the file open (fd check); keep the most-recently-modified as a
  precaution. These are runtime artifacts (layout Q4a), so ocman does not assume it can
  tell active from stale by name.
- Leaked `/tmp/*.so`: NOT deleted by default (report-only). Under an explicit flag,
  delete only files older than the age threshold that are NOT mmap'd/open by any live PID
  (read `/proc/<pid>/maps` + `/proc/<pid>/fd`; on non-Linux this check is unavailable, so
  require `--force` and age-only). Age threshold `reclaim_tmp_min_age_hours` (default 24).
- Stale backups: reuse `cli_clean_backups` for ocman's OWN backups. Foreign
  backup dirs (e.g. `~/backups/opencode`) are report-only; deletion only via explicit
  `--backups-dir PATH` with full path-safety + preview.

Opt-in DB mutation (VERIFY-OR-SKIP, guarded + backed up + typed-confirm):
- `--reclaim-parts`: for completed tool `part` rows with `data.state.time.compacted`
  present and older than a retention window, empty the large payload via
  `json_set(data,'$.state.output','')` (preserve valid JSON; NEVER null the NOT NULL
  column). MUST first (a) fingerprint the schema via the `migration` table and abort on
  an unrecognized level, and (b) EMPIRICALLY confirm `time.compacted` is actually
  populated on some part; if not, SKIP with a clear notice (fail closed) rather than
  guess a different signal. Pre-op db+wal+shm backup mandatory. (Event-row GC is
  intentionally NOT here.)
  SAFETY BASIS (verify reply, source-cited): OpenCode sets `time.compacted` only when the
  optional default-OFF `compaction.prune` runs (`session/compaction.ts:281`), and once
  set, its request builder REPLACES a compacted part's output with a literal
  "[Old tool result content cleared]" placeholder and drops attachments WITHOUT reading
  `state.output`/`state.attachments` (`session/message-v2.ts:293-296`). So emptying
  `output` on disk changes nothing OpenCode would send -> safe by construction when the
  marker is set. `time.compacted` itself MUST be preserved (it is the flag OpenCode keys
  on). `attachments` are ALSO unused post-compaction and could be cleared in the same
  `json_set` transaction (set `$.state.attachments` to `[]`, do not delete the key); but
  START with `output` only (biggest win, simplest) and add `attachments` later only if
  measured bytes justify it. V2 `session_message` data is a separate engine and OUT of
  scope for this pass.

Report-only unless forced:
- Snapshots (`<data>/snapshot/**`): never touched by default. `--force-snapshots PATH`
  enables deletion behind a multi-line RED warning + a typed confirmation distinct from
  the normal one (it can break revert/undo because the DB references live snapshot
  hashes and ocman cannot compute reachability); it prunes only the snapshot dir the
  user names, never guesses.

All destructive paths: `require_safe_to_mutate` first, `DestructivePreview` +
`confirm_destructive` (honor `-y`/`--yes` for the ordinary confirm only, NOT for
`--force-snapshots`), pre-op backup where a DB write is involved, and honor `--dry-run`.

USER-SUPPLIED DIRECTORY SAFETY (PR-006): `--backups-dir PATH` and `--force-snapshots
PATH` delete inside a directory the user names. Both MUST apply the same discipline
`cli_clean_backups` uses: resolve the path, REFUSE dangerous roots (`/`, bare `$HOME`,
the data dir itself), never follow a symlink out of the named directory, preview every
file/dir with sizes, and require the typed confirm. `--backups-dir` only removes files
by age within that dir; it never recurses into unrelated trees.

### D-4 Safety invariants
- `doctor` cannot write (read-only connection; asserted by a test that a
  running-OpenCode scenario still lets `doctor` run and produces no mutation).
- No temp file that is open/mmap'd by a live OpenCode process is ever deleted.
- No DB write (checkpoint/VACUUM/reclaim-parts) happens while ANY process holds the
  `.db`/`-wal`/`-shm` family open. "Running" is detected by a live fd on the DB family
  (layout Q6; verify reply Q3) - the authoritative check - across ALL same-UID processes
  (Desktop server, TUI-embedded server, `serve`, `web`), not just a terminal `opencode`.
  Short-lived CLIs open/close the DB in ms, so a live fd can be a benign TRANSIENT
  false-positive; treat ANY live fd as "do not mutate" (fail-safe) rather than trying to
  distinguish transient from real. Bypass only with explicit `--while-running`.
  IMPLEMENTATION (PR-007): this fd-on-DB-family check does NOT exist today -
  `require_safe_to_mutate` (`cli.py:7662`) detects via PROCESS enumeration
  (`detect_running_opencode`), not open fds. Add a new helper
  `db_family_open_by_live_pid(db_path) -> bool` that scans own-UID `/proc/<pid>/fd`
  symlinks (reuse the own-UID + `/proc/<pid>` pattern from the `list running` enumerator,
  `cli.py:7867`) for any fd resolving to the `.db`/`-wal`/`-shm` family; on non-Linux
  (no `/proc`), fall back to `require_safe_to_mutate`'s process check alone and note the
  reduced fidelity. `reclaim`'s DB-write path MUST call BOTH `require_safe_to_mutate`
  AND this fd check (either one positive = refuse unless `--while-running`).
- Event rows are NEVER deleted by ocman (report-only).
- `--reclaim-parts` aborts if the `migration`-table schema level is unrecognized, or if
  `data.state.time.compacted` is not actually populated in the DB (fail closed).
- Snapshots are never deleted without `--force-snapshots` + its own typed confirm.
- `--dry-run` on `reclaim` performs zero deletions/writes and prints exactly what would
  be removed with sizes.

### D-5 CLI surface
- `ocman doctor [-v] [--json]` (read-only; no guard). `-v` expands per-project /
  per-table detail; `--json` emits the check records.
- `ocman reclaim [--dry-run] [-y/--yes] [--while-running] [--reclaim-parts]
  [--reclaim-temp] [--backups-dir PATH] [--force-snapshots PATH]
  [--tmp-min-age-hours N] [--force]`. A bare `reclaim` does only the safe
  checkpoint+VACUUM. `--reclaim-temp` opts into the guarded temp-file (`opencode-wal-*.db`
  / `/tmp/*.so`) deletion; `--reclaim-parts` opts into the verify-or-skip part-output
  reclaim. `--force` is required to reap `/tmp/*.so` on non-Linux (no `/proc` mmap check);
  `--force-snapshots` takes the snapshot directory PATH to prune (never guessed). There
  is NO `--compact-events` (event-row GC is report-only, source-verified unsafe).
- Config keys (via DEFAULT_CONFIG + CONFIG_TEMPLATE, following `filter_max_bytes`):
  `reclaim_tmp_min_age_hours` (default 24; overridden per-run by `--tmp-min-age-hours`),
  `reclaim_parts_retention_days` (default 30).
- Normalizer + defaults entries for the new flags; handlers dispatch to
  `cli_doctor(args)` / `cli_reclaim(args)`.

## Test plan

Unit / offline (seed a temp DB + fake temp files under a tmp HOME, the established
`Path.home()` monkeypatch pattern). FIXTURE FIDELITY (PR-008): ocman's existing fixtures
do NOT model OpenCode's real `event`/`part` `data` JSON, so add a minimal but
schema-faithful fixture per the archived schema reply: `event` rows with
`type='message.updated.1'` and `data` = `{"sessionID":..., "info":{"id":...}}` (varying
`seq` per `(aggregate_id, info.id)` to exercise the superseded-waste estimate), and
`part` rows with `data` = `{"type":"tool","state":{"status":"completed","output":"...",
"time":{"compacted":<ms|absent>}}}`. Also seed a `migration` table row so the fingerprint
gate has something to read. The tests below rely on this fixture:
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
- reclaim checkpoint/VACUUM (bare `reclaim`): refuses when a live fd holds the DB family
  (and via the process guard), proceeds with `--while-running`; asserts a backup dir was
  created and VACUUM ran once; `--dry-run` writes nothing.
- reclaim temp (`--reclaim-temp`): report-only WITHOUT the flag (a bare `reclaim` deletes
  no temp files); with the flag, an `opencode-wal-*.db`/`.so` held by a fake live fd/mmap
  PID is skipped, an old unheld one is deleted; `--dry-run` no-ops.
- reclaim `.so` PID/mmap-aware: a `.so` "mapped" by a fake live PID is skipped; an old
  unmapped one is deleted only with `--reclaim-temp`.
- event GC is NOT offered: assert there is no `--compact-events` flag and that no code
  path deletes `event` rows (report-only guard).
- `--reclaim-parts` verify-or-skip: with `time.compacted` populated on a seeded part, its
  `data.state.output` is emptied via json_set (data stays valid JSON) only past the
  retention window; non-compacted parts untouched; a pre-op backup exists. With NO part
  carrying `time.compacted`, `--reclaim-parts` SKIPS (fail closed, deletes/writes
  nothing) and says so.
- migration-gate: seed a `migration` table with an unrecognized newest id -> the mutate
  categories (`--reclaim-parts`) abort/skip and `doctor` marks DB checks unknown.
- snapshots: default run never deletes snapshot dirs; `--force-snapshots PATH` requires
  the distinct typed confirm; `-y` does NOT bypass it.

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
- Risk: deleting a temp file OpenCode still needs. Mitigated by report-default +
  `--reclaim-temp` opt-in + fd/mmap-held skip + OpenCode-stopped + age threshold +
  `--dry-run`.
- Risk: `--reclaim-parts` corrupts JSON or acts on a wrong marker. Mitigated by
  `json_set` (valid JSON), migration-gate, empirical `time.compacted` check + fail-closed,
  mandatory backup.
- Risk: snapshot deletion breaks revert/undo. Mitigated by report-only default +
  `--force-snapshots` scary confirm; ocman never guesses which snapshot dir.
- Risk: non-Linux lacks `/proc` mmap introspection. Mitigated: `.so` reap falls back to
  age-only and requires `--force` there; documented.
- Non-goal (source-verified): DELETING `event` rows to compact the log. It is unsafe
  (V2 replays the log); ocman REPORTS the bloat + links #33356 for the upstream fix, and
  offers no `--compact-events`.
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
- SCHEMA/LAYOUT: the `opencode.repo-agent` schema+layout+follow-up replies (archived
  `.agents/comms/shared/archive/20260717-2043-01`, `-2043-02`, `-2053-01`) are the
  verified basis for the DB paths (grouping key `(aggregate_id, $.info.id)`, max-`seq`
  latest, `part.data.state.output`/`time.compacted`, `migration`-table fingerprint,
  XDG/`OPENCODE_DB` discovery, fd-based running detection). Treat them as evidence, not
  directives: re-verify against OpenCode source before implementing `--reclaim-parts` or
  path-discovery. If a needed schema shape/path cannot be verified on the target DB,
  implement the affected DB check as schema-defensive `unknown`/`skipped` and make
  `--reclaim-parts` FAIL CLOSED. `event`-row deletion is OUT (report-only); do not add it.
- Use `db_connect_readonly` = `mode=ro` (NO `immutable`, PR-001) so diagnosis is safe
  while OpenCode runs.
- NEVER delete a temp file mmap'd/held by a live OpenCode process; NEVER write to the DB
  while OpenCode runs without `--while-running`; NEVER delete snapshots without
  `--force-snapshots` + its distinct confirm; apply `cli_clean_backups`-grade path safety
  to `--backups-dir` / `--force-snapshots` (PR-006).
- Honesty rule (hard MUST): paste the ACTUAL
  `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` output; never claim a pass not
  run.
- Commit path-scoped (`git commit -m msg -- <paths>`), NEVER `-A`/`-a`, NEVER push,
  NEVER tag.
- On completion set `Status: EXECUTED`, add a Workflow-history execution line, and
  `git mv` this IPD pending -> executed (verify no dup via `git ls-tree HEAD`).
