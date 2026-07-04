---
description: Release discipline: decide the version bump from the actual changes, draft the changelog and human release notes (prose-style guide; breaking changes prominent), and update CHANGELOG/version files with confirmation. Never publishes, tags, pushes, or deploys. Distinct from release-review Section 9 (which executes a release).
argument-hint: "[optional target path or flags]"
---

Read and execute @.agents/workflows/release-notes/release-notes.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
