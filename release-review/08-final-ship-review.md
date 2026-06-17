# 08 Final Ship Review

## Purpose

Assess whether the current project is ready to ship as a robust, well-written, well-documented, stable, secure, maintainable, feature-complete project for its intended scope.

Be practical but conservative. The goal is not to claim perfection. The goal is to determine whether the project is as close to release-ready as reasonably possible for its intended scope.

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

Read all run artifacts, current Git status, local commits made during the run, validation results, CI assessment, deprecation candidates, findings and action registers, implementation plan, and Section 7 results.

## Allowed actions

Allowed: run final validation commands, inspect final diffs, update final artifacts, make final small cleanup edits if necessary and safe, create a final local commit if tracked files changed, prepare push/no-push plan, and write final report.

Not allowed unless explicitly permitted: remote push, publish/deploy/release/upload/change remote state, start a new review run automatically, or make broad new implementation changes that should have gone through Section 7 planning.

## Final review checks

Review project purpose/scope, feature completeness, correctness, stability, security/privacy, edge cases, performance, test coverage, regression protection, docs/specs/examples, API/CLI/UI/config/schema/storage/integration consistency, packaging/build, deployment/operations, installation/first-run, versioning/changelog/release notes, backward compatibility/migration, developer and operator experience, user-facing rough edges, documented limitations, deprecation candidates, CI readiness, and release blockers.

## Final bug/security sanity audit

Before writing the final report, create or update:

```text
repository-review/<RUN_ID>/final-bug-security-audit.md
```

This is not a full repeat of Section 2. It is a final post-implementation sanity audit focused on whether changes made during the run introduced or left unresolved material issues.

Review:

1. New or modified code paths.
2. New or modified tests.
3. New or modified configuration, CI, packaging, scripts, schemas, examples, and documentation.
4. Changed file handling, path handling, subprocess use, network behavior, serialization, deserialization, authentication, authorization, logging, error handling, and secret handling.
5. Any unresolved HIGH or CRITICAL findings.
6. Whether final validation failures indicate latent bugs or release blockers.
7. Whether any implemented change created a new compatibility, security, privacy, or reliability risk.

Record:

1. New findings, if any, with run-specific IDs.
2. Previously identified issues still unresolved.
3. Issues confirmed resolved.
4. Residual risk.
5. Whether the final release recommendation changes.

If a new material issue is found, update the finding and action registers and decide whether it must be fixed before final completion. Do not hide or minimize late-discovered issues.

## Final validation

Run the most appropriate repository-native validation commands available and safe. Record all results in `10-validation-results.md`. If validation cannot be run, explain why and assess release risk.

## Final schema validation check

Before the final report, update `schema-validation.md` with final status.

Confirm, where applicable:

1. Schemas and data contracts were discovered and assessed.
2. Repository-native schema validation commands were run, or inability to run them was explained.
3. Representative examples, fixtures, golden files, sample configs, documented payloads, imports, exports, migrations, or serialized outputs were validated when practical.
4. Schema, implementation, documentation, tests, examples, and generated artifacts are synchronized or remaining drift is recorded.
5. Public schema or serialized-output compatibility risks are identified and reflected in the final recommendation.

Use `SCH` IDs for unresolved schema issues.

## Final finding categories

Categorize remaining findings as must fix before release, should fix before release if time allows, acceptable known limitation if documented, or nice to have after release.

For each final finding, include ID, title, severity, affected area, why it matters, recommended fix, affected audiences, public behavior change assessment, required artifact updates, and whether it blocks release.

Use `REL` IDs for final release decisions and blockers. Preserve earlier IDs when referring to unresolved items.

## Push/no-push plan

Create or update `repository-review/<RUN_ID>/11-push-plan.md` with current branch, local commits, Git status, whether the user explicitly permitted pushing, push recommendation, risks, suggested command if permitted, and no-push rationale if permission is absent.

Do not push unless explicitly permitted.

## Restart assessment

Decide whether a new review run should be started. Recommend restart only when implementation changed enough that earlier audit results may be stale, substantial architecture or behavior was discovered late, validation exposed issues requiring another broad pass, or major CI/packaging/public contract/security changes were made. Do not restart merely because minor fixes were made. Do not start a new run automatically.

## Final report

Save the final report to `repository-review/<RUN_ID>/12-final-response.md`, then present the same content to the user.

The final response must begin with these two tables.

### Completed actions

| Unique ID | Description of what was done | Files changed | Commit | Validation |
|---|---|---|---|---|

### Identified but not addressed

| Unique ID | Description of what was not done | Reason | Recommended next step |
|---|---|---|---|

The second table must include audit findings identified but not implemented, not only actions that were attempted and left incomplete.

After the tables, include summary of changes, tests and validations run, CI assessment summary, deprecated-code assessment summary, documentation and artifact updates, remaining risks, push/no-push decision, final GO/CONDITIONAL GO/NO-GO recommendation, and restart recommendation.

## TodoWrite guidance

If TodoWrite is available, reconcile all todos against the findings and action registers, mark statuses accurately, and do not leave stale in-progress todos.

## Judgment guidance

Be honest. Do not claim release readiness if validation failed, critical tests are missing, security blockers remain, or public contract risk is unresolved.

A CONDITIONAL GO is appropriate when the project is mostly ready but has limited, clearly documented prerequisites. A NO-GO is appropriate when unresolved blockers would likely harm users, operators, developers, integrations, maintainers, security, or release reliability.

## Non-applicable guidance

If release concepts do not apply to the repository, provide a readiness assessment for the nearest equivalent, such as major run readiness, internal adoption readiness, or handoff readiness.

## Exit criteria

The run is complete only when final validation, push/no-push plan, restart assessment, release recommendation, completed and unaddressed tables, final response file, and user-facing final response are complete.
