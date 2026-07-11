# Implementation Plan

## Run

- Run ID: 20260618-023542
- Created: 2026-06-18T02:40:00+02:00
- Based on sections completed: Sections 1 through 6

## Scope summary

This implementation addresses five quality, correctness, test coverage, and documentation findings identified during the pre-release audit:
1. Deletion of the deprecated and obsolete `rebuild_opencode.sh` script.
2. Refactoring recursive project/session deletion code to remove thread-unsafe global `builtins.input` monkeypatching, substituting it with clean parameterization.
3. Hardening the session queries/deletions against SQLite variable limit overflows for sets of sessions >999.
4. Adding integration testing for TUI project deletion flows.
5. Supplementing the `README.md` arguments table with the missing `--delete-project` CLI flag.

## Explicit non-goals

- Structural separation of `ocman.py` (which must remain monolithic for portability).
- Adding complex new functional workflows not requested by the user.

## Change batches

| Batch ID | Source finding IDs | Description | Files likely to change | Risk | Public behavior change | Required validation | Commit plan | Status |
|---|---|---|---|---|---|---|---|---|
| `20260618-023542-B1` | `20260618-023542-S1-DEP1` | Remove `rebuild_opencode.sh` | None (Delete `rebuild_opencode.sh`) | Very Low | None | Verification of deletion | Local commit | planned |
| `20260618-023542-B2` | `20260618-023542-S2-E1`, `20260618-023542-S2-E2` | Add batching for SQLite queries and add `confirm` flag to CLI deletion functions | `ocman.py`, `ocman_tui/app.py` | Low | CLI prompt can be bypassed programmatically | Run existing unit tests | Local commit | planned |
| `20260618-023542-B3` | `20260618-023542-S3-T1` | Add `test_tui_app_project_deletion()` test | `tests/test_tui.py` | Low | None | Execute pytest suite | Local commit | planned |
| `20260618-023542-B4` | `20260618-023542-S4-D1` | Document `--delete-project` flag | `README.md` | Low | None | View updated file | Local commit | planned |

## Deferred findings

None.

## Blocked findings

None.

## Wont-do findings

None.

## Deprecated-code decisions

| Candidate ID | Decision | Evidence | Action |
|---|---|---|---|
| `20260618-023542-DEP1` | Safe to remove now | Deprecated header warning and duplication of native `ocman` features | Remove `rebuild_opencode.sh` |

## CI decisions

No changes are planned for CI as the existing workflow is correct and checks the full matrix.

## Validation plan

Before and after applying each change batch, run:
- `PYTHONPATH=. pytest` to verify regression status.

## Commit plan

- Commit 1: `Remove deprecated rebuild_opencode.sh script (20260618-023542-B1)`
- Commit 2: `Add confirm flag to CLI deletions and batch queries to avoid SQLite variable limit (20260618-023542-B2)`
- Commit 3: `Add test coverage for TUI project deletion wizard (20260618-023542-B3)`
- Commit 4: `Document --delete-project in README.md argument reference (20260618-023542-B4)`
