# TODO / Backlog Reconciliation

Sources discovered in Section 1 (full triage in Section 5):
- TODO.md: 2 SHIPPED-annotated (chunk-large-sessions, spend), 1 deferred stretch (forked/shared-spend de-dup).
- In-code TODO/FIXME/HACK/XXX markers in shipped source: none.

(Per-item triage appended in Section 5.)

## Section 4 doc-vs-backlog reconciliation
- TODO.md documented features (chunk-large-sessions, spend) are implemented and shipped (SHIPPED annotations accurate).
- No documented-but-unimplemented feature. The 1 deferred item (forked/shared-spend de-dup) is honestly labeled deferred, not claimed as present. No doc/backlog contradiction.

## Section 5 full triage (feature view) - FINAL

| Item | Source | Classification | Disposition |
|---|---|---|---|
| Chunk large sessions on recover/compact | TODO.md (SHIPPED 2026-07-17) | stale/obsolete-as-todo | Shipped; the SHIPPED stanza is a breadcrumb, not open work. Not a release blocker. |
| `ocman spend` | TODO.md (SHIPPED 2026-07-15) | stale/obsolete-as-todo | Shipped; SHIPPED stanza. Not a release blocker. |
| Forked/shared-spend de-duplication | TODO.md (deferred stretch) | out-of-scope-for-release | Legitimately deferred stretch goal; honestly labeled; NOT expected in 1.3.0. Leave tracked. |
| In-code TODO/FIXME/HACK/XXX | source | n/a | None exist (0). |

No must-before-release or should-before-release TODO item. The only open item (forked-spend
de-dup) is out-of-scope-for-release. TODO.md is honest. (User separately raised whether to keep
SHIPPED stanzas in TODO.md at all; that is a convention preference, not a release blocker, and
is NOT actioned by this review.)
