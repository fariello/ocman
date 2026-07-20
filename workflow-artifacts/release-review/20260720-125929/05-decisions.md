# 05 Decisions

- DEC-01: Review subject is the `ocman` project (package `ocman/` + `ocman_tui/`, tests,
  docs, packaging, CI). Excluded from review scope per 00-run-protocol.md:
  `.agents/workflows/` and `workflow-artifacts/`. Recorded per the scope-exclusion rule.
- DEC-02: This is a re-review triggered by the user after a large batch of cross-platform
  CI-hardening changes since the prior GO (run 20260719-140024). Convergence goal applies
  (loop guard): this run will not recommend a fresh broad restart unless a genuinely new
  broad surface is discovered.
- DEC-03: Conversation context IS available and is the authoritative secondary source for
  intent/rationale on the intervening changes (macOS firmlink fix, fail-fast diagnostic,
  vistab floor, DECISIONS.md). Durable conclusions are already captured in DECISIONS.md.
- DEC-04: The pervasive LSP "is not a known attribute of module ocman" / textual
  dynamic-attr errors are PRE-EXISTING known false positives (ocman/__init__.py delegates
  via __getattr__; textual widgets use dynamic attributes). Not findings.

## Section 1 decisions

- DEC-05 (pre-flight gate): Cursory look at TODO.md + pending plans/prompts found NO real
  signal (no pending IPDs, no staged prompts, no status/location mismatch, no blocking TODO).
  Per protocol, the interactive ask is SKIPPED and the audit proceeds silently. (The one
  in-scope item, CI fail-fast restore, is a normal finding S1-CI1, not a pending-plan blocker.)
- DEC-06 (parallel lanes): NOT engaged. This is a focused delta re-review; the substantive
  change surface is one product function (import rebase) plus tests/docs/CI. Independent audit
  surfaces of meaningful size are < 2 for the delta, so serial review is used (fan-out is pure
  overhead per the auto-engage >=2 rule). Whole-project sanity is folded into the serial pass.
- DEC-07: Universal fallback guiding principles apply (no GUIDING_PRINCIPLES.md).
