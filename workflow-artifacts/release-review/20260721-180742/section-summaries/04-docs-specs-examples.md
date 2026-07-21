# Section 4 - Documentation, Specifications, Examples

## What I did
- Verified README documents all 5 new 1.3.0 commands (lr+filters, session rename, reconnect,
  kill, doctor server check) in the command reference, each with defaults, safety notes, and
  the Linux-only caveat. README user docs are accurate and self-documenting.
- Checked CHANGELOG: the [1.3.0] entry accurately describes every shipped feature; date
  2026-07-20 slightly predates the cycle's last commit (2026-07-21) -> D01 (fix at bump).
- Assessed durable-knowledge / cold-start docs (KD):
  - README (intent + reference): current.
  - ARCHITECTURE.md: present and strong, but its enumerated top-level-verbs list omits
    reconnect/kill/rename -> A01.
  - DECISIONS.md: records significant cross-cutting decisions linking IPDs; the reconnect/kill
    process-signalling SAFETY model (a significant, cross-cutting safety decision) has no entry,
    only per-feature IPDs -> KD01.
  - Executed-IPD trail: all 5 features have full-rationale IPDs under .agents/plans/executed/.
- Reconciled TODO.md against docs: shipped items accurately annotated; the one deferred item
  is honestly labeled; no documented-but-unimplemented feature.

## Why
- The novice/UX lens: end users learn from README, which is complete. The cold-start-engineer
  lens (KD objective): a maintainer should be able to learn WHY the signalling model is shaped
  the way it is from DECISIONS.md, which is its intended home; today that rationale lives only
  in two IPDs.

## Findings
- **DR03** (from S1): AGENTS.md references nonexistent RELEASING.md / CONTRIBUTING.md.
- **S4-A01** (Low/Low): ARCHITECTURE top-level-verbs enumeration omits reconnect/kill/rename.
- **S4-KD01** (Low/Low): no DECISIONS.md entry for the reconnect/kill signalling safety model.
- **S4-D01** (Low/Low): CHANGELOG [1.3.0] date predates last commit; fix at promotion.

## What I considered but did NOT do
- Did NOT file a KD finding for rename or list-filters lacking DECISIONS entries: they are
  routine additive features fully covered by their IPDs; DECISIONS.md's own convention is
  SIGNIFICANT decisions only, and it links IPDs rather than duplicating. Only the signalling
  SAFETY model rises to that bar.
- Did NOT edit any doc here (audit-then-fix; Section 7 owns edits).
- Did NOT file a U-type in-product finding: the new commands' help/errors are consistent with
  existing conventions and were reviewed in each feature's plan-review; no manual-required task.
- The intent recovered from this session (why reconnect/kill are shaped this way) is verifiable
  directly against the code, so KD01's DECISIONS entry needs no user confirmation.
