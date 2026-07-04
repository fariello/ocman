---
description: Interrogate and coach: an expert persona examines the current context or a named artifact (spec/plan/design/decision), asks probing questions, surfaces gaps and assumptions, and coaches the author. `/advise <persona> [artifact]` (e.g. `/advise skeptic`, `/advise spec-editor plan.md`); bare `/advise` lists personas and asks. Interactive; edits planning/prose only with per-change consent; never runs code. The `advise-<persona>` rows below are the persona catalog, not separate commands.
agent: build
---

Read and execute @.agents/workflows/advise/advise.md.

The first argument names the expert PERSONA (e.g. `skeptic`, `spec-editor`, `architect`, `red-teamer`, `staff-engineer`, `domain-expert`, `naive-user`); any further arguments name the artifact to examine (a spec, plan, design, or decision doc) - otherwise the persona examines the current context. Resolve the persona to its charter `.agents/workflows/advise/personas/<persona>.md` and adopt it: conduct a genuine question-driven session, surface gaps and assumptions, and coach the author. It may edit a planning/prose artifact only with per-change consent; it never executes code. Accept case-insensitive aliases (e.g. `skeptic`/`grill`/`grill-me` -> skeptic, `mentor` -> staff-engineer, `red-team`/`adversary` -> red-teamer, `naive`/`novice` -> naive-user); on an unknown persona, show the closest matches. If NO persona was given, list the available personas (the `advise/personas/*.md` files) and ask the user which to use.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
