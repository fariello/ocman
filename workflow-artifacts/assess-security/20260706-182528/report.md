# Assessment run report - security (filter command + recovery-filename migration)

- Date / run ID: 20260706-182528
- Concern: security
- Scope: new surface only - `cli_filter`/`_safe_destination` in `ocman.py`, the
  `FILTER_USER_PROMPT_TEMPLATE` egress path, and `scripts/migrate_recovery_names.py`.
- IPD written: `.agents/plans/pending/20260706-assess-security-filter-and-migration.md`
- Verdict: **needs work** for security (one High no-op guard; the rest low-severity given the
  single-user local threat model)

## Threat model note

`ocman` is a single-user, local CLI operating on the user's own data with user-supplied paths.
There is no tenancy or privilege boundary; "attacker" and "victim" are the same person. Path-
escape findings are therefore accidental-data-loss / accidental-egress foot-guns rather than
external-breach vulnerabilities. The fixes remain worthwhile (honest guarantees + protecting the
user from mistakes) and are all low Remediation Risk.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| SEC-1 | High | Low | sec architect | `_safe_destination` is a structural no-op: `cli_filter` calls it with a base derived from the destination itself, so `is_relative_to` is always true and it rejects nothing (incl. `-oc /etc/...`). The RSP-6 "path-contained" guarantee is asserted but unenforced. |
| SEC-2 | Medium | Low | sec engineer | A symlinked output directory escapes containment; only the final path component is symlink-checked, not ancestors. |
| SEC-3 | Medium | Low | novice/stakeholder | `filter` reads an entire arbitrary file and sends it to an external LLM with no size/type guard; non-interactive mode proceeds without egress confirmation. |
| SEC-4 | Low | Low | novice | Non-UTF-8 input raises an uncaught `UnicodeDecodeError` (read_text catches only `OSError`). |
| SEC-5 | Low | Low | sec engineer | TOCTOU between symlink check and write/rename (negligible for a local tool). |
| SEC-6 | Low | Low | sec engineer | Redundant double-backup (`_backup_compacted_bu` + `write_text`'s `_backup_if_exists`). |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

1. SEC-1/SEC-2: make containment real - compute the allowed base independently of the
   destination and realpath every component so a symlinked ancestor cannot escape; add tests.
2. SEC-3: add a configurable input size cap + require explicit egress confirmation in
   non-interactive mode (mirror the destructive-confirm posture).
3. SEC-4: catch decode errors, raise a clean `RecoveryError`.
4. SEC-6: keep exactly one backup mechanism.
5. SEC-5: note the TOCTOU and add a cheap re-check before the migration rename (no FD-locking).

## Deferred (with reason)

- Heavy FD-level TOCTOU hardening (beyond a cheap re-check): Remediation Risk Medium-High on
  **complexity** - `O_NOFOLLOW`/FD-locking plumbing is disproportionate for a single-user local
  tool (KISS). The cheap re-check is proposed; the heavy version is deferred. (Effort/time is not
  the reason.)

## Out-of-repo / organizational notes

- None. Everything is addressable in-repo.

## Next step

Review the IPD (optionally run `plan-review` on it) and approve before execution. This workflow
does not execute the plan.
