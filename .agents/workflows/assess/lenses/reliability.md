# Lens: Reliability, resilience, and fault tolerance

Focus the assessment on whether the system keeps working correctly under failure,
load, and adverse conditions - and recovers gracefully when it does not.

## Lead personas

Architect and operator/stakeholder (uptime and trust), with the software engineer on
the failure-handling code paths.

## Rubric

- **Failure handling:** every external call (network, DB, queue, file, subprocess,
  third-party API) can fail - is each failure caught, classified, and handled?
- **Timeouts & retries:** sensible timeouts everywhere; retries with backoff and
  jitter; retries are idempotent; bounded attempts; no retry storms.
- **Degradation:** does the system degrade gracefully (partial functionality) rather
  than failing hard? Fallbacks and circuit breakers where warranted.
- **Recovery & resume:** can interrupted work resume safely without duplicating or
  corrupting completed/verified output (the resume/idempotency data-integrity class)?
  Crash-consistency of persisted state.
- **Resource exhaustion:** behavior under out-of-memory/disk/connections; backpressure;
  bounded queues and buffers (cross-reference memory-resources).
- **Concurrency & coordination:** correct behavior with multiple instances/runs;
  locks/leases; no split-brain; correct stop/signal targeting.
- **Data durability:** acknowledged writes are durable; transactions/atomicity;
  backup/restore where relevant.
- **Dependency health:** single points of failure; health/readiness checks;
  startup/shutdown ordering and graceful shutdown.
- **Idempotency of side effects:** notifications, payments, external mutations are not
  duplicated on retry.

## IPD emphasis

Propose making failure paths first-class and tested (fault injection where feasible).
Prioritize anything that can lose/corrupt data or duplicate a real-world side effect
(money, messages) as Blocker/High. Many reliability fixes (add a timeout, make a retry
idempotent, bound a buffer) are low Remediation Risk; propose by default.
