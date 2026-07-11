# Execution Plan

## Run

- Run ID: `20260625-124339`
- Repository: `/home/gfariello/VC/ocman`
- Branch: `main`
- Initial HEAD: `26da22765355651c68f237ef3fcf0963cb57b7db`
- Created: `2026-06-25T12:43:39-04:00`
- Agent/model, if known: Antigravity (Gemini 1.5 Pro)

## Repository understanding

`ocman` (OpenCode Manager) manages agent sessions, including recovery, backup, cleanups, compaction, and now session/project moving and portable session export/import. The project is primarily used as a CLI tool and a Textual TUI dashboard. Release intent is to package version `1.0.2` (incrementing from `1.0.1`) with all the new move and export/import features, verifying safety, security, compatibility, and correctness.

## Review strategy

We will proceed sequentially through Sections 1 to 8:
- Section 1: Setup and Inventory (Current Phase).
- Section 2: Quality, Security, and Edge Cases (focusing on path traversal, SQL injection, error rollback safety).
- Section 3: Tests & Regressions (verifying all 52 tests, check for gaps in new move/export/import tests).
- Section 4: Documentation (verifying README, CHANGELOG, CLI help strings).
- Section 5: Usability & Maintainability (TUI dialog flow, argument parsing, error format).
- Section 6: Packaging & Compatibility (verify build hooks, dependencies, Python version targets, adding a basic Github Actions CI).
- Section 7: Implementation (execute safe improvements).
- Section 8: Final validation & user gate.
- Section 9: Build and prepare for packaging.

## Section plan

| Section | Planned focus | Expected artifacts | TodoWrite item | Status |
|---|---|---|---|---|
| 1 Current state | Initial setup, inventory, and execution planning | `00-run-metadata.md`, `01-repository-inventory.md`, `02-execution-plan.md`, registers, `deprecation-candidates.md` | Section 1 | completed |
| 2 Quality/security/edge cases | Audit safety, database transactions, path operations, and resource leaks | `final-bug-security-audit.md` | Section 2 | not_started |
| 3 Tests/regression | Validate current tests, identify coverage gaps, run test suites | Registers update | Section 3 | not_started |
| 4 Docs/specs/examples | Check README, CHANGELOG, verify help-text alignment with new commands | Registers update | Section 4 | not_started |
| 5 Feature/usability/maintainability | Review TUI responsiveness, CLI argument usability, and logger readability | Registers update | Section 5 | not_started |
| 6 Compatibility/packaging/CI/release | Verify `pyproject.toml`, check dependencies, schema check, configure basic CI | `ci-assessment.md`, `schema-validation.md` | Section 6 | not_started |
| 7 Implementation | Consolidate and execute planned fixes | `09-implementation-plan.md`, code changes, commits | Section 7 | not_started |
| 8 Final ship review | Run final tests, package checks, compile final response, request gate approval | `10-validation-results.md`, `11-push-plan.md`, `12-final-response.md` | Section 8 | not_started |

## Known constraints

- Avoid remote pushing during the audit phases.
- No destructive database commands unless isolated.
- Ensure to use `PYTHONPATH=.` when invoking commands since local imports reference `ocman` directly.

## Non-goals

- Refactoring major backend code that is outside the scope of session management/moving/exporting.
- Aesthetic TUI overhauls not related to usability issues.

## Parallel audit lane plan

Controlled parallel lanes will not be used. The repository size is small to moderate and can be audited sequentially by the primary agent to maintain single-agent context consistency and reduce synchronization overhead.

## Validation approach

- `PYTHONPATH=. pytest` (run all unit tests)
- `python3 -m py_compile ocman.py ocman_tui/*.py` (check syntax compilation)
- `pip install --dry-run .` or standard package build `python3 -m build` to verify packaging.

## Commit and push approach

- Git ignore file `repository-review/` is already configured.
- Local git commits will be made for any changes during implementation, referencing Action IDs.
- No remote pushes will occur until Section 9 after user approval.

## Updates

None.
