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
| 1 | EC-1 | On a canonical-name collision during migration, print an **explanatory** message (not just "SKIP"): name the two source files, explain that minute-precision names collided, and tell the user to rename/inspect manually or re-run with `--force` to overwrite (with the loss that implies). Keep the safe default (skip, source preserved). **PRE-1 (plan-review):** the current guard only checks apply-time `dst.exists()` (`migrate_dir:84`), so it misses **two in-plan sources that target the same canonical name** - at dry-run BOTH print "WOULD RENAME" to the same target (misleading; verified), and at apply the second is silently skipped. Detect **in-plan duplicate targets** by grouping the planned renames by target: any target claimed by >1 source is a collision reported in BOTH dry-run and apply (rename the first deterministically - e.g. earliest by original name - and skip/flag the rest). Also add a one-line note in `--help`/README that canonical names are minute-precision and same-minute artifacts of one session can collide. | scripts/migrate_recovery_names.py:41-92 | Low | Tests: (i) two same-minute legacy files -> **dry-run** reports the collision (not two plain "WOULD RENAME"); (ii) apply renames exactly one, skips the other with the explanatory message, and **both source files still exist** (data-safety invariant); (iii) collision with a pre-existing canonical file still skips safely |
| 2 | EC-2 | In `cli_filter`, after reading the input, **refuse empty/whitespace-only content** with a clear `RecoveryError("Input file is empty: ...")`. **PRE-3 (ordering):** this check must sit **after** the file read but **before** the security IPD's size-cap/secret-scan and the API call, so the three guards form one ordered gate (read -> empty-check -> size-cap -> secret-scan -> send). Coordinate placement when executing both IPDs to avoid duplicate/parallel guards. | ocman.py:4875-4903 | Low | Test: empty and whitespace-only input raise `RecoveryError`; API not called (monkeypatched) |
| 3 | EC-3 | `.strip()` the `--scope` value (and treat all-whitespace as absent) before the "at least one of --project/--scope" check so whitespace-only scope is rejected consistently with empty/None. Use the stripped value for the scope text sent to the model too. | ocman.py:4892-4896 | Low | Test: `--scope "   "` raises the same `RecoveryError` as empty scope |
| 4 | EC-4 | Add a lightweight guard in `canonical_recovery_name`: validate `kind in RECOVERY_KINDS` (raise `ValueError` on a bad kind) so a wrong-kind caller fails loudly instead of writing an unparseable name. KISS - one membership check, no new abstraction. **Verified safe:** all in-code callers pass literal kinds (`"compacted"`/`"restart"`, ocman.py:3497,3688,4814,4941); the only dynamic caller (`migrate_recovery_names.py:61`) already filters `kind not in RECOVERY_KINDS` first (line 52), so the raise cannot break an existing path. | ocman.py (canonical_recovery_name) | Low | Test: `canonical_recovery_name(..., 'bogus')` raises `ValueError`; each real kind still works |
| 5 | EC-5 | Make `parse_recovery_name` suffix matching **case-insensitive**. **PRE-2 (precision):** lowercase only for the `endswith` **detection** (`name.lower().endswith(f".{k}.md")`); keep the `stem` slice on the ORIGINAL `name` (the matched suffix length is identical regardless of case, so the original-case session id is preserved unchanged). Do NOT lowercase the returned session id or timestamp. | ocman.py:3431-3440 (parse_recovery_name) | Low | Test: `X.RESTART.MD` parses to kind `restart`; a mixed-case sid (`Ses_AbC`) round-trips with case preserved |
| 6 | EC-7 | Add regression tests pinning the `dt=None`-on-invalid-date behavior (both legacy and canonical forms), documenting it as intended (safe mtime fallback). No code change. | tests only | Low | Tests green |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| EC-6 | - | - | NOT deferred as risky - it is simply **not worth code**: real opencode session ids are `ses_<base62>`, never a bare 8-digit string, so the mis-split is unreachable in practice and the canonical form round-trips. Documented as a known parser limitation; a regression test records the current behavior. If session-id formats ever change, revisit. | Add a comment in `parse_recovery_name` noting the date-only legacy ambiguity. |
| (seconds precision itself) | Medium-High | functionality | Raising canonical names back to **seconds** precision to avoid EC-1 collisions would reverse the deliberate `YYYYMMDD-HHMM` decision (and its tests/docs), re-introduce the longer names the user chose against, and still not fully avoid collisions. Handling the collision gracefully (Step 1) is the right fix; changing the scheme is not. | n/a |

## Scope check

- Over-scope: none proposed. Do NOT add content-hash suffixes or a collision-avoidance counter to
  canonical names - that would complicate the naming scheme the user deliberately kept simple
  (Complexity axis). Step 1's in-plan duplicate-target detection (PRE-1) is a migration-time
  reporting improvement, NOT a change to the naming scheme itself, so it stays within KISS.
- Under-scope (added above): empty-input rejection (EC-2), whitespace-scope rejection (EC-3),
  kind validation (EC-4), case-insensitive suffix (EC-5), and the collision explanation (EC-1).

## Required tests / validation

- `tests/test_recovery_naming.py`: EC-4 (bad kind raises `ValueError`), EC-5 (case-insensitive
  parse + mixed-case sid round-trips with case preserved; PRE-2), EC-7 (invalid-date -> `dt=None`),
  EC-6 (documented date-only ambiguity behavior).
- `tests/test_file_tools.py`: EC-2 (empty/whitespace input refused, API not called),
  EC-3 (whitespace-only scope refused).
- `tests/test_migrate_recovery_names.py` (PRE-1/PRE-4): EC-1 same-minute collision -
  (i) **dry-run reports the collision** (not two plain "WOULD RENAME"); (ii) apply renames exactly
  one and skips the other with the explanatory message; (iii) **both source files still exist**
  after apply (data-safety invariant); (iv) collision with a pre-existing canonical file skips safely.
- Full suite green: `PYTHONPATH=. pytest` (currently 150 passed, 2 skipped).

## Spec / documentation sync

- README/`--help`: note that canonical recovery names are **minute-precision** and that two
  artifacts of the same session generated within the same minute can collide (the migration skips
  the second; live generation backs up via `.bu.NNN`). Document that `filter` rejects empty input.
- Coordinate with the pending **security IPD** (`20260706-assess-security-filter-and-migration.md`):
  EC-2/EC-3 (input validation) sit right next to that plan's size-cap/secret-scan changes in
  `cli_filter`; execute them in one pass. **Guard ordering (PRE-3):** read -> empty/whitespace
  check (EC-2) -> size-cap (security Step 2) -> secret-scan (security Step 3) -> send. Implement as
  one ordered gate; do not create two separate validation blocks.

### Plan-review revisions (2026-07-06, applied in place)

- **PRE-1 (High):** Step 1 only handled apply-time `dst.exists()`; it missed **in-plan duplicate
  targets** (two same-minute sources), which produce a misleading dry-run and a silent apply-time
  skip. Rewritten to group planned renames by target and report the collision in dry-run AND apply;
  tests now assert the dry-run surfaces it and both sources survive.
- **PRE-2 (Low):** Step 5 made precise - lowercase only for suffix detection, slice on the original
  name so the session-id case is preserved; added a mixed-case round-trip test.
- **PRE-3 (Low):** documented the execution ORDER of the `cli_filter` guards shared with the
  security IPD (empty-check before size-cap before secret-scan).
- **PRE-4 (Low):** added the data-safety assertion (both sources present after a collision) to the
  EC-1 tests.
- **Verified safe:** EC-4's `ValueError` cannot break an existing path (all in-code callers pass
  literal kinds; the migration filters kind first).

## Open questions

1. **EC-1 collision handling:** three options - (a) skip + explain (proposed; KISS, no silent
   renames), (b) auto-disambiguate the second same-minute file (append `-2`), or (c) skip only when
   contents differ but silently drop an exact-duplicate. Proposed (a). (b) complicates the scheme;
   (c) risks a wrong "duplicate" judgment. This is a human call.
2. **EC-5 case-insensitivity:** worth doing for macOS safety, but ocman is Linux-primary. Confirm
   you want it (proposed yes; one-line, zero-risk).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered changes, run the validation, and sync docs. Prefer executing
   it together with the security IPD (shared `cli_filter` edits).
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
