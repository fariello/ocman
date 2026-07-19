# CI assessment

Existing CI (adequate; no change recommended):
- `.github/workflows/ci.yml`: matrix ubuntu/macos/windows x Python 3.10-3.14; `pip install
  -e .[dev]`; `pytest` (PYTHONPATH=.). Good coverage of the supported platforms/versions.
- `.github/workflows/secret-scan.yml`: gitleaks over full history, .gitleaksignore baseline.
  NOTE: this job would flag the 6 synthetic test fixtures until S2-S1 baselines them
  (Section 7 action A2). After baselining, CI stays green.

No CI additions recommended: the repo has no configured linter/type-checker, so adding one
would be speculative (not a repository-native command) and out of scope. A wheel-build check
job could be a future nice-to-have but is not release-blocking (build verified locally in S6).

## Published-version check
- PyPI published latest: 1.1.0. Proposed release: 1.2.0 (minor). 1.2.0 > 1.1.0 -> valid bump.
- Local wheel build: `ocman-1.1.0-py3-none-any.whl` built cleanly via `python -m build`;
  contains ocman/ + ocman_tui/ + scripts/migrate_recovery_names.py; entry point
  `ocman = ocman:main`. (Will rebuild as 1.2.0 after the Section 7 bump.)
