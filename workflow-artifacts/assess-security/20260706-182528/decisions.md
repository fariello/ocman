# Decisions and assumptions - assess-security (filter + migration) run 20260706-182528

## Concern and scope
- Concern: security. Lens: `.agents/workflows/assess/lenses/security.md`.
- Scope narrowed (per user's pre-release request) to the NEW surface only: `cli_filter` /
  `_safe_destination` in `ocman.py`, the `FILTER_USER_PROMPT_TEMPLATE` egress path, and
  `scripts/migrate_recovery_names.py`. This is deliberately not a whole-project security pass;
  `release-review` will do the broad fix-in-place review.

## Project conventions discovered
- No `GUIDING_PRINCIPLES.md`; principles from `ARCHITECTURE.md` ("Design principles":
  intuitive/self-documenting, configurable-over-hardcoded, KISS, honest documentation) +
  universal fallback.
- Established precedent for file-writing features: path-contained, symlink-safe, fail-soft
  (RSP-6, executed IPD `20260704-assess-functionality-restart-to-project-prompts.md`).
- IPD lifecycle: `.agents/plans/pending/` -> `.agents/plans/executed/`. Run records under
  `workflow-artifacts/assess-<concern>/<RUN_ID>/` (committed, out of review scope).
- Scope exclusions honored: did not assess `.agents/workflows/` or `workflow-artifacts/`.

## Key decisions / assumptions
- **Threat model is the decisive lens here.** Single-user local CLI, user-supplied paths, no
  tenancy/privilege boundary. This intentionally downgrades path-escape findings from
  "breach/BLOCKER" (as they would be server-side) to "accidental data loss / accidental egress /
  foot-gun." The verdict is "needs work" primarily because of SEC-1 (a guard that claims to
  protect but does nothing) - honest-guarantees matters even when the real risk is low.
- **SEC-1 rated High severity** despite the benign threat model: an asserted-but-unenforced
  security control is worse than none (false assurance), and the plan-review explicitly claimed
  containment. Remediation Risk is Low, so it is fixed by default.
- **Findings verified by repro, not inferred:** the containment no-op and the symlinked-dir
  escape were both reproduced (`_safe_destination` allowed writes outside the base); the
  non-UTF-8 `UnicodeDecodeError` was reproduced by calling `cli_filter` on binary input.

## What was intentionally NOT proposed and why (Remediation-Risk axis)
- **File-descriptor-level TOCTOU hardening** (`O_NOFOLLOW`, FD locking) beyond a cheap
  pre-rename symlink re-check: DEFERRED on the **complexity** axis (Medium-High). Disproportionate
  for a single-user local tool (KISS). The cheap re-check is proposed.
- **No virus/secret scanner, no egress allow-list, no per-file classification:** over-scope for a
  local CLI (complexity). Not proposed.

## Open questions for the user (also in the IPD)
1. Non-interactive `filter` egress: refuse without an explicit confirm flag (safer) vs. keep
   auto-proceed for scripting?
2. Default input size cap value; make it a config key (`filter_max_bytes`)?
3. `-oc` outside the source dir: honor silently (user's explicit path) vs. warn vs. confirm?
   Proposed: honor + print destination.
