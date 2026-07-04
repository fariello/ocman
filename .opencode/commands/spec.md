---
description: Front of funnel: turn a fuzzy request into a reviewable specification (goals, non-goals, users, requirements, testable acceptance criteria, constraints, open questions). Guided/interactive; writes the spec to the repo's convention. Produces the artifact that `/advise spec-editor` interrogates and `plan-review` reviews.
agent: build
---

Read and execute @.agents/workflows/spec/spec.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
