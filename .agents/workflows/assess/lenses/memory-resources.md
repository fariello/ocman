# Lens: Memory, resources, and lifetimes

Focus the assessment on memory and resource correctness: leaks, unbounded growth,
lifetime hazards, and concurrency/state safety. This is the deep `MEM` pass from
`../release-review/00-run-protocol.md` as a standalone assessment. High value for
long-running services, native code, and data-heavy or concurrent systems.

## Lead personas

Software engineer (primary), with the architect on resource-lifecycle design and the
operator on long-running/production behavior.

## Rubric

- **Leaks & unbounded growth:** caches/maps/lists/queues/log or history buffers that
  never evict or cap; accumulation across a long-running process or a loop; growth
  proportional to total work rather than working set.
- **Unclosed/unreleased resources:** files, sockets, handles, DB connections/cursors,
  locks, temp files, subprocesses, watchers/listeners - including on error/exception
  paths. Connection-pool exhaustion.
- **Lifetime hazards:** use-after-free/close, double-free/close, dangling references,
  retaining large objects/buffers longer than needed, references that defeat GC,
  reference cycles where they matter.
- **Concurrency/state safety:** data races, missing synchronization, TOCTOU,
  non-idempotent retries, shared mutable state without protection, deadlock/livelock
  risk.
- **Bounded resource use:** backpressure; bounded queues/buffers; streaming vs.
  loading everything into memory; recursion depth bounds; large-input handling.
- **Cleanup discipline:** does cleanup run on every path (success, error, cancel,
  shutdown)? RAII/`defer`/`finally`/context-manager usage matches the language.
- **Resource accounting under load:** behavior as inputs/users grow; what happens at
  the limit (graceful vs. crash - cross-reference reliability).

## How to verify

Apply to whatever the language exposes (manual memory, GC retention, RAII/ownership,
context managers, `defer`/`finally`, pools). Read the actual lifecycle code; where
feasible, propose a leak/growth test (e.g. run-and-measure, valgrind/heap snapshot,
soak test) so the fix is provable.

## IPD emphasis

A confirmed leak or unbounded-growth path affecting long-running/production use is at
least Medium and often High (it can exhaust memory/handles and destabilize a live
system). Most fixes (evict/cap a cache, close in a `finally`, bound a buffer) are low
Remediation Risk; propose by default with a test that demonstrates the bound.
