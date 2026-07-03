---
description: Assess data-exfiltration resistance (egress paths, leakage, DLP-relevant patterns) and propose an IPD.
agent: build
---

Read and execute @.agents/workflows/assess/assess.md.

Apply the concern lens @.agents/workflows/assess/lenses/data-exfiltration.md on top of that harness: it selects the concern, its lead personas, and its rubric. Assess that single concern deeply and write an IPD into the project's pending-plans directory; do not change code and do not execute the plan.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
