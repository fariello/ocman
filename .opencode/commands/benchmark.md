---
description: Guided performance benchmarking (informational, not a regression gate): author an ISOLATED benchmarks/ suite in the target repo (inert when unused), deeply capture and diagnose the machine/environment (`bench_env.py`: CPU/RAM/GPU/load/filesystem, flags NFS working sets, powersave governor, swapping, busy/login-node with suggested remedies), run with warm-up and >=2 iterations, detect HPC schedulers and (on explicit per-submission consent) generate + submit a job script, and produce a shareable, anonymizable results bundle. Read-only on system state; never publishes.
agent: build
---

Read and execute @.agents/workflows/benchmark/benchmark.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
