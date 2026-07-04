# IPD: Assess functionality - copy restart.md into the project's .agents/prompts/pending/

- Date: 2026-07-04
- Concern: functionality completeness
- Scope: NARROWED (user request) to: when ocman writes a `*.restart.md`, also drop a copy
  into the working project's `.agents/prompts/pending/` when that project uses an
  `.agents/plans` or `.agents/prompts` convention, with a specific name + backup scheme.
- Status: PENDING (awaiting human approval; not executed)
- Author: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us

## Goal

Make recovered restart documents land where the user's agent workflows expect them.
When ocman generates a `*.restart.md`, and the project being worked on contains a
`.agents/plans/` **or** `.agents/prompts/` directory, also write a copy to:

```
<project>/.agents/prompts/pending/YYYYMMDD-<session_id>.restart.md
```

- `YYYYMMDD` = the date the session was **last updated** (from the DB).
- `<session_id>` = the opencode session id (e.g. `ses_XXXX`).
- On name collision, back up the existing file to `…​.restart.bu.NNN.md` (NNN from `001`,
  incrementing) **before** writing the new copy at the canonical name.

## Project conventions discovered (Step 0)

- Guiding principles: none dedicated; universal fallback + `ARCHITECTURE.md` (honest docs, KISS).
- Pending-plans: `.agents/plans/pending/`; validation `PYTHONPATH=. pytest`.
- Restart file is written in `recover_from_export` at **ocman.py:3473-3481** via
  `write_text(restart_path, render_restart_context(...))`; default name
  `opencode-<utc-ts>-<safe_session_id>.restart.md` under `output_dir` (`args.out`,
  default `./opencode-recovery`).
- `session.updated` is `str(time_updated)` epoch-ms and may be `"unknown"` (ocman.py:8044, 4387);
  `_fmt_ts` (3679) already parses epoch-ms → date.
- Existing `_backup_if_exists` (3276-3312) uses a **different** scheme (`.NN.bak`, 2-digit from 01,
  and it *renames* the file) — NOT the requested `.restart.bu.NNN.md` (3-digit from 001). A new
  helper is needed.
- Working-dir candidates: `--session-dir`/`opencode_cwd` (ocman.py:8001-8029), the session's DB
  `directory`, and CWD. The request's "project being worked on" must be pinned (see RSP-2 / open Q1).

## Findings

| ID | Severity | Rem. Risk | Persona | Finding | Evidence |
|----|----------|-----------|---------|---------|----------|
| RSP-1 | Medium | Low | stakeholder / power user | restart.md not copied into the project's prompts dir | ocman.py:3473-3481 |
| RSP-2 | High | Medium (functionality) | architect / QA | "the project being worked on" is ambiguous (3 candidate dirs); wrong choice writes into an unintended repo | ocman.py:8001-8029, args.out |
| RSP-3 | Medium | Low | QA | `YYYYMMDD` must derive from session last-updated (epoch-ms string, may be "unknown") | ocman.py:8044, 4387; _fmt_ts:3679 |
| RSP-4 | Medium | Low | software engineer | Requested backup scheme (`.restart.bu.NNN.md`, 001+) differs from existing `_backup_if_exists` (`.NN.bak`, 01+, renames) | ocman.py:3276-3312 |
| RSP-5 | Low | Low | QA | session id must be filesystem-safe in the filename | ocman.py:2510, 3460 |
| RSP-6 | Medium | Low | security / QA | Writing into another repo must be path-contained, symlink-safe, and fail-soft (must not break primary recovery output) | write flow |
| RSP-7 | Low | Low | power user | Side-effect needs discoverability + opt-out | new behavior |
| RSP-8 | Low | Low | QA | Copy ONLY the restart file (scope guard) | request text |

## Proposed changes (ordered, validatable)

| Step | Source IDs | Change | Files | Rem. Risk | Validation |
|------|-----------|--------|-------|-----------|------------|
| 1 | RSP-2 | Add `resolve_project_dir(session, session_dir)` returning the target project dir by precedence: (a) explicit `--session-dir` if a real dir; else (b) `session.raw["directory"]` if it exists on disk; else (c) `Path.cwd()`. Return `None` if none resolves. **Confirm precedence in open Q1 before building.** | ocman.py | Low | Unit test each precedence branch with temp dirs |
| 2 | RSP-1, RSP-3, RSP-5 | Add `project_prompt_copy_name(session) -> str` = `f"{YYYYMMDD}-{safe_filename(session.session_id)}.restart.md"`, where `YYYYMMDD` parses `session.updated` as epoch-ms (reuse `_fmt_ts` date logic) and falls back to `get_startup_timestamp_local("%Y%m%d")` when unavailable/"unknown". | ocman.py | Low | Test: epoch-ms → correct date; "unknown" → startup-date fallback; odd session id → safe name |
| 3 | RSP-4 | Add `_backup_restart_bu(path) -> Path | None`: if `path` exists, rename it to `<stem-before-.restart.md>.restart.bu.NNN.md` with the next free `NNN` (zero-padded 3, starting `001`); copy+unlink fallback on rename failure; return the backup path. Distinct from `_backup_if_exists`. | ocman.py | Low | Test: first collision → .bu.001.md; second → .bu.002.md; new file then written at canonical name |
| 4 | RSP-1, RSP-6, RSP-7, RSP-8 | Add `maybe_copy_restart_to_project(restart_path, session, project_dir, enabled) -> Path | None`: if `enabled` and `project_dir` contains `.agents/plans` OR `.agents/prompts`, compute `dest = project_dir/.agents/prompts/pending/<name>` (step 2); **assert `dest` resolves under `project_dir/.agents/prompts/pending`** (reject symlink/traversal escape); `mkdir(pending, parents=True)` only under an existing `.agents` (do not create `.agents` itself if absent — but it exists by the trigger condition); if `dest` exists, back it up (step 3); `shutil.copy2(restart_path, dest)`; print an `[INFO]` line with the path. **Wrap the entire function body in try/except** so any failure warns and returns None, never aborting recovery. Copy ONLY the restart file. | ocman.py | Low | Tests: trigger only when .agents/plans or .agents/prompts present; correct dest name; collision → backup then copy; copy failure → warns, primary output intact; ONLY restart copied |
| 5 | RSP-1 | Call `maybe_copy_restart_to_project(...)` in `recover_from_export` right after the restart file is written (ocman.py:3481), passing the resolved project dir and the enabled flag. Add the copied path to the returned `generated_paths` list. | ocman.py:3473-3482 | Low | Existing recovery tests pass; e2e test: a temp "project" with .agents/plans gets the copy after recover_from_export |
| 6 | RSP-7 | Add opt-out: config key `copy_restart_to_project_prompts` (default `true`) + a `--no-project-prompt` CLI flag; the flag overrides config. Thread `enabled` into `recover_from_export`. | ocman.py (DEFAULT_CONFIG, template, parse_args), CHANGELOG | Low | Test: flag/config false → no copy; default → copy |
| 7 | docs | README (recovery section) documents the auto-copy, its trigger, the filename/backup scheme, and the opt-out; CHANGELOG `[Unreleased]` Added entry. | README.md, CHANGELOG.md | Low | Docs only |

## Deferred / out of scope (with reason)

| Finding ID | Rem. Risk | Axis | Reason | Recommended later step |
|------------|-----------|------|--------|------------------------|
| (copy transcript/prompt/compacted too) | — | scope | Request is restart-only (RSP-8); copying the others is unrequested scope creep | Separate decision if wanted |

## Scope check

- **Over-scope (avoid):** Do not create `.agents/` where it does not exist (only act when the project
  already uses the convention). Do not copy non-restart artifacts. No new dependency (`shutil`/`pathlib`).
  Do not write outside `<project>/.agents/prompts/pending/`.
- **Under-scope (add):** the copy itself (RSP-1), the correct name/date (RSP-3), the requested backup
  scheme (RSP-4), and safety/fail-soft (RSP-6) are the core and are all proposed.

## Required tests / validation

- `PYTHONPATH=. pytest` stays green + new unit tests for: `resolve_project_dir` precedence,
  `project_prompt_copy_name` (epoch-ms + "unknown" fallback + safe id), `_backup_restart_bu`
  (001/002 increment), and `maybe_copy_restart_to_project` (trigger condition, correct dest,
  collision→backup→write, **path-escape rejection**, **fail-soft on copy error**, restart-only).
- Determinism: use temp "project" dirs with/without `.agents/plans`/`.agents/prompts`; assert on exact
  filenames and that a copy failure leaves the primary `output_dir` restart file intact.

## Spec / documentation sync

- README recovery section: document the trigger, the `<project>/.agents/prompts/pending/YYYYMMDD-<id>.restart.md`
  destination, the `.restart.bu.NNN.md` backup scheme, and the `--no-project-prompt` / config opt-out.
- CHANGELOG `[Unreleased]` Added entry.

## Open questions

1. **Precedence for "the project being worked on" (RSP-2).** Proposed: `--session-dir` → session's DB
   `directory` (if on disk) → CWD. Is that the right order? In particular, should CWD take priority (the
   repo you're literally sitting in) over the session's recorded directory? (Assumption: `--session-dir`
   first, then session directory, then CWD.)
2. **Trigger vs destination mismatch.** The trigger is "`.agents/plans` OR `.agents/prompts` exists" but the
   destination is always `.agents/prompts/pending/`. If a project has `.agents/plans` but not
   `.agents/prompts`, should ocman create `.agents/prompts/pending/`? (Assumption: yes — create
   `prompts/pending` under the existing `.agents`.)
3. **Opt-out surface.** Config key + `--no-project-prompt` flag, default ON — acceptable? (Assumption: yes.)
4. **Date basis.** `YYYYMMDD` from session last-updated in **local** time or UTC? (`_fmt_ts` uses UTC.)
   (Assumption: local time, to match filenames users expect; confirm.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT
auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered steps and run the validation.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
