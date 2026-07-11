# benchmark

Guided performance benchmarking (informational, not a regression gate): author an ISOLATED
benchmark, capture the environment, and report results honestly. Run `/benchmark`, or from
any agent: "read and execute `.agents/workflows/benchmark/benchmark.md`".

## Subdirectories

- `tools/` - deterministic helpers (e.g. `bench_env.py`, which captures host/environment
  details for a reproducible benchmark record).
