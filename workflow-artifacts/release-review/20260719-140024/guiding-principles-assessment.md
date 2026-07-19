# Guiding-principles adherence assessment

No dedicated GUIDING_PRINCIPLES.md; assessed against ARCHITECTURE.md's principles section
and the universal fallback (00-run-protocol). Verdict per principle:

| Principle | Adherence | Evidence |
|-----------|-----------|----------|
| Intuitive / self-documenting (learn-as-you-go) | STRONG | Curated 3-tier help; `doctor` "Suggested order"; no-args "Next steps"; TUI empty states + typed-yes DANGER ZONE; a dedicated self-doc assess+fix pass shipped this cycle (errors that teach, traceback guard, reclaim discoverability, self-explaining TUI labels). |
| General-case / configurable over hardcoded | GOOD | Config keys for retention, chunk sizes, reclaim ages, egress cap; SESSION_RELATIONAL_TABLES centralizes the table model; duration parser accepts general forms. A few fixed thresholds (LONG_SESSION_* trigger) are intentional and documented. |
| KISS | GOOD | Near-monolith cli.py is a deliberate single-maintainer trade-off (documented in ARCHITECTURE); the TUI reuses CLI logic via core.py rather than reimplementing (single implementation of every op). No speculative subsystems. |
| Honest documentation | STRONG | Docs describe current behavior; the stale-claim debt was fixed this cycle; CHANGELOG tracks every change; TODO.md marks SHIPPED items honestly. |

No GP violations found. No principles doc is queued for creation: ARCHITECTURE.md already
carries the principles, matching the project's existing convention.
