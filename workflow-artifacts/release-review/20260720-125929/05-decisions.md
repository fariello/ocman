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
