# Repository Inventory - 20260624-024342

## 1. Project State Summary

The `ocman` repository is an administration suite for the OpenCode agentic ecosystem. It is structured as a Python CLI/TUI application. The workspace is clean and has a passing suite of 36 unit and integration tests.

## 2. Project Type & Scope

- **Type**: Python CLI and TUI Package
- **Audience**: Developers and operators of OpenCode agents
- **Languages**: Python (>=3.10)
- **Dependencies**: `textual`, `rich`, `pysqlite3-binary`

## 3. Public Contract Summary

- **Package Entry Points**:
  - Python import: `ocman`
  - Textual TUI package: `ocman_tui`
- **CLI Commands**:
  - `ocman` (interactive session picker/recovery wizard)
  - `ocman --list-projects` / `-lp` (list database projects)
  - `ocman --list-sessions` / `-ls` (list database/CLI sessions)
  - `ocman --project <spec>` / `-P` (specify project filter)
  - `ocman --session <spec>` / `-s` (specify session filter)
  - `ocman --details` / `-D` (show details for a session)
  - `ocman --head <num>` / `-H` (preview start of session)
  - `ocman --tail <num>` / `-T` (preview end of session)
  - `ocman --compact [<model>]` / `-C` (compact session using LLM)
  - `ocman --show-models` / `-sm` (list models)
  - `ocman --delete` (delete session recursively)
  - `ocman --clean` (clean database sessions older than retention days)
  - `ocman --days <num>` (specify age threshold)
  - `ocman --clean-orphans` (prune orphaned records/files)
  - `ocman --clean-backups` (prune backups from backups folder)
  - `ocman --backup-opencode` (create ZIP backup)
  - `ocman --restore <zip>` (restore ZIP backup with rollback safety)
  - `ocman show logs` (view activity metrics)
  - `ocman ui` / `ocman gui` (launch interactive TUI dashboard)
  - `ocman info` (show database/session details)

## 4. Artifact Summary

- **Source Code**:
  - [ocman.py](file:///home/gfariello/VC/ocman/ocman.py) (monolithic main CLI script)
  - `ocman_tui/` (TUI application package)
    - `__init__.py`
    - `app.py` (Textual app)
    - `core.py` (TUI helpers)
    - `css/style.css` (TUI styles)
    - `widgets/database.py` (database screens)
    - `widgets/models.py` (model widget)
    - `widgets/sidebar.py` (sidebar navigation)
- **Packaging/Build Configuration**:
  - `pyproject.toml` (Hatchling backend, entry point defined as `ocman:main`)
  - `CHANGELOG.md`
  - `README.md`
  - `LICENSE`
- **Release-Review**:
  - Execution runbooks (`release-review/*.md`)

## 5. Test & Validation Inventory

- **Test Suite**: Located under `tests/`
  - `test_config_backup_restore.py` (backup/restore, backup cleanups)
  - `test_core.py` (Turn helpers and Turn truncations)
  - `test_ocman.py` (CLI parsing, database queries, resolutions, deletion runs)
  - `test_tui.py` (TUI screen/widgets loading and events)
- **Local Validation Command**: `pytest` or `python3 -m pytest`

## 6. Build/Packaging/CI Inventory

- **CI Workflow**: `.github/workflows/ci.yml` (runs `pytest` on Python 3.10-3.14 via GitHub Actions)
- **Packaging Target**: Standard Wheel and Source Distribution via Hatch build backend.

## 7. Deprecation Candidates

- `20260624-024342-S1-DEP1`: Inline redundant helper definitions in [ocman.py](file:///home/gfariello/VC/ocman/ocman.py) if duplicate functions are present in `ocman_tui/core.py`. (Need to analyze further in S6).

## 8. Recommended Next Actions

- `20260624-024342-S1-A1`: Proceed to Section 2 (Quality, Security, and Edge Cases Audit) to run static analysis, check file handling, path boundaries, error logging, and resource safety.
