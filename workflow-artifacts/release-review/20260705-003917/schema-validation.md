# Schema validation

## Data contracts
- `.ocbox` export bundle: `export_version` = "2.0" (ocman.py:5728) — UNCHANGED in this delta. Import still
  validates session-ID regex + allowlists tables/columns + accepts legacy "1.0"/db_data.json. No drift.
- Backup ZIP: db family + ocman.toml + ocman_history.json + session_diff/*.json — unchanged.
- `ocman.toml`: DEFAULT_CONFIG. Delta ADDED keys (`copy_restart_to_project_prompts`, and `history_max_runs`
  from 1.0.4) with defaults, merged over DEFAULT_CONFIG on save → old configs load fine (additive, no drift).
- `ocman_history.json`: cumulative + runs; runs capped by history_max_runs; back-compat load fills missing
  keys (_load_history). No migration needed.

## Drift found
- Documentation drift only: README documents `default_model` which is not a real config key (D1). This is a
  docs-vs-schema mismatch, fixed in S7. No code/serialized-format drift.

## Validation
Config round-trip and .ocbox import/export are covered by tests (test_config_parsing, test_config_backup_restore,
test_export_import). All pass.

## Verdict
No schema/serialized-format compatibility risk in the delta. One docs-vs-config drift (D1) fixed in S7.
