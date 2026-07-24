# IPD: enrich `ocman kill` confirm/choose preview (project, session guess, uptime, kind)

- Date: 2026-07-24
- Concern: UI/UX (CLI). `ocman kill` shows too little about what it is about to kill: only
  `PID <n> (opencode -s <sid>)`. The maintainer wants the richer context `lr` shows (project,
  session-id guess, uptime, kind, listener/auth) so the confirm is informed.
- Scope: `ocman/cli.py` (`cli_kill` preview + multi-instance choose lines only), `tests/test_ocman.py`.
  No new detection, no DB change, no signal-handling change, no dependency. Corrective IPD for the
  already-executed kill feature (`.agents/plans/executed/20260720-2350-01-kill-ipd.md`); per
  AGENTS.md a post-execution gap is closed with a NEW IPD, not by editing the executed one.
- Status: PROPOSED (not yet executed)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-24 (its_direct/pt3-claude-opus-4.8): maintainer ran `ocman kill` and noted the confirm
  line ("PID 2656219 (opencode -s ses_...)") lacks project / session-guess / uptime / kind.

## Evidence
- `cli_kill` preview (cli.py ~12426-12430) prints `Will {SIG} N opencode instance(s):` then, per
  target, `  PID {pid}  ({cmdline[:80]})`. The multi-instance choose loop (cli.py ~12405) prints
  `  {i}. PID {pid}  {kind}  {cmdline[:80]}`.
- The target dicts (from `_kill_targets` -> `_reconnect_candidates` / `detect_running_instances`,
  cli.py:8097) ALREADY carry: pid, user, elapsed (uptime), started, cwd, project, kind,
  listeners, auth, session (dict with id + provenance). So this is a PURE PRESENTATION change; no
  new detection or query is needed.

## Requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| KP-01 | The kill confirm preview shows rich per-instance context | For each `to_kill` target, render a multi-field block instead of just PID+cmdline: PID, Kind, Uptime (elapsed), Project (cwd/project), Session guess (session.id + a "(guess)" note reflecting provenance, since ocman cannot be certain which session a process uses), Listener/Auth when present. Reuse the SAME fields/labels `lr` uses so the two read consistently. | cli.py:12426-12430; dict fields cli.py:8097 |
| KP-02 | The multi-instance "choose which to kill" list shows the same context | Enrich the numbered choose lines (cli.py ~12405) with project + session-guess + uptime + kind, not just kind+cmdline, so the choice is informed too. | cli.py:12405 |
| KP-03 | Keep the honest session caveat | The session id is a best-guess attribution (opencode does not track process->session); label it "(best guess)" exactly as `lr`/reconnect do, never implying certainty. | existing reconnect/lr caveat wording |
| KP-04 | No behavior change beyond presentation | Do NOT change target selection, signal handling, confirm/dry-run/force, exit codes, or the PID-reuse guard. Only what is PRINTED changes. | cli_kill kill loop unchanged |

## Design decisions to settle in plan-review (OPEN)
- KP-01 format: a compact multi-line block per target (label: value) vs a one-line summary.
  RECOMMEND a short multi-line block per target (PID/Kind/Uptime/Project/Session), since a kill
  is destructive and the extra lines aid the decision; confirm.
- Whether to also show Listener/Auth (the security columns) on the kill preview, or keep those to
  `lr` only. RECOMMEND include a brief Listener/Auth line only when a listener exists.

## Non-goals
- No change to detection, selection, signalling, guards, flags, or exit behavior.
- Not touching `reconnect` (its one-confirm covers kill+relaunch); this is the standalone `kill`.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output). Add/extend a `cli_kill` preview
  test asserting the confirm output for a fake target includes the PID, project, session-guess,
  uptime, and kind (capture stdout via the existing test harness / monkeypatched detection).
- Confirm dry-run still prints the enriched preview and performs zero side effects.
- No em/en dash in authored prose.

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one per KP-*) BEFORE coding.
- Open questions: KP-01 format, listener/auth inclusion (resolve in plan-review).
- Scope fence: `ocman/cli.py` (cli_kill preview + choose lines ONLY), `tests/test_ocman.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion (this is CLI, testable headlessly; no TUI hand-test needed) + green
  tests, git mv pending/ -> executed/.
- Release: rides 1.3.0; covered by the eventual delta release-review.

## Deferred / open
- The OPEN decisions above are resolved in plan-review before execution.
