# Schema validation

Public serialized formats (no dedicated schema files):
- `--json` envelope `{schema_version, command, <command>: payload}` (spend/doctor/running/
  list). schema_version is a stable integer; unchanged this cycle. Tested by the JSON tests
  (e.g. spend --json). No drift.
- `.ocbox` bundle: meta.json (with `kind`) + db_data/<table>.jsonl. Unchanged this cycle;
  round-trip export/import tested. No compatibility risk.
- `ocman.toml` config: rendered from DEFAULT_CONFIG_TEMPLATE; README template validated as
  parseable TOML and complete (S4). The FU-01 fix made partial saves preserve unmanaged keys.

No SCH findings. No new schema tooling introduced (none warranted).
