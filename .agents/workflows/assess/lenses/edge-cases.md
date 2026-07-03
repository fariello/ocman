# Lens: Edge cases and failure modes

Focus the assessment on boundary conditions, unusual inputs, and failure modes that
the happy path ignores. Complements use-cases (whole scenarios) and bugs (defects in
existing behavior) by systematically probing the limits.

## Lead personas

QA engineer and software engineer, with the security-minded view on malicious inputs.

## Rubric

- **Input boundaries:** empty, null/None, zero, negative, max/overflow, very large,
  unicode/emoji, whitespace, mixed encodings, malformed, injection-shaped.
- **Collection boundaries:** empty list, single item, huge list, duplicates, ordering
  assumptions, pagination limits.
- **State boundaries:** uninitialized, partially-initialized, already-done, concurrent
  modification, re-entry, resume after interruption (cross-reference reliability).
- **Resource boundaries:** out of memory/disk/handles, timeouts, slow dependencies,
  rate limits, exhausted quotas/budgets.
- **Time & ordering:** clock skew, time zones, DST, leap conditions, events arriving
  out of order, retries causing duplicates (idempotency).
- **External failure:** dependency down/slow/returns garbage; partial responses;
  network partition; truncated reads driving a wrong decision.
- **Error paths:** is every error path actually correct (cleanup, rollback, no double
  response, no orphaned state)? Error paths are the least-tested code.
- **Numeric/precision:** float rounding, division by zero, integer overflow, currency.

## IPD emphasis

For each material edge case, propose either correct handling or an explicit, tested
decision to reject it, plus a regression test that encodes it. Prioritize edge cases
that can corrupt data, crash on a reachable path, or make a wrong automated decision.
Most edge-case hardening is low Remediation Risk; propose by default.
