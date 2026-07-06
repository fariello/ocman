# IPD: Assess security - `ocman filter` + recovery-filename migration

- Date: 2026-07-06
- Concern: security
- Scope: the newly added surface only - `cli_filter` / `_safe_destination` in `ocman.py`,
  the `FILTER_USER_PROMPT_TEMPLATE` egress path, and `scripts/migrate_recovery_names.py`.
  (Not a whole-project security pass; that is `release-review`'s job.)
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Make the new `filter` command and the migration script honor the security posture the project
already sets for file-writing features (path-containment, symlink-safety, fail-soft - the RSP-6
precedent) and for LLM egress (explicit consent, no silent transmission), so that the
plan-review's claimed guarantees are actually enforced rather than only asserted. The headline
issue is that the path-containment guard added for `filter` is structurally a no-op and enforces
nothing.

## Project conventions discovered (Step 0)

- Guiding principles: no dedicated file; `ARCHITECTURE.md` "Design principles"
  (intuitive/self-documenting, configurable-over-hardcoded, KISS, honest documentation) +
  universal fallback. Repo-wide precedent for file-writing features: **path-contained,
  symlink-safe, fail-soft** (RSP-6, `.agents/plans/executed/20260704-assess-functionality-restart-to-project-prompts.md`).
- Pending-plans location/format used: `.agents/plans/pending/` -> `.agents/plans/executed/`
  (IPD house format).
- Contributor/spec-sync contract: `AGENTS.md` + `.agents/` workflows. `PYTHONPATH=. pytest`.
- Stack / relevant context: single-file stdlib CLI (`ocman.py`); `call_compaction_api`
  (ocman.py:794) posts to an OpenAI-compatible endpoint and already refuses non-HTTPS
  (ocman.py:825).

## Threat model (governs severity)

`ocman` is a **single-user, local administration CLI**. The operator runs it on their own
machine against their own opencode data, and supplies the paths involved (`filter`'s input file,
`-oc`, the migration directory). There is no multi-tenant boundary, no network-exposed surface,
and no privilege separation between "attacker" and "victim" - they are the same person. This
lowers the *real* severity of path-escape findings from what they would be in a server context:
the practical risk is **accidental data loss / accidental egress / a foot-gun**, not an external
breach. Findings are rated with that context; the fixes are still worth doing (defense-in-depth,
honest guarantees, and protecting the user from their own mistakes), and their Remediation Risk
is low.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for acting now.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| SEC-1 | High | Low | sec architect | path-containment | `_safe_destination` is a **structural no-op**. `cli_filter` always calls it as `_safe_destination(out_dir / name, out_dir)` where `out_dir` is derived from the *same* path (`out_path.parent`, or `input_path.parent`). `resolved.is_relative_to(base)` is therefore always true, so the containment check never rejects anything, including `-oc /etc/evil.md`. The RSP-6/plan-review "path-contained" guarantee is asserted but not enforced. | ocman.py:4838-4853, 4939-4944 |
| SEC-2 | Medium | Low | sec engineer | symlink-safety | A **symlinked output directory** escapes the check: if `out_dir` (or an ancestor) is a symlink, both `dest` and `base` resolve through it, the containment check passes, and the write lands outside the apparent tree. `_safe_destination` only tests `is_symlink()` on the final component, not intermediate dirs. | ocman.py:4844-4852 (verified via repro) |
| SEC-3 | Medium | Low | novice / stakeholder | egress / cost | `filter` reads the **entire input file** into memory and sends it to an external LLM endpoint with **no size guard** and no file-type sanity check (extension-agnostic by design). A user can accidentally `filter` a huge or binary/secret-bearing file, transmitting its contents off-box. Mitigated by the interactive cost/`[Y/n]` confirm and the "will be sent to the API endpoint" note, but the confirm is skipped in non-interactive mode. | ocman.py:4876, 4903-4923 |
| SEC-4 | Low | Low | novice | error handling | Non-UTF-8 input raises an **uncaught `UnicodeDecodeError`** (the `read_text` try only catches `OSError`), surfacing a Python-internal message instead of a clean "not a text file" error. | ocman.py:4875-4878 (verified via repro) |
| SEC-5 | Low | Low | sec engineer | TOCTOU | Symlink checks in both `_safe_destination` and the migration script (`plan_migration` checks `is_symlink()`, `migrate_dir` renames later) have a **check-then-use race**. Negligible for a local single-user tool but worth a note; `os.rename`/atomic-write with `O_NOFOLLOW`-style intent would close it. | ocman.py:4851, scripts/migrate_recovery_names.py:48-58,92-99 |
| SEC-6 | Low | Low | sec engineer | redundant backup | `cli_filter` calls `_backup_compacted_bu(dest)` and then `write_text(dest, ...)`, which itself calls `_backup_if_exists(dest)`. Harmless (the first call already moved any existing file), but the double-backup path is confusing and could mask intent. Informational. | ocman.py:4946-4947, write_text |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | SEC-1, SEC-2 | Make containment real: define the **allowed base** independent of the destination. For the default (beside-source) case, base = `input_path.resolve().parent`; for `-oc`, treat an explicit `-oc` as the user's deliberate choice but still reject the *default-name* path escaping the source dir. Resolve **each path component** (use `os.path.realpath` on the parent and require the realpath'd parent to be inside the realpath'd base) so a symlinked ancestor cannot escape. If `-oc` is outside the source dir, require it to be an explicit absolute/relative path the user typed (it already is) and print where it will write. Add a unit test asserting a symlinked `out_dir` and a `..`-laden name are both rejected/normalized. | ocman.py:4838-4853, 4939-4944 | Low | New tests in `tests/test_file_tools.py`: symlinked dir rejected; `../escape` rejected; normal beside-source still allowed |
| 2 | SEC-3 | Add a configurable **input size cap** (e.g. default a few MB) before reading/sending; over the cap, refuse with a clear message and require an explicit `--max-bytes`/`--force`-style override. In **non-interactive** mode, do NOT silently proceed to send a file off-box: require an explicit `--yes`-style flag to confirm egress (mirror the destructive-confirm posture). | ocman.py:4876, 4917-4923 | Low | Test: oversized file refused without override; non-interactive without confirm flag refuses to call the API (monkeypatched) |
| 3 | SEC-4 | Catch `UnicodeDecodeError` (and decode errors generally) in the `read_text` block and raise a clean `RecoveryError("Input is not a UTF-8 text file: ...")`. | ocman.py:4875-4878 | Low | Test: binary input raises `RecoveryError`, not `UnicodeDecodeError` |
| 4 | SEC-6 | Drop the redundant `_backup_compacted_bu(dest)` OR switch `filter` to a write path that does not double-back-up; keep exactly one backup mechanism so a pre-existing target is backed up once, predictably. | ocman.py:4946-4947 | Low | Test: one backup file produced on collision (already covered; assert exactly one) |
| 5 | SEC-5 | Note the TOCTOU in code comments and, where cheap, tighten the migration rename to re-verify `not src.is_symlink()` immediately before `os.rename`. Do not over-engineer file-descriptor locking for a local tool (KISS). | scripts/migrate_recovery_names.py:88-99 | Low | Test: a symlink introduced between plan and apply is not renamed |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | All findings are low Remediation Risk and fixed by default. The full file-descriptor-level TOCTOU hardening (SEC-5) beyond a re-check is intentionally NOT proposed: FD-locking/`O_NOFOLLOW` plumbing would add disproportionate complexity (Complexity axis) for a single-user local tool. The cheap re-check is proposed; the heavy version is left out by KISS. | If ocman ever runs in a shared/multi-user context, revisit with real atomic-open primitives. |

## Scope check

- Over-scope: none. Do NOT add a virus scanner, an egress allow-list DB, or FD-locking - all
  disproportionate for a local single-user CLI (Complexity axis).
- Under-scope (added above): a real (not no-op) containment check (SEC-1/2), an egress size cap +
  non-interactive egress confirmation (SEC-3), and clean decode-error handling (SEC-4).

## Required tests / validation

- Extend `tests/test_file_tools.py`: symlinked-dir rejection, `..`-name rejection, oversized-input
  refusal, non-interactive egress-confirm gate, binary-input clean error, single-backup-on-collision.
- Extend `tests/test_migrate_recovery_names.py`: symlink-introduced-between-plan-and-apply not renamed.
- Full suite green: `PYTHONPATH=. pytest` (currently 150 passed, 2 skipped).

## Spec / documentation sync

- README/`--help`: document the new input size cap / override flag and the non-interactive egress
  confirmation, and clarify that `filter` sends file contents to the configured API endpoint
  (honest-docs principle). `-oc` behavior (explicit path is honored) stated plainly.

## Open questions

1. **Egress in non-interactive mode:** should `filter` refuse without an explicit confirm flag
   (safer, proposed), or keep the current "proceed" behavior for scripting convenience? This is a
   human security-vs-usability decision.
2. **Default input size cap:** what byte limit is sensible (proposed a few MB)? Should it be a
   config key (`filter_max_bytes`) consistent with the configurable-over-hardcoded principle?
3. **`-oc` outside the source dir:** honor silently (it is the user's explicit path), warn, or
   require a confirm? (Proposed: honor + print the destination.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered changes, run the validation, and sync docs.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
