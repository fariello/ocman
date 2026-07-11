# Final Validation Results

- **Run ID**: `20260625-124339`

## Automated Test Execution

- **Command**: `PYTHONPATH=. pytest`
- **Result**: Success
- **Output Summary**:
  ```text
  ============= test session starts ==============
  platform linux -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
  rootdir: /home/gfariello/VC/ocman
  configfile: pyproject.toml
  plugins: cov-7.1.0, anyio-4.13.0
  collected 56 items

  tests/test_config_backup_restore.py ...... [ 10%]
  tests/test_core.py ......                  [ 21%]
  tests/test_export_import.py .......        [ 33%]
  tests/test_move.py ........                [ 48%]
  tests/test_ocman.py ...................... [ 87%]
  tests/test_tui.py .......                  [100%]

  ============== 56 passed in 6.06s ==============
  ```

## Version Number Synchronization Check
- **Pyproject.toml version**: `1.0.2`
- **ocman.py `__version__`**: `1.0.2`
- **ocman_tui `__version__`**: `1.0.2`
- **Result**: Fully synchronized.

## CLI Parameter Check
- **Command**: `PYTHONPATH=. python3 ocman.py --help`
- **Result**: Verified that new arguments (`--move-project`, `--move-session`, `--to`, `--rebase-paths`, `--from`, `--metadata-only`, `--export-session`, `--import-session`, `--to-project`, `--new-project-path`) are listed correctly with detailed descriptions.
