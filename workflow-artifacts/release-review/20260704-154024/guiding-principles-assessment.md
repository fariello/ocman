# Guiding-Principles Assessment

No dedicated principles file; universal fallback applies, and ARCHITECTURE.md records a "Design principles"
section (added in the prior run). Finalized in Section 5; seeded here.

| Principle | Read (Section 1) |
|---|---|
| Intuitive / self-documenting | Delta improves it: TUI compaction now works; clearer worker error handling. |
| Configurable over hardcoded | New `history_max_runs` config key follows the precedence engine. Adherent. |
| KISS | Delta reduced duplication (shared `_rebased_dir`) and simplified the remap; net-positive. |
| Honest documentation | CHANGELOG `[Unreleased]` accurately describes the delta; the one gap is the version heading (S1-A1). |
