# TODO

Informal backlog of ideas not yet promoted to an IPD in `.agents/plans/pending/`.

## Chunk large sessions on recover/compact/export

Allow large sessions to be split into chunks so recovery/compaction/export output
(and LLM compaction input) stays manageable. Trigger when a session exceeds a size
threshold, e.g. > 2500 lines OR > 250 interactions (make the thresholds
configurable, not hardcoded). Open questions for when this is promoted to an IPD:
- What exactly is chunked: the recovered/compacted Markdown document, the compaction
  LLM input (to respect context limits), the .ocbox export, or all of them?
- Chunk boundaries: by interaction count, by line count, or by token estimate; never
  split mid-interaction/mid-message.
- Output shape: numbered files (`...part-01of03.md`) with a manifest/index, or a
  single file with clear chunk separators? Reconcile with the existing recovery
  filename convention.
- Reuse the existing counts (`db_get_session_stats`: msgs/interactions/parts) and
  the compaction token/cost estimator for the threshold checks.

## `ocman spend`: SHIPPED (2026-07-15)

Implemented via `.agents/plans/executed/20260715-assess-functionality-ipd.md` Step 8:
`ocman spend` (per-project table by default), `ocman spend <project> --sessions`
(per-session detail), `--historical` (adds the deletion ledger's saved spend as a
single global line; not attributable per project), and `--json`. Cost comes from the
live session `cost` columns plus the ledger `cumulative.cost_deleted`.

Deferred stretch goal (not yet built): forked/shared-spend de-duplication (attribute
shared ancestor tokens once across a fork tree rather than double-counting). Promote to
its own IPD if wanted.
