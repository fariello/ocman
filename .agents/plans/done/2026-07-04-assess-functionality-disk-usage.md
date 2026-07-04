# IPD: Assess functionality - disk-usage reporting (per-project + backups)

- Date: 2026-07-04
- Concern: functionality completeness
- Scope: **narrowed** (user request) to disk-usage reporting — how much space each
  project uses on disk, and how much the backups directory uses. Touches `ocman info`
  (`db_show_info`) and the CLI; TUI parity is a follow-up.
- Status: PENDING (awaiting human approval; not executed)
- Author: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us

## Goal

Give the user visibility into disk consumption: (a) how much the **backups** directory
occupies (a real pain point — observed 7.3 GB of backups, dominated by
`opencode-db-cleanup-*` dirs each holding a full ~2.8 GB DB copy), and (b) a
**per-project** on-disk breakdown. Do this honestly: report exact figures where they
exist and never present an estimate as exact (SQLite is a single shared file, so
per-project DB *bytes* are not directly measurable).

## Project conventions discovered (Step 0)

- Intent/audience: single-user local admin tool for opencode; `ocman info` is the
  existing "OPENCODE SYSTEM INFORMATION" command (`db_show_info`, ocman.py:6600-6684),
  already reporting DB-family size and a global session-diff total.
- Guiding principles: none dedicated; universal fallback + `ARCHITECTURE.md`
  (intuitive/self-documenting, configurable-over-hardcoded, KISS, **honest docs**).
- Pending-plans: `.agents/plans/pending/`; validation `PYTHONPATH=. pytest`.
- Relevant facts verified in code:
  - Backups live under `default_backup_dir` (config; default
    `~/.local/share/opencode/backups`) and contain both `*.zip` archives (from
    `--backup-opencode` / rollback ZIPs) and `opencode-db-cleanup-*` **directories**
    (from delete/cleanup DB-family backups). Sizing requires a recursive walk.
  - Session-diff files are `~/.local/share/opencode/storage/session_diff/<session_id>.json`;
    `session.id → session.project_id` gives **exact** per-project attribution of those bytes.
  - Per-project DB bytes are NOT available (one shared `opencode.db`).

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate.

| ID | Severity | Rem. Risk | Persona | Area | Finding | Evidence |
|----|----------|-----------|---------|------|---------|----------|
| FUNC-1 | Medium | Low | stakeholder / power user | backup disk usage | No command reports backup-dir usage; users accumulate GBs unseen | ocman.py:6600-6684; default_backup_dir |
| FUNC-2 | Medium | Low | power user | per-project session-diff bytes | No per-project disk breakdown; session-diff bytes are exactly attributable via project_id | ocman.py:6600-6611; session.project_id |
| FUNC-3 | High | Medium-High (functionality) | QA / power user | per-project DB bytes | Per-project DB *bytes* are not measurable (shared SQLite file); presenting an estimate as exact would violate honest-docs | single opencode.db |
| FUNC-4 | Low | Low | novice / UI-UX | discoverability | New info must be discoverable (`ocman info` + documented flag) | README, preprocess_argv |
| FUNC-5 | Low | Low | power user | TUI parity | TUI admin tab could show the same figures (follow-up) | ocman_tui/widgets/database.py |

## Proposed changes (ordered, validatable)

| Step | Source IDs | Change | Files | Rem. Risk | Validation |
|------|-----------|--------|-------|-----------|------------|
| 1 | FUNC-1 | Add a helper `dir_usage(path) -> (total_bytes, file_count)` that walks a directory tree (files + nested dirs) and sums sizes, tolerating unreadable entries. | ocman.py | Low | Unit test on a temp tree with nested dirs + a zip-sized file |
| 2 | FUNC-1, FUNC-4 | Add a **"Backups (Disk Storage)"** section to `db_show_info`: path, total size (via step 1), number of backup archives/dirs, oldest/newest mtime. Print even when empty ("0 B, none"). | ocman.py:6680-6684 area | Low | Extend `test_db_show_info` to assert the Backups section appears; test with a seeded backup dir |
| 3 | FUNC-2, FUNC-3 | Add a per-project on-disk breakdown, invoked by an explicit flag (proposed `ocman info --by-project`, or `ocman info -P`). For each project: exact **session-diff bytes on disk** (sum sizes of `<session_id>.json` for that project's sessions), plus session/message/token counts. Sort by session-diff bytes desc. **Do NOT report per-project DB bytes**; add a one-line note that DB storage is a single shared file and is not attributable per project. | ocman.py (new helper + db_show_info branch) | Low | Test with 2 projects + seeded diff files of known sizes; assert bytes + counts + ordering; assert no misleading DB-bytes column |
| 4 | FUNC-4 | Document the new `info` behavior (backups section always; `--by-project` flag) in README argument reference + `ocman info` help/epilog. Optionally add a `disk`/`du` natural-language alias in `preprocess_argv` mapping to `info --by-project`. | README.md, ocman.py (parse_args/preprocess_argv) | Low | `test_preprocess_argv` extended if alias added; README updated |
| 5 | FUNC-1/2 | CHANGELOG entry under Added. | CHANGELOG.md | Low | Docs only |

## Deferred / out of scope (with reason)

| Finding ID | Rem. Risk | Axis | Reason | Recommended later step |
|------------|-----------|------|--------|------------------------|
| FUNC-3 (per-project DB *bytes*) | Medium-High | functionality | Not directly measurable from a shared SQLite file; any number is an estimate and would mislead (honest-docs). | If ever wanted, add a clearly-labeled "(estimated share)" figure computed from row/token proportion — separate, opt-in decision. |
| FUNC-5 (TUI parity) | Low | — | Deferred to a follow-up (CLI first); not required to answer the user's question. | After CLI lands, surface backups total + per-project view in the Database Admin tab. |

## Scope check

- **Over-scope (avoid):** No new dependency (`du` shell-out is unnecessary — `os.scandir`/
  `Path.stat` suffice and stay cross-platform, KISS). Do not add a full disk-analytics UI,
  charts, or historical size tracking — untraceable to the request.
- **Under-scope (add):** Backups usage (FUNC-1) and per-project session-diff bytes
  (FUNC-2) are the direct answer to the user's question and are proposed above.

## Required tests / validation

- `PYTHONPATH=. pytest` stays green + new tests: `dir_usage` unit test (nested dirs,
  unreadable entry tolerated), `db_show_info` backups-section test, per-project breakdown
  test (known byte sizes + counts + ordering, and absence of a per-project DB-bytes claim).
- Determinism: seed temp backup/storage dirs with fixed-size files; assert on exact bytes.

## Spec / documentation sync

- README argument reference + `ocman info` help updated (backups section; `--by-project`).
- CHANGELOG "Added" entry.

## Open questions

1. Preferred interface for the per-project view: a flag on the existing command
   (`ocman info --by-project`) vs a dedicated subcommand (`ocman disk` / `ocman du`)?
   (Assumption: `ocman info --by-project`, plus an optional `disk` NL alias.)
2. For per-project, is exact **session-diff bytes + row/token counts** sufficient, or do
   you also want an explicitly-labeled **estimated** per-project DB-size share? (Assumption:
   exact figures only; no estimated DB bytes, per honest-docs. Confirm.)
3. Should `ocman info` show the backups section **always**, or only with `-v`? (Assumption:
   always — it is high-value and cheap.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered steps and run the validation.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
