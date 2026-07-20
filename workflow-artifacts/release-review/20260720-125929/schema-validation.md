# Schema Validation


## Section 6 assessment

- ocman operates on the OpenCode SQLite DB (external schema it reads/repairs) and its own
  `.ocbox` export bundle format + `ocman.toml` config. The delta did NOT change the .ocbox
  format, the DB schema handling, or the config schema; it changed only the in-memory
  directory-string rebasing during import. So no schema drift is introduced this cycle.
- The export/import round-trip is covered by tests (test_export_import), which pass.
- No schema tooling introduced (none native; not warranted). Residual risk: none new for the delta.
