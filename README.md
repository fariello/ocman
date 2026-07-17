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
reclaimed (see `ocman db clean`, `ocman db clean-orphans`, and `ocman info`/`disk`).

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
*   **Robust Session Recovery & LLM Compaction**: Parses native OpenCode export files, strips metadata noise, truncates transcripts safely, and optionally compacts context using OpenAI-compatible LLM gateway APIs (`ocman session compact`) to produce clean restart files for fresh agent sessions.
*   **Flat-File Configuration**: Precedence-based configuration engine (`~/.config/opencode/ocman.toml`) with interactive setup helper (`ocman config create`).

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
ocman db info   # alias: ocman info

# Clean sessions older than 7 days and reclaim database disk space
ocman db clean --older-than 7d   # positional also works: ocman db clean 7 days
# (the old --days N flag still works but is a deprecated alias for --older-than)

# Scan and delete all orphaned database records/files
ocman db clean-orphans

# View historical deletion/recovery runs and all-time grand totals
ocman history show   # alias: ocman logs

# Create a complete ZIP backup of your OpenCode system state
ocman backup create

# Restore your OpenCode system state from a backup ZIP file (with rollback safety)
ocman backup restore ~/.local/share/opencode/backups/backup.zip
```

### CLI Session Recovery
```bash
# Recover interactively (lists sessions, lets you pick one)
ocman session recover

# Recover a specific session, truncating to the last 50 exchanges
ocman session recover SESSION_ID -mi 50

# Recover, truncate, and compact using an LLM gateway model
ocman session compact SESSION_ID model:uri/its_direct/pt1-qwen3-32b-us -mi 50

# Compact multiple sessions in one batch with a single confirmation
ocman session compact sess1 sess2 project:myproj model:gpt-4

# Split a very large session into ordered parts instead of truncating (nothing dropped)
ocman session recover SESSION_ID --chunk
# Compact a large session in parts (one API call per part, each fits the model)
ocman session compact SESSION_ID model:gpt-4 --chunk
```

> [!TIP]
> **Chunking vs truncating a large session.** By default, when a session exceeds the
> built-in size trigger (2500 transcript lines or 100 interactions) ocman offers to
> TRUNCATE it (keep only the most recent turns). With `--chunk` it instead SPLITS the
> whole session into ordered, self-contained files named
> `YYYYMMDD-HHMM-<session_id>.part-NNofMM.<kind>.md`, breaking only on interaction
> boundaries (never mid-turn) so nothing is dropped. The interactive large-session
> prompt also offers a `[c]hunk` choice. `--max-lines` / `--max-interactions` set the
> size of EACH part; the per-part defaults are the `chunk_max_lines` /
> `chunk_max_interactions` config keys. For `compact --chunk`, each part is sent to the
> LLM separately (so each fits the context window) and written as
> `...part-NNofMM.compacted.md`, with the pre-run cost table summing all parts. (This
> applies to `recover` and `compact`; `.ocbox` `export` is not chunked.)

> [!TIP]
> **Compacted files land in your project's prompts.** When you compact (`ocman session compact`) and the
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
./ocman.py help
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

### Getting help
`ocman` renders a compact, verb-first help screen (not the raw argparse dump):
*   `ocman help` (or `ocman -h`, `ocman --help`) shows the overview grouped by task (Browse, Recover & compact, Maintain, Backup).
*   `ocman help TOPIC` shows a focused section. Topics: `browse`, `recover`, `maintain`, `backup`, `move`, `config`.
*   `ocman help all` prints the complete command reference (every group, action, and option).
*   `ocman <command> -h` prints that specific command's own options and usage, e.g. `ocman db clean -h`, `ocman session -h`, or `ocman session compact -h`. This per-command help is auto-generated, while `ocman help` / `ocman help TOPIC` stay the curated overview.

### Command structure
`ocman` uses a noun-based, git/kubectl-style grammar: `ocman <group> <action> [options]`. The groups
are `session`, `project`, `db`, `backup`, `history`, and `config`. For example:
*   `ocman session list` lists sessions; `ocman session recover ID` recovers one.
*   `ocman project list` / `ocman project delete NAME` manage projects.
*   `ocman db info` / `ocman db clean` / `ocman db clean-orphans` maintain the database.
*   `ocman backup create` / `ocman backup restore PATH` handle backups.

A handful of top-level verbs are kept as convenient aliases for the most common actions:
*   `ocman search QUERY` = `ocman session search QUERY`
*   `ocman info` = `ocman db info`
*   `ocman disk` = `ocman db info --by-project`
*   `ocman logs` = `ocman history show`

**Word-order aliases.** The `list` verb accepts either word order, so you can read it whichever way
feels natural:
*   `ocman list projects` = `ocman project list` (short: `ocman lp`)
*   `ocman list sessions [NAME]` = `ocman session list [NAME]` (short: `ocman ls [NAME]`)

**Auto-detecting `move` and `export` verbs.** Two top-level verbs figure out whether you gave them a
project or a session, so you rarely need to say which:
*   `ocman move SPEC to DST` relocates whichever project or session `SPEC` names. The word `to` is
    optional sugar (`ocman move SPEC DST` and `ocman move SPEC --to DST` also work), and
    `--metadata-only` is still supported. This is equivalent to `ocman project move` /
    `ocman session move`. If `SPEC` matches both a project and a session, or is a bare integer (a
    list number), ocman prompts you on a TTY to select the target, or errors non-interactively. You can disambiguate by using the qualifier `session:SPEC` or `project:SPEC`, or by using the explicit commands `ocman move project SPEC to DST` or `ocman move session SPEC to DST`.
    * **Git-aware moves.** If the source is a git repository, ocman inspects it up front and, on a
      TTY, offers to handle the working tree before moving: for a dirty repo it can commit (staged
      only, or everything), quit so you can fix it, or proceed relying on a bulk copy; for a clean
      repo that is ahead/behind its upstream it can push and/or pull first. All questions are asked
      before anything is moved, so a git failure aborts before the point of no return. Chosen local
      git commands are run (git manages its own auth and output).
    * **Cross-machine moves (remote DST).** When `DST` is `host:/path` (or `user@host:/path`), ocman
      does NOT perform any network I/O itself. It gathers your choices, then PRINTS a copy-paste
      runbook (export the bundle, `scp` it, transfer the repo via git or bulk `tar` over `ssh`, then
      `ocman session import --new-project-path` on the remote), with every interpolated value
      shell-quoted. It never deletes the local copy for a remote move; after you have verified the
      remote import, reclaim local space with `ocman move SPEC to host:/path --confirm-remote-delete`.
    * **Existing local destination.** If a local `DST` already exists, ocman offers to reconsider,
      do a metadata-only update, back up and replace, replace without backup, or overlay the source
      on top (each with the appropriate warning).
*   `ocman export SPEC to FILE` exports whichever session or project `SPEC` names to a `.ocbox`
    bundle (`to` optional; `--to FILE` also works). Force the kind with `ocman export session SPEC`,
    `ocman export project SPEC`, or using `session:SPEC`/`project:SPEC` qualifiers. A project bundle contains the full project row, its
    `project_directory`/`workspace` rows, and every session (plus subagents) and diff.
    `ocman session import FILE` auto-detects the bundle kind and restores it; on a project import
    that collides with an existing project it prompts (back up / delete / move / merge / new / abort)
    or, non-interactively, refuses unless you pass `--to-project ID` or `--new-project-path PATH`.
*   **Qualifiers.** You can explicitly force the interpretation of any spec using the prefixes `session:SPEC`, `project:SPEC`, or `model:SPEC`. This prefix overrides auto-detection, prevents TTY prompts, and works in both interactive and non-interactive environments.

The remaining natural-language sugar is an optional `in [project|session] NAME` phrase, accepted by
`ocman session list`, `ocman session search`, and `ocman search`. For `session list` it is
equivalent to passing the project as the trailing `NAME` positional, and it lets multi-word project
names be written without quotes:
*   `ocman session list in my-project` = `ocman session list my-project`
*   `ocman session search bug in project My Project` = `ocman session search bug "My Project"`
*   `ocman search bug in my-project` = `ocman search bug my-project`

For search, `in NAME` accepts a **project or a session** and auto-detects which. Disambiguate an
ambiguous NAME with `ocman search "text" in project NAME` or `ocman search "text" in session NAME`;
an ambiguous or unmatched NAME errors.

### Current-directory scoping and the "global (/)" project
When you run `ocman list sessions` or `ocman search` without an explicit `--project`, ocman scopes to
your current directory. It first matches a known project worktree; if none matches, it falls back to
**directory scoping**: sessions whose working directory is your current directory or a subdirectory of
it, regardless of which project owns them.

This matters because OpenCode files sessions started in your home directory (or without a project) under
a catch-all project whose worktree is `/`. ocman labels that project **`global (/)`** to avoid confusing
it with the filesystem root, and does not treat `/` as a normal parent directory (it would match
everything). Directory scoping is what lets `ocman list sessions` run from `~` still find those
home-directory sessions; when results include sessions from the `global (/)` project, ocman prints a
loud, multi-line **NOTICE** explaining the mapping and how to view the true global project
(`ocman list sessions in /`).

When no single project is in scope (a directory scope, or all-projects), `ocman list sessions` prints a
richer per-session stanza: the session ID and its project directory, first/last active timestamps, cost,
and split input / output / cache token counts, plus the approximate message/interaction/part counts.
Single-project listings keep the compact one-line-per-session form.

### Database & Storage Status (`ocman db info`)
Prints a breakdown of your current database state on disk, including the SQLite database
family size, session-diff file storage, and a **Backups (Disk Storage)** section showing
the total size, count, and age range of your backups directory:
```bash
ocman db info   # alias: ocman info
# Add -v to trigger a SQLite database PRAGMA integrity check
ocman db info -v

# Add a per-project on-disk breakdown (session-diff bytes + session/message/token counts)
ocman db info --by-project
# Or the alias:
ocman disk
```
> [!NOTE]
> Per-project figures cover **session-diff files only**. The SQLite database is a single
> shared file, so its bytes are not attributable to an individual project.

The `--by-project` breakdown is rendered as an aligned table keyed by each project's
**directory** (worktree), with session/message counts, cost, split input/output/cache tokens, and
session-diff file count and size. The "Size on disk" line also explains the SQLite WAL/SHM sidecar
files (write-ahead log and its shared-memory index), which are normal and shrink after a checkpoint.
Per-project cost and tokens are **active** figures only; deleted (historical) cost is not attributable
per project and is shown as a single global line in the Usage Metrics summary.

### Historical Auditing (`ocman history show`)
Outputs a list of past cleanups and recoveries in reverse chronological order, ending with a comprehensive all-time totalization card:
```bash
ocman history show   # alias: ocman logs
```

### Automated Configuration Generator (`ocman config create`)
Runs an interactive setup assistant to generate a config file at `~/.config/opencode/ocman.toml`. If run non-interactively (e.g., in a script), it creates the config file with safe defaults. Pass `--force` to overwrite an existing config.
```bash
ocman config create
```

---

## Command Reference

`ocman` follows a noun-based, git/kubectl-style grammar: `ocman <group> <action> [options]`.
Global options work on any subcommand and may appear before or after it.

### Global options

| Option | Equivalent | Description |
|:---|:---|:---|
| | `--db PATH` | Override the standard SQLite database file path |
| `-v` | `--verbose` | Increase log verbosity (`-v` or `-vv`) |
| `-V` | `--version` | Print the ocman version and exit |
| `-h` | `--help` | Show help for the current command |

### `session` (work with sessions)

| Command | Description |
|:---|:---|
| `ocman session list [NAME]` | List sessions, optionally scoped to project `NAME` (default: CWD project). Also `session list in NAME`. Add `-A/--all-sessions` to include subagents. |
| `ocman session search QUERY [NAME]` | Search session content and titles (case-insensitive), optionally scoped to project `NAME`. `-n N`/`--limit N` caps results (default: 10); `-A/--all-sessions` includes subagents. Also `search QUERY in [project\|session] NAME`. |
| `ocman session show [specs...]` | Show details for sessions (bare form shows details). Accepts multiple target specs. `-H N`/`--head N` and `-T N`/`--tail N` preview the first/last N exchanges; `-A/--all-sessions` aids resolution. |
| `ocman session recover [specs...]` | Recover sessions to restart-ready Markdown (omit specs to pick interactively). Accepts multiple target specs. `--chunk` splits a large session into ordered `.part-NNofMM` files instead of truncating (nothing dropped); `-ml`/`-mi` set the per-part size. |
| `ocman session compact [specs...]` | Recover and LLM-compact sessions in batch. Accepts multiple target specs (sessions, projects, and a model). `--chunk` compacts each part separately (one API call per part) and writes `...part-NNofMM.compacted.md`. |
| `ocman session delete [specs...]` | Recursively delete sessions. Supports multiple target specs. Multi-target and project-expanded deletes run as ONE consolidated batch: a single backup, one transaction, one `VACUUM`, and one grand-total report (not once per session). Deleting a whole project's sessions by naming the project also removes the now-empty project row. `--dry-run` previews; `--force` bypasses process-lock checks; `-A/--all-sessions` aids resolution. |
| `ocman session export ID --to FILE` | Export a session and its subagents to a portable `.ocbox` bundle. |
| `ocman session import FILE` | Import a session from a `.ocbox` bundle. `--to-project ID` remaps to an existing project; `--new-project-path PATH` remaps to a new worktree; `--new-session-id` regenerates a fresh compliant session ID (single-session bundle only). Refuses if OpenCode is running; `--while-running` (alias `--force`) proceeds anyway. |
| `ocman session move ID --to DST` | Relocate a single session. `--metadata-only` updates DB paths only, bypassing the disk move. |

**Recovery options** (for `session recover` and `session compact`):

| Option | Equivalent | Description |
|:---|:---|:---|
| `-o DIR` | `--out DIR` | Output directory for recovery files (default: `./opencode-recovery`) |
| `-d DIR` | `--session-dir DIR` | Directory the session originally ran in |
| `-mi N` | `--max-interactions N` | Keep at most N user+assistant turn pairs (per part when `--chunk`) |
| `-ml N` | `--max-lines N` | Keep at most N transcript lines (truncates older turns; per part when `--chunk`) |
| | `--chunk` | Split a large session into ordered `.part-NNofMM` files instead of truncating (nothing dropped); `-ml`/`-mi` set the per-part size |
| `-t` | `--include-tools` | Include tool execution results and tool call messages |
| | `--all-roles` | Write all roles, not just user/assistant |
| `-ic FILE` | `--input-compact FILE` | Prepend a prior compacted file as context (repeatable) |
| `-ir FILE` | `--input-restart FILE` | Prepend a prior restart file as context (repeatable) |
| `-it FILE` | `--input-transcript FILE` | Prepend a prior transcript as context (repeatable) |
| `-oc FILE` | `--output-compact FILE` | Output path for the compaction prompt file |
| `-or FILE` | `--output-restart FILE` | Output path for the restart file |
| `-ot FILE` | `--output-transcript FILE` | Output path for the clean transcript |
| `-k` | `--keep-temp` | Keep the raw exported JSON file for debugging |
| `-cp` | `--clean-previous` | Remove prior recovery outputs generated for this session |
| `-ct` | `--clean-tmp` | Prune old exported JSON temporary files from `/tmp` |
| | `--show-secrets[=masked|raw]` | Display matched secrets context (default: masked) |
| | `--expunge-secrets` | Redact secrets from the transmitted payload and rewrite saved files |
| `-y` | `--yes` | Skip confirmation prompt and batch cost confirm |

### `project` (work with projects)

| Command | Description |
|:---|:---|
| `ocman project list` | List all projects in the database. |
| `ocman project delete NAME` | Recursively delete a project (all its sessions, files, and DB rows). `--dry-run` previews; `--force` bypasses process-lock checks. |
| `ocman project move SRC --to DST` | Relocate a project (re-assign the worktree path in the DB and on disk). `--metadata-only` updates DB paths only. |

### `db` (database info and maintenance)

| Command | Description |
|:---|:---|
| `ocman db info` | Show database and storage usage (incl. backups disk usage). `--by-project` adds a per-project on-disk session-diff breakdown. Alias: `ocman info` / `ocman disk`. |
| `ocman db clean [NAME] [AGE]` | Delete sessions older than the retention window, optionally scoped to project `NAME`. `--older-than AGE` sets the window; `AGE` accepts compact forms (`2h`, `5d`, `6w`, `6mo`, `1y`), a spelled-out `"30 days"`, or a bare number (days). A positional duration also works (`ocman db clean 30 days`, `ocman db clean myproject 6mo`). `--days N` is a deprecated alias for `--older-than`. Default: 5 days. `--dry-run` previews; `--force` bypasses process-lock checks. |
| `ocman db clean-orphans` | Remove orphaned records and sidecar diffs. `--dry-run` previews; `--force` bypasses process-lock checks. |
| `ocman db rebase --from A --to B` | Bulk rebase DB workspace path prefixes (both `--from` and `--to` are required). Refuses if OpenCode is running; `--while-running` (alias `--force`) proceeds anyway. |

### `backup` (backup and restore)

| Command | Description |
|:---|:---|
| `ocman backup create [specs...] [--to DIR]` | Create a system backup archive ZIP (default destination from config), or write per-target `.ocbox` bundles to a directory when targeting projects/sessions with `--to DIR`. Streams progress as it runs. |
| `ocman backup restore PATH...` | Restore configuration, database, and session diffs from one or more backup archives or directories (with batch-atomic rollback safety). Streams per-file progress as it runs. Refuses if OpenCode is running (it overwrites the live DB); `--while-running` (alias `--force`) proceeds anyway. |
| `ocman backup clean [AGE]` | Prune old backups; previews a KEEP/DELETE table before deleting (see Pruning Backups). `--older-than AGE` sets the window (compact `2h`/`5d`/`6w`/`6mo`/`1y`, `"90 days"`, or a bare number of days); a positional duration also works (`ocman backup clean 90 days`). `--days N` is a deprecated alias. `--dry-run` previews. |

### `history` (activity ledger)

| Command | Description |
|:---|:---|
| `ocman history show` | Show historical activity runs plus all-time totals. Alias: `ocman logs`. `--limit N` caps the shown runs; `--json` for machine output. |
| `ocman history clear` | Wipe the historical activity ledger and reset totals (asks for confirmation; `-y`/`--force` skips). |
| `ocman spend [PROJECT]` | LLM spend report: per-project table by default (cost + split tokens), `PROJECT --sessions` for per-session detail, `--historical` to add saved (deleted) spend from the ledger, `--json` for machine output. |

### `config` (configuration file)

| Command | Description |
|:---|:---|
| `ocman config create` | Interactively generate the `ocman.toml` file. `--force` overwrites an existing config. |

### Top-level verbs and aliases

| Command | Description |
|:---|:---|
| `ocman search QUERY [NAME]` | Alias of `ocman session search`. Scope with a trailing `NAME` positional or `in [project\|session] NAME` (auto-detects; disambiguate with `in project NAME` / `in session NAME`). `-n N`/`--limit N` sets the max matching lines shown per session (default: 10). |
| `ocman list projects` / `ocman list sessions [NAME]` | Word-order aliases of `ocman project list` / `ocman session list [NAME]`. Short forms: `ocman lp` / `ocman ls [NAME]`. |
| `ocman list running` | List running OpenCode instances (pid/user/uptime/kind/dir/project/session) and flag insecure control servers (unauthenticated or non-loopback listeners) in bold red. Observe-only; current user by default (`--all-users` opt-in). `--probe` confirms auth via a read-only `GET /app` on your own loopback listeners; `--json` for machine output. Fails loud if it cannot reliably enumerate (never a false "all clear"). Linux-focused. |
| `ocman move SPEC to DST` | Auto-detects whether `SPEC` is a project or a session and relocates it. `to` is optional (`--to DST` also works); `--metadata-only` supported. Equivalent to `ocman project move` / `ocman session move`. Disambiguate an ambiguous or numeric `SPEC` with `ocman move project\|session SPEC to DST`. |
| `ocman export SPEC to FILE` | Auto-detects whether `SPEC` is a session or a project and exports it to a `.ocbox` bundle (`to` optional; `--to FILE` also works). Force the kind with `ocman export session\|project SPEC`. `ocman session import FILE` auto-detects and restores either kind. |
| `ocman info` | Alias of `ocman db info`. |
| `ocman disk` | Alias of `ocman db info --by-project`. |
| `ocman logs` | Alias of `ocman history show`. |
| `ocman models` | List available LLM models from config with compatibility. |
| `ocman compaction-prompt` | Print the compaction prompt template, then exit. |
| `ocman ui` / `ocman gui` | Launch the interactive terminal dashboard. |
| `ocman help [TOPIC]` | Show help. `TOPIC` is one of `browse`, `recover`, `maintain`, `backup`, `move`, `config`, `all`. |
| `ocman filter FILE` | Re-scope a recovery/compacted document to one project/scope via the LLM. Requires `-P/--project` and/or `--scope`; reuses `-C/--compact` for model and `-oc` for output. Written next to the source (or `-oc`) as `YYYYMMDD-HHMM-<session_id>.<scope>.compacted.md`. Supports `--allow-secrets`, `--show-secrets[=masked\|raw]`, `--expunge-secrets`, and `--force`. Input is size-capped (`filter_max_bytes`) and scanned for secrets/PII before sending. |

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

# When using `ocman session compact`, also copy the generated *.compacted.md (the doc a fresh agent
# reads) into the working project's .agents/prompts/pending/ if that project uses the .agents
# convention. Only applies when compaction runs (--no-project-prompt overrides).
copy_restart_to_project_prompts = true

# CLI and recovery behavior settings
keep_temp = false
include_tools = false
all_roles = false

# Egress guards for `filter` and `session compact` (content sent to the LLM API).
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

### Pruning Backups (`ocman backup clean`)
`ocman backup clean --older-than AGE` prunes old backups (positional durations such as
`ocman backup clean 90 days` also work). Before deleting anything it prints a
table of **all** backups, each tagged **DELETE** (past the retention window) or **KEEP**,
with a right-aligned Size column and last-modified time, plus a running "N to delete, M kept"
summary. If the prune would remove **every** backup, it prints a forceful warning that no
rollback backups will remain. With many retained backups the KEEP rows are summarized; use
`-v` to list them all. `AGE` accepts compact forms (`2h`, `5d`, `6w`, `6mo`, `1y`; `mo` and `y`
are approximate), a spelled-out `"90 days"`, or a bare number of days (fractions ok, e.g. `0.25` =
6 hours). The old `--days N` flag still works as a deprecated alias.

### Safety while OpenCode is running

OpenCode does not take a cross-process lock on its database, so mutating that shared
state while an OpenCode instance is running can corrupt it. Every mutating command
(session/project delete, `db clean`, `db clean-orphans`, session/project move,
session/project import, `backup restore`, and `db rebase`) checks for running OpenCode
instances first. If any are found it lists them and refuses by default; you can proceed
with `--while-running` (alias: `--force`), or, at an interactive prompt, by typing `yes`.
Detection matches any `opencode` process (not just `--continue`). On Linux, if ocman
cannot determine whether OpenCode is running it errs on the safe side and refuses unless
`--while-running` is given. Note that `-y`/`--yes` only skips the ordinary confirmation
prompt, not this running-instance check; use `--while-running` for that.

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
