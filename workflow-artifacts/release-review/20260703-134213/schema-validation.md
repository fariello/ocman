# Schema Validation

## Discovered data contracts
1. **`.ocbox` export bundle** (ZIP): `meta.json` (fields: export_version "2.0", exported_at, main_session_id,
   all_session_ids, source_project), `db_data/<table>.jsonl` per `SESSION_RELATIONAL_TABLES`,
   `session_diffs/<sid>.json`. No formal JSON Schema file; the format is defined by the export/import code.
2. **Backup ZIP**: opencode.db (+ -wal/-shm), ocman.toml, ocman_history.json, session_diff/<name>.json.
   Restore expects at least `opencode.db` present (validated at ocman.py:6796).
3. **`ocman.toml`** config: keys in `DEFAULT_CONFIG` (db_path, history_path, default_out_dir,
   default_backup_dir, default_model, default_retention_days, keep_temp, include_tools, all_roles).
4. **`ocman_history.json`** sidecar ledger: `{"runs": [...]}`.

## Validation performed
- Import already validates: table names (allowlist `SESSION_RELATIONAL_TABLES` / `.isidentifier()`), session-ID
  format (`^[a-zA-Z0-9_\-]+$`). Covered by `test_import_session_sql_injection_rejection` and
  `test_import_session_path_traversal_rejection`.
- Round-trip export→import validated by `test_bundle_session_data`, `test_import_session_*`.
- Backup→restore round-trip validated by `test_backup_opencode`, `test_restore_from_zip`.
- Config load/save validated by `test_load_save_config`.

## Compatibility / drift
- `export_version` is "2.0"; the import code also handles a legacy `db_data.json` (old format) for backward
  compatibility. No forward-compat versioning check beyond that. Acceptable for a personal tool.
- **SCH note (not a blocker):** the restore path lacks member-path sanitization on `extractall` (S2-S1); this
  is the one data-contract-adjacent safety gap, fixed in S7.

## CI opportunity
- No schema-specific CI needed beyond the existing pytest coverage.

## Residual risk
- No formal JSON Schema files; the contracts are code-defined and test-covered. Introducing schema tooling
  would be over-scope (KISS) — not done.
