# Decisions and assumptions - assess-functionality (disk-usage) 20260704-153701

## Concern / scope
- Concern: functionality completeness. Lens: functionality.md.
- Scope: NARROWED by the user to disk-usage reporting (per-project + backups). Not a
  whole-project functionality sweep.
- Lead personas: stakeholder, power user, novice, QA.

## Project conventions discovered
- `ocman info` (`db_show_info`) is the existing system-info command; reports DB-family
  size + global session-diff total. Backups + per-project breakdown are absent.
- Backups dir = mixed `*.zip` + `opencode-db-cleanup-*` directories → recursive sizing needed.
- Session-diff files map to projects via `session.project_id` (exact attribution).
- Honest-docs principle governs FUNC-3.
- Out of scope (framework): `.agents/workflows/`, `workflow-artifacts/`.

## Key decisions
- Verdict **needs work** for this capability.
- **Do not report per-project DB bytes** (FUNC-3): single shared SQLite file; an estimate
  would mislead. Report exact session-diff bytes + row/token counts per project instead.
- No shell-out to `du`; use `os.scandir`/`Path.stat` for cross-platform correctness (KISS).
- Backups section shown always (cheap, high value) — assumption, see open Q3.
- Per-project view behind an explicit flag (`--by-project`) so default `info` stays concise.

## What was intentionally NOT proposed (and why)
- Per-project DB byte figures (misleading; deferred with honest-docs rationale).
- Full disk-analytics UI / charts / historical size tracking (over-scope, untraceable).
- TUI parity now (deferred to follow-up; CLI answers the user's question first).

## Open questions for the user
1. Interface: `ocman info --by-project` vs dedicated `ocman disk`/`du` subcommand?
2. Per-project: exact session-diff bytes + counts only, or also an explicitly-labeled
   estimated DB-size share?
3. Show backups section always, or only under `-v`?
