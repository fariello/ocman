# Changelog

## [Unreleased]

## [1.3.0] - 2026-07-20

### Added
- **`ocman kill [PATTERN]`: stop the opencode running here (or matching PATTERN) without
  relaunching.** The no-relaunch counterpart to `reconnect`: with no argument it targets the
  opencode running at/under the current directory; `ocman kill <PATTERN>` matches by the same
  fields as `list running` (working dir / project / attributed session, case-insensitive). One
  match is killed; several prompt you to choose (including "all"). Own-user processes only
  (verified via `/proc/<pid>` owner), with the same PID-reuse guard as reconnect. SIGTERM by
  default with a short wait; `--force` (`-9`) escalates a survivor to SIGKILL. Confirms by
  default (`-y` to skip, `--dry-run` to preview); exits non-zero if anything survived. Linux-only.
- **`ocman reconnect`: recover an orphaned opencode after an SSH/network drop.** When a dropped
  connection leaves `opencode` running detached in your project, reconnect (from that directory)
  finds the opencode running at/under the current dir, kills it, and foreground-relaunches
  `opencode -s <session>` in your current shell. It resumes the killed process's `-s` session if
  it was launched with one, else the most-recently-updated session for the directory; with
  several instances it asks which to kill (including "all"). Safety: own-user processes only
  (verified by `/proc/<pid>` owner), a PID-reuse guard re-checks the target immediately before
  signalling, SIGTERM with a short wait (it stops rather than relaunch if the process will not
  exit), one confirmation covering kill+relaunch, and `--dry-run` / `-y`. Linux-only (process
  detection is Linux-only). Because it re-execs in your current shell, the new opencode inherits
  that shell's environment; only `-s <session>` is reproduced, not the old process's other flags.
- **Rename a session from the CLI.** `ocman session rename <SESSION> --to "New title"`, with a
  natural top-level alias `ocman rename <SESSION> to "New title"` (the word `to` is optional).
  `<SESSION>` is resolved the usual way (list number from `ocman ls`, `ses_...` id, or a unique
  title substring). The change is a single guarded `session.title` update in a transaction:
  it refuses while OpenCode is running (with `--force` / `--while-running` to override) and
  prints an honest note that OpenCode does not track which process uses which session, so ocman
  cannot tell whether that specific session is open (the running check is for the database as a
  whole). Supports `--dry-run`; a `to` inside a quoted title is preserved.
- **`lr` short alias for `list running`.** Parity with the existing `lp` (`list projects`)
  and `ls` (`list sessions`) short aliases.
- **Optional case-insensitive filter on the list commands.** `list projects` / `lp`,
  `list sessions` / `ls`, and `list running` / `lr` now accept an optional trailing
  `PATTERN` that narrows the output by a case-insensitive substring match:
  - `lp <PATTERN>` keeps projects whose directory OR name matches.
  - `lr <PATTERN>` keeps running instances whose working directory, project, OR attributed
    session (id / title / directory) matches. Session matching does not require `--long`.
  - The filter is applied before `--limit`, and `--json` reflects the filtered set (an
    empty match emits a well-formed empty payload and exits 0, so it stays scriptable).

### Changed
- **`ls <ARG>` now falls back to a session filter instead of erroring.** Previously,
  `list sessions <ARG>` where `<ARG>` did not resolve to a project printed "No matches
  found" and exited non-zero. Now it keeps the existing project-scope PRECEDENCE (if
  `<ARG>` uniquely resolves to a project, it scopes to that project's sessions, exactly as
  before) and otherwise treats `<ARG>` as a case-insensitive filter over session title,
  directory, and project. This is additive: every previously-working `ls <project>`
  invocation behaves identically; only the previously-fatal case becomes a useful filter.

## [1.2.0] - 2026-07-20

### Changed
- **Unified, richer session listings.** `session list` (and `ls` / `list sessions`),
  `search`, and the interactive session pickers now render every session through one
  shared "header": an identity line plus two tables (Start / Last active / Duration /
  Tokens In / Tok Out / Tok Cache; and Messages / Interactions / DB Parts / Cost),
  grouped under a `Project:` line. Table headers are bold on a blue background when
  color is enabled (honoring `NO_COLOR` / `FORCE_COLOR`; never low-contrast). The list
  number matches what `recover <N>` resolves. Pass `-b` / `--brief` for the previous
  terse one-line-per-session form. "Last active" is the last-updated time and
  "Duration" is derived from the timestamps (there is no separate "finished" marker).

### Added
- **TUI parity, Phase 5 (project bundles, move, backup clean, search, filter).** Completes
  CLI/TUI parity. The TUI can now export a whole project to an `.ocbox` bundle and import
  either a session or a project bundle (auto-detected from the bundle). It gains a local
  session move (updates the session's working directory; remote/git-aware moves stay on the
  CLI, with an in-app note), a "Prune Old Backups" action, a session content-search box
  (results select into the current session), and a "Filter" action that re-scopes a
  recovery/compacted document via the LLM using the same egress guards as compaction. Also
  hardened the transcript-export worker's error path (it no longer touches a widget off the
  UI thread, so a background export failing while a modal is open cannot crash the worker).
- **TUI parity, Phase 4 (bulk actions, duration prune, chunking).** The TUI sidebar now
  supports multi-select (press Space on a session to add/remove it), enabling batch actions:
  Batch Delete (one consolidated backup/transaction/VACUUM via the same path as the CLI,
  behind a typed-yes confirmation that offers to write recovery extracts first) and Batch
  Export (one `.ocbox` per selected session). The Database Admin prune form accepts a
  duration string (2h/5d/6w/6mo/1y or "30 days") in addition to integer days, an optional
  project scope, and a "write recovery extracts first" toggle. The recovery-file generator
  gained a "Split into parts (chunk)" option that writes ordered `.part-NNofMM` files
  instead of one file, matching `recover --chunk`.
- **TUI parity, Phase 3 (spend + running views).** Two new read-only TUI tabs. "Spend"
  shows per-project LLM cost and split tokens (with an "include historical/deleted spend"
  toggle for the grand total), rendered from the same `gather_spend()` data the CLI uses,
  so the numbers match `ocman spend`. "Running" lists running OpenCode instances
  (pid/user/uptime/kind/listener/auth/project) and raises a loud red banner for insecure
  control servers (no auth, or non-loopback bind); if detection is unreliable it says so
  explicitly rather than showing a misleading empty "all clear". Both are observe-only.
- **TUI parity, Phase 2 (storage checkup + guarded reclaim).** The TUI gains a new
  "Storage" tab: a read-only checkup that runs the same checks as `ocman doctor` (schema,
  DB/WAL size, integrity, event bloat, compacted parts, orphans, old sessions, backups,
  temp leftovers, snapshots) in a background thread and renders them with the reclaimable
  now / opt-in / reported-only totals; plus guarded reclaim actions (checkpoint + VACUUM,
  reclaim temp files, reclaim compacted parts, prune a backups directory), each behind a
  preview-and-confirm, reusing the CLI's guards (refused while OpenCode holds the DB open
  unless you opt in, backup first). The dangerous snapshot-force reclaim is intentionally
  not in the TUI; a note points to `ocman reclaim --force-snapshots` / `ocman doctor` on
  the command line.
- **TUI parity, Phase 1 (delete safety).** The interactive TUI no longer deletes more
  destructively than the CLI: the session and project delete confirmations now include a
  "Write recovery extracts first" option (default ON) that writes the
  `.prompt`/`.restart`/`.transcript` files for each affected session before deleting,
  reading straight from the database (never launching OpenCode). The previously dead
  "Clear Historical Activity Log (Planned)" button is now a working control that wipes the
  activity ledger (run records and all-time totals) behind a typed-yes confirmation,
  sharing the same `clear_history_ledger()` logic as `ocman history clear`.
- **Bare-word `help` works like `--help`.** After a command, a trailing (or
  interspersed) `help` word is treated as `--help`, so `ocman session delete help`,
  `ocman db clean help`, etc. print that command's usage. The top-level `ocman help
  [topic]` overview is unchanged.
- **Recovery extracts before deletion.** Before deleting sessions, ocman now offers to
  write the readable recovery artifacts (`.prompt.md` / `.restart.md` / `.transcript.md`)
  for each session so their content is not lost. This is default ON and folded into the
  delete confirmation; `--extracts` forces it (skipping the extra question), `--no-extracts`
  skips it, and `-y` / a non-interactive run assumes yes. Files go to the recovery output
  directory (default `./opencode-recovery`, override with `-o`). Extraction reads each
  session directly from the SQLite database (it does NOT launch OpenCode), so it works even
  with OpenCode stopped and is fast in bulk. Available on `session delete`, `project delete`,
  and `db clean` (age-based prunes). A session that cannot be rendered is skipped with a
  warning and the delete still proceeds.
- **`ocman doctor` and `ocman reclaim`: diagnose and reclaim OpenCode disk usage.**
  `doctor` is a read-only checkup (safe even while OpenCode is running) that reports DB/
  WAL size, integrity, event-log bloat, compacted-part output, orphaned rows/diff files,
  old sessions, ocman + foreign backup inventory, temp leftovers (`opencode-wal-*.db`,
  `/tmp/*.so`), and snapshots; each finding names the `ocman` command that fixes it and
  links the upstream OpenCode issue where relevant, with a summary that separates
  "ocman can reclaim now" from opt-in and report-only bytes. `reclaim` performs guarded
  cleanup: a bare run does only offline `wal_checkpoint(TRUNCATE)` + `VACUUM` (refused
  while any process holds the DB open unless `--while-running`, backup taken first);
  `--reclaim-temp`, `--reclaim-parts` (verify-or-skip, never deletes the event log),
  `--backups-dir PATH`, and `--force-snapshots PATH` are opt-in, previewed, and
  path-safe. New config keys `reclaim_tmp_min_age_hours` and `reclaim_parts_retention_days`.
- **Chunk large sessions (`--chunk` on `recover` / `compact`).** Instead of only being
  able to truncate a large session (dropping older turns), you can now split it into
  ordered, self-contained parts named `YYYYMMDD-HHMM-<session_id>.part-NNofMM.<kind>.md`.
  Splitting happens on interaction boundaries (never mid-turn), so nothing is dropped.
  `--max-lines` / `--max-interactions` set the per-part size (defaults from the new
  `chunk_max_lines` / `chunk_max_interactions` config keys); the interactive large-
  session prompt gains a `[c]hunk` choice. `compact --chunk` sends each part to the LLM
  separately (so each fits the context window), writes `...part-NNofMM.compacted.md`,
  and sums all parts in the pre-run cost table. Export (.ocbox) is not chunked.

### Fixed
- **Project import rebases session directories even when the OS canonicalizes the
  worktree.** On macOS, paths like `/home`, `/var`, and `/tmp` are firmlinks, so resolving a
  bundle worktree (e.g. `/home/me/proj`) yields a different canonical path
  (`/System/Volumes/Data/home/me/proj`). Because the resolved worktree was compared against
  the raw stored `session.directory`, the prefix did not match and the imported sessions were
  left pointing at the old worktree instead of the new project root. The rebase now resolves
  the stored directory before matching (via the shared `_rebased_dir` helper), so
  `import --new-project-path` rebases correctly on macOS as it already did on Linux/Windows.
- **Require `vistab>=1.3.0` so a clean install works on Python 3.12.** The dependency floor
  was `>=1.1.3`, which allowed the published `vistab 1.2.0`; that release fails to import on
  Python 3.12 (`NameError: name 'Set'` from an un-imported annotation), so a fresh
  `pip install ocman` was broken on 3.12. `vistab 1.3.0` fixes the import and provides the
  table styling ocman uses (`set_color`/`set_header_style`); the floor is now `>=1.3.0`.
- **Self-documentation: errors that teach, and no leaked tracebacks.** Two error messages
  advertised removed flags (`--show-models` / `--list-projects`); they now name the real
  commands (`ocman models` / `ocman list projects`). An unexpected (non-RecoveryError)
  exception no longer prints a raw Python traceback: the CLI shows a clean one-line
  `Error: Unexpected error: ...` with a "re-run with -v" hint, and `-v`/`--verbose` still
  shows the full traceback for debugging. The `--older-than` parse error now shows the
  accepted formats (`2h/5d/6w/6mo/1y/'30 days'`) at the point of failure; "Database/Session/
  Project not found" errors now include a recovery hint; "Invalid selection/choice" prompts
  now show the accepted range or option set. `reclaim` is now discoverable via
  `ocman help maintain` and the overview (not only `help all`/`doctor`). TUI Storage reclaim
  buttons are relabeled to be self-explaining ("Compact database (checkpoint + VACUUM)",
  "Reclaim compacted tool output (parts)").
- **Saving config no longer resets keys the caller did not pass.** `save_ocman_config`
  now merges the passed keys over the EXISTING config (falling back to defaults only for
  keys never set), instead of over `DEFAULT_CONFIG`. Previously a partial save (notably
  every TUI config-form save, including the automatic save on tab switch / exit) silently
  reset unmanaged keys (`chunk_max_*`, `reclaim_*`, `filter_*`,
  `copy_restart_to_project_prompts`, `history_max_runs`) to their defaults. A full
  reset-to-defaults still resets everything.
- **`parse_recovery_name` folded a trailing name segment into the session id.** A
  filter output like `...<sid>.<scope>.compacted.md` (and now chunk part names) parsed
  the session id as `<sid>.<scope>` instead of the bare `<sid>`. It now strips one
  trailing segment and re-parses, so both forms round-trip correctly.

### Changed
- **Guard against mutating the DB while OpenCode is running.** Every destructive/
  mutating command (session/project delete, batch delete, db clean, clean-orphans,
  session/project move, session/project import, backup restore, db rebase) now checks
  for running OpenCode instances first, since OpenCode has no cross-process session
  lock and a concurrent instance could corrupt state. If any instance is running, the
  command lists them and refuses by default; proceed with `--while-running` (alias:
  `--force`) or, interactively, by typing `yes`. Detection uses a broad matcher (any
  `opencode` process, not just `--continue`) and is fail-closed on Linux (if it cannot
  determine whether OpenCode is running it refuses unless `--while-running`) and
  fail-open with a caveat on other platforms. `-y/--yes` still only skips the ordinary
  confirm, not this running-instance check.
- **Accessibility: removed low-contrast dim/grey text.** Secondary output (notes, IDs,
  paths, disclaimers, and the TUI sidebar's ids/tags/empty-states) no longer uses the
  ANSI faint attribute or Rich `dim`; it renders as normal high-contrast text (the TUI
  uses a defined readable palette color). Meaning is carried by wording, never by
  reduced contrast, and color is never the sole signal.
- **`FORCE_COLOR` support.** Color output now honors `FORCE_COLOR` (force color on even
  without a TTY) alongside the existing `NO_COLOR` (which takes precedence), in both the
  main and help output paths.

### Added
- **`ocman list running`**: list running OpenCode instances (pid, user, uptime, kind,
  working directory, project, and a best-effort session with provenance) and flag
  insecure control servers. It detects which instances OWN a listening socket and, for
  those, classifies auth from the process environment (`OPENCODE_SERVER_PASSWORD`
  present = secured); a bold-red banner names any VULNERABLE (unauthenticated) or
  NETWORK-EXPOSED (non-loopback bind) listener with remediation. Observe-only:
  current-user by default (`--all-users` opt-in; others' auth shown as "unknown"),
  never calls state-changing endpoints, never prints secrets. `--probe` optionally
  confirms auth via a read-only `GET /app` on your OWN loopback listeners; `--json`
  for machine output. Fails loud (never a false "all clear") if it cannot enumerate.
- **`ocman spend`**: LLM spend reporting. Default is a per-project table (cost + split
  tokens, sorted by cost) with a live total; `ocman spend <project> --sessions` drills
  into per-session spend; `--historical` adds the deletion ledger's saved (deleted)
  spend as a single global line (not attributable per project) and a grand total;
  `--json` emits the machine-readable form.
- **`--json` machine-readable output** on `session list`, `project list`, and
  `history show`, via a shared emitter with a `schema_version` field (a documented,
  semi-stable contract; breaking shape changes bump the version and are noted here).
  Human output is unchanged when `--json` is absent. (`search` and `db info` JSON are
  deferred to a follow-up: their output is more nested and warrants its own schema.)
- **`--limit N` on `session list`, `project list`, and `history show`** to cap long
  output, with a note reporting how many rows were withheld (the cumulative grand
  totals in `history show` still cover all runs). The `db info` top-models count is now
  a named constant.
- **`--dry-run` for `move` and `session import`.** `session move` / `project move` /
  top-level `move` now accept `--dry-run` (show the plan, and for a remote destination
  the full runbook, without moving anything or running git); `session import --dry-run`
  reports the resolved import plan (ID remaps, target project) without writing to the
  database or disk.

### Changed
- **Consistent destructive-op flags.** `-y/--yes` (skip the typed confirmation) is now
  accepted by `project delete`, `db clean`, `db clean-orphans`, and `backup clean` (it
  was previously only on `session delete`/`compact`/`move`), so these can run
  unattended. `--force` continues to mean "bypass the process-lock check" everywhere;
  on `history clear` (which has no process lock) `--force` is now a documented
  back-compat alias for `-y`. The top-level `move` sugar now also accepts
  `--confirm-remote-delete`, `-y/--yes`, and `--force`, matching `session move` /
  `project move`.
- **Corrected `export` help.** The top-level `export` help no longer claims "project
  export is not yet supported"; project export is supported and auto-detected.

### Added
- **Short aliases `ocman ls` and `ocman lp`** for `ocman list sessions [NAME]` and
  `ocman list projects`.
- **Git-aware, cross-machine `ocman move`.** `move SPEC to DST` now inspects a git source repo and,
  on a TTY, offers to handle the working tree before moving (commit staged/all, or push/pull a clean
  but diverged repo), asking everything up front so a git failure aborts before anything moves. When
  `DST` is a remote `host:/path`, ocman performs NO network I/O: it prints a shell-quoted, copy-paste
  runbook (export bundle, scp, git-or-tar repo transfer, remote import with `--new-project-path`) and
  never deletes the local copy. A guarded `--confirm-remote-delete` reclaims local space after you
  verify the remote import. An existing local destination now offers backup/replace/overlay choices
  instead of a hard error. Git commands ocman runs use argv (never a shell); printed commands are
  `shlex.quote`-escaped.
- **Richer multi-project `list sessions` output.** When no single project is in scope, each session is
  shown with its ID and project directory, first/last active timestamps, cost, and split
  input/output/cache token counts (alongside the approximate message/interaction/part counts).
  Single-project listings keep the compact one-line-per-session form.
- **Loud global-mapping NOTICE.** Listing sessions from a home/ad-hoc directory whose sessions are filed
  under OpenCode's global (`/`) project now prints a highly visible NOTICE explaining the mapping and how
  to view the true global project (`ocman list sessions in /`).
- **Per-project cost and tokens.** `ocman list projects` shows each project's active cost and split
  input/output/cache tokens; `ocman disk` (`db info --by-project`) renders an aligned table keyed by
  project directory with sessions, messages, cost, split tokens, and session-diff file count/size.
- **WAL/SHM explanation** in `db info` output, clarifying the SQLite write-ahead-log and shared-memory
  sidecar files under "Size on disk".
- **`fmt_int` / `fmt_cost` helpers** for consistent comma-separated integer and currency formatting.

### Changed
- **Total/accumulated cost figures** in `db info` and history totals are now comma-separated (e.g.
  `$4,231.56`) instead of a bare four-decimal number.
- **Batch session delete is now one consolidated operation.** Deleting multiple sessions
  (an explicit list, or a project expansion) no longer repeats the backup, `VACUUM`, and
  rollback report once per session. It now takes a single family backup, runs one
  transaction and one `VACUUM`, writes one history entry, and prints one grand-total report
  (sessions/messages/rows/files removed, database size before/after, total reclaimed) with a
  single rollback stanza. Single-session `session delete ID` output is unchanged.
- **Deleting a project's sessions by naming the project now removes the empty project row.**
  When you delete a whole project's sessions (e.g. `ocman session delete <project>`), the
  now-empty `project` row (and its `project_directory`/`workspace` rows) is removed in the
  same transaction, so the project no longer lingers with zero sessions. A plain
  `session delete ID1 ID2` that happens to empty a project does NOT remove the project row.

### Added
- **`ocman filter <input>` command:** re-scopes an existing recovery/compacted document to a
  single project/scope via the LLM, dropping out-of-scope content. Scope is given with
  `--project <name|id|path>` (resolved against the database) and/or `--scope "free text"`
  (e.g. `"ocman only"`); at least one is required. It reuses the compaction model selection
  (`-C/--compact [MODEL]`), the token/cost estimate, and the confirmation flow, and reuses the
  compaction system prompt (which treats the document as untrusted evidence, not instructions)
  with a dedicated filter user prompt. The result is written next to the source (or to `-oc`) as
  `YYYYMMDD-HHMM-<session_id>.<scope>.compacted.md`; a pre-existing target is backed up to
  `*.compacted.bu.NNN.md`. The output path is path-contained and symlink-safe, and the input file
  is never modified.
- **`scripts/migrate_recovery_names.py`:** a one-shot migration to normalize recovery filenames
  written by older ocman versions to the new canonical scheme. Operates on the given directory
  (top-level only, no recursion), skips symlinks, skips already-canonical files, refuses to
  overwrite an existing target unless `--force`, and never deletes a source on a failed rename.
  Detects in-plan duplicate targets (two files that collide on the minute-precision name) and
  reports them in both dry-run and apply, preserving both sources. Supports `--dry-run` (preview)
  and `--yes` (skip the confirmation prompt).
- **Pre-egress guards for `filter` and `--compact`:** before sending content to the LLM API, ocman
  now enforces a configurable input size cap (`filter_max_bytes`, default 5 MB; override with
  `--force`) and a secret/PII scan (`filter_secret_scan`, `conservative` by default or `aggressive`
  for sensitive environments) that stops the send if a likely private key, API token, JWT, bearer
  token, credential assignment, or SSN is detected. Bypass the scan with the new `--allow-secrets`.
  Detections are reported by type and line number only; the secret value is never echoed.
- **TUI recovery/compaction parity with the CLI:** the TUI now writes recovery artifacts using the
  canonical `YYYYMMDD-HHMM-<session_id>.<kind>.md` scheme (full session id, `.prompt.md`), honors
  the configured `default_out_dir` instead of a hardcoded path, and (like the CLI) copies the
  compacted file into a project's `.agents/prompts/pending/` when enabled.

### Changed
- **Canonical recovery-artifact filenames:** all recovery outputs (CLI **and TUI**) now use one
  scheme, `YYYYMMDD-HHMM-<session_id>.<kind>.md` in **local time**, where `<kind>` is one of
  `transcript`, `restart`, `prompt`, or `compacted`, and all artifacts for a session share the
  `YYYYMMDD-HHMM-<session_id>` stem. This reconciles a prior inconsistency where the deterministic
  writer used a UTC, seconds-precision `opencode-...` prefix while the in-project compacted copy
  used a local, date-only name. The in-project copy (into `.agents/prompts/pending/`) is now
  `YYYYMMDD-HHMM-<session_id>.compacted.md` (timestamp = session last-updated, local). The TUI's
  compaction-prompt file is now `.prompt.md` (was `.compact-prompt.md`). Existing files can be
  normalized with `scripts/migrate_recovery_names.py`.
- **`--compact` egress behavior change:** the already-existing `--compact` path is now also subject
  to the size cap and secret/PII scan above. A non-interactive `--compact` on a transcript that
  contains a detected secret will now stop and require `--allow-secrets` to proceed.
- **Overwrite-collision handling** (shared by `filter`, `--compact`, and the migration script):
  before overwriting an existing recovery file, ocman checks whether opencode/ocman is running; if
  so it refuses (the CLI errors and exits, the TUI declines) so a live session's files are never
  clobbered. When safe, it backs up the existing file (`*.bu.NNN.md`) by default and can delete it
  interactively; non-interactive runs always back up and never delete. (The running-instance check
  is best-effort and POSIX-only; on Windows the backup default is the safety net.)
- **New config keys** `filter_max_bytes` and `filter_secret_scan` are added with safe defaults;
  existing `ocman.toml` files continue to work unchanged.

## [1.0.6] - 2026-07-05

### Changed
- **License changed from BSD-3-Clause to Apache-2.0.** The project is now licensed under the
  Apache License 2.0 (see `LICENSE` and the new `NOTICE`). Apache-2.0 requires that redistributions
  and derivative works retain the `NOTICE` file and display its attribution reasonably prominently
  ("Based on the original ocman by Gabriele G. R. Fariello — https://github.com/fariello/ocman"),
  and it adds an explicit patent grant. Also corrected the copyright holder to the full name
  (Gabriele G. R. Fariello) in `LICENSE` and `pyproject.toml`.
  Note: the previously published **1.0.5** artifact on PyPI was released under BSD-3-Clause and
  remains available under those terms; the Apache-2.0 license applies to this repository state and
  subsequent releases.

### Added
- **`NOTICE`** file with the required Apache-2.0 attribution string.
- **`CITATION.cff`** so the project can be cited (GitHub "Cite this repository"); a Citation section
  was added to the README.

## [1.0.5] - 2026-07-05

### Documentation
- **README positioning ("actually reclaims space"):** README now states ocman's core value: it deletes
  orphaned/old rows and their on-disk session-diff files and runs `VACUUM` to physically shrink the SQLite
  file, reporting the reclaimed bytes, with the author's measured comparison against `ocgc` v0.1.0
  (a 2.9 GB DB shrank to ~2.8 GB under ocgc vs ~1.9 GB under ocman's orphan cleanup).
- **README config template corrected:** documented the real key `default_compaction_model` (default `""`)
  instead of the nonexistent `default_model`.
- **README Argument Reference completed:** added the previously-undocumented flags
  (`-lp/--list-projects`, `-ls/--list-sessions`, `-P/--project`, `-A/--all-sessions`, `-D/--details`,
  `-H/--head`, `-T/--tail`, `-V/--version`, `-ir/--input-restart`, `-it/--input-transcript`,
  `-oc/--output-compact`, `--show-compaction-prompt`, `--show-logs`) and the `disk`/`du` + `delete project`
  natural-language commands; `ARCHITECTURE.md` notes the `preprocess_argv` commands and the TUI `css/` dir.
- **`--create-config` prompt wording** updated from "restart file" to "compacted file" to match the
  compacted-copy behavior (the `copy_restart_to_project_prompts` config key is unchanged for compatibility).

### Added
- **Compacted files copied into the project's prompts:** when recovering a session with
  `--compact` and the working project uses the `.agents` convention (has `.agents/plans/` or
  `.agents/prompts/`), ocman also copies the LLM-generated `*.compacted.md` (the document a fresh
  agent reads) into `<project>/.agents/prompts/pending/` named `YYYYMMDD-<session_id>.compacted.md`
  (date = session last-updated, local). A pre-existing copy is backed up to
  `*.compacted.bu.NNN.md` (from `001`). The project is resolved as `--session-dir` → the session's
  recorded directory → the current directory. Only applies when compaction runs (a plain recovery
  copies nothing). The copy is fail-soft (never breaks recovery) and can be disabled with
  `--no-project-prompt` or the `copy_restart_to_project_prompts` config (default true). (CLI
  recovery path; the TUI compaction action is a follow-up.)
- **`--clear-history` now confirms before wiping:** it previously erased the activity ledger and
  all-time totals with no prompt. It now shows how many run records will be erased and requires a
  typed `yes`; `--force` bypasses the prompt for scripts.

### Changed
- **Informative "opencode is running" safety check:** when `--delete`, `--delete-project`, or
  `--clean`/`--clean-orphans` refuse because opencode is running, the error now lists **each**
  detected process (PID, TTY, uptime, start time, working directory on Linux, and a best-effort
  project name) and how many are running, instead of a single generic line. The check errs
  toward inclusion (a genuine running instance is never missed on a destructive gate), excludes
  ocman's own process, and fails open if it cannot enumerate processes. `--force` still bypasses
  only this lock (never a confirmation). One shared `check_opencode_process_lock` helper replaces
  the three duplicated `pgrep` checks.
- **Unified destructive-action confirmations:** session delete, project delete, and the age-based
  cleanup/orphan prune now confirm through the shared destructive-confirmation seam (consistent
  typed-`yes` handling). Behavior is unchanged; in particular `--force` still only bypasses the
  running-`opencode` process-lock, never the confirmation prompt.
- **`ocman --clean-backups` shows a full KEEP/DELETE preview:** before confirming a prune it
  now lists **all** backups with column headers (`Backups`/`Size`/`Days`/`Modified`/`Action`),
  a right-aligned Size column and a right-aligned `Days` (age, 2 decimals) column, and a
  color-independent `DELETE`/`KEEP` tag per item, plus a
  "N to delete, M kept" summary and a header naming the concrete cutoff timestamp. If the prune
  would remove **every** backup, a forceful warning states that no rollback backups will remain.
  Retained rows are summarized beyond 20 (use `-v` to list all). Built on a new shared
  destructive-confirmation seam
  (`DestructivePreview` + `render_destructive_preview` + `confirm_destructive`) that other
  destructive commands will adopt.
- **`--days` accepts fractions:** the cleanup/backup retention window (`--clean --days`,
  `--clean-backups --days`, and `default_retention_days`) now accepts floating-point days,
  e.g. `--days 0.25` = 6 hours.

### Added
- **Disk-usage reporting in `ocman info`:** a **Backups (Disk Storage)** section (total size,
  count, oldest/newest) so backup growth is visible without shell tools, plus an optional
  per-project breakdown via `ocman info --by-project` (or the `ocman disk` alias) showing
  exact session-diff bytes and session/message/token counts per project. Per-project DB
  bytes are intentionally not reported, because the SQLite database is a single shared file.

## [1.0.4] - 2026-07-04

### Fixed
- **TUI compaction:** The TUI LLM-compaction action was non-functional; it called
  `render_compact_prompt` and `call_compaction_api` with the wrong arguments and treated
  the API's string result as a dict, so compaction always failed. Fixed all three call
  sites (and the "write compaction prompt" export action) and added test coverage.
- **TUI stability:** Background worker threads (export, delete, compaction, backup,
  restore, cleanup) that outlive the app no longer crash with
  `RuntimeError: App is not running`; late UI callbacks are now safely dropped.
- **Session import (correctness):** On session-ID collision, id references inside
  session-diff files are now remapped by exact match. The previous whole-string
  substitution could corrupt unrelated text that merely contained an id as a substring.
- **Config save:** `save_ocman_config` now merges over defaults, so saving a partial
  config (e.g. from the TUI settings form) can never fail to render when new config
  keys are added.

### Changed
- **Performance, session import:** Collision-time id remapping is a single structural
  pass instead of an O(diffs × ids) per-id whole-string replace (~26× faster per diff on
  a 300-session subtree in local measurement).
- **Performance, move/rebase:** `db_move_project_metadata`, `db_move_session_metadata`,
  and `db_rebase_paths` share one directory-rebasing helper (resolves prefixes once);
  behavior is unchanged.
- **Performance, export:** Table JSONL is staged in a per-run temp directory (unique
  name, single-shot cleanup) instead of fixed-named files in the shared temp dir.

### Added
- **`history_max_runs` config (default 500):** Caps the number of detailed run records
  retained in the activity ledger (oldest trimmed on save); cumulative all-time totals
  are always preserved. Set to 0 for no limit.
- **Opt-in performance benchmarks** (`tests/test_perf.py`, run with `OCMAN_BENCHMARK=1`);
  informational only, never a CI gate.

## [1.0.3] - 2026-07-03

### Added
- **Cross-platform support**: Windows/macOS path compatibility and a macOS/Windows CI matrix
  (Python 3.10-3.14). On non-Linux platforms the CLI falls back to the standard-library `sqlite3`
  module when `pysqlite3` is unavailable.
- **Progress reporting**: Real-time progress feedback during session exports and imports.
- **Logging**: Standardized log prefix to `[INFO]` with verbose progress reporting.

### Changed
- **Low-memory exports**: Session exports stream table rows to JSONL in batches to keep memory flat.

### Fixed
- **TUI move/export/import crash**: `MoveProjectModal`, `ExportSessionModal`, and `ImportSessionModal`
  background workers called `self.call_from_thread`, which only exists on the `App`; the operation
  completed but the app then raised `AttributeError` and exited non-zero. Now use
  `self.app.call_from_thread`.
- **TUI delete summary**: The post-deletion summary could raise `UnboundLocalError` when session
  metadata could not be fetched; summary fields now have safe defaults.

### Security
- **Restore hardening (Zip-Slip)**: `--restore` now validates every ZIP member path before extraction
  and rejects entries that would escape the destination directory.
- **Export connection safety**: The export database connection is now always closed, including on the
  error path.

### Documentation
- Added `ARCHITECTURE.md` describing entry points, the CLI/TUI relationship, data contracts
  (`.ocbox`, backup ZIP, `ocman.toml`), the database model, and the rollback-safety pattern.

## [1.0.2] - 2026-06-25

### Added
- **CLI/TUI Relocation**: Support for relocating/moving projects and sessions, either physically or metadata-only (`--move-project`, `--move-session`, `--to`, `--metadata-only`, `--rebase-paths`).
- **CLI/TUI Export & Import**: Support for exporting sessions into `.ocbox` ZIP bundles and importing them, complete with UUID remapping and path rebasing (`--export-session`, `--import-session`, `--to-project`, `--new-project-path`).

### Security
- **Hardened Import Engine**: Implemented whitelisting of table names and strict regex validation of session IDs on session import to prevent SQL Injection and Path Traversal vulnerabilities.

## [1.0.1] - 2026-06-24

### Fixed
- Fixed SQLite database connection leaks under exception pathways in TUI and CLI.
- Aligned output recovery files and compaction prompt filenames to share a single process startup timestamp.
- Added unit and integration tests covering SQLite error recovery, CLI argument execution paths, and process startup timestamps.

## [1.0.0] - 2026-06-19


### Added
- **PyPI Release**: Officially published the package under the name `ocman`.
- **CLI**: Added `-V` / `--version` flags for printing version information.
- **CLI**: Added automated cleanup options (`--clean`, `--days`, `--clean-orphans`).
- **CLI**: Added `--info` for inspecting database sizes, status, and WAL integrity.
- **CLI**: Added `--backup-opencode` and `--restore` for rollback-protected system state backups.
- **CLI**: Added `--delete-project` to recursively prune a project from database and filesystem.
- **CLI**: Positional subcommand preprocessing (e.g., `ocman show logs`, `ocman list projects`).
- **TUI**: Reorganized dashboard layout (Database Admin tab, Activity logs audit tab, live Config settings tab).
- **TUI**: Integrated rollback-safe backup and restoration controls within the UI.

### Changed
- Renamed project to `ocman` (OpenCode Manager), unifying script entry points and package namespace.

### Fixed
- Fixed TUI event loop race conditions in test execution and consolidated namespace mocks in the test runner.
- Hardened dependency graph by declaring `anyio` under optional dev dependencies.

## [0.2.0] - 2026-06-04

### Added

- **CLI**: `--list-projects`, `--project`, `--list-sessions`, `--details`,
  `--head N`, `--tail N` for browsing sessions without the TUI.
- **CLI**: `--compact [MODEL]` replaces `--use-model`. Interactive model
  selection when no model specified.
- **CLI**: `--delete` to delete a session with confirmation.
- **CLI**: `--all-sessions` to show subagent/child sessions (hidden by default).
- **CLI**: CWD auto-detects project (including from subdirectories).
- **TUI**: Project switching (`g` key): browse all projects from database.
- **TUI**: Session deletion (`d` key, then `y` to confirm).
- **TUI**: Subagent session toggle (`a` key): hidden by default, shown with ⤷.
- **TUI**: Session Detail redesign: fixed header, scrollable exchanges,
  `f`/`l` scroll to top/bottom, `/` search with bold red highlights.
- **TUI**: Screen titles in header bar for all screens.
- **TUI**: Sessions loaded from SQLite database (shows all sessions, not
  just the filtered subset from `opencode session list`).
- File backup before overwrite (`.01.bak`, `.02.bak`, etc.).
- `COMPACTION_MAJOR_ISSUE` tag for one-shot prompt safety.

### Changed

- **File naming**: All output files now named `opencode-YYYYMMDD-HHMMSS-SESSION_ID.<type>.md`
  (was `opencode-recovery-SESSION_ID-TIMESTAMP.<type>.md`).
- **Prompt type**: `.compact-prompt.md` renamed to `.prompt.md`.
- **Model list**: `--show-models` now shows only compatible models, sorted by
  name, numbered for selection.
- **Timestamps**: CLI listings show `YYYY-MM-DD HH:MM` (no epoch numbers).
- **Colors**: CLI listings use bold for emphasis, no dim/grey for info text.
- Prompts upgraded to v3 (no "ask questions" language, one-shot enforcement).

### Fixed

- **Critical**: TUI deadlock on WSL: uses plain threads + polling instead of
  textual's worker API (which deadlocks on WSL due to futex contention).
- **Critical**: TUI freeze on detail view: never calls `Static.update()`;
  uses screen replacement pattern instead.
- **Critical**: Terminal corruption on kill: signal handlers + atexit restore
  terminal state (mouse tracking, cursor visibility).
- Rich markup escaping for all user content (session titles, turn text).
- Search key passthrough (typing during `/` search no longer triggers bindings).
- Preview line width adapts to actual timestamp length per line.
- Subprocess timeouts (30s for detail export, 120s for recovery export).
- Textual rendering errors suppressed on exit (logged to `/tmp/orsession-errors.log`).

## [0.1.1] - 2026-06-02

### Security

- **F-02**: `ModelInfo.__repr__` now masks `api_key` (shows only first 4 chars)
  to prevent accidental secret exposure in logs, tracebacks, or debug output.
- **F-03**: HTTPS enforcement for API endpoints now uses `urllib.parse.urlparse`
  hostname validation instead of substring matching. Previously, a URL like
  `http://evil.localhost.attacker.com` could bypass the check. Now only
  `localhost`, `127.0.0.1`, and `::1` are accepted as local exceptions.

### Fixed

- **F-01**: Removed dead `base_url` assignment in `extract_models_from_config`
  (CLI script line 386). The value was immediately overwritten on the next line.
- **F-06**: Fixed license mismatch: `pyproject.toml` now correctly declares
  `BSD-3-Clause` to match the actual LICENSE file (was incorrectly set to MIT).
- **F-07**: Synced `COMPACTION_USER_PROMPT_TEMPLATE` in `orsession/core.py`
  with the full version from the CLI tool. The core version was missing detailed
  section instructions (sections 1-9, Agent Operating Guidance, Style), which
  meant TUI-generated compaction prompts were lower quality than CLI-generated ones.
- **F-10**: `orsession --version` now reads from `orsession.__version__` instead
  of a hardcoded string. Version will no longer drift between files.
- **F-13**: Moved `from datetime import datetime, timezone` from inside a method
  body in `CompactionScreen._run_compaction` to module-level imports.
- **F-04**: File Browser delete operations (`d` and `D`) now require confirmation
  via a second keypress. First press shows a warning notification; pressing the
  same key again confirms deletion.
- Fixed `ContextSelectionScreen._render` method name collision with textual's
  `Widget._render`. Renamed to `_render_context_ui`.

### Documentation

- **F-18**: README now documents the `orsession` TUI app (installation via
  `pip install .`, features, and usage). Clarified that the CLI tool remains
  stdlib-only while the TUI has `textual`/`rich` dependencies.
- **F-15**: SPEC updated from "curses-based TUI" to "textual-based TUI"
  throughout.
- **F-16**: SPEC file layout section updated to reflect actual package structure
  (`orsession/__init__.py`, `app.py`, `core.py` + `pyproject.toml`).
- **F-17**: SPEC acceptance criteria updated with checkmarks for implemented
  features and "deferred to v0.2" annotations for features not yet built
  (help overlay, session list search, fork indicator, in-content search,
  custom path input, recover-another-session sub-flow, save-elsewhere,
  JSON-lines logging).

## [0.1.0] - 2026-06-01

### Added

- Initial implementation of `orsession` TUI application with 8 screens:
  Session List, Session Detail, Full Preview, Recovery Wizard,
  Model Selection, Context Selection, Compaction, File Browser.
- `orsession/core.py` shared module extracted from CLI tool.
- `pyproject.toml` with textual/rich dependencies and `orsession` entry point.
- `opencode_recover_session.py` optionally imports from `orsession.core`
  when installed (fallback to bundled implementations).
- `SPEC-orsession.md` functional specification.
- Support for `{file:PATH}` syntax in opencode config for API keys.
