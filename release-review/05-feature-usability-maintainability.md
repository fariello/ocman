# 05 Feature Completeness, Usability, and Maintainability

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
- Use TodoWrite if available, but treat `repository-review/<RUN_ID>/` as authoritative.
- Mark non-applicable checks explicitly rather than forcing findings.
- Prefer meaningful fixes, not checklist compliance.


## Required inputs

Read the repository inventory, findings from Sections 1 through 4, public contracts, examples, README, docs, source structure, architecture, developer setup, operational setup, and relevant TODO-like notes.

## Allowed actions

Allowed: inspect files, run safe workflow-clarifying commands, record findings and candidate actions, update artifacts.

Not allowed: feature implementation, refactoring, file reorganization, or removing/deprecating code.

## Review checks

Assess project intent, implemented workflows, incomplete workflows, documented features missing or partial, implemented features undocumented, implied user/operator/developer needs, API ergonomics, naming clarity, CLI/UI/workflow usability, defaults, help text, error messages, installation/setup/build/packaging clarity, onboarding, configuration clarity, user/operator-facing error handling, contributor maintainability, technically correct but awkward behavior, refinements required before robust release, useful non-blocking features, and code/artifacts that appear unused, obsolete, duplicated, confusing, or harmful to onboarding.

## Finding categories

Categorize each finding as required for release, strongly recommended soon, nice to have later, or should be explicitly out of scope.

For each item, record ID, title, affected area, why it matters, recommended action, whether public behavior changes, and required artifact updates.

Use `F` for feature gaps, `U` for usability/developer/operator experience, `M` for maintainability, and `DEP` for deprecation candidates.

## Required outputs

Update the registers, decisions, commands, checkpoints, and deprecation candidates.

Create or append a Section 5 summary covering feature completeness, usability, developer experience, operator experience, maintainability, onboarding concerns, required-for-release items, recommended-soon items, nice-to-have items, out-of-scope items, deprecated/obsolete/stale/confusing candidates, and recommended next actions.

## TodoWrite guidance

If TodoWrite is available, track feature/usability/maintainability review as high-level todos.

## Judgment guidance

Do not invent features. A missing capability is a release issue only if implied by the repository's purpose, public contract, docs, examples, or intended audience. Favor small practical improvements over architecture redesign.

## Non-applicable guidance

If the repository is a small library, script, documentation set, or internal tool, scale expectations accordingly.

## Exit criteria

Before moving to Section 6, feature completeness and usability are assessed for the intended scope, maintainability risks are recorded, candidate actions are recorded, deprecation candidates are updated, and the checkpoint is recorded.
