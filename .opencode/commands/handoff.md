---
description: Session-continuity generator: capture this session's ephemeral context (discussion, decisions and their why, abandoned approaches, tacit preferences) into a resume document so a fresh session resumes with continuity. Session context is the core, the on-disk record a thin frame. Writes a `Kind: session-handoff` draft to the gitignored `.agents/prompts/local/` lane, applies a sensitivity/privacy gate, and never auto-commits (the human promotes). Optional focus argument.
agent: build
---

Read and execute @.agents/workflows/handoff/handoff.md.

If the user provided arguments, treat them as an optional focus for the handoff (an area or thread to emphasize, e.g. `release`); omit to capture the whole session: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
