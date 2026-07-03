# CI Assessment

## Existing CI
`.github/workflows/ci.yml`: on push/PR to main; matrix (ubuntu/macos/windows × Python 3.10-3.14);
`pip install -e .[dev]`; `pytest` with `PYTHONPATH=.`. Good, broad, safe. No publish/deploy steps.

## Assessment
- **Tests:** covered (matrix pytest). Adequate.
- **Lint/format:** none configured. The repo has no ruff/flake8/black config. Adding a linter to CI would
  require choosing/adding tooling not present in the repo — over-scope for this run (KISS; would also risk
  failing CI on pre-existing style). NOT added.
- **Type check:** none configured. The type checker produces many false positives on pysqlite3/textual dynamic
  patterns; adding mypy/pyright to CI now would be noisy and require config/annotations — over-scope. NOT added.
- **Build check:** could add a `python -m build`/`pip install .` smoke, but the matrix already does
  `pip install -e .[dev]` which exercises packaging metadata. Marginal value; NOT added.
- **Security/dependency scan:** minimal deps; over-scope for a personal tool. NOT added.

## Decision
No CI changes this run. The existing CI is safe, cross-platform, and materially validates the release.
Adding linters/type-checkers would require introducing tooling/config not in the repo and risks noise —
that exceeds the low-risk bar for CI changes in `00-run-protocol.md`.

## Note
CI runs on branch `main` / PRs to `main`. The remote is `opencode-recover`; if the repo is renamed to
`ocman`, CI is unaffected (branch-based, not name-based).
