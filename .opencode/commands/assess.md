---
description: Assess ONE concern deeply and propose an IPD. `/assess <concern> [scope]` (e.g. `/assess security`, `/assess prose src/`); bare `/assess` lists concerns and asks. The `assess-<concern>` rows below are the concern catalog (they define the lenses), not separate commands.
agent: build
---

Read and execute @.agents/workflows/assess/assess.md.

The first argument names the CONCERN to assess (e.g. `security`, `prose`, `compliance-readiness`); any further arguments narrow the scope (a path/module) or carry options. Resolve the concern to its lens `.agents/workflows/assess/lenses/<concern>.md` and apply it on top of the harness (assess that single concern deeply and write an IPD; do not change code or execute the plan). Accept case-insensitive aliases and common short forms (e.g. `a11y` -> accessibility, `perf` -> performance, `deps`/`supply` -> supply-chain); on an unknown concern, show the closest matches. If NO concern was given, list the available concerns (the `assess/lenses/*.md` files) and ask the user which to run.

If the user provided arguments, treat them as the concern to assess plus an optional scope, e.g. `security` or `prose src/`; bare invocation lists the concerns and asks: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
