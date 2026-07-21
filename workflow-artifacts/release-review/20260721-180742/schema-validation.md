# Schema Validation

## Discovered schemas / data contracts
- ocman has no standalone schema files. Its public serialized contracts are:
  1. `--json` outputs on scriptable commands (list projects/sessions/running, spend, doctor,
     lr filters). 45 json references in cli.py.
  2. The opencode SQLite DB schema (external, owned by OpenCode; ocman reads/writes it).
  3. `ocman.toml` config keys.
  4. The portable export/import bundle format (.ocbox).

## Assessment
- 1.3.0 added NO new serialized format and changed NO existing one. New commands either
  produce human output (reconnect/kill/rename) or reuse existing --json shapes:
  - lr/lp/ls filters: the filter narrows the SAME existing json payload; an empty match emits
    a well-formed empty payload (tested: test_list_*_filter_no_match_json_is_empty).
  - doctor server check: adds a new check ROW into the existing doctor json envelope
    (test_run_doctor_checks_includes_listening_servers); envelope shape unchanged.
- No schema drift. No backward-incompatible serialization change. No SCH finding.

## Backward compatibility
- The one CHANGELOG "Changed" item (`ls <ARG>` fallback) preserves project-scope PRECEDENCE
  (regression test test_list_sessions_project_scope_precedence_preserved), so every
  previously-working invocation behaves identically; only the previously-fatal case becomes a
  useful filter. Additive, not breaking.
- No CI validation gap for schemas (there is no schema tooling to run; the json contracts are
  covered by unit tests).
