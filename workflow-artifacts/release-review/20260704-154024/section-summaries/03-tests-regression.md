# Per-Phase Report — Section 3: Tests and Regression

## Section
- Section: 3 | Run ID: 20260704-154024 | Status: complete

## Personas applied
- Testing/regression expert (2), QA/QC (1).

## What I did
- Ran the `verify` tool (`run_checks.py`) for evidence → it reported 2 failed test checks. Investigated:
  the tool ran the bare `pytest` console script, which (unlike `python -m pytest`) does not add cwd to
  `sys.path`, so in this local venv it imported the **installed PyPI ocman 1.0.3** (non-editable) instead of
  the working tree. Under the documented `PYTHONPATH=. pytest` and under CI (`pip install -e .[dev]` +
  `PYTHONPATH: .`), the suite is **91 passed, 2 skipped**. Recorded authoritative evidence in
  `10-validation-results.md` and the shadowing artifact as S3-R1 (not a code failure).
- Confirmed the delta's regression coverage: recovery/compaction (`test_recovery.py`), config parsing
  (`test_config_parsing.py`), TUI compaction e2e (red→green), worker-guard, zip-slip, delete-summary,
  history-cap, legacy-import, non-canonical-move — every prior High/LIVE finding is pinned (S3-T1).

## Why I did it
- Section 3 now mandates evidence-not-self-report; running the verifier surfaced the invocation subtlety,
  which is itself a (mild) release-relevant observation about how tests must be run.

## What I considered but did NOT do
| Considered | Why not | Next |
|---|---|---|
| "Fix" the 2 verify failures | They are a local-env shadowing artifact, not repo defects; CI is green | Record honestly (S3-R1) |
| Add a conftest.py to force repo-root on sys.path | Medium risk (could mask real install/packaging issues) + README already documents the invocation | Defer |
| Add new tests | Delta coverage is adequate | None |

## Key findings
| ID | Type | Sev | Rem.Risk | Title | Status |
|---|---|---|---|---|---|
| S3-T1 | T | Low | Low | Delta test coverage adequate | completed |
| S3-R1 | R | Low | Medium | Bare `pytest` can test an installed copy (documented; CI-safe) | identified (defer) |

## Deferrals (Fix Bar)
| ID | Rem.Risk | Axis | Why | Safe partial? |
|---|---|---|---|---|
| S3-R1 | Medium | functionality | A sys.path-forcing conftest could mask real packaging/install problems; README already warns and CI is correct | Documentation already exists |

## Non-applicable checks
- No coverage-gate config (intentional, prior run).

## Validation / commands
- `PYTHONPATH=. pytest` → 91 passed, 2 skipped (authoritative). verify tool run saved. See 10-validation-results.md.

## Handoff to next section
- Section 4: docs honesty for the delta (CHANGELOG `[Unreleased]` → the version heading is the S1-A1 fix).
