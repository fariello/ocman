# Decisions and assumptions - assess-self-documentation (process-lock) 20260704-175217

## Concern / scope
- Concern: self-documentation ("errors that teach"). Lens: self-documentation.md.
- Scope: NARROWED by the user to the running-opencode check blocking --delete/--delete-project/--clean.
- Lead personas: complete novice + UI/UX, with power user and QA.

## Project conventions discovered
- Current check: `pgrep -f "opencode --continue"`, returncode-only, single fixed message, duplicated 3x
  (ocman.py:4599-4609/4847-4856/5847-5856). Windows skips it.
- Feasibility (Linux, verified): `ps -o pid,tty,etimes,lstart,args` + `/proc/<pid>/cwd` are fast, no recursion.
- Out of scope (framework): `.agents/workflows/`, `workflow-artifacts/`.

## Key decisions
- Verdict **needs work** (uninformative error).
- Honest-docs boundary drives the two deferrals:
  - **Session id (SD-4):** not reliably derivable from a process → do not print a guess on a destructive
    screen; substitute best-effort *project* attribution by CWD.
  - **Last-activity (SD-5):** not cheap/reliable → report start time + elapsed instead (exact, cheap).
- **False positives (SD-3):** `pgrep -f` substring matching is a real correctness issue (matched ocman's own
  probe command during this assessment); the new detector must filter to plausible opencode processes and
  exclude self.
- No new dependency (parse `ps`, use `/proc`); no psutil; no process-killing; stay within ~2s.

## What was intentionally NOT proposed (and why)
- Printing a per-process session id (SD-4): guess risk on a destructive op (honest-docs). Deferred.
- True CPU/IO last-activity (SD-5): fuzzy/platform-specific/costly. Deferred; start+elapsed instead.
- Offering to kill the processes for the user: over-scope + dangerous. Not proposed.
- macOS CWD via `lsof`: extra per-process cost against the 2s budget; propose omitting CWD on non-Linux.

## Open questions for the user
1. Is best-effort **project** (from CWD) an acceptable stand-in for the requested "session id"?
2. Strict vs lenient plausible-opencode filter?
3. OK to omit CWD on macOS (no /proc) to stay within the time budget?
