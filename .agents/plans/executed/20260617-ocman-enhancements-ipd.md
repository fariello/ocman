# Implementation Plan - Configuration, Backup, and Restore Enhancements

This document details the design and implementation plan for adding:
1. Flat-file configuration (`ocman.toml`) at `~/.config/opencode/ocman.toml`.
2. Interactive config generator via `ocman --create-config`.
3. A configuration settings screen in the TUI (`ocman ui`).
4. A backup utility via `ocman --backup-opencode [dest]` and the TUI.
5. Archive-based restoration via `ocman --restore <file_or_dir>` and the TUI, featuring automated rollback safety.

---

## User Review Required

> [!IMPORTANT]
> - **Zero External Dependencies**: All TOML parsing/generation and ZIP archiving will be done using Python's standard libraries (`zipfile` and custom parsing helpers). No extra pip packages are required.
> - **Config File Override Precedence**: Configuration precedence will follow: **Default values < Config File values < CLI command-line arguments**. Command-line args always have the highest priority.
> - **Backup/Restore scope**: The backup operation will capture the entire active state of the opencode/ocman ecosystem: SQLite database (including `-wal`/`-shm` if active), `ocman_history.json`, `ocman.toml`, `opencode.json`/`opencode.jsonc`, and all session JSON files under `~/.local/share/opencode/storage/session_diff/`.
> - **Rollback Safety**: Prior to any restoration, a temporary fallback backup of the current state is automatically created. If extraction fails midway, the state is rolled back to prevent data loss.

---

## Open Questions

- *None.* The architectural design handles the stdlib-only constraint safely, and the TUI flows map directly to existing Textual paradigms.

---

## Proposed Changes

### Configuration Engine (`ocman.py`)

#### [MODIFY] [ocman.py](file:///home/gfariello/VC/ocman/ocman.py)

1. **Config Helper Functions**:
   - `load_ocman_config()`: Checks for `~/.config/opencode/ocman.toml`. If found, reads and parses its key-value pairs line-by-line (using `#` to skip comments). Resolves path keys (e.g. `db_path`) by expanding `~` to the home directory.
   - `save_ocman_config(config_dict)`: Formats and writes configuration values into a predefined, highly-commented TOML template.
   - `get_effective_setting(key, cli_arg_value, default)`: Merges default, file-level config, and CLI-level args.

2. **Interactive Configuration Creator (`--create-config`)**:
   - Add the `--create-config` CLI flag.
   - If stdout/stdin is a TTY:
     - Ask if the user wants to customize values or accept defaults.
     - Prompt sequentially for each config value with its default option in brackets (e.g. `SQLite Database Path [~/.local/share/opencode/opencode.db]: `).
   - If stdout/stdin is not a TTY or `--force` is provided: Write the default commented `ocman.toml` directly.

3. **Backup Engine (`--backup-opencode`)**:
   - Add the `--backup-opencode` CLI flag, accepting an optional destination.
   - If no destination is specified, it uses `default_backup_dir` from the configuration (default: `~/.local/share/opencode/backups`).
   - If the destination is a directory, it generates a filename format `opencode-backup-YYYYMMDD-HHMMSS.zip`.
   - If it's a file path ending in `.zip`, it writes directly there.
   - Recursively compresses the database, wal/shm logs, sidecar history, configs, and session diff files.
   - Prints full metrics on files backed up and archive size.

4. **Restoration Engine (`--restore`)**:
   - Add the `--restore` CLI flag.
   - Checks if target is a ZIP file or directory:
     - If ZIP: Extract to a temporary folder and verify presence of `opencode.db`.
     - If directory: Verify presence of `opencode.db`.
   - Creates a fallback safety backup under `~/.local/share/opencode/backups/rollback_before_restore_YYYYMMDD_HHMMSS.zip`.
   - Overwrites active files (database, history, configs, and storage directory files) with the backup contents.
   - Outputs completion statistics.

---

### TUI Integration (`ocman_tui/`)

#### [MODIFY] [app.py](file:///home/gfariello/VC/ocman/ocman_tui/app.py)

1. **Configuration Settings Tab**:
   - Add `TabPane("Configuration Settings", id="tab-config")` into `TabbedContent`.
   - Implement the config form layout using Textual widgets (`Input`, `Checkbox`, `Button`, `Label`).
   - Bind widgets to `on_mount` config load.
   - Handle `"Save Config"` and `"Reset to Defaults"` button clicks. Saving updates the settings in-memory immediately.

2. **Background Restore Worker Dialog**:
   - Add a restore confirmation dialog (`RestoreBackupModal`) to prompt the user for the ZIP/directory path.
   - Launch background threads for backup/restore operations in the main app (`_do_backup_worker` / `_do_restore_worker`) to keep the UI responsive.
   - Refresh the sidebar tree view and database metrics upon successful restore.

#### [MODIFY] [database.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/database.py)

- Update the layout of `DatabaseAdminWidget` to include a new **BACKUP & RESTORE** section in the operations card or as a separate card.
- Add buttons `Create Backup` (`#btn-create-backup`) and `Restore Backup` (`#btn-restore-backup`).
- Implement button event handlers to trigger backup generation or present the restore dialog.

---

## Verification Plan

### Automated Tests
- Run `PYTHONPATH=. pytest -v` (covers all existing database, model, and TUI tests).
- Add new test suite `tests/test_config_backup_restore.py` to verify:
  - TOML parser loading correct settings.
  - TOML writer generating correctly commented file.
  - `--create-config` generating expected file with defaults in non-interactive mode.
  - `--backup-opencode` creating a valid zip file containing correct directory structures.
  - `--restore` successfully rebuilding database records and storage files from both directory and ZIP formats, including verification of rollback files created on failure.

### Manual Verification
- Execute `ocman --create-config` and walk through the interactive prompts.
- Verify contents of generated `~/.config/opencode/ocman.toml`.
- Run `ocman ui` to test interactive TUI Configuration Settings panel, and run backup/restore from the TUI directly.
- Execute `ocman --backup-opencode` and check the file size and zip contents.
- Force a restore via `ocman --restore` using the created ZIP file and ensure the session logs restore correctly.
