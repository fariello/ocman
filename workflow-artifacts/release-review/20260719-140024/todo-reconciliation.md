# TODO / backlog reconciliation (seed; finalized in Section 5)

Source: TODO.md (informal backlog) + in-code markers.

| Item | Source | Classification | Note |
|------|--------|----------------|------|
| Chunk large sessions | TODO.md | stale/done | SHIPPED 2026-07-17; note documents it |
| ocman spend | TODO.md | stale/done | SHIPPED 2026-07-15; note documents it |
| Forked/shared-spend de-duplication | TODO.md | out-of-scope-for-release | Explicitly deferred stretch goal; no IPD; not a blocker |
| ses_XXXX / [XXXXX] | code | n/a | False-positive marker hits (example text / doc glyph) |

No must-before-release or should-before-release TODO items. TODO.md is honest (SHIPPED
notes could be pruned, but that is cosmetic; assess in Section 5).

## Section 5 finalization (feature view)

Full triage confirmed - no release blockers in the backlog:
- Chunk large sessions: SHIPPED (done). No action.
- ocman spend: SHIPPED (done). No action.
- Forked/shared-spend de-duplication: out-of-scope-for-release. A legitimately-deferred
  stretch goal with no IPD; does not block. Leave tracked.
- In-code markers: false positives (n/a).

Cosmetic option (NOT a release action): the two SHIPPED notes in TODO.md could be pruned,
but they honestly document what shipped and one deferred idea; leaving them is fine and
keeps the "resolved-differently" rationale for chunking discoverable. No finding filed.
