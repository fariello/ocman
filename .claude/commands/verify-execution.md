---
description: Post-execution cross-check: verify an EXECUTED plan (IPD) was actually done as written (read the diff, check each required change, re-run the repo's real validation via /verify), always write a run record, and EMIT a corrective IPD for any gap (never fixes in place; commits only its own files path-scoped, safe to run while another agent works). Verdict MATCHES/DIVERGES/INCOMPLETE + GO/NO-GO on "truly executed?". Used to cross-check another agent's or a past session's work.
argument-hint: "[optional target path or flags]"
---

Read and execute @.agents/workflows/verify-execution/verify-execution.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
