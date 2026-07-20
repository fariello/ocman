# Section 4 - Docs, Specs, Examples (per-phase report)

## What I did

- Verified the CHANGELOG `[1.2.0]` section documents the delta honestly: it includes the
  macOS firmlink import-rebase fix and the `vistab>=1.3.0` floor, both in plain language with
  the "why". `[Unreleased]` is correctly empty (the delta is part of the pending 1.2.0).
- Confirmed DECISIONS.md carries dated entries for every delta decision (vistab floor, 3-OS
  support, cross-platform test helpers, the fail-fast diagnostic WITH its explicit restore
  follow-up, the symlink-test approach, and DECISIONS.md adoption). This is the durable
  cold-start knowledge the runbook wants; it was created/backfilled this cycle.
- Ran an em/en dash scan across README, ARCHITECTURE, DECISIONS, CHANGELOG, TODO, AGENTS
  (the project's no-dash prose convention). Only two matches, both sanctioned exceptions: the
  verbatim NOTICE-style attribution line in CHANGELOG, and AGENTS.md's own sentence describing
  the rule.
- Filed S4-D1 (docs honest, completed) and S4-D2 (changelog release date slightly stale).

## Why

- The runbook's honest-documentation and cold-start-knowledge goals are central. For a delta
  re-review, the check is that the docs describe what the code now does and that the "why" of
  the cross-platform work is captured for future maintainers. It is.

## Findings

- S4-D1 (D, Low/Low, completed): docs honestly reflect the delta; dash convention respected.
- S4-D2 (D, Low/Low, identified): `[1.2.0] - 2026-07-19` predates the finalized release; the
  date should match the actual tag date. Fix at tag time (Section 9) or in Section 7.

## What I considered but did NOT do

- **Rewriting README/ARCHITECTURE for the delta:** not needed. The delta changed internal path
  logic, not any user-facing command/flag/help text, so there is no user-doc drift to correct.
- **Editing the workflow-artifacts historical decisions.md notes** that say "no DECISIONS.md":
  out of scope (run records, append-only) and already reconciled by the DECISIONS.md adoption
  entry.
