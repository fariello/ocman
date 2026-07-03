# Lens: Performance

Focus the assessment on runtime and resource performance: speed, throughput,
latency, and efficiency under realistic and peak load.

## Lead personas

Software engineer and architect, with the power-user and stakeholder views on
"is it fast enough for real use and scale?".

## Rubric

- **Hot paths:** identify the most-executed / most-expensive code paths; are they
  efficient? Profile or reason from the code, do not guess.
- **Algorithmic complexity:** quadratic-or-worse loops, repeated work, missing
  memoization/caching, unnecessary recomputation.
- **Data access:** N+1 queries, missing indexes, over-fetching, chatty I/O, lack of
  batching/pagination, sync I/O on hot paths.
- **Allocation & memory pressure:** excessive allocation, copies, large buffers, GC
  churn (coordinate with the memory-resources lens if both apply).
- **Concurrency & parallelism:** serialization bottlenecks, lock contention,
  under-used parallelism, blocking calls.
- **Network & payloads:** payload size, round trips, compression, caching headers,
  connection reuse.
- **Startup / cold start / build time** where relevant.
- **Scaling:** behavior as data/users grow; any hardcoded assumptions that break at
  scale; "architect the seam, provision for today".
- **Measurement:** are there benchmarks/metrics to prove improvement? Propose adding
  them so changes are validatable rather than speculative.

## IPD emphasis

Tie each proposed optimization to evidence (a profile, a complexity argument, a query
plan) and to a measurable validation (a benchmark or metric), so the executed plan
can be proven to help. Avoid speculative micro-optimization (Complexity axis): propose
optimizations where there is evidence of real cost.
