# 10 Validation Results

| Command/check | Result | Notes |
|---|---|---|
| `PYTHONPATH=. pytest` (authoritative, CI-equivalent) | **91 passed, 2 skipped** | Documented repo command; matches CI (`pip install -e .[dev]` + `PYTHONPATH: .`) |
| `python -m pytest` (repo root) | 91 passed, 2 skipped | cwd on sys.path → resolves local ocman.py |
| verify tool `run_checks.py` (bare `pytest`) | 89 passed, **2 failed** — NOT a real failure | Console-script `pytest` does not add cwd to sys.path; picked up the **installed PyPI ocman 1.0.3** in this local venv (non-editable), which lacks this session's fixes. Environment shadowing, not a repo defect. See S3-R1. |
| `gitleaks detect` (Section 2) | 0 leaks / 156 commits | Authoritative secret scan |
| `scan_secrets.py` (Section 2) | 1582 candidates, all false positives | saved to secrets-scan.json |

## Evidence honesty note
The verify tool's 2 "failures" are a **local-environment artifact**: my dev venv has a non-editable PyPI
`ocman==1.0.3` in site-packages, so the bare `pytest` console script imported the stale installed package
instead of the working tree. Under the documented invocation (`PYTHONPATH=. pytest`) and under CI (editable
install + `PYTHONPATH: .`), the suite is fully green (91 passed). CI is not affected. Recorded as S3-R1
(a usability/robustness observation about invocation, not a code failure).

## Final validation (Section 8)
- Re-run after any Section 7 change; recorded in the Section 8 report.
