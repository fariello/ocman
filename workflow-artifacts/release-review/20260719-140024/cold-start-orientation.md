# Cold-start orientation assessment

Could a no-context engineer or LLM orient from the project's own tracked docs?

| Knowledge area | Home | Verdict |
|----------------|------|---------|
| Intent, goals, audience, scope | README.md top + pyproject description | ADEQUATE-STRONG: purpose ("administer, maintain, repair your OpenCode environment") and audience are clear up front. |
| Philosophy / principles | ARCHITECTURE.md principles section | ADEQUATE: principles stated; matches the fallback set. |
| Architecture / approach | ARCHITECTURE.md (structure, CLI/TUI relationship, DB model, guards) | STRONG: updated this cycle; explains the 9-tab TUI, the CLI<->TUI single-implementation rule, and the destructive-op guard model. |
| Decision rationale + alternatives | The executed-IPD trail under .agents/plans/executed/ (each IPD records goal, alternatives, deferrals, and axis-named trade-offs) + CHANGELOG | ADEQUATE: the project's decision-log convention IS the IPD trail; rationale and alternatives are captured there (e.g. why remote move / snapshot-force stay CLI-only, why chunk sizes are config vs the fixed trigger). No dedicated DECISIONS.md, and none is needed given this convention. |

Verdict: a fresh engineer/LLM can, from the repo alone, explain what ocman is for, how it
is built, and why the key decisions were made. No KD gap requiring a new doc. (Recorded for
the Section 8 cold-start verdict.)
