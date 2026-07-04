# Assessment run report - self-documentation (process-lock error)

- Date / run ID: 20260704-175217
- Concern: self-documentation ("errors that teach")
- Scope: NARROWED to the "opencode is running" check that blocks --delete/--delete-project/--clean
- IPD written: .agents/plans/pending/2026-07-04-assess-self-documentation-process-lock.md
- Verdict: **needs work** — the safety check works but its error is uninformative: one generic line
  regardless of how many opencode processes are running, with no detail to identify or manage them.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| SD-1 | Medium | Low | novice / UI-UX | Generic one-line error; no count/PID/CWD/TTY/start info to act on |
| SD-3 | Medium | Low | QA / power user | `pgrep -f` substring match → false positives (matches any command line containing the string) |
| SD-2 | Low | Low | software engineer | Detection copy-pasted across 3 call sites |
| SD-4 | Low | Med-High | power user | Per-process session id not reliably derivable (deferred; show best-effort project instead) |
| SD-5 | Low | Medium | power user | True "last activity" not cheap/reliable (deferred; show start+elapsed instead) |

(Full list incl. SD-6/SD-7 in `findings.csv`.)

## Proposed plan (summary)

1. One `detect_running_opencode()` helper: single `ps` call + `/proc/<pid>/cwd` (Linux), plausible-process
   filter (no bare substring), exclude self, hard timeout, graceful degrade.
2. A `format_running_opencode()` producing a count header + one line per process (PID, TTY, elapsed, started,
   CWD) + an actionable footer (close these, or `--force`).
3. Best-effort CWD→project attribution from the DB (not a session id).
4. Replace the 3 duplicated `pgrep` blocks with the helper, preserving control flow (found+!force→raise;
   force→bypass; none→proceed) and the win32 skip.
5. README + CHANGELOG.

## Deferred (with reason)

- SD-4 per-process **session id**: Remediation Risk Medium-High / functionality — opencode does not expose it
  via a stable process signal; a guessed id on a destructive-op screen would mislead. Best-effort project
  (by CWD) proposed instead.
- SD-5 true **last-activity**: Medium / functionality — fuzzy/platform-specific/not cheap within ~2s. Report
  start time + elapsed (exact, cheap) instead.

## Next step

Review the IPD (optionally run `plan-review`) and approve before execution. This workflow did not execute the
plan and changed no application code.
