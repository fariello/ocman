# Implementation Plan 03 - Multi-session actions & project expansion

Status: EXECUTED

IPD 03 in the execution order. Depends on IPD 02 (batch resolver). Lets
`compact`, `recover`, `show`, `delete`,
and `backup` operate on multiple sessions and on "all sessions in a project",
with the shared ambiguity policy.

---

## Motivation

Users want to act on several sessions at once, or on a whole project's sessions,
without invoking the command repeatedly. Today each of these accepts a single
`session` positional (`build_parser`, `ocman.py:5211-5262`).

---

## User Review Required

> [!IMPORTANT]
> - `compact` takes MULTIPLE sessions but exactly ONE model. Sessions vs model
>   are auto-detected via IPD 02; the one model applies to all sessions.
> - Project expansion: a positional that resolves to a project expands to that
>   project's sessions (root-only by default; `-A` includes subagents). Genuine
>   ambiguity uses IPD 02's prompt/verbose-error policy; the common case is not
>   taxed.
> - Multi-session delete: ONE preview of the whole set + a single typed confirm;
>   `-y/--yes` skips it, `--dry-run` previews only.
> - Multi-session compact cost: show a per-session and grand-total ESTIMATE and
>   the average up front (one confirm for the batch), and after the run sum the
>   provider-reported actuals. BOTH are labeled guesses: the estimate guesses
>   tokens in/out; the "actual" relies on config prices and API-reported tokens
>   which can under-report.

---

## Design

### Grammar

Change the positional(s) on `compact`, `recover`, `show`, `delete` to a single
variadic `specs` (`nargs="*"` for recover/compact so the interactive pick still
works with no spec; `nargs="+"` for show/delete which require at least one).
`backup create` gains the ability to accept session specs / a project (today it
backs up global state; see Backup below). All specs go through `resolve_targets`
(IPD 02) in the `main()` handler.

**Compact model is NOT a separate positional.** Today `compact` has TWO optional
positionals (`session` then `model`, `ocman.py:5226-5229`). argparse cannot
reliably split a variadic `specs` (`nargs="*"`) followed by a trailing optional
`model` positional (the greedy variadic swallows the model). So `compact` uses
ONE variadic `specs` list and the model is identified BY RESOLUTION: after
`resolve_targets(specs, kinds={session,project,model})`, partition results into
sessions (+ project expansions) and models. Require exactly one model: zero
models -> prompt/pick as today (`ocman.py:5872` model selection); two or more
resolved models -> error ("compact takes exactly one model"). This removes the
old two-positional grammar; document the change. (A user who wants to force
"this is the model" uses `model:NAME`, per IPD 02.)

### Per-command behavior

- **`compact` (multi-session, one model).** Resolve specs into sessions (+ maybe
  a project to expand) and at most one model. Refactor `run_compaction`
  (`ocman.py:5872`) so its cost estimate + confirm is a reusable step:
  - Phase 1: build each session's recovery transcript and per-session token/cost
    estimate (reusing existing estimate path, `ocman.py:5929-5938`).
  - Phase 2: print a table (session, est tokens, est cost), the grand total and
    average, with the explicit "these are estimates" note; one confirm for the
    whole batch (`-y` skips; see IPD 04).
  - Phase 3: run each; accumulate any provider-reported actual tokens/cost into a
    post-run total; print grand total + average actual with the "guess" caveat.
    Note: `call_compaction_api` already parses `usage.prompt_tokens/completion_
    tokens` but only PRINTS them (`ocman.py`, in `call_compaction_api` around the
    "Actual tokens" print). To sum actuals, `call_compaction_api` (and
    `run_compaction`) must RETURN the usage (e.g. return the text plus a small
    usage dict) rather than only printing it. If the provider omits `usage`, the
    actual total is reported as "unavailable" for that session (do not fabricate).
  - A per-session failure does not abort the batch by default: report it, keep
    going, and summarize successes/failures at the end (destructive-free op).
- **`recover` (multi-session).** Iterate; write each session's recovery files;
  summarize. No confirm needed (non-destructive, no egress).
- **`show` (multi-session).** Iterate; print each session's details/head/tail
  with a clear per-session header. `-H/-T/-D` apply to each.
- **`delete` (multi-session + project).** Resolve the full set, print ONE preview
  (count, ids, titles, and for a project expansion the project name), then a
  single typed confirm via `confirm_destructive` (`ocman.py:8209`). `-y/--yes`
  skips the typed confirm; `--dry-run` previews only; `--force` still bypasses
  only the process-lock. Delete each via `db_delete_session_recursive`.
- **`backup` with session/project scope.** `backup create` today snapshots whole
  opencode state. Adding "all sessions in a project" here means: allow
  `backup create` to target a project (or session list) and produce per-session
  or per-project `.ocbox` bundles (reuse `bundle_session_data` /
  `bundle_project_data` from the executed project-export work). Exact surface:
  `ocman backup create <specs> to <dir>` writes one bundle per resolved target
  into the directory; with no specs it keeps the current whole-state ZIP
  behavior. (If this overlaps too much with `session export`, the reviewer may
  fold it into export instead; flagged as an open design point.)

### Subagents

Expansion and project-scope default to root sessions; `-A/--all-sessions`
includes subagents. Explicitly-named subagent ids are always honored. Note
`-A/--all-sessions` currently exists only on `list`/`search`/`show`/`delete`
(`ocman.py:5218`, `5240`); it MUST be ADDED to `compact` and `recover` for
project expansion to honor the root-only default there.

### `-y/--yes`

Add `-y/--yes` to `compact` and `delete` (skips their confirms). Does NOT resolve
ambiguity and does NOT bypass the process-lock. (Definition shared with IPD 04.)

---

## Tests

- compact: multiple sessions + one model resolves; two models errors; zero
  models prompts (mocked). Cost table shows per-session + grand total + average
  with the estimate/guess labels. Provider actuals summed when present, and
  reported "unavailable" when the API omits `usage`.
- compact grammar: the old two-positional `compact SESSION MODEL` form is
  replaced by one variadic `specs` list; assert `compact SES MODEL` still works
  via resolution (SES resolves to a session, MODEL to a model) and that
  `model:NAME` forces the model. This is a breaking grammar change; call it out
  in docs.
- compact: one session failing mid-batch does not abort the others; summary
  reports it.
- recover/show: iterate over N sessions; per-session output present.
- delete: single preview + one confirm for N sessions; `-y` skips; `--dry-run`
  deletes nothing; project expansion deletes the project's (root) sessions and
  all with `-A`.
- project expansion: a project spec expands; ambiguity uses IPD 02 policy;
  empty project is a clear error.
- backup: per-target bundles written for a session list / project (if kept in
  this IPD).

---

## Docs

- README + help: multi-session usage for compact/recover/show/delete, project
  expansion, `-y/--yes`, and the cost-estimate caveats.
- ARCHITECTURE: note the batch handlers and the `run_compaction` refactor seam.

---

## Non-goals

- Parallel/concurrent execution of the batch (sequential is fine; KISS).
- Cross-session dedup or combined single-file compaction of multiple sessions.
