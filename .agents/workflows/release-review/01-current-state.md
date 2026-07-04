# 01 Current State and Repository Inventory

## Context contract

- **Read:** `00-run-protocol.md`, `fix-decision-policy.md`, this file. `reference.md` on demand.
- **Produce:** `00-run-metadata.md`, `01-repository-inventory.md`, `02-execution-plan.md`, initialized registers and `05`/`06`/`08`, `deprecation-candidates.md`, and the seeds of `todo-reconciliation.md`, `guiding-principles-assessment.md`, `persona-review.md`; per-phase report `section-summaries/01-current-state.md`.
- **Done when:** the Exit gate at the bottom of this file is satisfied.

## Purpose

Understand the repository as it exists now before recommending or making changes. Reconcile actual implementation, tests, documentation, build files, packaging, release artifacts, and recent changes.

This is primarily a review and discovery section. Do not modify tracked project files except for required run setup, such as removing a stale `workflow-artifacts/` line from `.gitignore` so the run artifacts can be tracked.

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

Read `release-review/README.md`, `release-review/00-run-protocol.md`, existing run metadata, repository files relevant to project identity, public contract, tests, docs, packaging, build, CI, deployment, and release.

Recommended inspection targets include `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, package/build files, source directories, test directories, docs directories, CI workflows, release notes, schemas, API definitions, CLI entry points, config files, and examples.

Also discover, in this section:

- **Guiding-principles document(s):** `GUIDING_PRINCIPLES.md`, `PRINCIPLES.md`, `.agents/GUIDING_PRINCIPLES.md`, a "Principles" section in `README.md`/`CONTRIBUTING.md`, or any equivalent referenced by `AGENTS.md`. Record its location and a concise summary of each principle. If none exists, record that the universal fallback principles in `00-run-protocol.md` apply.
- **Backlog / TODO sources:** `TODO.md`, `TODO`, `TODOS.md`, `BACKLOG.md`, `ROADMAP.md`, `KNOWN_ISSUES.md`, `.agents/TODO.md`, issue-tracker exports, and in-code `TODO`/`FIXME`/`HACK`/`XXX` markers. Inventory each source and roughly how many open items it holds. Do not triage them yet beyond noting obvious release blockers; full triage happens across Sections 2 through 7 and is consolidated in `todo-reconciliation.md`.
- **Pending agent plans and staged prompts:** implementation plans / IPDs and queued prompt files that were prepared but not yet executed. Check `.agents/plans/pending/` (and any sibling `pending/`-style plan-staging dir), IPDs anywhere whose `Status:` line marks them pending/awaiting-approval/not-executed, `prompts/`/`.agents/prompts/` or similar staging dirs, and any status/location mismatch (a plan in `done/` still marked pending, or vice versa). List each pending plan or staged prompt with its path and apparent status. Do NOT execute any of them. Classify each against this release (in-scope-and-pending, deferred to a later release, or stale/superseded); this list feeds the loud Section 8 Go/No-Go warning per `00-run-protocol.md`.
- **Project intent and stakeholders:** what outcome/goal the project exists to serve, and who its users, operators, and stakeholders are. This grounds the eight-persona review.

## Allowed actions

Allowed: inspect files, run non-destructive discovery commands, create and update run artifacts, remove a stale `workflow-artifacts/` line from `.gitignore` if present (run artifacts are committed deliverables), and make a local setup commit of the initialized run artifacts (and any `.gitignore` change) when safe.

Not allowed: product code changes, test changes, documentation changes except run artifacts, deleting files, or moving files.

## Review checks

Determine what the project currently does, likely project type and scope, likely public contract, existing tests and validation commands, documentation and specifications, build/packaging/deployment/CI/release artifacts, recent changes, obvious drift among artifacts, stale or obsolete candidates, and major ambiguities that affect later sections.

Apply the review scope exclusions from `00-run-protocol.md`: do not inventory or characterize `release-review/` (the runbook) or `workflow-artifacts/` (run records) as part of the project. Exclude them from project type, size, structure, test, and documentation assessments. Record in `01-repository-inventory.md` that these directories are present but out of scope (unless the user has explicitly made the framework itself the subject of the review).

## Required outputs

Update or create `00-run-metadata.md`, `01-repository-inventory.md`, `02-execution-plan.md`, `03-findings-register.csv`, `04-action-register.csv`, `05-decisions.md`, `06-commands.md`, `08-checkpoints.md`, and `deprecation-candidates.md`.

In `01-repository-inventory.md`, include current project state summary, project type and scope, intended outcome/goal and audience (users, operators, stakeholders), guiding-principles document location and summary (or fallback note), backlog/TODO source inventory, public contract summary, artifact summary, test and validation inventory, documentation inventory, build/packaging/CI/deployment/release inventory, recent changes, drift or inconsistencies with IDs, key ambiguities with IDs, visible release-quality concerns with IDs, deprecation candidates with IDs, and recommended next actions with IDs.

Initialize `todo-reconciliation.md`, `guiding-principles-assessment.md`, and `persona-review.md` in this section so later sections can append to them.

Create the per-phase report `section-summaries/01-current-state.md` (what was done, why, what was considered but not done) per `00-run-protocol.md`.

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

1. Create `workflow-artifacts/release-review/<RUN_ID>/audit-lanes/`.
2. Define lane scopes.
3. Instruct lanes to remain read-only.
4. Require each lane to use `templates/audit-lane-report.md`.
5. Preserve main-agent ownership of synthesis, official IDs, registers, implementation planning, commits, validation, final report, and push/no-push decision.

If not using parallel lanes, record the reason in `05-decisions.md`.

## Exit gate

Do not proceed to Section 2 until all are true (MUST):

- [ ] `00-run-metadata.md` and `01-repository-inventory.md` are complete enough to guide later review.
- [ ] `02-execution-plan.md` exists; registers are initialized.
- [ ] Guiding-principles doc, backlog/TODO sources, and durable-knowledge doc locations are discovered and recorded (or noted absent).
- [ ] Pending agent plans (IPDs) and staged prompts discovered and inventoried with path + status (or noted absent), for the Section 8 Go/No-Go warning.
- [ ] `deprecation-candidates.md`, `todo-reconciliation.md`, `guiding-principles-assessment.md`, `persona-review.md` are initialized.
- [ ] Parallel-audit decision recorded in `05-decisions.md`.
- [ ] Per-phase report `section-summaries/01-current-state.md` written.
- [ ] Checkpoint recorded in `08-checkpoints.md` and committed.
