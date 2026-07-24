---
description: Toolkit discovery: list what this toolkit can do (core workflows, the `/assess` concerns, any personas) and the installed framework version, read from the manifest. Optional filter argument (`/list-workflows security`, `/list-workflows assess`). Read-only.
agent: build
---

Read and execute @.agents/workflows/list-workflows/list-workflows.md.

If the user provided arguments, treat them as an optional filter to narrow the catalog (a concern, area, or category, e.g. `security` or `assess`); omit to list everything: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
