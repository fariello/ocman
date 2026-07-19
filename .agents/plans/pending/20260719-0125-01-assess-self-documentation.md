# IPD: Assess self-documentation - make the product teach the user in place

- Date: 2026-07-19
- Concern: self-documentation (learn-as-you-go, in-product clarity)
- Scope: whole product's in-product self-documentation: the CLI (`ocman/cli.py`: help
  system, error messages, flag/command naming, first-run) and the TUI (`ocman_tui/`:
  labels, hints). Repo docs (README/ARCHITECTURE) are out of scope (that is the
  `documentation` lens, already assessed separately).
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-19 /assess self-documentation (its_direct/pt3-claude-opus-4.8): assessed the CLI
  and TUI for learn-as-you-go clarity; proposed 8 changes.
- 2026-07-19 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED.
  PR-001 ("Database not found" is at 7+ sites, not 2 -> fix all via a shared message/helper),
  PR-002 (pin the SD-02 catch-all to the outer try at cli.py:15779/16309, use the in-scope
  `verbosity`, no double "Error:" prefix), PR-003 (add concrete automated tests, not just
  manual checks), PR-004 (SD-05: range OR token-set, do not fabricate a range). OQ-1 (reclaim
  in help maintain + overview pointer) and OQ-2 (clean message default, traceback under -v)
  resolved by the maintainer. GO - PENDING HUMAN APPROVAL.

## Goal

Ensure a naive user can learn ocman WHILE USING IT, without external docs: names reveal
intent, help is discoverable and accurate, errors teach recovery (and show valid input),
and no raw stack trace leaks. ocman is already strong here (curated three-tier help,
`doctor`'s "Suggested order", a "Next steps" no-args screen, TUI empty states +
worked-example placeholders + typed-"yes" DANGER ZONE confirmations). This plan fixes the
specific places where the product still makes the user guess, look up, or hit a dead end.

## Project conventions discovered (Step 0)

- Guiding principles: AGENTS.md + universal fallback (intuitive/self-documenting,
  general-case/configurable, KISS, honest docs). Prose rule: NO em/en dashes in authored
  text (the em-dash "not available" table glyph is the only sanctioned exception).
- Plans: `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`; front-matter
  Status draft -> to-review -> reviewed -> approved -> executed.
- Contributor contract: AGENTS.md (path-scoped commits, never push, paste REAL pytest
  output). This plan touches `ocman/cli.py` (and possibly `ocman_tui/`), so executed changes
  MUST run the suite and paste the real output.
- Stack: `ocman/cli.py` CLI + `ocman_tui/` Textual TUI. Error seam: `die(message, exit_code)`
  (`cli.py:1198`) and `RecoveryError` (`cli.py:1084`). Duration parser
  `parse_duration_to_days` raises `DurationError` (`cli.py:4941`). Top-level `main()` catch
  handles only `KeyboardInterrupt` + `RecoveryError` (`cli.py:16309-16313`).

## Findings

Severity = user impact if left alone; Remediation Risk = the Fix-Bar gate. Persona:
NOV = complete novice (lead), UX = UI/UX engineer, PU = power user. Tag from the evidence
pass: GOOD (kept, not a finding), WEAK, GAP.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| SD-01 | High | Low | NOV | errors/accuracy | Two user-facing error strings advertise flags that DO NOT EXIST on the current CLI: `"Use --show-models to see available models."` and `"Use --list-projects to see available projects."` The current commands are `ocman models` and `ocman list projects`; following the error's advice fails. An error that teaches a dead end is worse than a vague one. | `cli.py:828`, `cli.py:7525` (flags not registered; real verbs at `cli.py:6435`, `list projects`) |
| SD-02 | Medium | Medium | NOV/PU | errors/GAP (traceback leak) | `main()`'s top-level catch handles only `KeyboardInterrupt` and `RecoveryError`; any other exception surfaces as a raw Python traceback to the user. The lens treats a leaked stack trace as a self-doc failure. | `cli.py:16309-16313` |
| SD-03 | Medium | Low | NOV | errors/examples-at-point-of-use | The duration parse error omits the accepted formats that the `--older-than` help already lists. `DurationError` messages ("could not parse duration: ...", "unknown time unit: ...") and the `_die_cli("invalid --older-than value: ...")` wrapper do not show `2h/5d/6w/6mo/1y/"30 days"` at the moment of failure. | `cli.py:4935,4939,4941`, `cli.py:6558`; help has it at `cli.py:6150` |
| SD-04 | Low | Low | NOV | errors/recovery | "Database not found at {path}" gives no next step (how to point at a DB or create one). | `cli.py:8064`, `cli.py:8612` |
| SD-05 | Low | Low | NOV | errors/recovery | Bare "Invalid selection"/"Invalid choice" messages do not state the valid range. | `cli.py:5320`, `cli.py:7406`, `cli.py:9283` |
| SD-06 | Low | Low | NOV | errors/recovery | "Session {id} not found in database." offers no "run `ocman list sessions`" hint. | `cli.py:8087` |
| SD-07 | Low | Low | NOV/PU | discoverability | `reclaim` is absent from `ocman help` overview AND every `help TOPIC`; it appears only in `ocman help all` and operationally in `doctor` output. A user browsing the overview or topics never learns it exists as a command. (Intentional today, but a real discoverability gap for a headline capability.) | `build_help` `cli.py:5504+` (no reclaim row), `help all` `cli.py:5671-5679` |
| SD-08 | Low | Low | NOV/UX | TUI naming | Two Storage-tab reclaim buttons rely on the confirm-modal preview to be understood: `"Reclaim compacted parts"` and `"Checkpoint + VACUUM"` are jargon on the button face. | `ocman_tui/widgets/storage.py:91,93` (explained only at `:231,:249`) |

Deliberately NOT findings (verified GOOD, keep as-is): the centralized `die`/`RecoveryError`
seam; errors that name the exact recovery flag (`--while-running`, `--force`,
`filter_max_bytes`); config-not-found listing searched paths; ambiguous-model enumeration;
the three-tier curated help with per-command `-h`; `doctor`'s numbered "Suggested order" and
reclaim buckets; the no-args "Next steps" screen; TUI empty states, worked-example
placeholders, DANGER ZONE + typed-"yes" confirmations, read-only/observe-only tab labels, and
the running-tab fail-loud "NOT an all-clear". Jargon verbs (`filter`, `rebase`) and terse
recovery short flags (`-mi/-ml/-ic`) are left as-is: renaming a shipped, documented CLI
surface is a compatibility change (Medium-High on the compatibility axis) that outweighs the
self-doc gain, and each already carries a clear `help=` string.

## Proposed changes (ordered, validatable)

Ordered accuracy-first (highest harm: a dead-end error), then the traceback guard, then the
teaching-error and discoverability polish.

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | SD-01 | Fix the two stale-flag error strings to name the real commands: `"Use 'ocman models' to see available models."` (`cli.py:828`) and `"Use 'ocman list projects' to see available projects."` (`cli.py:7525`). Grep the whole file for any other `--show-models` / `--list-projects` in user-facing strings and fix those too. | `ocman/cli.py` | Low | grep shows no user-facing `--show-models`/`--list-projects` remain; the two messages name commands that actually run. |
| 2 | SD-02 | Add a top-level catch-all as the LAST handler on the outer `try:` in `main()` (the try opens at `cli.py:15779`; handlers are `except KeyboardInterrupt` `:16309` then `except RecoveryError` `:16312`). Add `except Exception as e:` AFTER the RecoveryError handler: if `verbosity` (the local at `cli.py:14805`, in scope in the handler) is truthy, `raise` (keep the full traceback for debugging); else `die(f"Unexpected error: {e}. Re-run with -v for the full traceback.")`. NOTE: `die` already prefixes `"Error: "` (`cli.py:1198`), so do NOT add another prefix. This must be the LAST except so it never shadows the KeyboardInterrupt/RecoveryError handling. | `ocman/cli.py` | Medium | A forced unexpected exception on the normal path prints a clean one-line `Error: Unexpected error: ...` with the `-v` hint and NO "Traceback" text on stderr; with `-v` the traceback still shows; KeyboardInterrupt (exit 130) and RecoveryError paths unchanged. |
| 3 | SD-03 | Make the duration failure teach the valid formats at the point of use: include `"(accepted: 2h, 5d, 6w, 6mo, 1y, or '30 days')"` in the `DurationError` surfaced to the user (either in the messages at `cli.py:4935/4939/4941` or in the `_die_cli` wrapper at `cli.py:6558`; prefer the wrapper so the CLI-facing message is consistent). | `ocman/cli.py` | Low | `ocman db clean --older-than blah` prints an error that includes the accepted-format example. |
| 4 | SD-04, SD-06 | Add a recovery hint to the "not found" errors. NOTE (PR-001): `"Database not found at {path}"` appears at SEVEN+ sites (`cli.py:8064, 8612, 8793, 9763, 9810, 9859, 10848`), not two. Fix ALL of them consistently: EITHER route them through a single shared message/helper (preferred, e.g. a `_db_not_found_error()` returning the RecoveryError, so the wording lives in one place) OR grep-drive an identical edit to every occurrence. Append `"Point at a database with --db PATH, or run OpenCode first to create one."`. Also `"Session {id} not found in database."` (`cli.py:8087`) -> add `"Run 'ocman list sessions' to see available sessions."`; and `"Project with ID {id} not found in database."` (`cli.py:8808`) -> add `"Run 'ocman list projects' to see available projects."` | `ocman/cli.py` | Low | grep confirms EVERY "Database not found" occurrence carries the hint (no bare one remains); the session/project not-found messages end with an actionable next step. |
| 5 | SD-05 | Give the bare "Invalid selection/choice" prompts a valid-range or valid-set hint. Where a numeric range is known at the call site (`cli.py:5320, 9283`), show it (e.g. `"Invalid selection: {choice} (enter a number 1-{n})"`); where the accepted options are a fixed token set rather than a range (`cli.py:7406` "Invalid choice."), show the accepted tokens instead. Do not fabricate a range that is not known at the site. | `ocman/cli.py` | Low | each interactive-selection error names the accepted range OR the accepted token set. |
| 6 | SD-07 | Improve `reclaim` discoverability WITHOUT crowding the overview: add `reclaim` to the `maintain` help TOPIC (it is a maintenance capability), and add a one-line pointer in the overview's maintain group (e.g. under `doctor`) like `"reclaim   reclaim disk (see 'ocman help maintain')"`. Do not dump all reclaim flags into the overview. | `ocman/cli.py` (`build_help` / the maintain topic) | Low | `ocman help maintain` shows `reclaim`; the overview points to it; `help all` unchanged. |
| 7 | SD-08 | Make the two TUI reclaim button faces self-explaining: `"Checkpoint + VACUUM"` -> `"Compact database (checkpoint + VACUUM)"`; `"Reclaim compacted parts"` -> `"Reclaim compacted tool output (parts)"`. Keep the confirm-modal preview as the detailed explanation. | `ocman_tui/widgets/storage.py` | Low | button labels convey intent without opening the modal; storage tests still pass. |

## Deferred / out of scope (with named axis)

| Finding | Remediation Risk | Axis | Reason | Recommended later step |
|---------|------------------|------|--------|------------------------|
| Rename jargon verbs/flags (`filter`, `rebase`, `-mi/-ml/-ic`, `.ocbox`, "subagent") | Medium-High | Compatibility | Renaming a shipped, documented CLI surface breaks users' muscle memory and scripts; each already has a clear `help=` string, so the self-doc gain is small vs. the compat cost. | If ever renamed, do it with deprecated aliases in a dedicated compatibility IPD. |
| Chain the no-args screen to `doctor`/`config create` | Low | (proposed-adjacent) | Reasonable, but the no-args screen is already a strong "Next steps" surface; adding a `doctor`/`config` pointer is a nice-to-have. Folded into SD scope only if trivial during Step 6; otherwise a small follow-up. | Optional one-line addition to `print_no_project_context_help`. |

## Scope check

- Over-scope: none. Every proposed change is an in-product wording/guard fix; no new
  subsystems, no renames of shipped surfaces (guarded above).
- Under-scope: the traceback guard (SD-02) is the one non-wording fix; it is included
  because a leaked stack trace is squarely a self-documentation failure per the lens.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE THE ACTUAL runner output.
- Concrete automated tests to ADD (PR-003), not just manual checks:
  - SD-01: a test asserting no user-facing `--show-models` / `--list-projects` string remains
    in `ocman/cli.py` (grep-style assertion over the source, or assert the two specific error
    strings now contain `ocman models` / `ocman list projects`).
  - SD-02: drive `main()` (or the outer handler) with a forced non-RecoveryError exception and
    assert stderr contains `Error: Unexpected error:` and NOT `Traceback` when `-v` is absent;
    and that `-v` propagates the exception (traceback shown / re-raised). Use the existing
    argv-monkeypatch + capsys pattern used by other `main()` tests.
  - SD-03: assert the CLI duration-failure path (`db clean --older-than nope`, or `_die_cli`)
    output contains the accepted-format example (e.g. `6mo`).
  - SD-04/06: assert a representative "Database not found" and "Session not found" message now
    contains its recovery hint.
- Manual checks: `ocman help maintain` lists `reclaim`; the TUI storage buttons read clearly
  (existing storage tests stay green). No em/en dashes introduced.

## Spec / documentation sync

In-product text only; no README/ARCHITECTURE change required (those were synced separately).
A short CHANGELOG "Fixed"/"Changed" note for the stale-flag errors and the traceback guard.

## Open questions

- OQ-1 (SD-07): RESOLVED (maintainer 2026-07-19) - add `reclaim` to the `help maintain`
  topic AND a one-line pointer in the overview's maintain group (Step 6 reflects this; the
  overview pointer is now required, not optional).
- OQ-2 (SD-02): RESOLVED (maintainer 2026-07-19) - clean message by default, full traceback
  only under `-v` (Step 2 reflects this).

No open questions remain.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution and is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it; sets `Status: reviewed`).
2. Execution checklist (MUST): before coding, create a TodoWrite checklist with one item per
   Step above, plus the full-suite run with pasted output, the CHANGELOG note, the
   path-scoped commit, and the Status-executed + `git mv` to `executed/`.
3. On approval, set `Status: approved`, apply the ordered changes, run the validation, and
   confirm no em/en dashes were introduced.
4. Commit path-scoped; NEVER push. Then set `Status: executed` and `git mv` this IPD from
   `pending/` to `executed/` (verify no pending/executed duplicate).
