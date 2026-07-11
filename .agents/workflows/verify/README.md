# verify

Proof, not prose: discover the repo's own test/lint/build/type-check commands, run them,
and report honest pass/fail evidence. Run `/verify`, or from any agent: "read and execute
`.agents/workflows/verify/verify.md`".

## Subdirectories

- `tools/` - the deterministic runner `run_checks.py`, which discovers and executes the
  repo's checks and emits structured results.
