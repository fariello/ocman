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

- **CLI (`ocman.py`)** (console script `ocman`, defined in `pyproject.toml`). A single,
  self-contained module. It uses a noun-based, git/kubectl-style subcommand grammar:
  `ocman <group> <action> [options]`, where the groups are `session`, `project`, `db`,
  `backup`, `history`, and `config` (e.g. `ocman session recover ID`, `ocman db clean`).
  A handful of top-level verbs are kept as aliases (`search`, `info`, `disk`, `logs`,
  `models`, `compaction-prompt`, `filter`, `move`, `export`, `ui`/`gui`, `help`).
  `build_parser()` builds the parser tree; `main()` parses arguments (`parse_args`) and
  `_normalize()` folds the parsed subcommand namespace back into a flat namespace that
  `main()` dispatches on. Global options (`--db`, `-v/--verbose`, `-V/--version`,
  `-h/--help`) work on any subcommand, before or after it. Per-command `-h` prints that
  command's own argparse-generated usage; only the root `-h`/`help` use the curated
  verb-first renderer (`build_help`).

  `preprocess_argv` applies natural-language sugar on top of the grammar: word-order list
  aliases (`list projects` / `list sessions [NAME]`), the optional `to` keyword for
  `move`/`export` (`move X to Y` == `move X Y`), and an `in [project|session] NAME` phrase in
  `search`/`session search`. Shared helpers keep behavior consistent: `resolve_targets()`
  resolves multiple specifiers that could be projects, sessions, or models, handling
  kind-qualified prefixes (`session:SPEC`, `project:SPEC`, `model:SPEC`) to bypass auto-detection.
  Resolution happens within command handlers in `main()` (not during normalization) to allow for
  interactive TTY prompting and detailed non-interactive ambiguity errors.
  `resolve_target()` remains as a single-target legacy wrapper. `resolve_model_spec()` resolves model specifiers.
  `parse_duration_to_days()` parses `--older-than`/positional durations (`2h`, `5d`, `6w`,
  `6mo`, `1y`, or spelled-out `"30 days"`; `mo`/`y` are approximate). The legacy `--days` is a
  hidden alias of `--older-than`.  `backup create` supports writing per-target `.ocbox` bundles to a directory with `--to DIR`, in addition to streaming progress for full ZIP backups. `backup restore` streams the same progress during configuration and database restore.

  Recovery artifacts share a canonical local-time name `YYYYMMDD-HHMM-<session_id>.<kind>.md`
  (`kind` = transcript/restart/prompt/compacted); `canonical_recovery_name`/`parse_recovery_name`
  are the single source of truth, and `scripts/migrate_recovery_names.py` normalizes files
  written by older versions.
- **TUI (`ocman_tui/`)** (a Textual application). Launched via `ocman ui` / `ocman gui`.
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
- **`.ocbox` export bundle** (a ZIP): `meta.json`, one `db_data/<table>.jsonl` per relational
  table (streamed in batches to keep memory flat), and `session_diffs/<session_id>.json`
  storage files, all written by the shared `_write_ocbox` packer. A **session** bundle
  (`export_version: 2.0`, no `kind`) covers `SESSION_RELATIONAL_TABLES` for one session
  subtree. A **project** bundle (`export_version: 3.0`, `kind: "project"`,
  `main_session_id: null`) additionally covers the project-scoped tables
  (`PROJECT_RELATIONAL_TABLES`: `project`, `project_directory`, `workspace`) and every session
  in the project. Import auto-detects the kind (a missing `kind` means a session bundle, so
  legacy `.ocbox` files still import), validates session-ID and project-ID format
  (`^[a-zA-Z0-9_\-]+$`) and the project worktree (absolute, no traversal), allowlists table and
  column names, and remaps session IDs on collision. Project import resolves project identity
  independently (prompt / `--to-project` / `--new-project-path` / non-interactive refusal),
  inserts the project row inside the import transaction (no orphan on failure), and never runs
  project/workspace ids through the session id map. A legacy `db_data.json` single-blob format
  is still accepted on session import.
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
  Size column, and a `DELETE`/`KEEP` `Action` word per item (color is enhancement only), plus a
  forceful "this will ... ALL N ..." warning when nothing is kept), and a `confirm_destructive()`
  I/O function that owns the typed-`yes` prompt and honors `dry_run`/`assume_yes`.   New destructive
  operations should build a `DestructivePreview` and call these rather than hand-rolling a prompt.
  Adopters: `backup clean` (full KEEP/DELETE preview), session/project delete, the age-based
  cleanup/orphan prune, and `history clear` (now confirmed; `--force` bypasses). The delete/prune
  ops keep printing their own detailed row/file listing and call `confirm_destructive(..., render=False)`
  so the seam owns only the dry-run/irreversible/typed-`yes` tail.
  Note: a `force` flag bypasses only the running-`opencode` process-lock, never the typed-`yes`
  prompt. The prompt is skipped only via `confirm_destructive(assume_yes=...)`, wired from an
  op's existing prompt-skip condition (e.g. the delete functions' `confirm=False`, used by the TUI).

## Design principles

- **Intuitive / self-documenting.** A noun-based subcommand CLI (`ocman <group> <action>`,
  git/kubectl-style) with a custom verb-first help renderer (`ocman help` and per-command
  `-h`) instead of the raw argparse dump, `config create`, typed confirmations on destructive
  actions, and actionable output. Users should learn it as they go.
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
