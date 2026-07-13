# Changelog

## [Unreleased]

### Added
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
