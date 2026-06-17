# 06 Compatibility, Packaging, CI, Deployment, and Release Artifacts

## Purpose

Review compatibility, packaging, build, deployment, CI, versioning, changelog, migration, and release artifact readiness.

Focus on whether the project can be safely shipped without breaking existing users, integrations, automation, documentation, workflows, or assumptions.

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

Read the repository inventory, findings from Sections 1 through 5, package/build files, CI workflows, deployment configuration, version metadata, changelog, release notes, migration guidance, and public API/CLI/schema/config/serialized output definitions.

## Allowed actions

Allowed: inspect packaging/build/CI/release files, run safe build/package checks if available, inspect GitHub Actions workflows, record findings and candidate actions, and update `ci-assessment.md`.

Not allowed: editing packaging files, adding or changing CI, publishing, deploying, uploading, releasing, changing versions, or altering migration scripts/release automation.

## Review checks

Review public API behavior, CLI commands/flags/outputs/exit behavior, UI if relevant, configuration, environment variables, defaults and precedence, schemas, serialized outputs, messages/file formats, logging, error handling, existing callers/scripts/integrations/workflows, platform compatibility, dependency assumptions, database/storage/migration compatibility, build files, packaging metadata, deployment configuration, installation/first-run behavior, version metadata, changelog/release notes, migration guidance, documentation accuracy after recent changes, tests needing updates, CI or GitHub Actions needing updates, and deprecated or obsolete entry points, package exports, workflows, scripts, examples, or release artifacts.

## Schema validation and compatibility assessment

Create or update `schema-validation.md`.

Identify schemas and data contracts, including explicit schema files and implicit public serialized formats. Validate them when repository-native commands or practical sample validation paths exist.

Assess:

1. Syntax validity for schema files.
2. Whether examples, fixtures, golden files, sample configs, documented payloads, imports, exports, and generated artifacts conform to schemas.
3. Drift among implementation, schemas, docs, tests, and examples.
4. Backward compatibility risks.
5. Versioning or migration concerns.
6. Missing validation for external or user-provided data.
7. CI opportunities for schema validation.

Record schema issues using `SCH` IDs.

## CI and GitHub Actions assessment

Create or update `ci-assessment.md`. Assess whether CI should include linting, formatting checks, unit tests, type checks, build checks, packaging checks, security/dependency checks, documentation checks, or matrix testing.

Only recommend CI changes when repository-native commands are clear, the workflow is low risk, it does not publish/deploy/release/upload/change remote state, it does not require unknown secrets, and it materially improves release readiness.

## Required outputs

Update the registers, decisions, commands, checkpoints, validation results if checks are run, `ci-assessment.md`, and deprecation candidates.

Create or append a Section 6 summary covering confirmed regressions, plausible risks, backward compatibility risks, packaging/build risks, deployment/operational risks, missing regression tests, versioning/changelog/migration concerns, CI recommendations, deprecated/obsolete release artifacts, recommended mitigations, and breaking changes needing release notes.

Use `R`, `P`, `O`, `CI`, and `DEP` IDs as appropriate.

## TodoWrite guidance

If TodoWrite is available, track compatibility/packaging/release review and CI assessment as high-level todos.

## Judgment guidance

Do not add CI just because CI is absent. Add or recommend CI only when clear validation commands exist and the workflow would be safe. Do not infer breaking changes without comparing public contracts, docs, examples, and tests.

## Non-applicable guidance

If the repository has no packaging, deployment, release process, or CI, mark those areas not applicable unless their absence materially affects release readiness.

## Exit criteria

Before moving to Section 7, compatibility/release risks are recorded, packaging/build/deployment/versioning/changelog concerns are recorded, CI assessment exists, candidate actions are recorded, deprecation candidates are updated, checkpoint is recorded, and Sections 1 through 6 are complete enough to create the implementation plan.
