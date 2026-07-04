# ocman (OpenCode Manager)

`ocman` is a comprehensive command-line interface (CLI) and terminal user interface (TUI) administration suite for the [OpenCode](https://opencode.ai) agentic ecosystem. 

While it retains powerful capabilities for extracting and compacting crashed or bloated session transcripts, `ocman` serves as a complete database, configuration, and system maintenance manager for your OpenCode environment.

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

---

## Installation

### Prerequisite Dependencies
*   **CLI tool (`ocman` / `ocman.py`)**: Zero external dependencies—requires only Python 3.10+ and the `opencode` CLI on your `PATH`.
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

### Database & Storage Status (`ocman info`)
Prints a breakdown of your current database state on disk, including:
```bash
ocman info
# Add -v to trigger a SQLite database PRAGMA integrity check
ocman info -v
```

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
| `-or FILE` | `--output-restart FILE`| Output path for the restart file |
| `-ot FILE` | `--output-transcript` | Output path for the clean transcript |
| `-sm` | `--show-models` | List available LLM models from config with compatibility |
| `-C [MODEL]`| `--compact [MODEL]` | Triggers LLM compaction. Prompted if MODEL is omitted |
| | `--clean` | Delete database sessions older than the retention window |
| | `--days N` | Set cleanup retention window in days (default: 5) |
| | `--clean-orphans` | Remove orphaned records and sidecar diffs |
| | `--db PATH` | Override standard SQLite database file path |
| | `--delete` | Recursively delete the session specified by `-s` |
| | `--delete-project`| Recursively delete the project specified by `-P` (includes all project sessions/files/DB rows) |
| | `--dry-run` | Run cleanup/delete tasks without writing changes |
| | `--force` | Bypass active process lock checks during delete/cleanup |
| | `--info` | Show database and storage usage information |
| | `--clear-history` | Wipes the historical activity ledger and resets totals |
| | `--create-config` | Interactively generate the `ocman.toml` file |
| | `--backup-opencode` | Create a system backup archive ZIP file |
| | `--restore PATH` | Restore configuration, database, and diffs from backup |
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
| `-v` | `--verbose` | Increase log verbosity (`-v` or `-vv`) |

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

# Default LLM model used for compaction
default_model = "uri/its_direct/pt1-qwen3-32b-us"

# Default retention window in days for database cleanups
default_retention_days = 5

# Maximum detailed run records kept in the activity history ledger (0 = unlimited).
# Cumulative all-time totals are always preserved; only the per-run detail list is capped.
history_max_runs = 500

# CLI and recovery behavior settings
keep_temp = false
include_tools = false
all_roles = false
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

