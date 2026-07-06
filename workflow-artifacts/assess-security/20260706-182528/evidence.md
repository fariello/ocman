# Evidence - assess-security (filter + migration) run 20260706-182528

## Files inspected
- `ocman.py`
  - `_safe_destination` (4838-4853) - containment + symlink guard used by `filter`.
  - `cli_filter` (4856-4952) - read input, resolve scope/project, model + cost + confirm,
    call API, compute output name, backup, write.
  - `FILTER_USER_PROMPT_TEMPLATE` (~3105) and `COMPACTION_SYSTEM_PROMPT` (2701) - egress content.
  - `call_compaction_api` (794-883) - HTTPS-only enforcement confirmed (825-829); Bearer token
    header (852); 300s timeout.
  - `write_text` (3321-3345) and `_backup_compacted_bu` (3392) - backup/write behavior (SEC-6).
  - `resolve_project` (3861) - `--project` resolution (returns dict with name/directory/id).
  - `parse_recovery_name` / `canonical_recovery_name` - output-name derivation (4930-4942).
- `scripts/migrate_recovery_names.py` - `plan_migration` (symlink skip, top-level only),
  `migrate_dir` (containment guard `dst.resolve().parent != directory`, atomic os.rename).

## Commands / repros run (read-only, temp dirs)
- Containment no-op (SEC-1): called `_safe_destination(op, op.parent)` (the exact call shape
  `cli_filter` uses) with `op` inside a `sub/` dir -> **allowed**, confirming the check never
  constrains because base derives from the destination.
- Symlinked-dir escape (SEC-2): created `linkdir -> /tmp/otherdir`, called
  `_safe_destination(linkdir/'y.compacted.md', linkdir)` -> **allowed**, resolving outside the
  apparent tree.
- Non-UTF-8 input (SEC-4): wrote `\xff\xfe\x00\x01...` to a `.restart.md`, called `cli_filter`
  -> raised **`UnicodeDecodeError`** (uncaught), not `RecoveryError`.
- Migration script (context): ran `plan_migration`/`migrate_dir` on a temp dir with legacy +
  canonical + symlink + non-recovery files -> legacy renamed, canonical/symlink/other skipped;
  containment guard present and sound.
- Full test suite (baseline, not a security check): `PYTHONPATH=. pytest` -> 150 passed, 2 skipped.

## Not exhaustively tested / assumptions
- Did not fuzz the regexes in `parse_recovery_name` beyond the cases in `test_recovery_naming.py`
  (naming correctness is a separate concern; edge-cases lens would cover it).
- HTTPS enforcement in `call_compaction_api` was read, not re-exercised, this run.
- TOCTOU (SEC-5) reasoned from code, not raced empirically (inherently timing-dependent;
  negligible for a local tool).

## Scope exclusions honored
- Did not assess `.agents/workflows/` or `workflow-artifacts/` as project code.
