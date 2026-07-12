# plan-review-long

The multi-file ("long") variant of `plan-review`: the same pre-execution plan reviewer, split
into a small orchestrator plus one file per phase (discover/snapshot, review/revise,
resolve/finalize) with a shared rubric and report template. The orchestrator loads one step at a
time to reduce directive drift on long runs. Kept in deliberate parity with the single-file
`../plan-review/plan-review.md`.

Run `/plan-review-long [path]`, or from any agent: "read and execute
`.agents/workflows/plan-review-long/plan-review-long.md`" (it will read its own step files in
order).
