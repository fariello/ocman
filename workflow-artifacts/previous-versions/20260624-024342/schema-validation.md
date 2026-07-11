# Schema Validation

## Run

- Run ID: 20260624-024342
- Updated: 2026-06-24 02:55:00 (Local Time)

## Schema and data contract inventory

| ID | Schema or contract | Location | Public/internal | Consumers/producers | Status |
|---|---|---|---|---|---|
| 20260624-024342-SCH1 | SQLite database schema | ~/.local/share/opencode/opencode.db | Internal | Producer: opencode; Consumer: ocman | Valid (validated via tests) |
| 20260624-024342-SCH2 | ocman.toml config schema | ~/.config/opencode/ocman.toml | Internal | Producer: ocman; Consumer: ocman | Valid |
| 20260624-024342-SCH3 | ocman_history.json history schema | ~/.local/share/opencode/ocman_history.json | Internal | Producer: ocman; Consumer: ocman | Valid |

## Validation commands

| Command | Purpose | Result | Notes |
|---|---|---|---|
| pytest | Implicitly validates database queries against schema in test fixtures | Clean | 36 passed |

## Examples, fixtures, and sample data validation

| ID | Example/fixture/sample | Schema or contract | Result | Notes |
|---|---|---|---|---|
| 20260624-024342-SCH-F1 | test_opencode.db fixture | SQLite schema | Clean | Initialized in test setup fixture |

## Drift findings

*(None)*

## Compatibility concerns

*(None)*

## CI opportunities

*(None. The database is user-local, and schema definitions are mocked directly in unit tests).*

## Final status

Schema validation is sufficient for release. No compatibility concerns or schema drift detected.
