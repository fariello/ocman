# Repository Inventory - 20260617-173940

- **Project Name**: `orsession` / `ocman`
- **Current Project State Summary**: The project is in a complete and functional state. The CLI tool `ocman.py` has been fully implemented, renamed from `opencode_recover_session.py`, packaged using Hatchling, and verified. Database cleaning features (`--clean`, `--clean-orphans`) are fully working and tested on the database.
- **Project Type and Scope**: Single-repo utility project with a standalone Python CLI tool and a companion TUI application for OpenCode session recovery.

## Codebase Structure & Artifact Summary
The repository contains the following artifacts:
- [ocman.py](file:///home/gfariello/VC/ocman/ocman.py): Standalone CLI utility for session recovery and database pruning.
- [pyproject.toml](file:///home/gfariello/VC/ocman/pyproject.toml): Packaging and dependency manifest.
- [SPEC-orsession.md](file:///home/gfariello/VC/ocman/SPEC-orsession.md): Design and specification for TUI pages and CLI details.
- [README.md](file:///home/gfariello/VC/ocman/README.md): High-level user documentation.
- [CHANGELOG.md](file:///home/gfariello/VC/ocman/CHANGELOG.md): History of project updates.
- [LICENSE](file:///home/gfariello/VC/ocman/LICENSE): BSD-3-Clause license file.
- [rebuild_opencode.sh](file:///home/gfariello/VC/ocman/rebuild_opencode.sh): Database dump/rebuild shell helper.
- `orsession/`: TUI package directories containing `app.py` and `core.py`.
- `scripts/check_orsession.sh`: Diagnostic script for checking thread deadlock state.

## Public Contract Summary
- **CLI Commands**:
  - `ocman`: Recovers, lists, compacts, and deletes/cleans up sessions.
  - Arguments: `-s/--session`, `-d/--session-dir`, `-o/--out`, `-c/--clean`, `--clean-previous`, `--delete`, `--clean-orphans`, `--days`, `--db`, `--dry-run`, `--force`.
- **TUI Command**:
  - `orsession`: Launches the visual Textual terminal UI.

## Test & Validation Inventory
- No Python test files (`test_*.py` or `*_test.py`) exist in the repository.
- No test directories are present.
- Dev dependencies list `pytest>=7.0`, indicating that a testing harness is planned but not implemented.

## Documentation Inventory
- `README.md` and `SPEC-orsession.md` are the primary documentation files.

## Build/Packaging/CI/Deployment/Release Inventory
- **Packaging**: Uses `hatchling` as the build backend, packaging `orsession` package and `ocman.py` module.
- **CI/CD**: No CI configurations (e.g. GitHub Actions, `.github/workflows/`) exist in the repository.
- **Deployment/Release**: Local installation via pip (`pip install -e .`).

## Recent Changes
- Renamed the recovery script from `opencode_recover_session.py` to `ocman.py` and registered the `ocman` package command.
- Integrated age-based cleanup and orphan sweeping directly into `ocman.py`.
- Fixed `pyproject.toml` packaging setup to correctly install `ocman.py` as a top-level module via `force-include`.
- Implemented grouped project and session detail feedback before database pruning.

## Drift or Inconsistencies
- **20260617-173940-S1-R1**: Minor references to the TUI's dependencies in `SPEC-orsession.md` might be slightly outdated compared to what is declared in `pyproject.toml`.

## Key Ambiguities
- **20260617-173940-S1-Q1**: No major ambiguities exist; the database structure and relation keys have been successfully mapped and validated.

## Visible Release-Quality Concerns
- **20260617-173940-S1-T1**: Total lack of automated unit or integration tests for CLI operations and TUI core module logic.
- **20260617-173940-S1-CI1**: Absence of any continuous integration (CI) workflows to enforce linting or run validation automatically.

## Deprecation Candidates
- **20260617-173940-S1-DEP1**: `--use-model` / `-m` argument in `ocman.py` (deprecated in favor of `--compact`).
- **20260617-173940-S1-DEP2**: `rebuild_opencode.sh` script (obsolete/redundant).

## Recommended Next Actions
- **20260617-173940-S1-A1**: Introduce a basic test suite under a new `tests/` directory to cover core SQL and recovery logic in `ocman.py` and `orsession/core.py`.
- **20260617-173940-S1-A2**: Establish a simple GitHub Actions CI workflow to run syntax validation or pytest checks.
