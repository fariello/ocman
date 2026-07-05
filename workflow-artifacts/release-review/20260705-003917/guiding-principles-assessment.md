# Guiding-principles assessment

Principles doc: `ARCHITECTURE.md` → "Design principles" (binding for this review).

| Principle | Adherence (delta) | Evidence / notes | Findings |
|---|---|---|---|
| Intuitive / self-documenting | Strong (one nit) | Destructive KEEP/DELETE previews + typed-`yes` + IRREVERSIBLE warning; detailed process-lock report; `--by-project`/`disk` disk visibility; `--create-config`. Nit: `--create-config` prompt still says "restart file". | U2 (Low) |
| Configurable over hardcoded | Upheld | New config keys (`history_max_runs`, `copy_restart_to_project_prompts`); retention accepts fractions; centralized `SESSION_RELATIONAL_TABLES`. | — |
| KISS | Upheld | Destructive-confirm seam is a real general-case abstraction (4 adopters), not speculative; process-lock consolidated 3 duplicated pgrep checks into 1 helper. Monolith growth (S2-M1) is a stated, accepted trade-off. | S2-M1 (deferred) |
| Honest documentation | **Violated (fixable)** | README documents a nonexistent config key (`default_model`); value prop understated. | D1 (High), U1 (Med) — fix S7 |

Overall: the delta strengthens self-documenting/KISS/configurable adherence; the only real breach is the
honest-documentation one (D1), which is a Low-remediation-risk doc fix scheduled for Section 7.
