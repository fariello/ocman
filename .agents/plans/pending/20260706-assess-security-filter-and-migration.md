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

### Plan-review revisions (2026-07-06, applied in place)

This IPD was hardened by `plan-review` before approval. Changes made to the plan (not code):
- **PR-1 (High):** Step 1's fix wording conflated the mutually exclusive default-output vs.
  explicit-`-oc` cases; rewritten to specify each case separately and to realpath the destination
  **parent** (not just the final component).
- **PR-2 (High):** `run_compaction` already sends the transcript to the API non-interactively with
  no confirm (verified), so SEC-3's non-interactive-confirm proposal would create two divergent
  egress postures. The egress decision is now scoped to **both** paths (Open Question 1) rather
  than to `filter` alone.
- **PR-3 (Medium):** removed the vague "`--yes`-style" flag; the fix must reuse `--force` or add
  one clearly-named flag (Open Question 4), not invent a third idiom.
- **PR-4 (Medium):** the size cap is settled as a config key `filter_max_bytes` (+ CLI override)
  per configurable-over-hardcoded; only the default value remains open.
- **PR-5 (Low):** tests now require the symlinked-**ancestor** case, which is the actual SEC-2 gap.
- **PR-6 (Low):** SEC-6 flagged as tangential-to-security (code cleanliness) so it does not expand
  the security fix; kept because Remediation Risk is Low.

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | SEC-1, SEC-2 | Make containment real by splitting the two **mutually exclusive** cases explicitly (the prior wording conflated them - PR-1): **(a) default output (no `-oc`):** the file is written beside the source with a generated name; base = `os.path.realpath(input_path.parent)` and the realpath'd destination parent MUST equal/stay inside that base - reject `..`-laden generated names and any symlinked **ancestor** that would escape. **(b) explicit `-oc`:** this IS the user's deliberately chosen destination, so containment is NOT enforced against the source dir (there is no default-name path in this case); instead only (i) refuse to clobber/write **through** an existing symlink at the destination, and (ii) print the resolved destination so the write location is never a surprise. Use `os.path.realpath` on the parent (not just the final component) so an intermediate symlink cannot silently redirect the write. | ocman.py:4838-4853, 4939-4944 | Low | New tests in `tests/test_file_tools.py`: (a) symlinked **ancestor** dir escape rejected, `../escape` generated name rejected, normal beside-source allowed; (b) explicit `-oc` outside source dir honored but destination printed and symlink-at-dest refused |
| 2 | SEC-3 | Add a **configurable input size cap** as a config key `filter_max_bytes` in `ocman.toml` (consistent with `default_retention_days` etc. per configurable-over-hardcoded; PR-4), with a CLI override; check `input_path.stat().st_size` before reading, and over the cap refuse with a clear message naming the size and the override. **Non-interactive egress (PR-2/PR-3 - resolve before implementing):** `run_compaction` already sends the full transcript to the API non-interactively with no confirm flag (ocman.py confirm block), so making `filter` require a confirm flag would create **two divergent egress postures**. Decide via Open Question 1 whether to (x) keep `filter` consistent with compaction (proceed non-interactively, rely on the size cap as the guard), or (y) tighten **both** `filter` and `run_compaction` to require an explicit egress-confirm. Do NOT invent a new confirmation idiom: reuse the existing `--force` semantics or add one clearly-named flag - specify which in the fix, do not leave it as "`--yes`-style". | ocman.py:4876, 4917-4923; run_compaction confirm block; load_ocman_config | Low | Test: oversized file refused (cap from config) unless override; whichever egress decision (x/y) is chosen is covered by a test and applied consistently to both paths if (y) |
| 3 | SEC-4 | Catch `UnicodeDecodeError` (and decode errors generally) in the `read_text` block and raise a clean `RecoveryError("Input is not a UTF-8 text file: ...")`. | ocman.py:4875-4878 | Low | Test: binary input raises `RecoveryError`, not `UnicodeDecodeError` |
| 4 | SEC-6 | Drop the redundant `_backup_compacted_bu(dest)` OR switch `filter` to a write path that does not double-back-up; keep exactly one backup mechanism so a pre-existing target is backed up once, predictably. | ocman.py:4946-4947 | Low | Test: one backup file produced on collision (already covered; assert exactly one) |
| 5 | SEC-5 | Note the TOCTOU in code comments and, where cheap, tighten the migration rename to re-verify `not src.is_symlink()` immediately before `os.rename`. Do not over-engineer file-descriptor locking for a local tool (KISS). | scripts/migrate_recovery_names.py:88-99 | Low | Test: a symlink introduced between plan and apply is not renamed |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | All findings are low Remediation Risk and fixed by default. The full file-descriptor-level TOCTOU hardening (SEC-5) beyond a re-check is intentionally NOT proposed: FD-locking/`O_NOFOLLOW` plumbing would add disproportionate complexity (Complexity axis) for a single-user local tool. The cheap re-check is proposed; the heavy version is left out by KISS. | If ocman ever runs in a shared/multi-user context, revisit with real atomic-open primitives. |

## Scope check

- Over-scope: SEC-6 (redundant double-backup) is a code-cleanliness item, not strictly a security
  finding (PR-6); kept because Remediation Risk is Low, but flagged as tangential so it does not
  expand the security fix. Do NOT add a virus scanner, an egress allow-list DB, or FD-locking -
  all disproportionate for a local single-user CLI (Complexity axis).
- Under-scope (added above): a real (not no-op) containment check (SEC-1/2), an egress size cap
  (SEC-3), and clean decode-error handling (SEC-4). **Consistency scope (PR-2):** the egress
  posture must be decided for `filter` AND `run_compaction` together, not for `filter` alone.

## Required tests / validation

- Extend `tests/test_file_tools.py`: (a) default-output containment - symlinked **ancestor** dir
  escape rejected (not just final-component symlink; PR-5), `..`-name rejected, normal
  beside-source allowed; (b) explicit `-oc` outside source honored + destination printed +
  symlink-at-destination refused; oversized-input refusal (cap from config); binary-input clean
  `RecoveryError`; exactly-one-backup-on-collision.
- If the egress decision is (y), add a `run_compaction` non-interactive egress test too so both
  paths stay consistent.
- Extend `tests/test_migrate_recovery_names.py`: symlink-introduced-between-plan-and-apply not renamed.
- Full suite green: `PYTHONPATH=. pytest` (currently 150 passed, 2 skipped).

## Spec / documentation sync

- README/`--help`: document `filter_max_bytes` (config key + CLI override) and the egress posture
  chosen in Open Question 1, and clarify that `filter` (and, if touched, `--compact`) sends file
  contents to the configured API endpoint (honest-docs principle). State `-oc` behavior plainly
  (explicit path honored, destination printed). If the egress decision changes `run_compaction`,
  add a CHANGELOG note for that behavior change.

## Open questions

1. **Egress in non-interactive mode (decide for BOTH `filter` and `run_compaction`; PR-2):**
   (x) keep both consistent by proceeding non-interactively and relying on the size cap as the
   guard, or (y) tighten both to require an explicit egress-confirm flag. Whichever is chosen must
   be applied consistently across the two API-egress paths; do not silently leave compaction on a
   different posture than filter. This is a human security-vs-usability decision.
2. **Default `filter_max_bytes` value:** the config-key decision is settled (it WILL be a config
   key with a CLI override, per configurable-over-hardcoded; PR-4); only the default **value** is
   open (proposed a few MB).
3. **`-oc` outside the source dir:** confirmed approach - honor (user's explicit path) + print the
   resolved destination + refuse a symlink at the destination. Flag if you want a stronger gate
   (warn/confirm) instead.
4. **Confirmation idiom (PR-3):** if Open Question 1 chooses (y), which flag - reuse `--force`
   (note its current bypass-polarity) or add one new clearly-named flag? Pick one; do not
   introduce a third confirmation style.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered changes, run the validation, and sync docs.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
