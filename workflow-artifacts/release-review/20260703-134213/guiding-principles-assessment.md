# Guiding-Principles Assessment (finalized in Section 5)

No dedicated guiding-principles document exists. Universal fallback principles apply.

| Principle | Verdict | Evidence / notes |
|---|---|---|
| Intuitive / self-documenting | **Adherent** | Rich `--help` (short forms + examples), natural-language `preprocess_argv`, `--create-config`, TUI tabs with key hints, typed-confirmation on destructive ops, copy-paste rollback instructions after deletes. |
| Solve general case / configurable over hardcoded | **Adherent** | `ocman.toml` precedence engine; centralized `SESSION_RELATIONAL_TABLES`; paths configurable; model selection configurable. |
| KISS | **Mostly adherent** | Single-file `ocman.py` is large (8040 lines) but internally sectioned; a personal tool, so a monolith is a defensible trade-off. Not flagged as a violation. |
| Honest documentation | **Minor violations** | CHANGELOG missing 1.0.3 (S1-A1); README clone URL (S1-A2) and rollback filename (S4-U1) drift. All low-risk fixes queued for S7. |

## Establishment of a principles document
- Decision: given a single maintainer and KISS, do NOT create a standalone `GUIDING_PRINCIPLES.md`. Instead
  fold a short "Design principles" note into the new `ARCHITECTURE.md` (S4-KD1). This records the philosophy
  (stdlib-only CLI, rollback-safety-first, self-documenting UX, honest docs) without doc sprawl.

## Unresolved GP findings
- None beyond the honest-documentation fixes already tracked (S1-A1, S1-A2, S4-U1), which are handled under
  the Fix Bar in Section 7.
