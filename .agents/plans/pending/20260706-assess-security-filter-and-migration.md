# IPD: Assess security - `ocman filter` + recovery-filename migration

- Date: 2026-07-06
- Concern: security
- Scope: primarily the newly added surface - `cli_filter` / `_safe_destination` in `ocman.py`,
  the `FILTER_USER_PROMPT_TEMPLATE` egress path, and `scripts/migrate_recovery_names.py`. The
  egress guards (size cap + secret scan, Steps 2-3) additionally extend to the already-shipped
  `run_compaction`/`--compact` egress path by user decision, since it shares the same LLM-send
  risk. (Not a whole-project security pass; that is `release-review`'s job.)
- Status: PENDING (awaiting human approval; open questions resolved 2026-07-06; not executed)
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
| 2 | SEC-3 | **Input size cap.** Add config key `filter_max_bytes` in `ocman.toml` (configurable-over-hardcoded; PR-4), **default 5 MB**, CLI-overridable via `--force`. Check `input_path.stat().st_size` (for `filter`) / assembled-prompt length (for `--compact`) before sending; over the cap, refuse with a clear message naming the size, the cap, and that `--force` overrides. Applies to **both** `filter` and `run_compaction` (Q2b). Non-interactive egress is **left as-is** (both paths still proceed without a `[Y/n]`; PR-2 decision (x)) - the accidental-egress guard is the size cap plus the secret scan in Step 3, not a blanket confirm gate. | ocman.py:4876, 4917-4923; run_compaction; load_ocman_config | Low | Test: oversized `filter` input and oversized compaction prompt both refused unless `--force`; cap value read from config |
| 3 | SEC-3 | **Pre-egress secret/PII scan (NEW, decided interactively).** Before any API send, scan the outbound text (the `filter` document; the `--compact` assembled prompt) with a curated **high-signal** heuristic: private-key blocks (`-----BEGIN ... PRIVATE KEY-----`), API-key shapes (AWS `AKIA[0-9A-Z]{16}`, GitHub `ghp_`/`gho_`/`ghu_`/`ghs_`, generic `Bearer <token>` / JWT `eyJ...`), `KEY=VALUE` assignments where KEY matches `password|secret|api[_-]?key|token` **and** VALUE is token-like (non-trivial length/entropy, not a bare English word), and US SSN (`\b\d{3}-\d{2}-\d{4}\b`). Applies to **both** paths, in **interactive and non-interactive** mode (Q1b). On a hit: **error** listing the matched detector types and line numbers **redacted** (never echo the secret), and require the new **`--allow-secrets`** flag to proceed (a plain `[Y/n]` does NOT bypass it; Q4). **Conservative by default** (only high-confidence/structured matches; a bare word "password" in prose must NOT trip it - avoids alarm fatigue on recovery docs that discuss auth). Add config key `filter_secret_scan = "conservative" | "aggressive"` (default `conservative`); `aggressive` additionally flags bare keywords for sensitive environments (Q1d). Implement as a small pure function `scan_for_secrets(text, mode) -> list[SecretHit]` (type + line, no value) so it is unit-testable in isolation. | new `scan_for_secrets` in ocman.py; call sites in `cli_filter` (before `call_compaction_api`) and `run_compaction`; load_ocman_config | Low | Tests: each detector matches a positive sample; conservative mode does NOT flag prose "password"; aggressive mode does; a hit raises `RecoveryError` unless `--allow-secrets`; error output contains type+line but NOT the secret value |
| 4 | SEC-4 | Catch `UnicodeDecodeError` (and decode errors generally) in the `read_text` block and raise a clean `RecoveryError("Input is not a UTF-8 text file: ...")`. | ocman.py:4875-4878 | Low | Test: binary input raises `RecoveryError`, not `UnicodeDecodeError` |
| 5 | SEC-6 | Drop the redundant `_backup_compacted_bu(dest)` OR switch `filter` to a write path that does not double-back-up; keep exactly one backup mechanism so a pre-existing target is backed up once, predictably. | ocman.py:4946-4947 | Low | Test: one backup file produced on collision (already covered; assert exactly one) |
| 6 | SEC-5 | Note the TOCTOU in code comments and, where cheap, tighten the migration rename to re-verify `not src.is_symlink()` immediately before `os.rename`. Do not over-engineer file-descriptor locking for a local tool (KISS). | scripts/migrate_recovery_names.py:88-99 | Low | Test: a symlink introduced between plan and apply is not renamed |

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
  (SEC-3, Step 2), a **pre-egress secret/PII scan** (SEC-3, Step 3 - added per the interactive
  decision), and clean decode-error handling (SEC-4). **Consistency (PR-2):** the size cap and the
  secret scan are applied to `filter` AND `run_compaction` together; non-interactive egress is
  intentionally left proceeding (guarded by the cap + scan, not a blanket confirm).
- Newly in scope by user decision: the secret scan touches the already-shipped `--compact` path.
  This is deliberate (close the leak everywhere) and is a documented behavior change (see
  CHANGELOG note). It is NOT over-scope: it is the chosen remediation for SEC-3's egress risk.

## Required tests / validation

- Extend `tests/test_file_tools.py`: (a) default-output containment - symlinked **ancestor** dir
  escape rejected (not just final-component symlink; PR-5), `..`-name rejected, normal
  beside-source allowed; (b) explicit `-oc` outside source honored + destination printed +
  symlink-at-destination refused; oversized-input refusal (cap from config, `--force` overrides);
  binary-input clean `RecoveryError`; exactly-one-backup-on-collision.
- Secret-scan tests (new `test_secret_scan.py` or in `test_file_tools.py`): each detector matches a
  positive sample; **conservative** mode does not flag prose "password"; **aggressive** mode does;
  a hit raises `RecoveryError` unless `--allow-secrets`; the error names detector type + line but
  never the secret value (redaction assertion). Cover both `cli_filter` and `run_compaction` call
  sites (monkeypatch `call_compaction_api`, assert it is NOT called when a secret is detected
  without `--allow-secrets`).
- Size cap: oversized `filter` input AND oversized compaction prompt both refused unless `--force`.
- Extend `tests/test_migrate_recovery_names.py`: symlink-introduced-between-plan-and-apply not renamed.
- Full suite green: `PYTHONPATH=. pytest` (currently 150 passed, 2 skipped).

## Spec / documentation sync

- README/`--help`: document `filter_max_bytes` (config key, default 5 MB, `--force` override),
  `filter_secret_scan` (conservative|aggressive, default conservative), and `--allow-secrets`.
  Clarify that both `filter` and `--compact` send content to the configured API endpoint and are
  scanned for secrets/PII first (honest-docs). State `-oc` behavior plainly (explicit path honored,
  resolved destination printed, symlink-at-dest refused).
- **CHANGELOG:** the secret scan + size cap now also gate the already-shipped `--compact` path -
  this is a (safety-adding) behavior change to existing functionality, so note it explicitly. A
  previously-passing non-interactive `--compact` on a secret-bearing transcript will now stop and
  require `--allow-secrets`.

## Open questions

*Resolved interactively 2026-07-06 (recorded here for the executing agent):*

1. **Non-interactive egress (PR-2):** RESOLVED = keep both `filter` and `--compact` proceeding
   non-interactively as today (no blanket confirm gate). The accidental-egress guards are the
   **size cap (Step 2)** and the **secret/PII scan (Step 3)**, both applied to both paths.
2. **Secret scan (Q1b/Q1c/Q1d):** RESOLVED = scan **both** paths, **always** (interactive and
   non-interactive); curated **high-signal** detectors; bypass with **`--allow-secrets`**;
   **conservative by default** with a `filter_secret_scan = "aggressive"` config opt-in for
   sensitive environments.
3. **`filter_max_bytes` (Q2):** RESOLVED = config key, **default 5 MB**, `--force` override,
   applied to **both** paths.
4. **`-oc` output (Q3):** RESOLVED = honor the explicit path (no source-dir containment) + print
   the resolved destination + refuse a symlink at the destination.
5. **Bypass flags (Q4):** RESOLVED = new **`--allow-secrets`** for the secret-scan bypass; reuse
   existing **`--force`** for the size-cap override. Do not add a third confirmation idiom.

6. **Overwrite-collision handling (cross-plan, decided 2026-07-06 in the edge-cases IPD):** the
   live `filter`/`compact` write path (which this IPD hardens) shares the edge-cases IPD's new
   collision helper: on a would-overwrite, first check whether opencode/ocman is running or the
   target is being modified; if unsafe, CLI errors+exits / TUI refuses+advises quitting; if safe,
   interactively prompt to back up (`.bu.NNN`) or delete, defaulting non-interactively to safe
   backup (never delete). Execute that helper ONCE (shared) and call it from `cli_filter`/
   `run_compaction` here. See edge-cases IPD Step 1.

*Remaining for the executing agent:* none blocking. The `aggressive`-mode keyword list and the
exact token-likeness threshold for `KEY=VALUE` detection are implementation details to tune with
the tests (keep conservative-mode false positives at zero on the existing recovery-doc fixtures).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered changes, run the validation, and sync docs.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
