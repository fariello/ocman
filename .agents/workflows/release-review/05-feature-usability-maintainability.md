# 05 Feature Completeness, Usability, and Maintainability

## Context contract

- **Read:** `00-run-protocol.md`, `fix-decision-policy.md`, this file, Sections 1-4 findings, the registers, `guiding-principles-assessment.md`, `cold-start-orientation.md`. Personas: all eight (led by novice, power user, UI/UX, architect, stakeholder).
- **Produce:** `F`/`U`/`M`/`GP`/`KD`/`TODO` findings (with Remediation Risk); guiding-principles adherence and cold-start orientation assessments; updates to registers, `persona-review.md`, `guiding-principles-assessment.md`, `cold-start-orientation.md`, `todo-reconciliation.md`; per-phase report `section-summaries/05-feature-usability-maintainability.md`.
- **Done when:** the Exit gate at the bottom of this file is satisfied.

## Purpose

Review the project for feature completeness, usability, developer experience, operator experience, maintainability, onboarding quality, and practical future improvements.

The goal is not to invent unnecessary features. The goal is to determine whether the project feels complete, coherent, useful, maintainable, and ready for its intended audience.

This section is an audit pass. Implementation happens in Section 7.

## Standing constraints for this section

- Preserve public behavior unless a change is clearly justified.
- Do not make speculative changes.
- Do not create broad refactors or formatting churn.
- Use run-specific unique IDs for every finding and action.
- Update the finding and action registers before leaving this section.
- Use TodoWrite if available, but treat `workflow-artifacts/release-review/<RUN_ID>/` as authoritative.
- Mark non-applicable checks explicitly rather than forcing findings.
- Prefer meaningful fixes, not checklist compliance.


## Required inputs

Read the repository inventory, findings from Sections 1 through 4, public contracts, examples, README, docs, source structure, architecture, developer setup, operational setup, and relevant TODO-like notes.

## Allowed actions

Allowed: inspect files, run safe workflow-clarifying commands, record findings and candidate actions, update artifacts.

Not allowed: feature implementation, refactoring, file reorganization, or removing/deprecating code.

## Review checks

Assess project intent, implemented workflows, incomplete workflows, documented features missing or partial, implemented features undocumented, implied user/operator/developer needs, API ergonomics, naming clarity, CLI/UI/workflow usability, defaults, help text, error messages, installation/setup/build/packaging clarity, onboarding, configuration clarity, user/operator-facing error handling, contributor maintainability, technically correct but awkward behavior, refinements required before robust release, useful non-blocking features, and code/artifacts that appear unused, obsolete, duplicated, confusing, or harmful to onboarding.

This is the section where all eight personas matter most. Reason explicitly from each (`00-run-protocol.md`) and append findings to `persona-review.md`:

- **Novice (persona 7):** Sit down as someone with no domain knowledge. Can you install it, run the first useful thing, and understand what happened, guided only by what the product tells you? Every place you had to guess, ask, or look up is a `U` finding.
- **Sophisticated power user (persona 6):** Are advanced flows, automation/scripting, escape hatches, and scale ergonomics present? File `F`/`U` findings for friction that would frustrate an expert.
- **UI/UX engineer (persona 3):** Flow clarity, consistency, feedback on actions, accessibility, contrast, keyboard operability where a UI exists.
- **Architect (persona 4):** Is the design solving the general case or hardcoding special cases? Is it extensible and configurable without speculative bloat? Are abstractions earning their keep (KISS)? File `M`/`F` findings, and propose elegant simplifications only when they are safe and clearly net-positive.
- **Stakeholder (persona 8):** Does the project actually deliver its intended outcome for its audience? File `F` findings where the stated goal is not met.

### Self-documenting / learn-as-you-go bar (mandatory)

Continue the self-documenting bar from Section 4, now from the behavior/feature side: the released project should be intuitive enough that users learn it as they go. File `U` findings (and feed safe, in-scope ones to Section 7) for confusing flows, poor defaults, missing inline guidance, unclear error recovery, and anything that effectively requires reading a manual or taking a course to perform a basic task. Prefer in-product self-explanation (clear naming, helpful defaults, good error messages, inline hints, discoverable help) over compensating documentation.

### Guiding-principles adherence (mandatory; type `GP`)

Using the guiding-principles document discovered in Section 1 (or the universal fallback principles in `00-run-protocol.md`), evaluate the project against each stated principle. File a `GP` finding for each violation, referencing the specific principle. Record a per-principle assessment in `guiding-principles-assessment.md`. Common principle dimensions to check, when the project's principles include them: intuitive/self-documenting, accessibility, solve-for-the-general-case, configurable-over-hardcoded, KISS, API-first/integrable, and documentation/handoff readiness. Do not invent principles the project has not adopted; assess against what it actually states (or the fallback).

**Establish the principles document if absent.** If the project has no guiding-principles document, file a `KD`/`GP` finding to create one in Section 7. Do not fabricate principles: recover the project's actual philosophy from the conversation (guarded secondary source per `00-run-protocol.md`), existing docs, and observable design choices, confirm material points with the user or mark them "inferred, needs confirmation", then record the agreed principles. A short, honest principles document the team actually holds is better than an aspirational invented one.

### Cold-start orientation assessment (mandatory; type `KD`)

From the complete-novice (persona 7) and stakeholder (persona 8) viewpoints, judge whether someone with no prior context - human or LLM - could read the project's own tracked docs and come away understanding its intent, goals, philosophy, architecture/approach, and the rationale behind major decisions. Concretely: could a fresh LLM, given only the repo, explain what this project is for, how it is built, and why the key decisions were made? For each area that fails this test, file a `KD` finding to establish or improve the relevant doc (intent/overview, principles, architecture, decisions log) in Section 7, respecting the project's existing convention. Recover the "why" from the conversation as a guarded secondary source and verify material claims per `00-run-protocol.md`. Record the assessment so Section 8 can issue the cold-start verdict.

### TODO.md / backlog reconciliation (feature view)

Triage remaining `TODO.md`/backlog/roadmap items from a feature-completeness and usability standpoint: which are release blockers, which are safe to do now, which are legitimately out of scope, and which are stale. Update `todo-reconciliation.md` and file `TODO`/`F`/`U` findings accordingly.

## Finding categories

Categorize each finding as required for release, strongly recommended soon, nice to have later, or should be explicitly out of scope.

For each item, record ID, title, affected area, why it matters, recommended action, whether public behavior changes, and required artifact updates.

Use `F` for feature gaps, `U` for usability/developer/operator experience and self-documenting gaps, `M` for maintainability, `GP` for guiding-principles violations, `KD` for knowledge/handoff-documentation and cold-start orientation gaps, `TODO` for backlog items bearing on release, and `DEP` for deprecation candidates.

## Required outputs

Update the registers, decisions, commands, checkpoints, deprecation candidates, `persona-review.md`, `guiding-principles-assessment.md`, and `todo-reconciliation.md`.

Create the per-phase report `section-summaries/05-feature-usability-maintainability.md` (what was done, why, what was considered but not done) covering feature completeness, usability and self-documenting assessment, developer experience, operator experience, maintainability, architecture/extensibility observations, guiding-principles adherence, cold-start orientation assessment (`KD`), onboarding concerns, required-for-release items, recommended-soon items, nice-to-have items, out-of-scope items, deprecated/obsolete/stale/confusing candidates, and recommended next actions.

## TodoWrite guidance

If TodoWrite is available, track feature/usability/maintainability review as high-level todos.

## Judgment guidance

Do not invent features. A missing capability is a release issue only if implied by the repository's purpose, public contract, docs, examples, or intended audience. Favor small practical improvements over architecture redesign.

## Non-applicable guidance

If the repository is a small library, script, documentation set, or internal tool, scale expectations accordingly.

## Exit gate

Do not proceed to Section 6 until all are true (MUST):

- [ ] Feature completeness and usability assessed for the intended scope through all eight personas (notes in `persona-review.md`).
- [ ] Self-documenting / learn-as-you-go bar applied from the behavior side.
- [ ] Guiding-principles adherence assessed in `guiding-principles-assessment.md`; a missing principles doc is queued for creation.
- [ ] Cold-start orientation assessed in `cold-start-orientation.md`; `KD` findings filed for gaps.
- [ ] Backlog/TODO items triaged (feature view) in `todo-reconciliation.md`.
- [ ] Maintainability and architecture risks recorded with Remediation Risk; deprecation candidates updated.
- [ ] Per-phase report written; checkpoint recorded and committed.
