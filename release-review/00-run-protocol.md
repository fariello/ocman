# 00 Run Protocol

This file defines the global rules for the release review. These rules apply to all sections.

## Authority model

1. `README.md` is the controlling instruction.
2. This file defines shared rules.
3. Section files `01` through `08` define phase-specific tasks.
4. `repository-review/<RUN_ID>/` is the authoritative run record.
5. TodoWrite, if available, is live progress tracking only.

If a section file appears to conflict with this protocol, follow this protocol and record the conflict in `05-decisions.md`.

## Core behavior

Proceed autonomously through the full review unless invoked through a planning-only command. In planning-only mode, complete Sections 1 through 6, create `09-implementation-plan.md`, and stop before Section 7 implementation.

Proceed autonomously through the full review. Use judgment. Do not stop for minor uncertainty. Record assumptions and proceed conservatively.

Stop or pause only for a true safety blocker, such as risk of deleting user data, exposing or committing secrets, running ambiguous destructive commands, needing unavailable credentials, being unable to separate this run's changes from pre-existing user changes, or needing to alter public behavior without enough evidence or validation.

## Required run directory

Create:

```text
repository-review/<RUN_ID>/
```

Use a timestamp run ID:

```text
YYYYMMDD-HHMMSS
```

Add `repository-review/` to `.gitignore` if not already ignored.

Required artifacts:

| Artifact | Purpose |
|---|---|
| `00-run-metadata.md` | Run ID, timestamp, agent/model if known, repository path, Git metadata, initial status, environment summary. |
| `01-repository-inventory.md` | Project type, structure, languages, frameworks, public contracts, tests, docs, build/release artifacts. |
| `02-execution-plan.md` | Lightweight plan for the full review and audit, updated when material facts change. |
| `03-findings-register.csv` | Durable register of all findings, including addressed and unaddressed findings. |
| `04-action-register.csv` | Durable register of all candidate actions, implemented changes, deferred items, and blockers. |
| `05-decisions.md` | Decisions, assumptions, non-applicable judgments, scope choices, and rationale. |
| `06-commands.md` | Commands run, purpose, result summary, and whether output was clean or had errors. |
| `07-commits.md` | Local commits made, files included, source action IDs, and validation. |
| `08-checkpoints.md` | Section boundary checkpoints and reconciliation notes. |
| `09-implementation-plan.md` | Consolidated implementation plan created after Sections 1 through 6 and before Section 7. |
| `10-validation-results.md` | Tests, builds, linters, type checks, security checks, documentation checks, and manual validation. |
| `11-push-plan.md` | Push/no-push decision, rationale, branch/remotes, and recommended next action. |
| `12-final-response.md` | Final saved report matching the user-facing final response. |
| `deprecation-candidates.md` | Deprecated, obsolete, stale, unused, superseded, or misleading code and artifact candidates. |
| `ci-assessment.md` | CI and GitHub Actions assessment, recommendations, changes made, or reasons no change was made. |
| `schema-validation.md` | Discovered schemas, schema validation commands, sample payload/config/example validation, compatibility risks, and schema drift findings. |
| `final-bug-security-audit.md` | Final post-implementation bug, correctness, security, privacy, and unsafe-change sanity audit before completion. |
| `section-summaries/` | Exact per-section summary files for Sections 1 through 8. |
| `audit-lanes/` | Optional reports from controlled parallel read-only audit lanes used after Section 1. |

If any artifact is not applicable, create it anyway and mark it as not applicable with rationale.

## Unique ID system

Every finding, candidate action, implemented change, deferred item, blocked item, deprecated-code candidate, CI candidate, decision, release concern, and final recommendation must have a unique run-specific ID.

Use this pattern:

```text
<RUN_ID>-S<section>-<TYPE><number>
```

Examples:

```text
20260606-142233-S1-A1
20260606-142233-S2-B1
20260606-142233-S2-S1
20260606-142233-S3-T1
20260606-142233-S4-D1
20260606-142233-S5-M1
20260606-142233-S6-CI1
20260606-142233-S7-X1
20260606-142233-S8-REL1
```

Recommended type codes:

| Type | Meaning |
|---|---|
| `A` | General action or artifact concern |
| `B` | Bug or correctness issue |
| `S` | Security or privacy issue |
| `E` | Edge case, error handling, cleanup, recovery, or resource issue |
| `T` | Test gap or test concern |
| `D` | Documentation, specification, example, or help-text issue |
| `F` | Feature completeness issue |
| `U` | Usability, developer experience, or operator experience issue |
| `M` | Maintainability issue |
| `R` | Regression, compatibility, migration, or public contract risk |
| `P` | Packaging, build, release artifact, or versioning issue |
| `O` | Operations or deployment issue |
| `CI` | CI or GitHub Actions issue or recommendation |
| `SCH` | Schema, data contract, serialized format, migration, payload, or config validation issue |
| `DEP` | Deprecated, obsolete, stale, or unused code/artifact candidate |
| `X` | Concrete implemented change |
| `REL` | Final release decision, blocker, or release readiness finding |
| `Q` | Question or ambiguity |
| `DEC` | Decision or judgment call |

Restarts are new runs with new IDs. A restarted run may reference earlier run IDs but must not reuse them.

## Register requirements

Maintain `03-findings-register.csv` and `04-action-register.csv` throughout the run. Use these statuses: `identified`, `planned`, `completed`, `deferred`, `blocked`, `not_applicable`, `superseded`, and `wont_do`.

Findings must include ID, section, type, severity, title, status, affected area, evidence, impact, recommended action, public behavior change, required artifact updates, source files, validation, and next step.

Actions must include ID, source finding IDs, section, status, description, files changed, commit, validation, reason not done, and recommended next step.

## TodoWrite protocol

If running in OpenCode and TodoWrite is available, use TodoWrite for live progress visibility. Create one todo per major section and one per implementation batch. Keep todo statuses aligned with the run artifacts. Reconcile TodoWrite against the registers before the final report.

Do not use TodoWrite as the official record. If TodoWrite is unavailable, continue without it and record progress in the run directory.

## Optional controlled parallel audit mode

After Section 1 completes the repository baseline, the main agent may use controlled parallel read-only audit lanes for Sections 2 through 6 when doing so is likely to improve review breadth, reduce missed findings, or manage a large repository more effectively.

Parallel audit mode is optional. Do not force it for small or simple repositories.

Allowed lane scopes include:

1. Code quality, correctness, security, privacy, and edge cases.
2. Tests, fixtures, coverage, and regression protection.
3. Documentation, specifications, examples, and help text.
4. Compatibility, packaging, build, CI, deployment, versioning, and release artifacts.
5. Schemas, data contracts, migrations, examples, fixtures, and serialized outputs.
6. Deprecated, obsolete, stale, unused, duplicated, or superseded code and artifacts.

Rules for parallel audit lanes:

1. The main agent must complete Section 1 before starting parallel lanes.
2. Lanes must be read-only.
3. Lanes must not edit tracked files.
4. Lanes must not update official registers directly.
5. Lanes must not create commits.
6. Lanes must not push to a remote.
7. Lanes must not make final release decisions.
8. Lanes must not assign official run-specific IDs.
9. Lanes should use temporary candidate IDs only.
10. Lanes must produce compact reports under `repository-review/<RUN_ID>/audit-lanes/` using `templates/audit-lane-report.md`.
11. The main agent must synthesize all lane reports before creating `09-implementation-plan.md`.
12. The main agent must deduplicate findings, assign official IDs, decide severity, update registers, and record decisions.
13. Section 7 implementation must remain serial.
14. Section 8 final review must remain serial.

If parallel lanes are not used, record that decision in `05-decisions.md` and continue serially.

## Command logging

For every meaningful command, append to `06-commands.md` the command, purpose, working directory, relevant assumptions, result, short output summary, and follow-up action if any.

Do not paste secrets or excessive logs. Summarize long outputs and save only relevant excerpts when needed.

## Commit policy

Use local commits for meaningful tracked repository changes when safe.

Before any commit, run `git status --short`, confirm the files to commit were changed by this run, avoid committing unrelated pre-existing changes, and run appropriate validation first or state why validation could not be run.

Commit at logical checkpoints: after adding `repository-review/` to `.gitignore`, after coherent implementation batches, after test/docs/CI updates when they form a reviewable unit, and after final validation cleanup if tracked files changed.

Use commit messages that reference action IDs. If changes cannot be separated from pre-existing user changes, do not commit. Record the blocker.

## Remote push policy

Do not push to a remote during the review. At the end, create `11-push-plan.md` with branch, local commits, permission status, push recommendation, risks, suggested command if permitted, and no-push rationale if permission is absent. Only push if explicitly permitted by the user.

## Implementation philosophy

Favor meaningful, safe improvements. Do not restrict fixes to only high-priority issues. Implement lower-severity changes when they add significant release value and are safe, well scoped, and validated.

Good changes include bug fixes, security hardening, correctness fixes, edge-case handling, cleanup fixes, important tests, accurate docs, packaging fixes, low-risk CI checks, clear deprecation markers, and small maintainability improvements that reduce real risk.

Avoid cosmetic churn, broad refactors, style-only rewrites, speculative features, file reorganization without clear value, public behavior changes without compatibility analysis, unnecessary dependencies, and workflows that publish, deploy, release, or upload artifacts without explicit permission.

## Deprecated-code analysis

Throughout the review, identify code, files, commands, examples, tests, configs, docs, workflows, or scripts that appear unused, obsolete, superseded, misleading, or harmful to maintainability. Record candidates in `deprecation-candidates.md`.

Classify each candidate as safe to remove now, safe to mark deprecated now, candidate for future removal, probably still needed, or unknown requiring human review.

Do not delete or deprecate something solely because it is old or not immediately referenced. Look for imports, references, tests, docs, package exports, CLI exposure, build scripts, CI workflows, changelog history, external contract risk, and usage patterns.

## CI and GitHub Actions

Assess whether CI should be added or updated. Record findings in `ci-assessment.md`.

You may add or update CI only when validation commands are clear, the workflow is low risk, it does not publish, deploy, release, upload artifacts, or change remote state, it does not require unknown secrets, it aligns with the repository language and package manager, and it materially improves release readiness.

Consider linting, formatting checks, unit tests, type checks, build checks, security or dependency checks, documentation checks, and matrix testing for supported versions. If CI is not added, explain why.

## Schema validation

Throughout the review, identify and validate schemas and data contracts when applicable.

Schemas may include:

1. JSON Schema.
2. OpenAPI or Swagger specifications.
3. GraphQL schemas.
4. XML Schema.
5. Database schemas or migrations.
6. Protocol buffers.
7. Avro, Parquet, or other data serialization contracts.
8. Configuration schemas.
9. Custom file format schemas.
10. Message, event, API payload, import, export, or serialized output contracts.

Record schema findings in `schema-validation.md` and the finding/action registers.

When repository-native validation commands exist, use them. When examples, fixtures, golden files, sample configs, documented payloads, or test data exist, validate representative samples against the relevant schemas when practical and safe.

Check for:

1. Schema syntax validity.
2. Drift between schemas, implementation, docs, examples, tests, and generated artifacts.
3. Backward compatibility risks for public schemas and serialized outputs.
4. Missing validation for user-provided or external data.
5. Migration or versioning concerns.
6. Generated schema artifacts that are stale or not reproducible.
7. CI opportunities for schema validation.

Do not introduce new schema tooling unless it is low risk, aligned with the repository, and clearly justified. If validation is not possible, explain why and record the residual risk.

## Validation expectations

Use repository-native commands when available. Prefer commands documented in README, package scripts, Makefiles, task runners, CI files, or contribution docs. Do not invent unsafe commands or install heavy new tooling just to validate unless the repository clearly requires it.

## Non-applicable handling

Some repositories will not have APIs, CLIs, UIs, packaging, deployment, docs, tests, or CI. Do not force findings. Mark non-applicable checks explicitly, explain why, and continue.

## Final report requirements

Save the final report to `repository-review/<RUN_ID>/12-final-response.md`, then present the same content to the user.

The final report must begin with two tables:

### Completed actions

| Unique ID | Description of what was done | Files changed | Commit | Validation |
|---|---|---|---|---|

### Identified but not addressed

| Unique ID | Description of what was not done | Reason | Recommended next step |
|---|---|---|---|

The second table must include audit findings that were identified but not implemented, not only actions that were started and left incomplete.

After the two tables, include summary of changes, validations run, CI assessment summary, deprecated-code summary, documentation and artifact updates, remaining risks, push/no-push decision, GO/CONDITIONAL GO/NO-GO recommendation, and restart recommendation.

## Restart assessment

At the end, decide whether a new review run should be started. Recommend a restart only when implementation changed enough that earlier audit results may be stale, substantial architecture or behavior was discovered late, validation exposed issues requiring another broad pass, or major CI, packaging, public contract, or security changes were made. Do not restart merely because minor fixes were made.

## Safety rules

Do not run destructive commands unless clearly necessary and safe. Do not delete user data, generated artifacts, databases, or untracked files without explicit justification. Do not expose or commit secrets. Do not install unnecessary dependencies. Do not change license terms. Do not alter public APIs without compatibility analysis. Do not modify deployment or release automation to publish externally without explicit permission. Stop and record a blocker if a change cannot be made safely.
