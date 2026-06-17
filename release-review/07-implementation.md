# 07 Implementation of Safe, Valuable Fixes

## Purpose

Create a consolidated implementation plan from Sections 1 through 6, then implement safe, meaningful, significant-value fixes.

This is the primary change-making section. It should favor useful release hardening over minimalism, but it must avoid churn, speculative work, broad refactors, and unsafe changes.

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

Read the findings register, action register, all section summaries from Sections 1 through 6, `deprecation-candidates.md`, `ci-assessment.md`, decisions, validation results, and current Git status.

## Required implementation plan

Before editing tracked project files, create `repository-review/<RUN_ID>/09-implementation-plan.md`.

The implementation plan must include scope summary, non-goals, change batches, unique implementation action IDs, source finding IDs, files likely to change, risk level, public behavior change assessment, required tests, required artifact updates, validation method, local commit grouping, deferred findings, blocked findings, deprecated-code decisions, and CI decisions.

Do not start implementation until the plan exists.

## Selection criteria

Implement findings when they are safe, well scoped, evidence-supported, likely to improve release readiness, validatable, and unlikely to break public behavior unless clearly justified.

Do not limit implementation to only high-priority items. Include lower-severity changes when they add significant value and are safe.

Defer or mark wont-do when a change is speculative, requires product judgment, needs unavailable credentials, risks public contract breakage without evidence, requires large refactoring, creates release/deployment side effects, cannot be validated, is cosmetic churn, or involves deprecation/removal without enough evidence.

## Allowed actions

Allowed: edit code, add/update tests, update docs/examples/specs/schemas/changelog/release notes, update packaging/build metadata when safe, add/update low-risk CI workflows when justified, mark code/docs deprecated when evidence is strong, remove obsolete code only when evidence is strong and risk is low, and create local commits.

Not allowed without explicit user permission: remote push, publish/deploy/release/upload, rotate credentials, delete user data, rewrite major architecture, change license terms, or remove public APIs/CLI commands/schemas/config fields without compatibility analysis and strong justification.

## Implementation order

Prefer safety/correctness fixes, tests protecting those fixes, edge-case/reliability fixes, docs/spec/example corrections, packaging/build/release metadata fixes, low-risk CI additions, deprecation markers, then small maintainability fixes that reduce real risk.

Keep related code, tests, and docs synchronized in the same batch when practical.

## Local commits

After each coherent implementation batch, run relevant validation, update registers, update `07-commits.md`, commit only this run's tracked changes, and reference action IDs in the commit message.

If pre-existing user changes cannot be separated, do not commit. Record the blocker and continue carefully if safe.

## CI additions

If adding GitHub Actions or CI, keep workflows minimal, use repository-native commands, avoid publish/deploy/release/upload/secrets, avoid broad matrices unless justified, document rationale in `ci-assessment.md`, and validate syntax where practical.

## Schema validation actions

For each schema-related action selected for implementation:

1. Confirm the schema or data contract is actually part of the project contract or internal validation path.
2. Validate syntax and representative examples when practical.
3. Keep schemas, implementation, tests, docs, examples, generated artifacts, changelog, and release notes synchronized.
4. Preserve backward compatibility for public schemas and serialized outputs unless a breaking change is clearly justified and documented.
5. Add or update schema validation tests or CI checks only when low risk and repository-native commands are clear.
6. Record results in `schema-validation.md` and `10-validation-results.md`.

## Deprecated-code actions

For each selected deprecation candidate, confirm evidence, check references/exports/docs/tests/package metadata/CLI exposure/build scripts/workflows/changelog history, choose the safest action, prefer staged deprecation when public contract risk exists, and update docs/tests/release notes if behavior or public surface changes.

## Required outputs

Update the implementation plan, registers, decisions, commands, commits, checkpoints, validation results, deprecation candidates, and CI assessment.

Create or append a Section 7 summary covering implemented scope, intentionally unimplemented scope, change batches, source finding IDs addressed, tests and validations, artifacts updated, local commits, remaining risks, and follow-up work.

## TodoWrite guidance

If TodoWrite is available, create todos for each implementation batch, mark each in progress before editing, mark complete only after validation/register updates/local commit decision, track deferred/blocked items at a high level, and reconcile TodoWrite with the action register before leaving Section 7.

## Judgment guidance

Do the work that improves release readiness, not the work that merely increases diff size. Small precise fixes are preferred.

## Non-applicable guidance

If no safe implementation work is found, do not fabricate changes. Record the rationale and proceed to final review.

## Exit criteria

Before moving to Section 8, implementation plan is complete, safe selected fixes are implemented or explicitly deferred/blocked/wont-do, relevant artifacts are synchronized, validation is run and recorded where possible, local commits are made or explained, actions are reconciled, and the checkpoint is recorded.
