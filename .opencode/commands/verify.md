---
description: Proof, not prose: discover the repo's own test/lint/build/type-check commands (`run_checks.py`), run the approved ones (confirm-per-check by default, `--yes` for batch; hard denylist for network/deploy/publish/install), and capture real exit codes/metrics/logs as committed evidence. Honest about what could not be verified. Reused by release-review and assess.
agent: build
---

Read and execute @.agents/workflows/verify/verify.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
