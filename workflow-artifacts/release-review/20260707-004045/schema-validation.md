# Schema validation (run 20260707-004045)

Data contracts in ocman: `.ocbox` bundle (meta.json export_version "2.0" + db_data JSONL + diffs),
whole-system backup ZIP, `ocman.toml` config, and the recovery-artifact filename scheme.

- **Recovery filename scheme (1.1.0 change):** canonical `YYYYMMDD-HHMM-<sid>.<kind>.md`.
  `parse_recovery_name` reads BOTH legacy forms + canonical (backward read-compat), covered by
  test_recovery_naming. No `.ocbox`/backup-ZIP format change in 1.1.0 (export_version unchanged).
- **ocman.toml:** two new keys added with safe defaults; `load_ocman_config` ignores unknown keys
  and merges from DEFAULT_CONFIG, so old configs load unchanged (test_config_parsing). No drift.
- No JSON Schema files to validate; contracts are code-defined and test-covered. No schema finding.
