# IPD: Assess self-documentation - make the product teach the user in place

- Date: 2026-07-19
- Concern: self-documentation (learn-as-you-go, in-product clarity)
- Scope: whole product's in-product self-documentation: the CLI (`ocman/cli.py`: help
  system, error messages, flag/command naming, first-run) and the TUI (`ocman_tui/`:
  labels, hints). Repo docs (README/ARCHITECTURE) are out of scope (that is the
  `documentation` lens, already assessed separately).
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-19 /assess self-documentation (its_direct/pt3-claude-opus-4.8): assessed the CLI
  and TUI for learn-as-you-go clarity; proposed 8 changes.

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
| 2 | SD-02 | Add a top-level catch-all in `main()` after the `RecoveryError` handler: `except Exception as e:` -> if verbose (`args.verbose`/global) is set, re-raise (keep the traceback for debugging); otherwise `die(f"Unexpected error: {e}\n(run with -v for details)")`. Never leak a bare traceback on the normal path; never swallow the info a developer needs. | `ocman/cli.py` | Medium | A forced unexpected exception on the normal path prints a clean one-line error + the `-v` hint (no traceback); with `-v` the traceback still shows. Existing error paths unchanged. |
| 3 | SD-03 | Make the duration failure teach the valid formats at the point of use: include `"(accepted: 2h, 5d, 6w, 6mo, 1y, or '30 days')"` in the `DurationError` surfaced to the user (either in the messages at `cli.py:4935/4939/4941` or in the `_die_cli` wrapper at `cli.py:6558`; prefer the wrapper so the CLI-facing message is consistent). | `ocman/cli.py` | Low | `ocman db clean --older-than blah` prints an error that includes the accepted-format example. |
| 4 | SD-04, SD-06 | Add a recovery hint to two common "not found" errors: `"Database not found at {path}"` -> add `"Point at a different database with --db PATH, or run OpenCode first to create one."`; `"Session {id} not found in database."` -> add `"Run 'ocman list sessions' to see available sessions."` | `ocman/cli.py` | Low | both messages now end with an actionable next step. |
| 5 | SD-05 | Give the bare "Invalid selection/choice" prompts a valid-range hint (e.g. `"Invalid selection: {choice} (enter a number 1-{n})"`), where the range is known at the call site. | `ocman/cli.py` | Low | each interactive-selection error names the accepted range. |
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
- Targeted checks: `ocman db clean --older-than nope` shows the accepted formats;
  a model-not-found and project-not-found error name real commands; a forced unexpected
  exception yields a clean message (no traceback) without `-v` and a traceback with `-v`;
  `ocman help maintain` lists `reclaim`; the TUI storage buttons read clearly (storage tests
  green).
- Add/extend unit tests where a helper is touched (e.g. the duration error text; the stale
  strings). No em/en dashes introduced.

## Spec / documentation sync

In-product text only; no README/ARCHITECTURE change required (those were synced separately).
A short CHANGELOG "Fixed"/"Changed" note for the stale-flag errors and the traceback guard.

## Open questions

- OQ-1 (SD-07): is keeping `reclaim` out of the plain overview intentional enough that you
  want ONLY the `help maintain` addition (not the overview pointer)? Leaning: add it to
  `help maintain` at minimum; the overview pointer is optional.
- OQ-2 (SD-02): on an unexpected exception, prefer `die(...)` with a `-v` hint (proposed), or
  always show the traceback? Leaning: clean message by default, traceback under `-v`.

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
