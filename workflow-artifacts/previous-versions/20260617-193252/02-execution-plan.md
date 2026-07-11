# Execution Plan

## Run

- Run ID: 20260617-193252
- Repository: /home/gfariello/VC/ocman
- Branch: main
- Initial HEAD: f823aa6e6f9308fe3b0765a4d9d0775a36c90056
- Created: 2026-06-17T19:32:52+02:00
- Agent/model, if known: Antigravity

## Repository understanding

The repository `ocman` is a utility suite for OpenCode session analysis, transcript recovery, LLM-based compaction, and SQLite database prunes and cleans. It consists of a command-line script (`ocman.py`) and a newly added Textual TUI (`ocman_tui`) package. The public contract includes option flags for recursive delete, age-based retention prunes, and LLM model price datatables.

## Review strategy

We will proceed sequentially through Sections 1 to 8:
1. Auditing current state and establishing a baseline (completed).
2. Quality/security/edge cases analysis: focusing on database locks, error handling, credentials leakage, path validation, and transaction rollbacks.
3. Tests/regression: auditing test coverage of the newly added widgets and regression isolation.
4. Docs/specs: checking README, specification files, spec vs implementation alignment.
5. Usability/maintainability: review of CLI argument help, log messages, code modularity.
6. Packaging/compatibility/CI: review of pyproject.toml, versioning, dependencies, and CI workflows.
7. Implementation: address any findings discovered during the review.
8. Final ship review: running final automated tests, documenting results, and preparing final response.

## Section plan

| Section | Planned focus | Expected artifacts | Status |
|---|---|---|---|
| 1 Current state | Baseline inventory and configuration check | `00-run-metadata.md`, `01-inventory.md` | completed |
| 2 Quality/security/edge cases | Audit error handlers, SQL queries, path traversal safeguards | `02-quality-security-edge-cases.md` | planned |
| 3 Tests/regression | Audit pytest coverage, test isolation, mock state | `03-tests-regression.md` | planned |
| 4 Docs/specs/examples | Audit spec files, README instructions, alignment | `04-docs-specs-examples.md` | planned |
| 5 Feature/usability/maintainability | Audit usability of new TUI tabs, console logging, CLI help | `05-feature-usability-maintainability.md` | planned |
| 6 Compatibility/packaging/CI/release | Dependency constraint updates, Hatch config, CI options | `06-compatibility-packaging-release.md` | planned |
| 7 Implementation | Execution of required bugfixes and hardening changes | `07-implementation.md`, commits | planned |
| 8 Final ship review | Run final tests, push plan, and final ship recommendation | `08-final-ship-review.md` | planned |

## Known constraints

- Untracked changes are present in the working tree from the TUI implementation (`ocman_tui/` and `tests/test_tui.py`). We will audit these files in their present state and commit them as part of Section 7.
- Modifying SQLite schemas should be avoided unless absolutely necessary for correctness.

## Non-goals

- Refactoring the core CLI execution loop of `ocman.py` without bug-related justification.
- Formatting-only updates (PEP8, sorting imports, etc.) without functional improvement.

## Parallel audit lane plan

Parallel audit lanes will not be used because this is a relatively small, focused repository, and a single serial review by the main agent will ensure absolute consistency and depth of analysis.

## Validation approach

We will execute `PYTHONPATH=. pytest -v` at each phase checkpoint to ensure zero regression.

## Commit and push approach

- Commits will be made locally at logical checkpoints during Section 7.
- No remote pushes will be executed unless the user gives explicit consent.
