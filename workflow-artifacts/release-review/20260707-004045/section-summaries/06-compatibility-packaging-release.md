# Section 6: Compatibility / Packaging / Release

## What I did
- Version consistency: 1.1.0 in ocman.py + pyproject (confirmed S1).
- Built the 1.1.0 wheel and inspected contents; ran `twine check` (PASSED).
- Backward compatibility: `parse_recovery_name` reads both legacy filename forms + canonical
  (old on-disk files still work); `load_ocman_config` ignores unknown keys and defaults the new
  ones (old ocman.toml loads unchanged). No `.ocbox`/backup-ZIP format change in 1.1.0.
- Schema/data-contract pass (schema-validation.md): no drift; contracts code-defined + test-covered.
- CI assessment (ci-assessment.md): existing matrix adequate; advisory recommendation to add a
  gitleaks secret-scan CI step (not a blocker; deferred to user).

## Findings
- **S6-C1 (Medium / RR Low):** the wheel ships `ocman.py` + `ocman_tui` only;
  `scripts/migrate_recovery_names.py` is NOT in the wheel (verified by building). Docs tell
  upgraders to run it, but `pip install` users don't have it. Not a functional break (migration is
  optional; old files still parse), but the documented upgrade tool is missing for the primary
  install method. Fix in S7: force-include `scripts/` in the wheel (action S6-A1).

## Why
- Packaging must deliver what the docs promise; the migration script is the one 1.1.0 artifact the
  docs point users to that packaging currently drops.

## What I considered but did NOT do
- Turning normalization into an `ocman` subcommand (so it always ships): rejected - the IPD
  deliberately kept it a standalone one-shot script (KISS); shipping the file is the smaller fix.
- Adding the gitleaks CI step in this run: left as an advisory recommendation (infra change; user
  holds release timing). No release blocker.
