# Decisions and assumptions

- Concern/scope: full release-review of the `ocman` project toward a release. Framework
  (`.agents/workflows/`) and `workflow-artifacts/` are OUT of review scope per 00-run-protocol.
- Guiding principles: no dedicated file; use ARCHITECTURE.md's principles section + the
  universal fallback. Recorded in guiding-principles-assessment.md.
- Parallel audit lanes: NOT engaged. Rationale: this is a single, well-understood project
  freshly and thoroughly reviewed this session (each change went assess -> plan-review ->
  execute), the tree is clean, and one coordinator can audit the modest surface efficiently.
  The >=2-surface auto-engage trigger is technically met, but the honest cost/benefit here
  favors a serial pass (the expensive reading was largely done during this session's
  per-change reviews). (00-run-protocol permits recording a serial decision.)
- Pre-flight gate: cursory look at TODO.md (all SHIPPED/deferred; no blockers) and pending
  plans (none). NO real signal -> per protocol, the bounded ask was SKIPPED and the audit
  proceeded. Not an assertion of readiness (that is Section 8's call).
- Version: propose 1.2.0 (minor). Rationale: this cycle adds features (doctor/reclaim, full
  TUI parity, spend/running, extract-on-delete, chunk, bundles) with no breaking changes;
  minor bump from the released 1.1.0. Assumption pending maintainer confirmation at the GO.
