# TODO / Backlog Reconciliation

## Sources discovered (Section 1)

- `TODO.md`: informal backlog. Items present are all SHIPPED-with-pointer or explicit deferrals.
- In-code markers: 2 `XXX` matches, both false positives (example ID string, docstring glyph).

## Triage (initial)

| Item | Source | Class | Note |
|---|---|---|---|
| chunk-large-sessions | TODO.md | done (SHIPPED 2026-07-17) | keep as historical note |
| ocman spend | TODO.md | done (SHIPPED 2026-07-15) | keep |
| forked/shared-spend de-dup | TODO.md | out-of-scope-for-release | explicit deferral; promote to IPD if wanted |
| `ses_XXXX` / `[XXXXX]` | cli.py | stale/obsolete=no | false positives, not real markers |

No `must-before-release` or `should-before-release` TODO items found. Full confirmation in Section 5.
