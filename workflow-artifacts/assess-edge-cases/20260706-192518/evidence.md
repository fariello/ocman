# Evidence - assess-edge-cases (filter + naming + migration) run 20260706-192518

## Files inspected
- `ocman.py`:
  - `RECOVERY_KINDS`, `canonical_recovery_name`, `parse_recovery_name` (naming source of truth).
  - `cli_filter` (4856-4952): input read, scope resolution (4881-4896), output-name derivation
    (4928-4942).
  - `safe_filename` (2517-2536): slug fallback + 80-char cap.
  - `_STARTUP_TIME_LOCAL` (103) and the timestamp helpers (106-113).
- `scripts/migrate_recovery_names.py`: `plan_migration` (symlink skip, top-level), `migrate_dir`
  (containment guard, collision skip, os.rename).

## Repro probes run (read-only, temp dirs; LLM + model mocked)
- `parse_recovery_name` battery: filter scope-form, sid-with-dashes, empty stem, just-kind,
  double-kind, invalid month/hour, 8-digit-sid date-shaped, uppercase suffix.
- `canonical_recovery_name`: empty sid (-> `session` fallback), unicode sid (-> ascii slug),
  bogus kind (-> accepted, produces `...bogus.md`).
- Round-trip: `canonical_recovery_name` -> `parse_recovery_name` for a `12345678-x` sid (holds)
  and a real `ses_1799fde97ffeB682fah1bBE3xL` (holds).
- `cli_filter`: empty input (sends empty doc), punctuation-only scope (-> `session` slug),
  200-char scope (-> 80-char slug), scope `''`/`'   '`/`None` (empty+None error, whitespace slips).
- Migration: two same-minute legacy files -> first renamed, second skipped (collision), both
  files remain on disk.
- Baseline: `PYTHONPATH=. pytest` -> 150 passed, 2 skipped (not a probe, context only).

## Not exhaustively tested / assumptions
- Did not test true concurrent execution (two ocman processes) - the migration is a single
  local invocation; concurrency is out of scope for this local tool.
- DST/timezone: reasoned from `_STARTUP_TIME_LOCAL = datetime.now()` (naive local); minute-level
  local rendering has no offset math, so DST does not corrupt the name (only shifts the wall-clock
  value, which is expected). Not separately reproed.
- Assumed real session ids are `ses_<base62>` (EC-6 unreachability rests on this).

## Scope exclusions honored
- Did not assess `.agents/workflows/` or `workflow-artifacts/` as project code.
