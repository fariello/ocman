# Implementation Plan

## Run

- Run ID: 20260624-024342
- Created: 2026-06-24 02:57:00 (Local Time)
- Based on sections completed: Steps 1 through 6

## Scope summary

The scope of this implementation is to fix the identified SQLite connection leaks under exception pathways, add unit tests to protect these paths, and add integration tests for CLI argument execution to increase coverage and release confidence.

## Explicit non-goals

- Refactoring the config parser or changing configuration key/value formats.
- Changing CLI flags or TUI styling/widget properties.
- Modifying the GitHub Actions workflows.

## Change batches

| Batch ID | Source finding IDs | Description | Files likely to change | Risk | Public behavior change | Required validation | Commit plan | Status |
|---|---|---|---|---|---|---|---|---|
| B1 | 20260624-024342-S2-E1 to E7 | Wrap connection creations in try-finally blocks or context managers to prevent leaks under exceptions | ocman.py, ocman_tui/widgets/database.py, ocman_tui/app.py | Low | None | pytest | Commit B1 changes referencing findings/actions | planned |
| B2 | 20260624-024342-S3-T1 | Add unit tests verifying connection closure under exceptions | tests/test_ocman.py | Low | None | pytest | Commit B2 changes referencing findings/actions | planned |
| B3 | 20260624-024342-S3-T2 | Add CLI arguments integration tests | tests/test_ocman.py | Low | None | pytest | Commit B3 changes referencing findings/actions | planned |

## Deferred findings

*(None)*

## Blocked findings

*(None)*

## Wont-do findings

*(None)*

## Deprecated-code decisions

| Candidate ID | Decision | Evidence | Action |
|---|---|---|---|
| 20260624-024342-S1-DEP1 | Keep | ocman_tui/core.py imports directly from ocman.py rather than duplicating code | None (keep as is) |

## CI decisions

| CI ID | Decision | Rationale | Action |
|---|---|---|---|
| 20260624-024342-CI1 | No change | The existing GHA configuration is sufficient and runs tests across Python versions. | None |

## Validation plan

- Run `pytest` before starting batch modifications to verify baseline state.
- Run `pytest` after each batch is implemented to verify no regressions and that new tests pass.

## Commit plan

- Commit 1: `Fix SQLite connection leaks in CLI and TUI (20260624-024342-S2-A1 through 20260624-024342-S2-A7)`
- Commit 2: `Add unit and integration tests for connection leaks and CLI argument handling (20260624-024342-S3-A1, 20260624-024342-S3-A2)`
