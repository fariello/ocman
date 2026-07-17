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
  run inside a SQLite transaction and print copy-paste rollback instructions. For multi-file
  restores, a single pre-batch safety backup is taken, and if any restore fails, the entire
  batch is rolled back to that original state.
- **One batch, one report.** Multi-session and project-expanded deletes go through
  `db_delete_sessions_batch`, which shares a single process-lock check, ONE family backup,
  ONE transaction, ONE `VACUUM`, ONE metrics write, and ONE consolidated grand-total report
  for the whole batch (rather than repeating them per session). The low-level row delete is
  factored into `_delete_session_rows` so both the single-session path
  (`db_delete_session_recursive`, whose output is unchanged) and the batch path reuse the
  same primitive. Empty-project cleanup (removing a `project` row plus its
  `project_directory`/`workspace` rows) happens inside that same transaction, but only for
  projects the user explicitly targeted (passed as `remove_project_ids`), never inferred
  from "0 sessions remain".
- **Git-aware, print-first cross-machine move.** `ocman move SPEC to DST` gathers every decision
  up front into a `MovePlan` (parsed dest, git decisions, transfer style, collision choice), asks a
  single confirmation, then acts. A local DST keeps the transactional dir-move plus DB-rebase (with
  rollback), fronted by up-front git-state handling (`git_state`/`run_git`, the first git integration;
  argv only, never a shell) and a destination-collision menu (existing dest can be backed up to a
  distinct `move-dest-backup-*`, replaced, or overlaid). A remote DST (`host:/path`) performs NO
  network I/O: it renders a shell-quoted runbook via `MovePlan.render_runbook()` and an ordered
  `TransferStep` list (the seam a future execute-mode would reuse). Interpolated values are
  `shlex.quote`-escaped; the local copy is never auto-deleted on a remote move (a guarded
  `--confirm-remote-delete` handles that after verification). Git remote/upstream is never guessed;
  submodule/LFS/bare-repo cases are out of scope.
- **Formatting is centralized.** `fmt_int` (comma-separated integers with optional width) and
  `fmt_cost` (`$` + comma-separated, fixed decimals) are the shared number/currency formatters used by
  the listing and disk-reporting output; both coalesce `None`/bad input to 0 so display never crashes.
- **Running-instance detection is observe-only.** `ocman list running` enumerates
  OpenCode processes (`detect_running_opencode(broad=True)` matches the `opencode`
  executable, not just `--continue`), maps listeners to pids via the kernel socket
  table (`ss -tlnpH`, IPv6-safe parse), and classifies a listener's auth from the
  process environment (`OPENCODE_SERVER_PASSWORD` presence, read owner-only from
  `/proc/<pid>/environ`, value never printed). Own-ness is decided by UID
  (`os.stat(/proc/<pid>).st_uid`), NOT the ps username (which ps truncates). It never
  calls state-changing endpoints, never reads another user's `/config`, and the only
  optional network action is a read-only `GET /app` (`--probe`) against your own
  loopback listeners. Detection FAILS LOUD (raises `RunningDetectionError` ->
  explicit "could not determine" message) rather than printing an empty list that
  reads as "all clear". Session/project attribution is reported with provenance
  (argv hint / DB lookup / directory one-to-many), never a fabricated 1:1.
- **Accessibility: no low-contrast text; color is never the sole signal.** Do NOT use the ANSI faint
  attribute (`\033[2m`) or Rich/Textual `dim` for text; it fails contrast expectations and is
  near-invisible on some terminals. Secondary information is conveyed by wording (and, in the TUI, a
  defined readable palette color such as `#a6adc8`), never by reduced contrast. `color_dim`/`_h_dim` are
  retained as no-op passthrough shims so call sites need not change. Color output is gated by
  `_color_enabled()` (stderr) and `_help_color_enabled()` (stdout) with identical precedence: `NO_COLOR`
  wins (off), else `FORCE_COLOR` forces on, else `TERM != dumb` and a TTY. Any information carried by
  color must remain fully meaningful with color stripped.
- **Historical metrics are global-only.** Deleted-session cost/token totals come from the deletion
  history sidecar, which has no `project_id`, so they are never attributed per project; per-project
  reporting (`list projects`, `disk --by-project`) shows *active* figures only, with historical kept as
  a single global line in `db info`'s Usage Metrics.
- **Untrusted input is validated at the boundary.** Import validates IDs/table/column names;
  restore validates ZIP member paths before extraction (Zip-Slip protection). SQL uses
  parameterized values with hardcoded/allowlisted identifiers. During single-session import,
  generating a new session ID routes through the existing structural ID-remap logic to consistently
  translate references across tables and sidecar JSON files.
- **Connections are closed deterministically** via `try/finally` around each DB operation.
- **Egress guards and safe secret redaction.** Outbound LLM payloads are scanned for secrets/PII. Users can view detections (`--show-secrets` context masked, or `--show-secrets=raw` requiring TTY confirmation). Detections can be redacted outbound via `--expunge-secrets` and optionally scrubbed from on-disk recovery outputs. Redaction runs on copies only; original transcripts, logs, and database records are never modified, and secret values are never logged.
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

- **Large-session chunking (`chunk_turns` + `part_recovery_name`).** `recover`/`compact`
  can split a large session into ordered parts instead of truncating. The pure seam
  `chunk_turns(turns, max_interactions=, max_lines=)` groups turns by the same
  interaction-boundary rule as `count_interactions` (a new interaction starts on a
  user turn whose predecessor was not a user turn) and packs whole interactions into
  each part up to the size limits; it never splits a turn or an interaction, and an
  oversized single interaction ships as its own part (nothing is dropped). Part files
  are named by `part_recovery_name(sid, dt, kind, part, total)` =
  `YYYYMMDD-HHMM-<sid>.part-NNofMM.<kind>.md` (zero-padded to the width of `total`;
  `total==1` yields the plain canonical name). This reuses the filter `.<scope>`
  sub-segment convention, and `parse_recovery_name` strips one trailing segment so both
  the chunk and filter forms round-trip to the bare session id. `recover --chunk`
  writes N transcript/restart/prompt sets; `compact --chunk` runs `run_compaction`
  (with an `output_name` per part) once per part and aggregates the cost table. Export
  (.ocbox) is intentionally NOT chunked (a bundle is DB rows for wholesale import, not
  readable/LLM text). The interactive `prompt_for_truncation` now returns a
  `LargeSessionChoice(mode=full|truncate|chunk, max_lines, max_interactions)`.

- **Running-OpenCode mutation guard (`require_safe_to_mutate`).** OpenCode has no
  cross-process session lock, so mutating the shared DB/files while an instance runs can
  corrupt state. Every mutating op routes through `require_safe_to_mutate(action, while_running=...)`
  before touching the DB: it calls `detect_running_opencode_status(broad=True)`, which
  returns a three-state signal (`some` / `none` / `unknown`). `none` proceeds silently
  (the unchanged happy path); `some` lists the instances and refuses (non-interactive) or
  asks for a typed `yes` (interactive), unless `while_running` (the `--while-running` /
  `--force` flag) is set; `unknown` fails CLOSED on Linux (refuse unless `while_running`)
  and fails OPEN with a printed caveat elsewhere. `check_opencode_process_lock(force=...)`
  is a thin back-compat shim over this guard (`force -> while_running`). Adopters: the
  delete/clean/orphan-prune ops (via the shim), plus session/project move, session/project
  import, backup restore, and db rebase (which call the guard directly). The TUI delete/move
  paths pass `force=True` (user already confirmed in a modal), so the guard proceeds without
  a blocking `input()`; ocman never fires a raw stdin prompt under Textual. Tests neutralize
  the guard by default (autouse `conftest` fixture reports "none running") so the suite is
  host-independent; guard-specific tests opt out with `@pytest.mark.real_process_detection`.

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
