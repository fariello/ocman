---
description: Assess-and-plan a high-risk migration (framework/DB/dependency-major/layout): inventory the blast radius, name the invariants that must survive, and propose a staged, reversible plan with characterization tests first and per-stage rollback + verify checks. Emits an IPD; does not execute.
agent: build
---

Read and execute @.agents/workflows/migrate/migrate.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
