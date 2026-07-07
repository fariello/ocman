# ocman (OpenCode Manager)

`ocman` is a comprehensive command-line interface (CLI) and terminal user interface (TUI) administration suite for the [OpenCode](https://opencode.ai) agentic ecosystem. 

While it retains powerful capabilities for extracting and compacting crashed or bloated session transcripts, `ocman` serves as a complete database, configuration, and system maintenance manager for your OpenCode environment.

---

## Why ocman? (it actually reclaims the space)

OpenCode's SQLite database grows without bound and has no built-in cleanup, and OpenCode also
writes session-diff files to disk. The whole point of a "garbage collector" for it is to *actually
give the space back*: both the rows in the database and the bytes on disk.

`ocman` does this by **deleting the orphaned/old rows and their on-disk session-diff files and then
running `VACUUM`** to physically shrink the SQLite file, and it reports exactly how many bytes were
reclaimed (see `--clean`, `--clean-orphans`, and `ocman info`/`disk`).

This is why the project exists. In the author's own testing, the alternative
[`ocgc`](https://pypi.org/project/ocgc/) (OpenCode Garbage Collector, v0.1.0), which advertises that
it "reclaims" this storage, shrank a 2.9 GB database only to ~2.8 GB, while `ocman`'s orphan cleanup
brought the *same* database down to ~1.9 GB. Reclaiming space you asked to be reclaimed is the
baseline `ocman` is built to actually meet.

---

## Core Capabilities

*   **Interactive TUI Dashboard (`ocman ui` / `ocman gui`)**: A rich, multi-tab terminal application built with Textual to browse projects, view session details, preview transcripts, run recovery wizards, manage settings, and perform database admin tasks.
*   **Database Administration & Maintenance**: Tools to inspect database size, execute automated age-based session cleanup, prune orphaned database records, and vacuum SQLite databases to reclaim disk space.
*   **System Backup & Restoration**: ZIP-archive backup of database files, configurations, sidecar history ledgers, and session storage files. Features an automated rollback safety net that restores your system state to a temporary backup if a restore operation fails mid-way.
*   **Historical Activity Logs**: Sidecar audit trails tracking all cleanups, deletions, and recoveries. Shows detailed breakdowns for each run and cumulative, all-time historical statistics (sessions pruned, messages deleted, cost saved, and disk space saved) both in the TUI and CLI.
*   **Robust Session Recovery & LLM Compaction**: Parses native OpenCode export files, strips metadata noise, truncates transcripts safely, and optionally compacts context using OpenAI-compatible LLM gateway APIs (`--compact`) to produce clean restart files for fresh agent sessions.
*   **Flat-File Configuration**: Precedence-based configuration engine (`~/.config/opencode/ocman.toml`) with interactive setup helper (`--create-config`).

---

## TL;DR / Quickstart

### Launch the TUI Dashboard
```bash
# Launch the interactive terminal UI dashboard
ocman ui
# Or use the alias
ocman gui
```

### Common CLI Maintenance & Admin Commands
```bash
# Show database size, session counts, model usage, and storage info
ocman info

# Clean sessions older than 7 days and reclaim database disk space
ocman --clean --days 7

# Scan and delete all orphaned database records/files
ocman --clean-orphans

# View historical deletion/recovery runs and all-time grand totals
ocman show logs

# Create a complete ZIP backup of your OpenCode system state
ocman --backup-opencode

# Restore your OpenCode system state from a backup ZIP file (with rollback safety)
ocman --restore ~/.local/share/opencode/backups/backup.zip
```

### CLI Session Recovery
```bash
# Recover interactively (lists sessions, lets you pick one)
ocman

# Recover a specific session, truncating to the last 50 exchanges
ocman -s SESSION_ID -mi 50

# Recover, truncate, and compact using an LLM gateway model
ocman -s SESSION_ID -mi 50 --compact uri/its_direct/pt1-qwen3-32b-us
```

> [!TIP]
> **Compacted files land in your project's prompts.** When you recover with `--compact` and the
> project you're recovering for uses the `.agents` convention (has `.agents/plans/` or
> `.agents/prompts/`), ocman also copies the LLM-generated `*.compacted.md` (the document a fresh
> agent reads) into `<project>/.agents/prompts/pending/` as `YYYYMMDD-HHMM-<session_id>.compacted.md`
> (timestamp = session last-updated, local time). A pre-existing copy is backed up to `*.compacted.bu.NNN.md`. The
> "project" is `--session-dir` if given, else the session's recorded directory, else the current
> directory. This only applies when compaction runs (a plain recovery copies nothing). Disable
> per-run with `--no-project-prompt`, or globally via `copy_restart_to_project_prompts = false`.

> [!NOTE]
> **Upgrading from an older ocman?** Recovery files are now named
> `YYYYMMDD-HHMM-<session_id>.<kind>.md` (local time). Older files (e.g.
> `opencode-YYYYMMDD-HHMMSS-<id>...`) still work as-is; to normalize them on disk, run
> `python scripts/migrate_recovery_names.py <dir> --dry-run` to preview, then again without
> `--dry-run` to apply. It never deletes a source and skips files already in the canonical form.

---

## Installation

### Prerequisite Dependencies
*   **CLI tool (`ocman` / `ocman.py`)**: Zero external dependencies; requires only Python 3.10+ and the `opencode` CLI on your `PATH`.
*   **TUI app (`ocman ui` / `ocman gui`)**: Requires the Python packages `textual` and `rich`.

### Installation Methods

#### 1. From PyPI (Recommended)
You can install `ocman` directly from PyPI:
```bash
pip install ocman
```

#### 2. From Source
To install the latest development version:
```bash
git clone https://github.com/fariello/ocman.git
cd ocman
pip install .
```

#### 3. Standalone Script (Zero-Dependency CLI Mode)
If you only need the CLI recovery features without the interactive TUI dashboard, you can run the standalone python script directly:
```bash
chmod +x ocman.py
./ocman.py --help
```


---

## The TUI Dashboard (`ocman ui`)

The interactive terminal user interface organizes your workflow across several tabbed workspaces:

1.  **Projects & Sessions**: Browse through workspace project directories and see active session trees. Shows session metadata, tokens count, and accumulated costs.
2.  **Session Preview**: Drill down into the selected session to inspect details or preview the scrollable conversation transcript.
3.  **Recovery Wizard**: Configure truncation boundaries (by line limit or user-agent interaction count), select a target LLM model with live cost estimation, and generate compacted files.
4.  **Database Admin**: Review database family details (WAL, SHM, database integrity), execute vacuums, and run backup or restoration threads directly with progress indicators.
5.  **Activity Log**: Browse detailed histories of past cleanups/recoveries, including a persistent `GRAND TOTALS` card summarizing all-time disk space saved, cost reclaimed, and pruned databases rows.
6.  **Configuration Settings**: Customize system settings (paths, LLM gateway parameters, retention defaults) with live auto-saving.

---

## CLI Command Usage & Examples

### Command Preprocessing
`ocman` intercepts natural subcommands at the CLI level for convenience. Positional commands are parsed and converted to internal flags:
*   `ocman list projects` or `ocman list porjects` $\rightarrow$ `--list-projects`
*   `ocman list sessions` $\rightarrow$ `--list-sessions`
*   `ocman list sessions in [project] my-project` $\rightarrow$ `--list-sessions --project "my-project"`
*   `ocman show logs` $\rightarrow$ `--show-logs`
*   `ocman disk` or `ocman du` $\rightarrow$ `--info --by-project`
*   `ocman delete project [name]` $\rightarrow$ `--delete-project [--project name]`

### Database & Storage Status (`ocman info`)
Prints a breakdown of your current database state on disk, including the SQLite database
family size, session-diff file storage, and a **Backups (Disk Storage)** section showing
the total size, count, and age range of your backups directory:
```bash
ocman info
# Add -v to trigger a SQLite database PRAGMA integrity check
ocman info -v

# Add a per-project on-disk breakdown (session-diff bytes + session/message/token counts)
ocman info --by-project
# Or the natural-language alias:
ocman disk
```
> [!NOTE]
> Per-project figures cover **session-diff files only**. The SQLite database is a single
> shared file, so its bytes are not attributable to an individual project.

### Historical Auditing (`ocman show logs`)
Outputs a list of past cleanups and recoveries in reverse chronological order, ending with a comprehensive all-time totalization card:
```bash
ocman show logs
```

### Automated Configuration Generator (`ocman --create-config`)
Runs an interactive setup assistant to generate a config file at `~/.config/opencode/ocman.toml`. If run non-interactively (e.g., in a script), it creates the config file with safe defaults.
```bash
ocman --create-config
```

---

## Argument Reference

| CLI Option | Equivalent | Description |
|:---|:---|:---|
| `-s ID` | `--session ID` | Session ID (skips interactive selection during recovery) |
| `-d DIR` | `--session-dir DIR` | Target project working directory where the session ran |
| `-o DIR` | `--out DIR` | Output directory for recovery files (default: `./opencode-recovery`) |
| `-k` | `--keep-temp` | Keep the raw exported JSON file for debugging |
| `-ct` | `--clean-tmp` | Prune old exported JSON temporary files from `/tmp` |
| `-cp` | `--clean-previous` | Remove prior recovery outputs generated for this session |
| `-t` | `--include-tools` | Include tool execution results and tool call messages |
| | `--all-roles` | Extract system and tool roles (not just user/assistant) |
| `-ml N` | `--max-lines N` | Maximum transcript lines to output (truncates older turns) |
| `-mi N` | `--max-interactions N`| Maximum user-assistant turn pairs to keep |
| `-ic FILE` | `--input-compact FILE` | Prepend a prior recovery summary as context (repeatable) |
| `-ir FILE` | `--input-restart FILE` | Prepend a prior restart file as context (repeatable) |
| `-it FILE` | `--input-transcript FILE` | Prepend a prior transcript as context (repeatable) |
| `-oc FILE` | `--output-compact FILE`| Output path for the compaction prompt file |
| `-or FILE` | `--output-restart FILE`| Output path for the restart file |
| `-ot FILE` | `--output-transcript` | Output path for the clean transcript |
| `-sm` | `--show-models` | List available LLM models from config with compatibility |
| | `--show-compaction-prompt` | Print the compaction prompt that would be sent, then exit |
| `-C [MODEL]`| `--compact [MODEL]` | Triggers LLM compaction. Prompted if MODEL is omitted |
| `-lp` | `--list-projects` | List all projects in the database |
| `-ls` | `--list-sessions` | List sessions (optionally for `-P/--project`) |
| `-P NAME` | `--project NAME` | Filter/select by project (name or ID) |
| `-A` | `--all-sessions` | Include subagent/child sessions (hidden by default) |
| `-D` | `--details` | Show detailed session metadata in listings |
| `-H N` | `--head N` | Show the first N sessions in a listing |
| `-T N` | `--tail N` | Show the last N sessions in a listing |
| | `--show-logs` | Show historical activity runs + all-time totals (`ocman show logs`) |
| | `--clean` | Delete database sessions older than the retention window |
| | `--days N` | Set cleanup retention window in days; accepts fractions, e.g. `0.25` = 6 hours (default: 5) |
| | `--clean-orphans` | Remove orphaned records and sidecar diffs |
| | `--db PATH` | Override standard SQLite database file path |
| | `--delete` | Recursively delete the session specified by `-s` |
| | `--delete-project`| Recursively delete the project specified by `-P` (includes all project sessions/files/DB rows) |
| | `--dry-run` | Run cleanup/delete tasks without writing changes |
| | `--force` | Bypass active process lock checks during delete/cleanup |
| | `--info` | Show database and storage usage information (incl. backups disk usage) |
| | `--by-project` | With `info`: add a per-project on-disk session-diff usage breakdown |
| | `--no-project-prompt` | Do not copy the compacted file (from `--compact`) into the project's `.agents/prompts/pending/` |
| | `--clear-history` | Wipes the historical activity ledger and resets totals (asks for confirmation; `--force` bypasses) |
| | `--create-config` | Interactively generate the `ocman.toml` file |
| | `--backup-opencode` | Create a system backup archive ZIP file |
| | `--restore PATH` | Restore configuration, database, and diffs from backup |
| | `--clean-backups` | Prune old backups (pair with `--days N`); previews a KEEP/DELETE table before deleting (see Pruning Backups) |
| | `--move-project PATH`| Relocate a project (re-assign worktree path in DB and disk) |
| | `--move-session ID` | Relocate a single session |
| | `--to PATH` | Destination path for moves, rebasing, and session exports |
| | `--metadata-only` | Update DB project/session paths only, bypassing disk move |
| | `--rebase-paths` | Bulk rebase DB workspace path prefixes (requires --from and --to) |
| | `--from PATH` | Source prefix path for bulk rebasing |
| | `--export-session ID`| Export a session and subagents to a portable `.ocbox` bundle |
| | `--import-session PATH`| Import a session from a portable `.ocbox` bundle |
| | `--to-project ID` | Remap imported session to an existing project ID |
| | `--new-project-path PATH`| Remap imported session to a new project worktree path |
| | `filter FILE` | Re-scope a recovery/compacted document to one project/scope via the LLM (command). Requires `-P/--project` and/or `--scope`; reuses `-C/--compact` for model and `-oc` for output. Written next to the source (or `-oc`) as `YYYYMMDD-HHMM-<session_id>.<scope>.compacted.md`. Input is size-capped (`filter_max_bytes`) and scanned for secrets/PII before sending. |
| | `--scope "TEXT"` | With `filter`: free-text scope of content to keep (e.g. `"ocman only"`) |
| | `--allow-secrets` | Bypass the pre-egress secret/PII scan for `filter` and `--compact` (send content even if a likely secret is detected). |
| `-v` | `--verbose` | Increase log verbosity (`-v` or `-vv`) |
| `-V` | `--version` | Print the ocman version and exit |

---

## Configuration Settings (`ocman.toml`)

`ocman` searches for configuration settings at `~/.config/opencode/ocman.toml`. Precedence follows: **Defaults < Config File < CLI arguments**.

### Default Layout Template
```toml
# SQLite Database Path
db_path = "~/.local/share/opencode/opencode.db"

# Historical Metrics JSON ledger path
history_path = "~/.local/share/opencode/ocman_history.json"

# Output directory for recovery files
default_out_dir = "./opencode-recovery"

# Default backup destination directory
default_backup_dir = "~/.local/share/opencode/backups"

# Default LLM model used for compaction (empty = you are prompted / pick at compaction time)
default_compaction_model = ""

# Default retention window in days for database cleanups
default_retention_days = 5

# Maximum detailed run records kept in the activity history ledger (0 = unlimited).
# Cumulative all-time totals are always preserved; only the per-run detail list is capped.
history_max_runs = 500

# When recovering with --compact, also copy the generated *.compacted.md (the doc a fresh agent
# reads) into the working project's .agents/prompts/pending/ if that project uses the .agents
# convention. Only applies when compaction runs (--no-project-prompt overrides).
copy_restart_to_project_prompts = true

# CLI and recovery behavior settings
keep_temp = false
include_tools = false
all_roles = false

# Egress guards for `filter` and `--compact` (content sent to the LLM API).
# Max input bytes before refusing (override per-run with --force). Default: 5242880 (5 MB).
filter_max_bytes = 5242880
# Secret/PII pre-egress scan: "conservative" (high-signal patterns) or "aggressive"
# (also bare keywords, for sensitive environments). A hit stops the send unless
# --allow-secrets is passed. Default: conservative.
filter_secret_scan = conservative
```

---

## Backup & Restoration Internals

### Backup Scope
The backup operation archives:
*   The SQLite database file (`opencode.db`) and write-ahead logs (`-wal`/`-shm`) if present.
*   The flat-file settings (`ocman.toml`).
*   The audit ledger (`ocman_history.json`).
*   All individual session JSON logs under `~/.local/share/opencode/storage/session_diff/`.

### Rollback Protection
Before executing a restoration, `ocman` packages the existing active state into a temporary archive (`~/.local/share/opencode/backups/rollback-before-restore-TIMESTAMP.zip`). If any stage of the restoration (file unpacking, database overwriting, config validation) throws an error, the rollback routine immediately triggers to extract the temporary rollback file, leaving your system state completely safe and unmodified.

### Pruning Backups (`ocman --clean-backups`)
`ocman --clean-backups --days N` prunes old backups. Before deleting anything it prints a
table of **all** backups, each tagged **DELETE** (past the retention window) or **KEEP**,
with a right-aligned Size column and last-modified time, plus a running "N to delete, M kept"
summary. If the prune would remove **every** backup, it prints a forceful warning that no
rollback backups will remain. With many retained backups the KEEP rows are summarized; use
`-v` to list them all. `--days` accepts fractions (e.g. `0.25` = 6 hours).

---

## Known Limitations

*   **Large session exports/recovery**: Recovery and compaction load the full exported session
    transcript into memory. Very large sessions (tens of MB or more) can therefore use several times
    that amount of RAM on constrained hosts. Portable `.ocbox` exports themselves stream to disk in
    batches and are not affected.

## Development & Test Verification

Run the test suite using `pytest`. The tests mock database instances and isolate file writes to verify config logic, TUI states, auto-saving hooks, and backup engines safely:

```bash
PYTHONPATH=. pytest
```

> [!IMPORTANT]
> **Module Resolution**: Always run `pytest` with `PYTHONPATH=.` prefix (or install the package in editable dev mode with `pip install -e .[dev]`). Otherwise, Python might resolve imports from the globally installed PyPI package instead of the local workspace directory, causing `ImportError` or test resolution errors.

### Performance benchmarks (opt-in)

Informational performance benchmarks live in `tests/test_perf.py`. They are skipped by
default (so they never gate CI) and print timings when explicitly enabled:

```bash
OCMAN_BENCHMARK=1 PYTHONPATH=. pytest tests/test_perf.py -s
```


---

## License, Attribution & Citation

`ocman` is licensed under the **Apache License 2.0** (see `LICENSE` and `NOTICE`).

**Attribution (required).** Under Apache-2.0 §4(d), any distribution of this software or a
derivative work must retain the `NOTICE` file and display its attribution reasonably
prominently. Concretely, derived/redistributed works must include the following, visibly,
in the project README (or equivalent top-level documentation) and in any "About"/credits
screen the software presents:

> Based on the original ocman by Gabriele G. R. Fariello (https://github.com/fariello/ocman).

**Citation.** If you use `ocman` in academic or scholarly work, please cite it. GitHub's
"Cite this repository" button (backed by `CITATION.cff`) provides ready-to-use formats. A
suggested citation:

> Fariello, Gabriele G. R. *ocman (OpenCode Manager)*. 2026. https://github.com/fariello/ocman

The attribution and citation requests impose no warranty or liability on the author; the
software is provided "AS IS" per the LICENSE.
