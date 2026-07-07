# TODO

Informal backlog of ideas not yet promoted to an IPD in `.agents/plans/pending/`.

## `ocman spend` — per-project / per-session spend reporting

Add an `ocman spend` command that shows a table of spend.

- **Per-project spend table** (default view): one row per project with its total spend.
- **Include historically saved spend**: account for spend that would otherwise be lost
  (e.g. sessions/projects already deleted or cleaned) — i.e. reflect cumulative historical
  spend, not just what is currently live in the DB.
- **Per-session detail**: allow drilling into per-session spend (e.g. `ocman spend <project>`
  or a `--sessions` flag).
- **Include/exclude historically saved spend**: a flag to toggle whether the historically
  saved spend is counted in the totals (show live-only vs. live + historical).
- **Avoid double-counting forked data (stretch)**: if a session was forked/branched, its
  shared/ancestor tokens or spend may be counted more than once across the fork tree. If there
  is a reasonable way to attribute shared spend once (dedupe forked/shared data) rather than
  double-count it across parent + children, do that. "Super awesome" but optional — do not block
  the core command on it.

Notes / open design questions (for when this is promoted to an IPD):
- Where does spend data come from — the opencode DB (per-message/model cost), ocman's historical
  activity ledger (`OPENCODE_HISTORY_PATH` / `--show-logs`), or both? Reconcile the two sources.
- What does "historically saved spend" mean precisely — spend on since-deleted sessions recorded
  in the ledger, and/or estimated cost avoided by compaction/cleanup? Clarify before building.
- Cost source of truth: reuse `estimate_cost` / model pricing already in `ocman.py`?
