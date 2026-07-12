# Plan Review Engineering Rubric

Apply only relevant items. `Not applicable` requires a reason.

## A. Plan completeness

Verify:

- problem, driver, goals, non-goals, scope, and exclusions;
- acceptance criteria;
- existing mechanisms to reuse;
- target components when knowable;
- ordered implementation steps and dependencies;
- assumptions and open questions;
- validation commands and expected evidence;
- rollout, rollback, recovery, and follow-up ownership;
- an execution contract in the gate: resolved open questions, a scope fence, the hard-MUST
  honesty rule (paste the actual runner output), path-scoped commit and never-push, and the
  lifecycle move.

The plan must be executable by another qualified agent or developer without
inventing architecture.

## B. Data and integrity

Check:

- transactions and rollback;
- concurrency, uniqueness, ordering, and lost updates;
- idempotency and retry behavior;
- production data-store dialect and parameter safety;
- migrations, indexes, and compatibility;
- audit integrity and provenance;
- retention, deletion, restoration, and archival.

## C. Security, privacy, and abuse resistance

Check:

- verified identity and default-deny authorization;
- route/action, object/row, tenant, and organization scope;
- bypass, impersonation, delegation, and break-glass paths;
- secret handling;
- boundary validation and unknown fields;
- injection and unsafe outbound access;
- upload validation, isolation, and scanning when needed;
- rate, replay, quota, and automation controls;
- privacy minimization and safe errors.

## D. Architecture, scale, and KISS

Check:

- existing canonical mechanisms are reused;
- one implementation exists per business action;
- new models, services, dependencies, abstractions, and execution paths are
  justified;
- async work, caches, partitioning, and scaling seams solve real needs;
- time and state assumptions are testable;
- speculative scale, reuse, and generic metadata systems are avoided.

## E. Invariants and compatibility

Check:

- every affected invariant is named and mapped to a test;
- intended correct behavior is preserved unless deliberately changed;
- accidental behavior is not frozen when project policy says to replace it;
- public API, schema, config, file-format, integration, and migration effects
  are explicit;
- breaking changes are approved, migrated, and documented.

## F. Testing and verification

Require relevant tests for:

- happy paths and validation failures;
- authorization and cross-scope denial;
- constraints, transactions, and rollback;
- retries, idempotency, and concurrency;
- dependency and integration failures;
- accessibility and user recovery;
- contracts, end-to-end behavior, and performance limits.

Use production-equivalent dependencies when differences matter. Keep fixtures
realistic. State exact commands, environments, and expected evidence.

## G. UX and accessibility

Check:

- minimum user effort and no repeated entry;
- clear defaults, terminology, and next steps;
- loading, empty, error, success, and recovery states;
- preserved input after correctable errors;
- contextual help and no silent failure;
- keyboard operation, focus, semantics, names, contrast, and assistive feedback;
- novice, power-user, and stakeholder outcomes.

## H. Operations and documentation

Check:

- structured logs and correlation where relevant;
- metrics, health, readiness, and actionable alerts;
- timeouts, retries, backoff, degraded behavior, and terminal failure paths;
- rollout, rollback, reconciliation, and recovery;
- logs do not expose secrets or unnecessary sensitive data;
- specs, docs, examples, schemas, and release notes remain synchronized.
