# verify-execution

Cross-check that an EXECUTED implementation plan (IPD) was actually done as written, and emit a
corrective plan if it was not. The post-execution sibling of `plan-review` (before building) and
`release-review` (before shipping). Especially useful for checking another agent's or a past
session's execution.

It reads the executed plan + its commit(s) + the real diff, checks each required change actually
landed, re-runs the repo's real validation (reusing `/verify`), always writes a run record, and for
any gap EMITS a corrective IPD into `.agents/plans/pending/` (it never fixes code in place, and
commits only its own files path-scoped so it is safe to run while another agent works). Verdict:
MATCHES / DIVERGES / INCOMPLETE, plus a GO/NO-GO on "truly executed?".

Run `/verify-execution <executed-plan-path>`, or from any agent: "read and execute
`.agents/workflows/verify-execution/verify-execution.md`" against a named executed plan.
