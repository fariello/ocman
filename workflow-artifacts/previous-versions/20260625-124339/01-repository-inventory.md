# Repository Inventory - Run `20260625-124339`

## 1. Current Project State Summary
The project is `ocman` (OpenCode Manager), which provides a CLI and a terminal user interface (TUI) to manage, recover, backup/restore, clean up, and compact `OpenCode` agentic sessions. It is actively developed in Python, with a textual TUI dashboard and a comprehensive set of unit tests in `tests/`.
A major new feature (Portable Session Export & Import + Move Project/Session) has just been locally committed. The workspace working tree is clean. The project builds and passes all 52 automated tests.

## 2. Project Type and Scope
- **Languages**: Python (3.10+)
- **Architecture**:
  - Backend core: `ocman.py` (standalone single-file script containing database operations, CLI commands, backup/restore, recovery, and compaction).
  - Frontend TUI: `ocman_tui` (package with Textual app in `app.py`, core TUI logic in `core.py`, styling in `css/style.css`, and custom widgets in `widgets/`).
- **Dependencies**: `textual`, `rich`, `pysqlite3-binary`, with dev dependencies `pytest` and `anyio`.

## 3. Public Contract Summary
- **CLI Commands**: `ocman ui` / `ocman gui` (launches TUI), `ocman info`, `ocman --clean`, `ocman --clean-orphans`, `ocman show logs`, `ocman --backup-opencode`, `ocman --restore <path>`, and recovery commands like `ocman -s <session_id>`.
- **New CLI Commands**: `--export-session`, `--import-session`, `--to-project`, `--new-project-path`, `--move-project <from_path>`, `--to <to_path>`.
- **Public API**: The module `ocman.py` is executable and importable as a library (e.g. `import ocman` by `ocman_tui.core`).

## 4. Artifact Summary
- Built package wheels are targeted for PyPI distribution.
- Existing distribution package in `dist/ocman-1.0.1-py3-none-any.whl` and `dist/ocman-1.0.1.tar.gz`.

## 5. Test and Validation Inventory
- Test Framework: `pytest` with `pytest-cov`.
- Test Files:
  - `tests/test_ocman.py`: Core CLI and recovery unit tests.
  - `tests/test_core.py`: TUI core module tests.
  - `tests/test_tui.py`: Textual UI widgets and workflow tests.
  - `tests/test_config_backup_restore.py`: Config file validation and backup rollback engine tests.
  - `tests/test_move.py`: Project and session move operation tests.
  - `tests/test_export_import.py`: Session export and import bundle tests.
- Validation Command: `PYTHONPATH=. pytest` (runs 52 test cases).

## 6. Documentation Inventory
- `README.md`: Explains core capabilities, quickstart, CLI options reference, configuration settings, and development/testing instructions.
- `CHANGELOG.md`: Tracks changes and version bumps.
- `agents/plans/`: Detailed design documents/IPDs outlining implementation architecture for moves and export/import.

## 7. Build/Packaging/CI/Deployment/Release Inventory
- Packaging: `pyproject.toml` using `hatchling` as the build backend.
- Build target wheels: `ocman_tui` and force-include of `ocman.py`.
- CI/CD: None present (no `.github/workflows/` or other CI configurations).

## 8. Recent Changes
- Implementation of Project/Session Move and Session Export/Import features including modal UIs in textual app and comprehensive CLI arguments. Added `test_move.py` and `test_export_import.py`.

## 9. Drift or Inconsistencies
- **20260625-124339-S1-D1**: The `pyproject.toml` lists version as `1.0.1`, which matches the built files in `dist/`. However, the user mentioned we cannot republish 1.0.0 and previously raised a concern about version bumping. If 1.0.1 is already built, we may need to bump to `1.0.2` for this release.
- **20260625-124339-S1-D2**: CLI documentation and TUI help screen do not yet document the newly added commands (`--export-session`, `--import-session`, `--move-project`).

## 10. Key Ambiguities
- **20260625-124339-S1-Q1**: Whether Python 3.14 (used locally to run tests) has specific package installation compatibility issues on target user machines with `pysqlite3-binary` or newer Textual versions.

## 11. Visible Release-Quality Concerns
- **20260625-124339-S1-REL1**: Missing CI workflows (GitHub Actions) to automate test running and validation on other Python versions.
- **20260625-124339-S1-REL2**: Import behavior of `ocman`: `tests` and TUI code imports `ocman` directly. If installed globally, it might conflict with the local workspace version of `ocman.py` depending on `PYTHONPATH` (as seen in the earlier pytest failure when PYTHONPATH was not specified).

## 12. Deprecation Candidates
- **20260625-124339-S1-DEP1**: `opencode.json` and `opencode.jsonc` in the root workspace directory are likely local/debug test configurations that do not belong in the distributed package. They are already ignored in `.gitignore`, but we should ensure they are not packaged by hatchling.

## 13. Recommended Next Actions
- **20260625-124339-S1-A1**: Execute Step 2 (Quality/Security Audit) using `release-review/02-quality-security-edge-cases.md` to identify bugs/correctness issues, especially around the new session move and export/import logic.
