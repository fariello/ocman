# 05 Decisions

## Scope

- DEC-01: Review scope excludes `.agents/workflows/` (this framework's installed copy) and
  `workflow-artifacts/` per 00-run-protocol review-scope-exclusions. This repo is `ocman`,
  the target project; it is NOT the framework's own repo, so the framework is out of scope.
- DEC-02: The subject of this promotion review is the 1.3.0 line. Baseline of "what changed
  since last final release" = commits since tag v1.2.0.

## Conversation context (intent recovery, guarded secondary source)

- DEC-03: This run has rich in-session context (the entire 1.3.0 cycle was executed in this
  session under assess/plan-review/release-review discipline). Per 00-run-protocol, conversation
  is evidence for intent/rationale only; code/tests/docs remain authoritative for behavior. The
  project already maintains DECISIONS.md (ADR log) and per-feature executed IPDs, so durable
  cold-start knowledge largely exists in-repo, not only in chat.

## Parallel audit lanes

- DEC-04: Running SERIAL (no parallel audit lanes). Auto-engage trigger technically met
  (2+ independent surfaces exist), but the review's actual audit surface is small and
  well-understood: the product delta since v1.2.0 is a single reviewer (this agent) already
  deeply familiar with, scoped to `ocman/cli.py` + one TUI widget + packaging + tests, and
  the whole cycle was built here under assess/plan-review discipline. Fan-out overhead
  (spawning read-only lanes, synthesizing, cross-unit conflict pass) exceeds its value for a
  delta this contained and familiar. Serial keeps grounding tight. Recorded per protocol.

## Pre-flight gate

- DEC-05: CLEAN SKIP. No pending IPDs, no staged prompts, empty comms inboxes, no in-code
  markers, TODO.md = 2 shipped-annotated + 1 known-deferred stretch. No real signal -> ask
  skipped, audit proceeds (see 00-run-metadata.md gate outcome).
