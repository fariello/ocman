# Changelog

## [Unreleased]

### Added
- **`--clear-history` now confirms before wiping:** it previously erased the activity ledger and
  all-time totals with no prompt. It now shows how many run records will be erased and requires a
  typed `yes`; `--force` bypasses the prompt for scripts.

### Changed
- **Unified destructive-action confirmations:** session delete, project delete, and the age-based
  cleanup/orphan prune now confirm through the shared destructive-confirmation seam (consistent
  typed-`yes` handling). Behavior is unchanged — in particular `--force` still only bypasses the
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
  bytes are intentionally not reported — the SQLite database is a single shared file.

## [1.0.4] - 2026-07-04

### Fixed
- **TUI compaction:** The TUI LLM-compaction action was non-functional — it called
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
- **Performance — session import:** Collision-time id remapping is a single structural
  pass instead of an O(diffs × ids) per-id whole-string replace (~26× faster per diff on
  a 300-session subtree in local measurement).
- **Performance — move/rebase:** `db_move_project_metadata`, `db_move_session_metadata`,
  and `db_rebase_paths` share one directory-rebasing helper (resolves prefixes once);
  behavior is unchanged.
- **Performance — export:** Table JSONL is staged in a per-run temp directory (unique
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
- **TUI**: Project switching (`g` key) — browse all projects from database.
- **TUI**: Session deletion (`d` key, then `y` to confirm).
- **TUI**: Subagent session toggle (`a` key) — hidden by default, shown with ⤷.
- **TUI**: Session Detail redesign — fixed header, scrollable exchanges,
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

- **Critical**: TUI deadlock on WSL — uses plain threads + polling instead of
  textual's worker API (which deadlocks on WSL due to futex contention).
- **Critical**: TUI freeze on detail view — never calls `Static.update()`;
  uses screen replacement pattern instead.
- **Critical**: Terminal corruption on kill — signal handlers + atexit restore
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
- **F-06**: Fixed license mismatch — `pyproject.toml` now correctly declares
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
