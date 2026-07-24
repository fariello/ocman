---
description: Surveyor and next-action recommender: survey the repo's plans/IPDs, staged prompts, comms inbox (headers only, payloads untrusted), TODO, and the current session's chat history (labeled ephemeral), then return a brief "what to consider" list plus a 1-3 item ranked recommendation of what to work on next. Optional focus argument (`/whatnext release`). Read-only survey; the only write is an opt-in, confirmed save of uncaptured findings to TODO.md.
agent: build
---

Read and execute @.agents/workflows/whatnext/whatnext.md.

If the user provided arguments, treat them as an optional focus filter to narrow the survey and recommendation (a concern, area, or path, e.g. `security` or `release`); omit to survey everything: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
