# TODO

Informal backlog of ideas not yet promoted to an IPD in `.agents/plans/pending/`.

## `ocman spend`: SHIPPED (2026-07-15)

Implemented via `.agents/plans/executed/20260715-assess-functionality-ipd.md` Step 8:
`ocman spend` (per-project table by default), `ocman spend <project> --sessions`
(per-session detail), `--historical` (adds the deletion ledger's saved spend as a
single global line; not attributable per project), and `--json`. Cost comes from the
live session `cost` columns plus the ledger `cumulative.cost_deleted`.

Deferred stretch goal (not yet built): forked/shared-spend de-duplication (attribute
shared ancestor tokens once across a fork tree rather than double-counting). Promote to
its own IPD if wanted.
