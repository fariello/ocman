# 01 Current State and Repository Inventory

## Purpose

Understand the repository as it exists now before recommending or making changes. Reconcile actual implementation, tests, documentation, build files, packaging, release artifacts, and recent changes.

This is primarily a review and discovery section. Do not modify tracked project files except for required run setup such as `.gitignore`.

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

Read `release-review/README.md`, `release-review/00-run-protocol.md`, existing run metadata, repository files relevant to project identity, public contract, tests, docs, packaging, build, CI, deployment, and release.

Recommended inspection targets include `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, package/build files, source directories, test directories, docs directories, CI workflows, release notes, schemas, API definitions, CLI entry points, config files, and examples.

## Allowed actions

Allowed: inspect files, run non-destructive discovery commands, create and update run artifacts, add `repository-review/` to `.gitignore` if required, and make a local commit for `.gitignore` only if changed and safe.

Not allowed: product code changes, test changes, documentation changes except run artifacts, deleting files, or moving files.

## Review checks

Determine what the project currently does, likely project type and scope, likely public contract, existing tests and validation commands, documentation and specifications, build/packaging/deployment/CI/release artifacts, recent changes, obvious drift among artifacts, stale or obsolete candidates, and major ambiguities that affect later sections.

## Required outputs

Update or create `00-run-metadata.md`, `01-repository-inventory.md`, `02-execution-plan.md`, `03-findings-register.csv`, `04-action-register.csv`, `05-decisions.md`, `06-commands.md`, `08-checkpoints.md`, and `deprecation-candidates.md`.

In `01-repository-inventory.md`, include current project state summary, project type and scope, public contract summary, artifact summary, test and validation inventory, documentation inventory, build/packaging/CI/deployment/release inventory, recent changes, drift or inconsistencies with IDs, key ambiguities with IDs, visible release-quality concerns with IDs, deprecation candidates with IDs, and recommended next actions with IDs.

## TodoWrite guidance

If TodoWrite is available, mark Section 1 in progress, track current-state reconciliation, and mark it complete only after outputs and registers are updated.

## Judgment guidance

Be practical. Do not infer public contracts solely from filenames. Look for evidence in exports, entry points, docs, tests, package metadata, schemas, command definitions, and examples.

Do not label something deprecated just because it is old. Record it as a candidate only when there is evidence or uncertainty worth preserving.

## Non-applicable guidance

If the repository lacks a given artifact type, record that fact. Do not force a finding unless the absence creates meaningful release risk.

## Parallel audit handoff

After Section 1 is complete, decide whether controlled parallel audit lanes would improve review quality.

Use parallel lanes when the repository is large, unfamiliar, or has clearly separable areas such as code, tests, docs, schemas, packaging, and CI.

If using parallel lanes:

1. Create `repository-review/<RUN_ID>/audit-lanes/`.
2. Define lane scopes.
3. Instruct lanes to remain read-only.
4. Require each lane to use `templates/audit-lane-report.md`.
5. Preserve main-agent ownership of synthesis, official IDs, registers, implementation planning, commits, validation, final report, and push/no-push decision.

If not using parallel lanes, record the reason in `05-decisions.md`.

## Exit criteria

Before moving to Section 2, run metadata is complete, repository inventory is complete enough to guide later review, execution plan exists, registers are initialized and updated, deprecation candidates file exists, and the section checkpoint is recorded.
