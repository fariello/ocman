# Implementation Plan (consolidated, Sections 1-6 -> Section 7)

## Scope summary
This follow-up review found the delta since v1.0.3 to be sound and well-tested. The **only product change**
required for release is the **1.0.4 version bump + CHANGELOG heading** (S1-A1). All other findings are
deferred-with-reason or recommend-only.

## Change batches

### Batch A — Release version bump (S7-A1 / S1-A1)
- `ocman.py:191`: `__version__ = "1.0.3"` → `"1.0.4"`.
- `pyproject.toml:7`: `version = "1.0.3"` → `"1.0.4"`.
- `ocman_tui/__init__.py`: fallback literal `"1.0.3"` → `"1.0.4"` (runtime still single-sources from ocman;
  keep the fallback in sync).
- `CHANGELOG.md`: rename `## [Unreleased]` → `## [1.0.4] - 2026-07-04` (keep the existing subsections).

## Files likely to change
`ocman.py`, `pyproject.toml`, `ocman_tui/__init__.py`, `CHANGELOG.md`. No logic changes.

## Risk / public behavior
Low Remediation Risk. No behavior change beyond the reported version string. Version tests
(`test_parse_args_version`, `test_cli_version`) reference `ocman.__version__` so they auto-track.

## Required validation
`PYTHONPATH=. pytest` stays green (91). `ocman --version` → 1.0.4; `ocman_tui.__version__` → 1.0.4.

## Deferred / recommend-only (not implemented this run)
| ID | Disposition | Rem.Risk / axis | Reason |
|---|---|---|---|
| S2-M1 | defer | Medium / complexity | Narrowing the worker-guard RuntimeError catch is more fragile than the current guard |
| S3-R1 | defer (documented) | Medium / functionality | A sys.path-forcing conftest could mask real install issues; README documents the invocation; CI is safe |
| S6-CI1 | recommend-only | Low | gitleaks-in-CI is a deliberate maintainer hardening decision, not a 1.0.4 blocker |
| DEP2 | defer | Medium / functionality | Public class/app rename risk |
| disk-usage IPD | separate | — | Approved-for-planning; needs its own execution approval; not a 1.0.4 change |

## Deprecated-code / CI decisions
No deprecations acted on. No CI changes (gitleaks recommended as CI1 follow-up).
