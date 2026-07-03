# Guiding-Principles Assessment

No dedicated guiding-principles document exists in the repo. Per `00-run-protocol.md`, the universal
fallback principles apply. Full per-principle verdict is finalized in Section 5; seeded here.

| Principle | Initial read (Section 1) |
|---|---|
| Intuitive / self-documenting | CLI has `-V`, natural-language preprocessing, `--create-config`, argument reference in README. TUI has tabs + key hints. To be assessed for `--help` quality and error clarity in S4/S5. |
| Solve general case / configurable over hardcoded | Config precedence engine (`ocman.toml`); table set centralized (`SESSION_RELATIONAL_TABLES`). Good. |
| KISS | Single-file 8040-line `ocman.py` is a monolith but internally organized; acceptable for a personal tool. |
| Honest documentation | Mostly honest; CHANGELOG drift (missing 1.0.3) and README clone-URL are the exceptions found so far. |

Establishment of a principles doc will be evaluated in Section 5 (KD finding candidate).
