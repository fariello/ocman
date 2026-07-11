# Schema and Data Contract Validation

- **Run ID**: `20260625-124339`

## Identified Schemas and Data Contracts

1. **SQLite Database Schema**: Represents the relational session database `opencode.db` containing `project`, `session`, `message`, `event`, etc. tables.
2. **Settings Config (`ocman.toml`)**: Key-value TOML configuration stored in `~/.config/opencode/ocman.toml`.
3. **Session Bundle JSON formats (`meta.json` and `db_data.json`)**: Formats serialized and compressed into `.ocbox` ZIP files during session exports.
4. **Sidecar Ledger JSON (`ocman_history.json`)**: Tracks historical activity logs and cumulative grand metrics.

## Schema Validation & Compatibility Assessment

### 1. SQLite Database Schema Integrity
- **Validation**: On application startup or when showing info, `ocman` can perform a database PRAGMA integrity check.
- **Findings**: The schema layout is compatible across Python SQLite drivers. Foreign key constraints are toggled correctly during batch operations.

### 2. Settings Config (`ocman.toml`)
- **Validation**: Parsed using Python's standard library parser.
- **Findings**: Settings auto-save and precedence rules (Defaults < Config File < CLI arguments) are validated and tested. No schema drift identified.

### 3. Session Bundle JSON formats (`meta.json`, `db_data.json`)
- **Validation**: Serialized via Python's standard `json` module.
- **Vulnerabilities**:
  - **20260625-124339-S2-S1 (SQL Injection)**: The data contract does not whitelist table keys or sanitize column names.
  - **20260625-124339-S2-S2 (Path Traversal)**: The session IDs inside `meta.json` are not validated against expected alphanumeric format prior to filesystem mapping.
- **Assessment**: These vulnerabilities will be resolved by introducing strict schema validation routines on session import (whitelisting table/column names, checking session ID structure).

### 4. Sidecar Ledger JSON (`ocman_history.json`)
- **Validation**: Automatically loaded and saved with fallback defaults.
- **Findings**: Safe against drift because missing keys in cumulative objects are default-initialized (e.g. `c.get("projects_deleted", 0)`).
