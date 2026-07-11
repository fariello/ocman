# Schema Validation

## Run

- Run ID: 20260618-023542
- Updated: 2026-06-18T02:39:40+02:00

## Schema and data contract inventory

| ID | Schema or contract | Location | Public/internal | Consumers/producers | Status |
|---|---|---|---|---|---|
| `20260618-023542-SCH1` | SQLite OpenCode DB schema | `~/.local/share/opencode/opencode.db` | Internal | OpenCode (producer/consumer), ocman (consumer/remover) | Valid |
| `20260618-023542-SCH2` | TOML ocman Configuration schema | `~/.config/opencode/ocman.toml` | Internal | ocman TUI/CLI (consumer/producer) | Valid |
| `20260618-023542-SCH3` | JSON Historical Activity Log schema | `~/.local/share/opencode/ocman_history.json` | Internal | ocman TUI/CLI (producer/consumer) | Valid |

## Validation commands

| Command | Purpose | Result | Notes |
|---|---|---|---|
| `ocman info -v` | Run SQLite PRAGMA integrity check on the database | Passed | Checked integrity natively in SQLite |

## Examples, fixtures, and sample data validation

| ID | Example/fixture/sample | Schema or contract | Result | Notes |
|---|---|---|---|---|
| `20260618-023542-SMP1` | `tests/test_tui.py` database fixture | SQLite OpenCode DB schema | Passed | Correctly seeds and queries the tables |
| `20260618-023542-SMP2` | `DEFAULT_CONFIG` / `DEFAULT_CONFIG_TEMPLATE` | TOML ocman config schema | Passed | Loaded properly by parser |

## Drift findings

| ID | Description | Affected artifacts | Severity | Next step |
|---|---|---|---|---|
| None | No schema or data contract drift identified | None | N/A | None |

## Compatibility concerns

| ID | Schema or output | Concern | Public behavior change | Recommendation |
|---|---|---|---|---|
| `20260618-023542-SCH-R1` | SQLite Foreign Keys | foreign_keys PRAGMA is explicitly toggled `OFF` during batch deletes. | If tables schema changes, orphan records might remain if not handled by SESSION_RELATIONAL_TABLES sequence. | Keep SESSION_RELATIONAL_TABLES synchronized with upstream OpenCode DB changes. |

## CI opportunities

| ID | Proposed check | Rationale | Recommendation |
|---|---|---|---|
| `20260618-023542-SCH-CI1` | Config schema parsing verification | Prevents invalid configurations from crashing startup | Add automated schema parsing tests in CI suite |

## Final status

Schema validation and compatibility are sufficient for release. The SQLite database integrity validation and atomic JSON ledger writes are robust and safe.
