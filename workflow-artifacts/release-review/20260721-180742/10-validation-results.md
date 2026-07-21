# 10 Validation Results

## Test suite (baseline, Section 1/3)
- Command: PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q
- Result: 473 passed, 2 skipped in 131.81s
- Skips: benchmark tests gated on OCMAN_BENCHMARK=1 (expected)
- Environment: Linux, Python 3.14 venv

## Section 7 post-implementation validation
- Version consistency: pyproject 1.3.0, cli.py __version__ 1.3.0, CITATION 1.3.0; `ocman --version` -> "ocman 1.3.0".
- Full test suite: 473 passed, 2 skipped in 136.32s (unchanged; edits behavior-neutral).
- Build: `python -m build` -> ocman-1.3.0.tar.gz + ocman-1.3.0-py3-none-any.whl.
- `twine check`: PASSED for sdist and wheel.
- gitleaks full history (414 commits): NO LEAKS FOUND (3 prior-run-artifact hits baselined).
- Dashes in authored prose: only the 2 sanctioned exceptions (CHANGELOG NOTICE attribution; AGENTS.md rule text quoting the glyph). No new violation.
