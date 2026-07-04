# Schema Validation (follow-up run)

Contracts unchanged from run 20260703-134213: `.ocbox` bundle (v2.0), backup ZIP, `ocman.toml`, history JSON.

## Delta impact
- **`ocman.toml`:** new key `history_max_runs` (int, default 500). **Additive and backward-compatible** —
  older configs without it fall back to the default; `save_ocman_config` now merges over `DEFAULT_CONFIG`
  so a partial config still renders. No migration needed. Covered by `test_history_*` + config tests.
- **`.ocbox` / backup ZIP / history JSON:** unchanged. Import validation (IDs/tables/columns) and restore
  Zip-Slip guard unchanged. `export_version` still 2.0.
- **History file:** the new trim-on-save caps `runs` length; `cumulative` totals preserved — no format change,
  purely a size bound. Backward/forward compatible (readers ignore list length).

## Validation performed
- Config round-trip + `history_max_runs` cap/zero tests pass; export/import round-trip + rejection tests pass.

## Verdict
No schema drift or compatibility risk introduced by the delta. No `SCH` finding.
