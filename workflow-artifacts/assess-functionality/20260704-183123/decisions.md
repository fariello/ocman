# Decisions and assumptions - assess-functionality (restart→project prompts) 20260704-183123

## Concern / scope
- Concern: functionality completeness. Lens: functionality.md.
- Scope: NARROWED by the user to auto-copying `*.restart.md` into a project's `.agents/prompts/pending/`.
- Lead personas: stakeholder, power user, architect, QA.

## Project conventions discovered
- Restart file written in `recover_from_export` (ocman.py:3473-3481) via `write_text` + `render_restart_context`.
- `session.updated` = epoch-ms as string, may be "unknown"; `_fmt_ts` (3679) parses epoch-ms → date.
- Existing `_backup_if_exists` uses `.NN.bak` (renames) — different from the requested `.restart.bu.NNN.md`.
- Working-dir candidates: `--session-dir`/`opencode_cwd`, session DB `directory`, CWD, `output_dir`.
- Out of scope (framework): `.agents/workflows/`, `workflow-artifacts/`. (Note: this feature legitimately
  writes into a *target project's* `.agents/prompts/`, which is that project's own dir, not this framework.)

## Key decisions
- Verdict **needs work** (feature absent).
- **Highest design risk = RSP-2** (which directory). Proposed precedence: --session-dir → session DB
  directory (if on disk) → CWD. Flagged as open Q1 for confirmation because a wrong choice writes into the
  wrong repo.
- **Requested backup scheme is new** (RSP-4): implement `.restart.bu.NNN.md` (001+) as a dedicated helper;
  do NOT reuse `_backup_if_exists` (`.NN.bak`, and it renames rather than keeping the new canonical file).
- **Safety (RSP-6):** cross-repo write must be path-contained (dest under `.agents/prompts/pending`),
  symlink/traversal-safe, and **fail-soft** — a copy failure must never abort the primary recovery output.
- **Scope guard (RSP-8):** copy ONLY the restart file, not transcript/prompt/compacted.
- No new dependency; opt-outable; only active when the project already uses the `.agents` convention.

## What was intentionally NOT proposed (and why)
- Copying non-restart artifacts: not requested (RSP-8).
- Creating `.agents/` from scratch: the feature only triggers when the convention already exists.
- Reusing `_backup_if_exists`: wrong scheme + it moves the file.

## Open questions for the user
1. Project-dir precedence (--session-dir → session dir → CWD)? Should CWD win over the session's dir?
2. If a project has `.agents/plans` but not `.agents/prompts`, create `.agents/prompts/pending`? (Assumed yes.)
3. Opt-out via config key + `--no-project-prompt`, default ON? (Assumed yes.)
4. `YYYYMMDD` in local time or UTC? (Assumed local; `_fmt_ts` uses UTC — confirm.)
