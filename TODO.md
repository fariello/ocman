# TODO

Informal backlog of ideas not yet promoted to an IPD in `.agents/plans/pending/`.

## Chunk large sessions on recover/compact: SHIPPED (2026-07-17)

Implemented via `.agents/plans/executed/20260717-chunk-large-sessions-ipd.md`:
`--chunk` on `session recover` and `session compact` splits a large session into
ordered, self-contained `YYYYMMDD-HHMM-<sid>.part-NNofMM.<kind>.md` files instead of
truncating (nothing dropped). Boundaries are whole interactions (never mid-turn);
`--max-lines`/`--max-interactions` set the per-part size, with defaults from the new
`chunk_max_lines` / `chunk_max_interactions` config keys. The interactive large-
session prompt gained a `[c]hunk` choice. `compact --chunk` sends each part to the LLM
separately (so each fits the context window) and sums the per-part cost table.

Resolved-differently vs the original idea: the ".ocbox export" was deliberately left
OUT of scope (a bundle is DB rows for wholesale import, not readable/LLM text, and
already streams; chunking it adds partial-bundle integrity cost for no use case). The
"is-large" TRIGGER stays the fixed 2500 lines / 100 interactions constants (the
original note's ">250 interactions" did not match the real 100); the two new config
keys size the PARTS, not the trigger.

## `ocman spend`: SHIPPED (2026-07-15)

Implemented via `.agents/plans/executed/20260715-assess-functionality-ipd.md` Step 8:
`ocman spend` (per-project table by default), `ocman spend <project> --sessions`
(per-session detail), `--historical` (adds the deletion ledger's saved spend as a
single global line; not attributable per project), and `--json`. Cost comes from the
live session `cost` columns plus the ledger `cumulative.cost_deleted`.

Deferred stretch goal (not yet built): forked/shared-spend de-duplication (attribute
shared ancestor tokens once across a fork tree rather than double-counting). Promote to
its own IPD if wanted.
