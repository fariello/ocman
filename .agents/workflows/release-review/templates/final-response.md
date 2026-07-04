# Final Release Review Report

## Completed actions

| Unique ID | Description of what was done | Files changed | Commit | Validation |
|---|---|---|---|---|
|  |  |  |  |  |

## Identified but not addressed

Include audit findings identified but not implemented, not only actions left
incomplete. Under the Fix Bar, anything not fixed was deferred because the
Remediation Risk of the fix is Medium-High or higher; the Reason must name the axis
(complexity / usability / security / functionality), not effort/time/cost. Any
`LIVE`/High data-integrity finding that was not fixed MUST appear here, flagged
`LIVE - needs user decision` (never silently moved to `TODO.md`).

| Unique ID | Description of what was not done | Remediation Risk + axis | Reason | Recommended next step |
|---|---|---|---|---|
|  |  |  |  |  |

## Fix Bar summary

State that the Fix Bar was applied (fix by default; defer only at Medium-High+
Remediation Risk). Give counts: findings fixed vs. deferred, and for deferrals, the
breakdown by Remediation-Risk axis (complexity / usability / security /
functionality). Confirm no finding was silently dropped and no fix was skipped
merely for effort/time/cost.

## Summary of changes

Summarize the most important changes made.

## Tests and validations run

| Command/check | Result | Notes |
|---|---|---|
|  |  |  |

## CI assessment summary

Summarize CI findings, changes made, recommendations, or reasons no CI changes were made.

## Schema validation summary

Summarize discovered schemas, validation performed, unresolved schema/data-contract risks, and CI/test coverage for schema validation.

## Deprecated-code assessment summary

Summarize deprecated, obsolete, stale, unused, or superseded candidates and what was done with them.

## Final bug/security/memory sanity audit summary

Summarize the final post-implementation bug, correctness, security, privacy, memory/resource, and unsafe-change audit results.

## TODO / backlog reconciliation summary

Summarize the triage of every `TODO.md`/backlog/roadmap and in-code `TODO`/`FIXME`
item: how many were must/should/out-of-scope/stale, which were fixed, which were
reclassified, which were escalated, and what edits were made to keep `TODO.md`
honest. Reference `todo-reconciliation.md`.

## Pending plans / staged prompts

State loudly whether any pending agent plans (IPDs) or staged prompt files were found
(`.agents/plans/pending/`, IPDs marked pending/awaiting-approval, `prompts/` staging
dirs, or status/location mismatches). If any in-scope pending item exists, lead with a
bold warning line, for example:

**WARNING: 2 pending plan(s)/prompt(s) NOT executed - review before release.**

| Path | Kind (IPD / prompt) | Status | In scope for this release? | Recommended action |
|---|---|---|---|---|
|  |  |  |  |  |

If none exist, state explicitly: "No pending plans or staged prompts." Any in-scope
pending item is a prerequisite/decision that blocks a clean GO (see Final release
recommendation).

## Guiding-principles adherence summary

Per-principle verdict against the repository's guiding-principles document (or the
universal fallback principles), with unresolved `GP` findings. Reference
`guiding-principles-assessment.md`.

## Eight-persona sign-off

One line per persona (QA/QC, testing/regression, UI/UX, architect, software
engineer, power user, novice, stakeholder): acceptable / conditional / no, with
blocking IDs.

## Self-documenting / learn-as-you-go assessment

State whether a novice could learn the project as they go without a manual or
course, what was improved to make the product more self-explanatory, and any
remaining `U` blockers.

## Cold-start orientation verdict

State whether a no-context engineer or LLM could orient from the project's own
tracked docs. Score each knowledge area and list remaining `KD` gaps and any
"inferred, needs confirmation" passages the user should verify.

| Knowledge area | Adequate / thin / missing | Doc / location | Action this run | Remaining `KD` IDs |
|---|---|---|---|---|
| Intent, goals, audience, scope |  |  |  |  |
| Philosophy / guiding principles |  |  |  |  |
| Architecture and approach |  |  |  |  |
| Design-decision rationale |  |  |  |  |

## Documentation and artifact updates

Summarize documentation, examples, specs, schemas, packaging, release notes, changelog, CI, or deployment artifacts updated or intentionally left unchanged.

## Remaining risks

List remaining material risks with unique IDs.

## Push/no-push decision

State whether pushing is recommended, whether permission exists, and what command should be used if permitted.

## Final release recommendation

GO, CONDITIONAL GO, or NO-GO.

Include rationale and blocking IDs if applicable.

If any in-scope pending plan / staged prompt was found (see Pending plans / staged
prompts above) or any unaddressed `LIVE`/High data-integrity finding remains, repeat the
loud warning here and state that the recommendation is at most CONDITIONAL GO with those
items named as explicit prerequisites. Do not issue a clean GO over an un-actioned
in-scope pending plan.

## Restart recommendation

State whether a new review run is recommended and why.

## Section 9 readiness

If GO or CONDITIONAL GO, state whether the project is ready to proceed to Section 9
release execution and exactly what user approval/prerequisites are required first.
If NO-GO, state that release execution must not proceed.
