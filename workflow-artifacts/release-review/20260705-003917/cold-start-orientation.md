# Cold-start orientation

| Knowledge area | Adequate / thin / missing | Doc / location | Action this run |
|---|---|---|---|
| Intent, goals, audience, scope | Adequate (but value-prop understated) | README.md | U1: add "actually reclaims space" |
| Philosophy / guiding principles | Adequate | ARCHITECTURE.md "Design principles" | none |
| Architecture and approach | Adequate | ARCHITECTURE.md | D4: add css/ |
| Design-decision rationale | Thin (improving) | CHANGELOG + .agents/plans/executed IPDs | none (existing convention) |

Verdict: a no-context engineer/LLM CAN orient from the project's own docs. Decision "why" lives in the
executed-IPD set + CHANGELOG rather than a single DECISIONS.md — acceptable per the project's convention.
No "inferred, needs confirmation" doc passages introduced. The ocman-vs-ocgc positioning is user-stated
intent; the *reclaim behavior* is code-verified (VACUUM + file deletion), so U1 is truthful, not aspirational.
