# .agents/plans/

Your Implementation Plan Documents (IPDs), organized by lifecycle state. Plan files are
named `YYYYMMDD-HHMM-NN-<slug>.md` (UTC date and time; `NN` is a two-digit per-minute
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
