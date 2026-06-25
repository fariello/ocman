# Changelog

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
