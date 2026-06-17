# 04 Documentation, Specifications, and Examples

## Purpose

Review documentation, specifications, examples, README content, help text, and navigation for accuracy, completeness, consistency, and usefulness. Documentation and specifications must reflect actual current behavior, not hoped-for or planned behavior.

This section is an audit pass. Documentation fixes happen in Section 7.

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

Read the repository inventory, findings from Sections 1 through 3, README, docs, API/CLI/schema/configuration/architecture/deployment/operational docs, examples, changelog, release notes, and help text if available.

## Allowed actions

Allowed: inspect documentation and examples, run non-destructive examples if safe, compare documented behavior against implementation and tests, record findings and candidate actions.

Not allowed: editing docs/examples, changing public behavior to match docs, or removing docs/examples.

## Review checks

Review README, user guides, API docs, CLI docs, architecture docs, configuration docs, schemas, specifications, operational docs, examples, installation/build instructions, packaging/release notes, known limitations, migration notes, and Markdown navigation bars.

Check for outdated claims, missing setup or usage steps, broken examples, terminology inconsistencies, missing limitations or assumptions, missing configuration/security/privacy/operational notes, implementation/docs/spec mismatches, confusing onboarding areas, undocumented implemented behavior, documented unimplemented behavior, partially implemented behavior not labeled clearly, and docs/examples referencing deprecated or obsolete artifacts.

## Required outputs

Update the registers, decisions, commands, checkpoints, and deprecation candidates if stale docs/examples reveal obsolete artifacts.

Create or append a Section 4 summary covering documentation health, specification health, major inaccuracies, missing or weak docs, examples needing correction, accurate docs, required pre-release updates, stale or misleading docs/examples, and recommended updates grouped by priority.

Use `D` for documentation/examples, `A` for artifact sync issues, and `DEP` for stale/deprecated docs or example candidates.

## TodoWrite guidance

If TodoWrite is available, track documentation/spec/example review at a high level.

## Judgment guidance

Favor accuracy over polish. A short accurate README is better than a long aspirational one. Do not add planned features to docs unless clearly labeled as future work or out of scope.

## Non-applicable guidance

If there are few or no docs, record that fact and assess whether the absence matters for the repository type and release intent.

## Exit criteria

Before moving to Section 5, documentation/spec/example accuracy has been assessed, material gaps and inconsistencies are recorded, candidate documentation actions are added, stale docs/examples are reflected in deprecation candidates if relevant, and the checkpoint is recorded.
