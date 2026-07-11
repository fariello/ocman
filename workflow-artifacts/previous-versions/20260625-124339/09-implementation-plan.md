# Implementation Plan

- **Run ID**: `20260625-124339`

## Scope Summary
Implement security fixes for session import, additional test coverage for security and CLI edge cases, update version numbers and release notes, update documentation for new CLI features, and configure GitHub Actions CI automation.

## Non-goals
- Large refactorings of CLI argument parser.
- Layout/aesthetic redesign of the textual UI.

## Change Batches

### Batch 1: Security Hardening (Highest Priority)
- **Actions**:
  - `20260625-124339-S2-X1`: Whitelist tables and validate column names in `extract_and_import_session`.
  - `20260625-124339-S2-X2`: Add strict alphanumeric/UUID regex check for session IDs to prevent path traversal.
- **Files**: `ocman.py`
- **Risk**: Low (Security improvement).

### Batch 2: Security and Edge Case Tests
- **Actions**:
  - `20260625-124339-S3-X1`: Add test cases verifying SQL Injection and Path Traversal attempts in import.
  - `20260625-124339-S3-X2`: Add test cases for CLI `--metadata-only` and interactive prompts on missing directories.
- **Files**: `tests/test_export_import.py`, `tests/test_move.py`
- **Risk**: Low.

### Batch 3: Version, Packaging, and Docs Sync
- **Actions**:
  - `20260625-124339-S1-X1`: Bump version to `1.0.2` in `pyproject.toml`.
  - `20260625-124339-S4-X1`: Add version `1.0.2` release notes to `CHANGELOG.md`.
  - `20260625-124339-S1-X2`: Document new CLI options in `README.md` and CLI help strings in `ocman.py`.
  - `20260625-124339-S1-X4`: Document `PYTHONPATH=.` requirements in `README.md`.
  - `20260625-124339-S1-X5`: Exclude `opencode.json` and `opencode.jsonc` from built packages by updating `pyproject.toml`.
- **Files**: `pyproject.toml`, `CHANGELOG.md`, `README.md`, `ocman.py`
- **Risk**: Low.

### Batch 4: CI Workflow
- **Actions**:
  - `20260625-124339-S1-X3`: Add GitHub Actions workflow `.github/workflows/ci.yml` running `pytest` across Python 3.10-3.14.
- **Files**: `.github/workflows/ci.yml`
- **Risk**: Low.

## Validation Method
- Run `PYTHONPATH=. pytest` locally to ensure all existing and new tests pass.
- Verify package build manually using `python3 -m build` or check Hatch build targets.
- Verify CLI help output prints updated commands.
