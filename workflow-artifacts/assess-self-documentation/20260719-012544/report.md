# Assessment - self-documentation (whole product: CLI + TUI)

Verdict: adequate (trending strong) for self-documentation.

ocman is already strong on learn-as-you-go: a curated three-tier help system
(`help` / `help TOPIC` / `help all`, plus per-command `-h`), `doctor`'s numbered
"Suggested order" and reclaim buckets, a no-args "Next steps" onboarding screen, and a
TUI full of empty states, worked-example placeholders, read-only/observe-only tab labels,
a DANGER ZONE with typed-"yes" confirmations, and a fail-loud running view. The gaps are
specific and low-risk: two errors advertise removed flags (a dead end), an unexpected
exception can leak a raw traceback, some errors do not show valid input at the point of
failure, and a couple of names lean on jargon.

IPD written: .agents/plans/pending/20260719-0125-01-assess-self-documentation.md

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| SD-01 | High | Low | NOV | Error strings advertise flags that no longer exist: "Use --show-models" (cli.py:828) and "Use --list-projects" (cli.py:7525); the real commands are `ocman models` / `ocman list projects`. Teaches a dead end. |
| SD-02 | Medium | Medium | NOV/PU | main()'s top-level catch handles only KeyboardInterrupt + RecoveryError (cli.py:16309-16313); any other exception leaks a raw traceback. |
| SD-03 | Medium | Low | NOV | Duration parse error omits the accepted formats the --older-than help already lists (cli.py:4941, 6558 vs 6150). |
| SD-04 | Low | Low | NOV | "Database not found at {path}" gives no next step (cli.py:8064, 8612). |
| SD-05 | Low | Low | NOV | Bare "Invalid selection"/"Invalid choice" with no valid range (cli.py:5320, 7406, 9283). |
| SD-06 | Low | Low | NOV | "Session {id} not found" offers no "list sessions" hint (cli.py:8087). |
| SD-07 | Low | Low | NOV/PU | `reclaim` is absent from the overview and all help TOPICs; only in `help all` / doctor output. |
| SD-08 | Low | Low | NOV/UX | TUI Storage buttons "Checkpoint + VACUUM" / "Reclaim compacted parts" are jargon on the button face (storage.py:91,93). |

## Proposed plan (summary)

1. Fix the two stale-flag error strings to name the real commands (SD-01).
2. Add a top-level catch-all in main() that prints a clean message by default and shows the
   traceback under -v (SD-02).
3. Make the duration failure teach the accepted formats at the point of use (SD-03).
4. Add recovery hints to "Database not found" and "Session not found" (SD-04, SD-06).
5. Give bare "Invalid selection/choice" prompts a valid-range hint (SD-05).
6. Improve `reclaim` discoverability via the `help maintain` topic (+ optional overview
   pointer) without crowding the overview (SD-07).
7. Make the two TUI reclaim button faces self-explaining (SD-08).

## Deferred (with reason)

- Renaming jargon verbs/flags (`filter`, `rebase`, `-mi/-ml/-ic`, `.ocbox`, "subagent"):
  Remediation Risk Medium-High on the compatibility axis (renaming a shipped, documented CLI
  surface breaks muscle memory/scripts); each already carries a clear `help=` string, so the
  self-doc gain does not justify the compat cost. Do only with deprecated aliases in a
  dedicated compatibility IPD if ever pursued.

Next step: review the IPD (optionally run plan-review on it) and approve before execution.
This workflow does not execute the plan.
