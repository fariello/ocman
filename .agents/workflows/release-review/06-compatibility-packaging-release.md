# 06 Compatibility, Packaging, CI, Deployment, and Release Artifacts

## Context contract

- **Read:** `00-run-protocol.md`, `fix-decision-policy.md`, this file, Sections 1-5 findings, packaging/CI/release files. `reference.md` (schema/CI lists) on demand. Lead personas: operator, stakeholder, software engineer.
- **Produce:** `R`/`P`/`O`/`CI`/`SCH`/`DEP` findings (with Remediation Risk); `ci-assessment.md`, `schema-validation.md` updates; register/`persona-review.md` updates; per-phase report `section-summaries/06-compatibility-packaging-release.md`.
- **Done when:** the Exit gate at the bottom of this file is satisfied. Sections 1-6 complete enough to build `implementation-plan.md`.

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
- Use TodoWrite if available, but treat `workflow-artifacts/release-review/<RUN_ID>/` as authoritative.
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

## Published-version check (registry-published projects)

If the project publishes to a package registry (e.g. a PyPI distribution declared in
`pyproject.toml`/`setup.cfg`, or an npm/crates/etc. package), determine the CURRENTLY-PUBLISHED
latest version and confirm the version this release proposes is a valid bump - strictly `>=` the
published version (a re-used or lower version cannot be published and signals a versioning mistake).
For PyPI, the packaged CLI exposes this via `agent_workflows.versioning.latest_pypi_version(name)`
and `next_version_ok(proposed, published)` (stdlib, zero-dep). Degrade gracefully: if the lookup
fails (offline, timeout, or the package is unpublished / first release), record that the check was
skipped and why - never block the review on network state. File a `PKG` finding if the proposed
version is not `>=` the published one, and surface the published-vs-proposed pair in
`ci-assessment.md` and the Section 8 report so the operator can pick the next version confidently.

## CI and GitHub Actions assessment

Create or update `ci-assessment.md`. Assess whether CI should include linting, formatting checks, unit tests, type checks, build checks, packaging checks, security/dependency checks, documentation checks, or matrix testing.

Only recommend CI changes when repository-native commands are clear, the workflow is low risk, it does not publish/deploy/release/upload/change remote state, it does not require unknown secrets, and it materially improves release readiness.

## Required outputs

Update the registers, decisions, commands, checkpoints, validation results if checks are run, `ci-assessment.md`, `persona-review.md`, and deprecation candidates.

Lead this section with the operator and stakeholder personas (see the persona-to-section map in `00-run-protocol.md`): a first-time installer/operator should be able to install, configure, and run the release guided by the artifacts themselves; file `U`/`O` findings where they cannot. Append at least one observation per lead persona to `persona-review.md`, or note "no new finding from persona X".

Create the per-phase report `section-summaries/06-compatibility-packaging-release.md` (what was done, why, what was considered but not done) covering confirmed regressions, plausible risks, backward compatibility risks, packaging/build risks, deployment/operational risks, install/first-run clarity, missing regression tests, versioning/changelog/migration concerns, CI recommendations, deprecated/obsolete release artifacts, recommended mitigations, and breaking changes needing release notes.

Use `R`, `P`, `O`, `CI`, and `DEP` IDs as appropriate.

## TodoWrite guidance

If TodoWrite is available, track compatibility/packaging/release review and CI assessment as high-level todos.

## Judgment guidance

Do not add CI just because CI is absent. Add or recommend CI only when clear validation commands exist and the workflow would be safe. Do not infer breaking changes without comparing public contracts, docs, examples, and tests.

## Non-applicable guidance

If the repository has no packaging, deployment, release process, or CI, mark those areas not applicable unless their absence materially affects release readiness.

## Exit gate

Do not proceed to Section 7 until all are true (MUST):

- [ ] Compatibility/regression, packaging/build, deployment/operational, and versioning/changelog/migration risks recorded with Remediation Risk.
- [ ] Install/first-run clarity assessed (operator persona).
- [ ] `ci-assessment.md` and `schema-validation.md` updated (or marked not applicable).
- [ ] Deprecation candidates updated; breaking changes flagged for release notes.
- [ ] One observation per lead persona appended to `persona-review.md`.
- [ ] Per-phase report written; checkpoint recorded and committed.
- [ ] Sections 1-6 are complete enough to create `implementation-plan.md`.
