# IPD: Cross-Platform Support and CI Matrix for macOS and Windows

## Goal
The goal of this enhancement is to ensure `ocman` installs and runs flawlessly on Linux, macOS, and Windows. We will verify compatibility automatically on every push and pull request using a multi-platform testing matrix in GitHub Actions.

## Proposed Changes

### 1. Dependency Adjustments in [pyproject.toml](file:///home/gfariello/VC/ocman/pyproject.toml)
* **Problem**: `pysqlite3-binary` is listed as a hard dependency. Since it lacks pre-compiled wheels for macOS and Windows, `pip install` can fail due to compilation errors.
* **Solution**: Use PEP 508 environment markers to make `pysqlite3-binary` a Linux-only dependency. macOS and Windows will automatically skip installing it and fall back to the standard library `sqlite3` module.
* **Diff Concept**:
  ```toml
  dependencies = [
      "textual>=3.0.0",
      "rich>=13.0.0",
      "pysqlite3-binary>=0.5.0; sys_platform == 'linux'",
  ]
  ```

### 2. Process Check Optimization in [ocman.py](file:///home/gfariello/VC/ocman/ocman.py)
* **Problem**: The database cleanup and maintenance functions call `pgrep` to check for active `opencode` processes. Although the code catches exceptions and passes on Windows, triggering `FileNotFoundError` on every cleanup is inefficient.
* **Solution**: Check `sys.platform` and only execute the `pgrep` process check on non-Windows platforms (e.g., Linux and macOS).
* **Diff Concept**:
  ```python
  if not force and sys.platform != "win32":
      import subprocess
      try:
          proc_check = subprocess.run(
              ["pgrep", "-f", "opencode --continue"],
              ...
          )
  ```

### 3. GitHub Actions CI Matrix Update in [.github/workflows/ci.yml](file:///home/gfariello/VC/ocman/.github/workflows/ci.yml)
* **Problem**: The current GitHub workflow only runs on `ubuntu-latest`.
* **Solution**: Update the workflow to run tests across a matrix of operating systems and Python versions.
* **Matrix Setup**:
  - `runs-on`: `[ubuntu-latest, macos-latest, windows-latest]`
  - `python-version`: `["3.10", "3.11", "3.12", "3.13", "3.14"]`
* **Handling OpenCode CLI in tests**:
  - Since tests rely on `opencode` command existence, we will ensure that test environments mock `opencode` commands or handle its absence gracefully. The test suite already mocks `opencode` CLI or database calls in `test_export_import.py`, `test_move.py`, etc., but we will verify this works properly across different platforms.

---

## Verification and Testing Plan

### Automated Tests
* Run `PYTHONPATH=. pytest` locally to verify that the test suite still runs cleanly on Linux.
* Push changes to remote origin on a test or main branch to trigger the GitHub Actions workflow.
* Inspect the GitHub Actions runner execution output for macOS, Windows, and Linux to verify that all 56 tests pass successfully on all three platforms.

### Manual Verification
* Inspect the built wheels/sdist distributions to ensure that platform-specific requirements markers are correctly baked in.
