# Repository Inventory

## Current Project State Summary

The repository contains `ocman`, a tool for managing, compacting, and recovering OpenCode developer sessions. It consists of a CLI script `ocman.py` (which has zero external dependencies) and a modern Textual-based TUI package `ocman_tui`. It also includes a test suite under `tests/` and a release review protocol under `release-review/`.

## Project Type and Scope

- **Type**: Python CLI and TUI application.
- **Audience**: OpenCode users, developers, and operators.
- **Frameworks/Libraries**:
  - Textual (TUI framework)
  - Rich (formatting/styling)
  - Pytest (testing)
  - SQLite3 (native standard library)
  - Hatchling (build backend)

## Public Contract Summary

- **CLI Commands**:
  - `ocman` (interactive session recovery)
  - `ocman ui` / `ocman gui` (launch the TUI app)
  - `ocman show logs` (display deletion history logs)
  - `ocman delete-project --project <id>` (recursively delete project and associated sessions)
  - `ocman --list-projects` / `--list-sessions` / `--delete` / `--clean`
- **TUI Interface**:
  - Project/session selector sidebar
  - Session details, metadata, and recovery prompt exporter tabs
  - Database Administration tab (database metrics, prune options, and activity logs)
  - Configuration settings tab

## Artifact Summary

- `ocman.py`: Core logic, database queries, and CLI entry point.
- `ocman_tui/app.py`: Main Textual application with screen modals.
- `ocman_tui/core.py`: Imports and aliases variables/functions from `ocman.py`.
- `ocman_tui/widgets/`: Sub-package for custom UI widgets (Database layout, Models table, Sidebar tree).
- `ocman_tui/css/style.css`: CSS styling for the Textual TUI.
- `pyproject.toml`: Project configuration and dependency declarations.
- `tests/`: Pytest suite (TUI and CLI).
- `rebuild_opencode.sh`: Obsolete, deprecated database optimization bash script.

## Test and Validation Inventory

- **Framework**: pytest (configured via `pyproject.toml`)
- **Coverage**:
  - Configuration backup and restore tests (`test_config_backup_restore.py`)
  - Core helper tests (`test_core.py`)
  - CLI and database operations (`test_ocman.py`)
  - TUI interface interactions (`test_tui.py`)
- **Validation command**: `PYTHONPATH=. pytest` (32 passing tests)

## Documentation Inventory

- `README.md`: High-level overview, CLI usage examples, installation instructions, and TUI details.
- Inline docstrings in `ocman.py` and `ocman_tui/app.py`.

## Build/Packaging/CI/Deployment/Release Inventory

- **Build Backend**: Hatchling
- **Build configuration**: `pyproject.toml`
- **CI**: No CI workflows exist currently (e.g., GitHub Actions).

## Recent Changes

- Added recursive project deletion to both CLI (`--delete-project`) and TUI (button + confirmation safety modal).
- Appended "Grand Totals" to TUI Activity Log and CLI `ocman show logs`.
- Ignored `repository-review/` and local test configs in `.gitignore`.

## Drift or Inconsistencies

- [20260618-023542-S1-A1] Untracked files `opencode.json` and `opencode.jsonc` exist in the repository root. Although they are now gitignored, they might confuse new contributors.

## Key Ambiguities

- None identified at this stage.

## Visible Release-Quality Concerns

- [20260618-023542-S1-DEP1] Obsolete script `rebuild_opencode.sh` exists in the repository root but is explicitly marked deprecated and superseded by `ocman --clean`. It should be evaluated for removal.

## Recommended Next Actions

- Proceed with Section 2 (Quality, Security, and Edge Cases) to audit the code for potential bugs, correctness, and resource leak issues.
