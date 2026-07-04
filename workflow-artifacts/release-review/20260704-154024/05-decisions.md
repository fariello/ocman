# 05 Decisions and Assumptions

## D1 — Out-of-scope dirs
`.agents/workflows/` (framework, updated to 20260704-01 — tooling only), `.opencode/`, `.claude/`,
`workflow-artifacts/`, and `.agents/plans/` (framework plan artifacts) are excluded from review scope.

## D2 — No parallel audit lanes
Small, cohesive delta since v1.0.3; serial single pass is higher-signal. (Protocol requires recording this.)

## D3 — Follow-up run / loop guard
This run is the follow-up the prior release-review (20260703-134213) set up. Per the loop guard, it will NOT
recommend a third broad pass; any residue is enumerated as targeted follow-ups.

## D4 — Guiding principles: fallback + ARCHITECTURE.md
No dedicated principles file; universal fallback applies, and ARCHITECTURE.md (prior run) records design
principles. See `guiding-principles-assessment.md`.

## D5 — Conversation as intent source
This session's history is the intent source: the user reported the move crash and the compaction interest,
approved the perf and testing IPDs, and asked about disk usage. All durable conclusions are already in
CHANGELOG/ARCHITECTURE; no new "inferred, needs confirmation" doc claims required.

## D6 — Target version assumption
Assume the release is **1.0.4** (patch): every delta change is a fix, an internal perf improvement, or one
additive backward-compatible config key (`history_max_runs`). No breaking public-contract change. Confirm Q1.

## D7 — Pending disk-usage IPD not executed here
`.agents/plans/pending/2026-07-04-assess-functionality-disk-usage.md` is an approved-for-planning-only
proposal awaiting separate execution approval; it is NOT part of this release and is not implemented here.
