# IPD: Assess edge-cases - `filter`, canonical naming, and the migration script

- Date: 2026-07-06
- Concern: edge-cases
- Scope: the new surface added in 1.1.0 - `canonical_recovery_name` / `parse_recovery_name`,
  `cli_filter`, and `scripts/migrate_recovery_names.py`. Not a whole-project pass.
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Harden the boundary behavior of the new recovery-naming helpers, the `filter` command, and the
migration script so that unusual-but-reachable inputs (same-minute duplicates, empty/whitespace
input, invalid embedded dates, odd session ids, wrong kinds) are handled correctly or rejected
with a clear message and pinned by a regression test - rather than silently producing a wrong
name, an empty LLM call, or a confusing half-migration. All findings are low Remediation Risk.

## Project conventions discovered (Step 0)

- Guiding principles: `ARCHITECTURE.md` "Design principles" (intuitive/self-documenting,
  configurable-over-hardcoded, KISS, honest documentation) + universal fallback.
- Pending-plans: `.agents/plans/pending/` -> `.agents/plans/executed/` (IPD house format).
- Contributor contract: `AGENTS.md` + `.agents/` workflows; `PYTHONPATH=. pytest`.
- Stack: single-file stdlib CLI (`ocman.py`); local single-user tool; canonical recovery name is
  `YYYYMMDD-HHMM-<session_id>.<kind>.md` (local, minute precision).

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. All repro-verified.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| EC-1 | Medium | Low | QA / software eng | time & collision | Canonical names are **minute-precision**, so two legacy files that differ only in the **seconds** field canonicalize to the SAME target. The migration renames the first and **safely skips** the second (no data loss - good), but only prints a terse "SKIP (target exists)"; the user is left with a confusing half-migrated pair and no explanation. Reachable: two recoveries of one session in the same minute. | repro: `opencode-20260101-120000-ses_x.restart.md` + `...120059...` both -> `20260101-1200-ses_x.restart.md`; second skipped |
| EC-2 | Low | Low | QA / novice | input boundary | `filter` sends an **empty or whitespace-only** input document to the LLM (incurring a real API call/cost) instead of refusing early. | repro: empty `.restart.md` -> wrote output after an empty send |
| EC-3 | Low | Low | software eng | input validation | A **whitespace-only `--scope`** (e.g. `"   "`) passes the "at least one of --project/--scope" check (`if scope:`), yielding a meaningless scope sent to the model and a `...session.compacted.md` name. Empty-string and None correctly error. | ocman.py:4892-4895 (repro: `scope='   '` wrote a file) |
| EC-4 | Low | Low | software eng | contract | `canonical_recovery_name` accepts a **bogus `kind`** with no validation (`kind='bogus'` -> `...x.bogus.md`), which `parse_recovery_name` then cannot classify. A wrong-kind caller bug would silently produce an unparseable artifact. | ocman.py (canonical_recovery_name); repro produced `20260101-0000-x.bogus.md` |
| EC-5 | Low | Low | QA | encoding/case | `parse_recovery_name` is **case-sensitive** on the suffix, so `*.RESTART.MD` is unrecognized and the migration silently ignores it. Harmless on Linux; on a case-insensitive FS (macOS) an odd-cased legacy file would be left un-migrated. | repro: `x.RESTART.MD` -> `('', None, '')` |
| EC-6 | Low | Low | software eng | parsing ambiguity | A **legacy date-only** name whose session id begins with 8 digits (`12345678-ses.restart.md`) mis-splits the leading digits as a (failed) date, losing them from the sid. Theoretical for real `ses_...` ids; the canonical `YYYYMMDD-HHMM-` form round-trips correctly. | repro: `12345678-ses.restart.md` -> `('ses', None, 'restart')` |
| EC-7 | Low | Low | QA | time (positive) | Invalid embedded dates (`month 99`, `hour 25`) correctly yield `dt=None`, so downstream falls back to mtime - the intended safe behavior. No fix; pin it with a regression test so it cannot regress. | repro: `20269901-1432-...` and `opencode-...250000...` -> `(sid, None, kind)` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | EC-1 | On a canonical-name collision during migration, print an **explanatory** message (not just "SKIP"): name the two source files, explain that minute-precision names collided, and tell the user to rename/inspect manually or re-run with `--force` to overwrite (with the loss that implies). Keep the safe default (skip, source preserved). Also add a one-line note in `--help`/README that canonical names are minute-precision and same-minute artifacts of one session can collide. | scripts/migrate_recovery_names.py:82-92 | Low | Test: two same-minute legacy files -> first renamed, second skipped with the explanatory message; both files still present |
| 2 | EC-2 | In `cli_filter`, after reading the input, **refuse empty/whitespace-only content** with a clear `RecoveryError("Input file is empty: ...")` before building the prompt or calling the API. | ocman.py:4875-4903 | Low | Test: empty and whitespace-only input raise `RecoveryError`; API not called (monkeypatched) |
| 3 | EC-3 | `.strip()` the `--scope` value (and treat all-whitespace as absent) before the "at least one of --project/--scope" check so whitespace-only scope is rejected consistently with empty/None. | ocman.py:4892-4896 | Low | Test: `--scope "   "` raises the same `RecoveryError` as empty scope |
| 4 | EC-4 | Add a lightweight guard in `canonical_recovery_name`: assert/validate `kind in RECOVERY_KINDS` (raise `ValueError` on a bad kind) so a wrong-kind caller fails loudly instead of writing an unparseable name. KISS - one membership check, no new abstraction. | ocman.py (canonical_recovery_name) | Low | Test: `canonical_recovery_name(..., 'bogus')` raises; each real kind still works |
| 5 | EC-5 | Make `parse_recovery_name` suffix matching **case-insensitive** (compare `name.lower()`), so odd-cased legacy files are recognized on any FS. Preserve the original-case session id in the returned value. | ocman.py (parse_recovery_name) | Low | Test: `X.RESTART.MD` parses to kind `restart` |
| 6 | EC-7 | Add regression tests pinning the `dt=None`-on-invalid-date behavior (both legacy and canonical forms), documenting it as intended (safe mtime fallback). No code change. | tests only | Low | Tests green |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| EC-6 | - | - | NOT deferred as risky - it is simply **not worth code**: real opencode session ids are `ses_<base62>`, never a bare 8-digit string, so the mis-split is unreachable in practice and the canonical form round-trips. Documented as a known parser limitation; a regression test records the current behavior. If session-id formats ever change, revisit. | Add a comment in `parse_recovery_name` noting the date-only legacy ambiguity. |
| (seconds precision itself) | Medium-High | functionality | Raising canonical names back to **seconds** precision to avoid EC-1 collisions would reverse the deliberate `YYYYMMDD-HHMM` decision (and its tests/docs), re-introduce the longer names the user chose against, and still not fully avoid collisions. Handling the collision gracefully (Step 1) is the right fix; changing the scheme is not. | n/a |

## Scope check

- Over-scope: none proposed. Do NOT add content-hash suffixes or a collision-avoidance counter to
  canonical names - that would complicate the naming scheme the user deliberately kept simple
  (Complexity axis); the migration skip-with-explanation (Step 1) is sufficient.
- Under-scope (added above): empty-input rejection (EC-2), whitespace-scope rejection (EC-3),
  kind validation (EC-4), case-insensitive suffix (EC-5), and the collision explanation (EC-1).

## Required tests / validation

- `tests/test_recovery_naming.py`: EC-4 (bad kind raises), EC-5 (case-insensitive parse),
  EC-7 (invalid-date -> `dt=None`), EC-6 (documented date-only ambiguity behavior).
- `tests/test_file_tools.py`: EC-2 (empty/whitespace input refused, API not called),
  EC-3 (whitespace-only scope refused).
- `tests/test_migrate_recovery_names.py`: EC-1 (same-minute collision: first renamed, second
  skipped with explanatory message, both files present).
- Full suite green: `PYTHONPATH=. pytest` (currently 150 passed, 2 skipped).

## Spec / documentation sync

- README/`--help`: note that canonical recovery names are **minute-precision** and that two
  artifacts of the same session generated within the same minute can collide (the migration skips
  the second; live generation backs up via `.bu.NNN`). Document that `filter` rejects empty input.
- Coordinate with the pending **security IPD** (`20260706-assess-security-filter-and-migration.md`):
  EC-2/EC-3 (input validation) sit right next to that plan's size-cap/secret-scan changes in
  `cli_filter`; execute them in one pass to avoid two edits to the same block.

## Open questions

1. **EC-1 message vs. auto-disambiguation:** is "skip + explain + tell the user" acceptable, or do
   you want the migration to auto-disambiguate a same-minute collision (e.g. append `-2`)? Proposed:
   skip + explain (KISS, no silent renaming surprises). Auto-suffixing would complicate the scheme.
2. **EC-5 case-insensitivity:** worth doing for macOS safety, but ocman is Linux-primary. Confirm
   you want it (proposed yes; it is a one-line, zero-risk change).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered changes, run the validation, and sync docs. Prefer executing
   it together with the security IPD (shared `cli_filter` edits).
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
