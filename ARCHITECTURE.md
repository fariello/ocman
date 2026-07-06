# Architecture

This document orients a new engineer (or an LLM with no prior context) to how `ocman`
is built and why. For *usage*, see `README.md`; for *changes over time*, see `CHANGELOG.md`.

## What ocman is

`ocman` (OpenCode Manager) is a single-user, local administration suite for the
[OpenCode](https://opencode.ai) ecosystem. It browses, recovers, and compacts opencode
sessions stored in a local SQLite database, and manages that database, its configuration,
and related on-disk state (backup/restore, cleanup, project/session move, and portable
export/import).

## Entry points

- **CLI — `ocman.py`** (console script `ocman`, defined in `pyproject.toml`). A single,
  self-contained module. Its `main()` parses arguments (`parse_args`), which first rewrites
  natural-language commands (`preprocess_argv`, e.g. `ocman list projects` → `--list-projects`)
  and then dispatches to the requested operation. The positional command accepts
  `info`, `help`, `ui`, `gui`, and `filter` (`ocman filter <input.md>` re-scopes a recovery
  document to one project/scope via the LLM); `preprocess_argv` additionally rewrites
  natural-language commands (`disk`/`du`, `delete project`, `list projects`/`list sessions
  [in …]`, `show logs`) into their equivalent flags.

  Recovery artifacts share a canonical local-time name `YYYYMMDD-HHMM-<session_id>.<kind>.md`
  (`kind` = transcript/restart/prompt/compacted); `canonical_recovery_name`/`parse_recovery_name`
  are the single source of truth, and `scripts/migrate_recovery_names.py` normalizes files
  written by older versions.
- **TUI — `ocman_tui/`** (a Textual application). Launched via `ocman ui` / `ocman gui`.
  `ocman_tui/app.py` holds `OrsessionApp` (the app) and its modal screens; `widgets/`
  holds tab widgets (database admin, sidebar, models); `css/` holds the Textual stylesheets.

### CLI/TUI relationship (important)

The TUI does **not** reimplement business logic. `ocman_tui/core.py` imports the CLI
functions from `ocman` (DB access, export/import, move, compaction, backup/restore,
config) and the TUI calls them. This keeps a single implementation of every operation.
Long-running operations run on background threads (`run_worker(..., thread=True)`), and
UI updates from those threads are marshalled back onto the Textual event loop with
`self.app.call_from_thread(...)` (note: `call_from_thread` lives on the `App`, not on a
`Screen`).

## Data contracts

- **SQLite database** (`~/.local/share/opencode/opencode.db` by default). The relevant
  tables and their session foreign-key columns are enumerated centrally in
  `SESSION_RELATIONAL_TABLES` in `ocman.py`; all delete/export/import/cleanup logic iterates
  that list, so table identifiers are never taken from untrusted input.
- **`.ocbox` export bundle** (a ZIP, `export_version: 2.0`): `meta.json`,
  one `db_data/<table>.jsonl` per relational table (streamed in batches to keep memory flat),
  and `session_diffs/<session_id>.json` storage files. Import validates session-ID format
  (`^[a-zA-Z0-9_\-]+$`), validates/allowlists table and column names, and remaps IDs on
  collision. A legacy `db_data.json` single-blob format is still accepted on import.
- **Backup ZIP**: the database family (`.db`/`-wal`/`-shm`), `ocman.toml`,
  `ocman_history.json`, and session `session_diff/*.json` files.
- **`ocman.toml`** (`~/.config/opencode/ocman.toml`): flat config with the keys in
  `DEFAULT_CONFIG`. Precedence is Defaults < config file < CLI arguments.
- **`ocman_history.json`**: an append-only sidecar ledger of cleanup/deletion/recovery runs,
  surfaced as per-run and grand-total activity logs.

## Cross-cutting design patterns

- **Rollback-safety first.** Every destructive operation (delete, move, restore) takes a
  backup of the affected state *before* acting and restores it if any step fails. Deletes
  run inside a SQLite transaction and print copy-paste rollback instructions.
- **Untrusted input is validated at the boundary.** Import validates IDs/table/column names;
  restore validates ZIP member paths before extraction (Zip-Slip protection). SQL uses
  parameterized values with hardcoded/allowlisted identifiers.
- **Connections are closed deterministically** via `try/finally` around each DB operation.
- **Destructive-confirmation seam.** Destructive commands present their outcome and confirm
  through one shared seam in `ocman.py`: a `DestructivePreview`/`PreviewItem` data model, a
  pure `render_destructive_preview()` (a color-independent table with headers, a right-aligned
  Size column, and a `DELETE`/`KEEP` `Action` word per item — color is enhancement only — plus a
  forceful "this will ... ALL N ..." warning when nothing is kept), and a `confirm_destructive()`
  I/O function that owns the typed-`yes` prompt and honors `dry_run`/`assume_yes`.   New destructive
  operations should build a `DestructivePreview` and call these rather than hand-rolling a prompt.
  Adopters: `--clean-backups` (full KEEP/DELETE preview), session/project delete, the age-based
  cleanup/orphan prune, and `--clear-history` (now confirmed; `--force` bypasses). The delete/prune
  ops keep printing their own detailed row/file listing and call `confirm_destructive(..., render=False)`
  so the seam owns only the dry-run/irreversible/typed-`yes` tail.
  Note: a `force` flag bypasses only the running-`opencode` process-lock, never the typed-`yes`
  prompt — the prompt is skipped only via `confirm_destructive(assume_yes=...)`, wired from an
  op's existing prompt-skip condition (e.g. the delete functions' `confirm=False`, used by the TUI).

## Design principles

- **Intuitive / self-documenting.** Rich `--help` (short forms + worked examples),
  natural-language commands, `--create-config`, typed confirmations on destructive actions,
  and actionable output. Users should learn it as they go.
- **Configurable over hardcoded.** Paths, retention, and model selection come from
  `ocman.toml` with CLI overrides; the DB table model is centralized, not special-cased.
- **KISS.** The CLI is intentionally one dependency-light module (standard library only for
  the CLI path; the TUI adds `textual`/`rich`). A monolith is a deliberate trade-off for a
  single-maintainer personal tool over premature modularization.
- **Honest documentation.** Docs describe current behavior; the changelog tracks each release.

## Testing

`PYTHONPATH=. pytest` runs the suite (`tests/`), covering config, backup/restore (including
rollback and Zip-Slip rejection), export/import (including SQL-injection and path-traversal
rejection), move, core, and TUI flows. CI runs this matrix across ubuntu/macos/windows and
Python 3.10-3.14.
