# .agents/plans/

Your Implementation Plan Documents (IPDs), organized by lifecycle state. Plan files are
named `YYYYMMDD-HHMM-NN-<slug>.md` (the creating machine's local date and time; `NN` is a two-digit per-minute
sequence, with `00` reserved for an orchestrator plan and `01+` for ordinary/child plans;
`<slug>` is lowercase kebab-case).

The lifecycle:

- **`pending/`** - new or under review/implementation; awaiting approval.
- **`executed/`** - implemented, verified, and tested (terminal; `done/` is an accepted alias).
- **`superseded/`** - replaced by a better/subsequent plan; kept for the record.
- **`not-executed/`** - deliberately decided against, no replacement.
- **`reusable/`** - recurring plans re-run repeatedly (not a terminal state).

**Never file an un-run plan in `executed/`** (that falsely claims it was implemented).
Retire a plan by prepending a `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>`
header and `git mv`ing it to `superseded/` or `not-executed/`. **Never silently delete a
plan** - retiring preserves the record and the reason.

**Private/brain-dir plans MUST be mirrored here.** If an agent keeps a plan/IPD in a
private, hidden, or tool-internal "brain"/memory/scratch dir (e.g. Antigravity/Gemini), it
MUST also keep an exact, conventions-compliant copy under `.agents/plans/` and move THAT copy
through the lifecycle; the tracked copy is the source of truth, the private copy is
disposable. (Also stated in the always-loaded `AGENT-WORKFLOWS` block.)

## Readiness status (front-matter)

The DIRECTORY records a plan's disposition (above); the plan's front-matter `Status:` line
records its READINESS within the lifecycle:

- `draft` - a stub or partial; not ready to review or execute.
- `to-review` - complete enough to critique; ready for `/plan-review` or a human. A
  normally-drafted plan is born here; use `draft` only for an explicit "capture now, finish
  later" stub.
- `reviewed` - `/plan-review` done and revisions applied; awaiting human sign-off.
- `approved` - a human signed off; ready to execute.
- Terminal (`executed` / `superseded` / `not-executed`) mirrors the directory; `reusable` is
  standing.

Each plan also keeps a `## Workflow history` section: an appended, dated line per workflow
that touched it (assess, plan-review, ...), so you can see the path a plan took. The
plan-mutating workflows commit (never push) as they go, so `git log` shows the progression.

## Execution contract in every plan's gate

Every IPD's `Approval and execution gate` MUST carry an execution contract so the plan is
safe to hand to any agent from its path alone:

1. All open questions RESOLVED (or explicitly OPEN, in which case the plan is NO-GO).
2. A SCOPE FENCE naming the exact files/areas to touch, with "do not expand scope; if it
   seems to need more, STOP and report".
3. The HARD MUST honesty rule: when you report tests/validation passed, paste the ACTUAL
   runner output; never claim success you did not run.
4. Commit ONLY the plan's own changed files, path-scoped; never `git add -A`/bare/`-a`;
   never push.
5. The lifecycle move on completion (`git mv` to the terminal directory, set `Status:`,
   append a `## Workflow history` line).

This restates, at the plan level, the standing `AGENT-WORKFLOWS` execution contract (see the
managed block in `AGENTS.md` and `CONTRIBUTING.md`); `/plan-review` and `/plan-review-long`
verify it is present and add it if missing.
