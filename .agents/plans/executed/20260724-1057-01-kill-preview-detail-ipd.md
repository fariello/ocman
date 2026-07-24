# IPD: enrich `ocman kill` confirm/choose preview (project, session guess, uptime, kind)

- Date: 2026-07-24
- Concern: UI/UX (CLI). `ocman kill` shows too little about what it is about to kill: only
  `PID <n> (opencode -s <sid>)`. The maintainer wants the richer context `lr` shows (project,
  session-id guess, uptime, kind, listener/auth) so the confirm is informed.
- Scope: `ocman/cli.py` (`cli_kill` preview + multi-instance choose lines only), `tests/test_ocman.py`.
  No new detection, no DB change, no signal-handling change, no dependency. Corrective IPD for the
  already-executed kill feature (`.agents/plans/executed/20260720-2350-01-kill-ipd.md`); per
  AGENTS.md a post-execution gap is closed with a NEW IPD, not by editing the executed one.
- Status: EXECUTED (2026-07-24; maintainer approved; 517 passed / 2 skipped)
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
| KP-01 | The kill confirm preview shows rich per-instance context | For each `to_kill` target, render a multi-field block instead of just PID+cmdline: PID, Kind, Uptime (elapsed), Project (cwd/project), and Session guess. The session dict from `_attribute_session` is one of: `{id, provenance}` (single), `{ids:[...], count, provenance}` (directory one-to-many), or `{provenance:"unknown"}` (PR-102). Render the id (or `<first-id> +N more` when `ids`/`count`>1, or `unknown`) FOLLOWED BY the existing human `provenance` string ("launched-with (may be stale)", "argv hint (not in DB)", "directory (one-to-many)", "unknown") - do NOT invent a new "(guess)" label; surface the provenance the code already computes (PR-101/PR-103). Reuse the same fields `lr` uses so the two read consistently. | cli.py:12426-12430; dict fields cli.py:8097; _attribute_session shapes cli.py:8160-8175 |
| KP-02 | The multi-instance "choose which to kill" list shows the same context | Enrich the numbered choose lines (cli.py ~12405) with project + session-guess + uptime + kind, not just kind+cmdline, so the choice is informed too. | cli.py:12405 |
| KP-03 | Keep the honest session caveat via the existing provenance string | Do NOT hardcode "(best guess)"; SURFACE the `provenance` value `_attribute_session` returns (e.g. "launched-with (may be stale)" is higher-confidence than "directory (one-to-many)"), which is more honest and needs no new wording. Never imply a certain 1:1 process->session mapping. | _attribute_session provenance strings cli.py:8162,8164,8173,8175 |
| KP-04 | No behavior change beyond presentation | Do NOT change target selection, signal handling, confirm/dry-run/force, exit codes, or the PID-reuse guard. Only what is PRINTED changes. | cli_kill kill loop unchanged |

## Design decisions (RESOLVED with maintainer 2026-07-24)
- KP-01 format: RESOLVED = a compact MULTI-LINE block per target (PID / Kind / Uptime / Project /
  Session+provenance on separate labeled lines).
- Listener/Auth: RESOLVED = show a Listener/Auth line ONLY when the instance actually has a
  listener; omit it for listener-less tui instances.

## Plan-review findings (2026-07-24)
| ID | Sev | Scope | Area | Evidence | Finding | Decision |
|----|-----|-------|------|----------|---------|----------|
| PR-101 | LOW | UNDER-SCOPE | F/UX | cli.py:8162-8175 | Surface the existing `provenance` string instead of a flat "(guess)"; it distinguishes launched-with (reliable) from directory-inferred | FIXED (KP-01/03 reworded) |
| PR-102 | LOW | UNDER-SCOPE | A/correctness | cli.py:8172 | The session dict may be `{ids:[...], count}` (one-to-many), not a single `id`; the preview must handle plural + unknown, not assume `session['id']` | FIXED (KP-01 pins the three shapes) |
| PR-103 | LOW | UNDER-SCOPE | E/testing | validation plan | Tests must cover the multi-instance choose list AND the three session shapes AND dry-run zero-side-effects | FIXED (validation expanded) |

## Workflow history
- 2026-07-24 /plan-review (its_direct/pt3-claude-opus-4.8): verified kill preview line
  (cli.py:12430), choose line (12406), and `_attribute_session` return shapes (single id / ids+count
  / unknown, with human provenance strings). Revisions: surface provenance not a flat guess (PR-101),
  handle the plural/unknown session shapes (PR-102), broaden tests (PR-103). Two format decisions
  resolved interactively (multi-line block; listener/auth only-when-present). Verdict: APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL.

## Execution record
- 2026-07-24 (its_direct/pt3-claude-opus-4.8): executed KP-01..04. Lifted `_sess_str` from a
  nested fn inside `cli_list_running` to module scope (single source of truth; already handles the
  three session shapes + provenance) and reused it in both the kill choose list and the confirm
  block. Confirm block is now a multi-line per-target block (PID / Kind / Uptime / Project /
  Session), with a Listener/Auth line ONLY when the instance has a listener. Choose list enriched
  with kind/uptime/project + a session sub-line. No change to selection, signalling, guards, flags,
  or exit behavior. Added 5 tests (single rich block; listener-less omits line; directory
  ids/count shape; multi-instance choose list; dry-run enriched preview + zero side effects).
  Full suite: 517 passed, 2 skipped (perf benchmarks gated on OCMAN_BENCHMARK=1). No new em/en
  dashes.

## Non-goals
- No change to detection, selection, signalling, guards, flags, or exit behavior.
- Not touching `reconnect` (its one-confirm covers kill+relaunch); this is the standalone `kill`.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output). Add/extend a `cli_kill` preview
  test (capture stdout; monkeypatch `_kill_targets`/detection to a fake target) asserting BOTH:
  (a) the single-target confirm block shows PID, kind, uptime, project, and the session id +
  provenance; (b) the multi-instance choose list (KP-02) shows the same context per numbered
  entry. Cover the three session shapes (single id, `ids`/`count` many, unknown) so PR-102 is
  exercised.
- Confirm `--dry-run` still prints the enriched preview and performs ZERO side effects (no signal).
- No em/en dash in authored prose.

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one per KP-*) BEFORE coding.
- Open questions: none (multi-line block; listener/auth only-when-present - resolved).
- Scope fence: `ocman/cli.py` (cli_kill preview + choose lines ONLY), `tests/test_ocman.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion (this is CLI, testable headlessly; no TUI hand-test needed) + green
  tests, git mv pending/ -> executed/.
- Release: rides 1.3.0; covered by the eventual delta release-review.

## Deferred / open
- None. Both open decisions resolved (multi-line block; Listener/Auth only when a listener exists).
