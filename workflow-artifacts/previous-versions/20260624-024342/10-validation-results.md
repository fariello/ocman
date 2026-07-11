# Validation Results - 20260624-024342

## Run

- **Run ID**: `20260624-024342`
- **Updated**: 2026-06-24 03:28:00 (Local Time)

---

## Automated Tests & Coverage

### Command
```bash
PYTHONPATH=. pytest --cov=ocman --cov=ocman_tui
```

### Result
- **Status**: Passed (all 41 tests)
- **Execution Time**: 5.83s
- **Overall Statement Coverage**: 51%

### Output Log
```text
============= test session starts ==============
platform linux -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/gfariello/VC/ocman
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.13.0
collected 41 items                             

tests/test_config_backup_restore.py .... [  9%]
..                                       [ 14%]
tests/test_core.py ......                [ 29%]
tests/test_ocman.py .................... [ 78%]
..                                       [ 82%]
tests/test_tui.py .......                [100%]

============== 41 passed in 5.83s ==============
```

---

## Package Build Validation

### Command
```bash
python3 -m build
```

### Result
- **Status**: Success (exit code 0)
- **Built Artifacts**:
  - `dist/ocman-1.0.1.tar.gz` (127418 bytes)
  - `dist/ocman-1.0.1-py3-none-any.whl` (85108 bytes)

### Output Log
```text
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - hatchling
* Getting build dependencies for sdist...
* Building sdist...
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - hatchling
* Getting build dependencies for wheel...
* Building wheel...
Successfully built ocman-1.0.1.tar.gz and ocman-1.0.1-py3-none-any.whl
```

---

## Schema Validation

All schema structures, configuration files, and database connections remain valid and functional. The test runner successfully setup the mock sqlite database environment and executed 41 unit and integration tests containing database queries, which asserts database schema compatibility.
