---
description: Toolkit discovery: list what this toolkit can do (core workflows, the `/assess` concerns, any personas) and the installed framework version, read from the manifest. Optional filter argument (`/list-workflows security`, `/list-workflows assess`). Read-only.
agent: build
---

Read and execute @.agents/workflows/list-workflows/list-workflows.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
