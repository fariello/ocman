---
description: Guided, idempotent, drift-aware repo setup AND conformance check: detect state, classify each area (conformant/partial/missing/outdated), then ask-before-each-change to install tools and add secret-scanning, the plan/IPD lifecycle (dirs + documented contract), .gitignore/CI/pre-commit/hygiene files. Safe to re-run after updates; stages changes.
agent: build
---

Read and execute @.agents/workflows/setup-repo/setup-repo.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
