# 00 Run Protocol

This file defines the global rules for the release review. These rules apply to all sections.

---

## Authority Model

1. `README.md` is the controlling instruction.
2. This file defines shared rules.
3. Section files `01` through `09` define phase-specific tasks.
4. `repository-review/<RUN_ID>/` is the authoritative run record.
5. Local progress tracking files (`task.md` and `walkthrough.md` in the App Data Directory) are for live visibility and tracking only.

If a section file appears to conflict with this protocol, follow this protocol and record the conflict in `05-decisions.md`.

---

## Core Behavior

Proceed autonomously through the full review. Use judgment. Do not stop for minor uncertainty. Record assumptions and proceed conservatively.

Stop or pause only for a true safety blocker, such as risk of deleting user data, exposing or committing secrets, running ambiguous destructive commands, needing unavailable credentials, being unable to separate this run's changes from pre-existing user changes, or needing to alter public behavior without enough evidence or validation.

---

## Required Run Directory

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
| `00-run-metadata.md` | Run ID, timestamp, agent/model details, repository path, Git metadata, initial status, environment summary. |
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
| `section-summaries/` | Exact per-section summary files for Sections 1 through 9. |
| `audit-lanes/` | Optional reports from controlled parallel read-only audit lanes used after Section 1. |

If any artifact is not applicable, create it anyway and mark it as not applicable with rationale.

---

## Unique ID System

Every finding, candidate action, implemented change, deferred item, blocked item, deprecated-code candidate, CI candidate, decision, release concern, and final recommendation must have a unique run-specific ID.

Use this pattern:
```text
<RUN_ID>-S<section>-<TYPE><number>
```
Examples:
- `20260606-142233-S1-A1`
- `20260606-142233-S2-B1`
- `20260606-142233-S2-S1`

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

---

## Register Requirements

Maintain `03-findings-register.csv` and `04-action-register.csv` throughout the run. Use these statuses: `identified`, `planned`, `completed`, `deferred`, `blocked`, `not_applicable`, `superseded`, and `wont_do`.

- **Findings** must include: ID, section, type, severity, title, status, affected area, evidence, impact, recommended action, public behavior change, required artifact updates, source files, validation, and next step.
- **Actions** must include: ID, source finding IDs, section, status, description, files changed, commit, validation, reason not done, and recommended next step.

---

## Antigravity Progress Tracking

You must maintain `task.md` (for the checklist) and `walkthrough.md` (for change/test summaries) in your App Data directory `/brain/` folder.
- Create/update `task.md` at the start of the run and update it at each section boundary.
- Mark statuses accurately (using `- [ ]` for pending, `- [/]` for in-progress, and `- [x]` for complete).
- Summarize changes and commands run in `walkthrough.md`.

---

## Command Logging

For every meaningful command, append to `06-commands.md` the command, purpose, working directory, relevant assumptions, result, short output summary, and follow-up action if any.

Do not paste secrets or excessive logs. Summarize long outputs and save only relevant excerpts when needed.

---

## Commit Policy

Use local commits for meaningful tracked repository changes when safe.

Before any commit, run `git status --short`, confirm the files to commit were changed by this run, avoid committing unrelated pre-existing changes, and run appropriate validation first or state why validation could not be run.

Commit at logical checkpoints: after adding `repository-review/` to `.gitignore`, after coherent implementation batches, after test/docs/CI updates when they form a reviewable unit, and after final validation cleanup if tracked files changed.

Use commit messages that reference action IDs. If changes cannot be separated from pre-existing user changes, do not commit. Record the blocker.

---

## Remote Push and Release Gating Policy

> [!IMPORTANT]
> **NO REMOTE PUSH IS ALLOWED DURING THE AUDIT PHASES (SECTIONS 1–8).**
> You must compile `repository-review/<RUN_ID>/11-push-plan.md` first, which details local commits, remotes, risks, and a push recommendation.
> 
> **MANDATORY GO/NO-GO GATE:**
> You are strictly prohibited from pushing code or tags to a remote repository, or executing any step in Section 9 (Release Execution), until the user has explicitly approved a **GO** or **CONDITIONAL GO** release decision in response to your final review report.

---

## Implementation Philosophy

Favor meaningful, safe improvements. Do not restrict fixes to only high-priority issues. Implement lower-severity changes when they add significant release value and are safe, well scoped, and validated.

Good changes include bug fixes, security hardening, correctness fixes, edge-case handling, cleanup fixes, important tests, accurate docs, packaging fixes, low-risk CI checks, clear deprecation markers, and small maintainability improvements that reduce real risk.

Avoid cosmetic churn, broad refactors, style-only rewrites, speculative features, file reorganization without clear value, public behavior changes without compatibility analysis, unnecessary dependencies, and workflows that publish, deploy, release, or upload artifacts without explicit permission.

---

## Deprecated-Code Analysis

Throughout the review, identify code, files, commands, examples, tests, configs, docs, workflows, or scripts that appear unused, obsolete, superseded, misleading, or harmful to maintainability. Record candidates in `deprecation-candidates.md`.

Classify each candidate as safe to remove now, safe to mark deprecated now, candidate for future removal, probably still needed, or unknown requiring human review.

Do not delete or deprecate something solely because it is old or not immediately referenced. Look for imports, references, tests, docs, package exports, CLI exposure, build scripts, CI workflows, changelog history, external contract risk, and usage patterns.

---

## CI and GitHub Actions

Assess whether CI should be added or updated. Record findings in `ci-assessment.md`.

You may add or update CI only when validation commands are clear, the workflow is low risk, it does not publish, deploy, release, upload artifacts, or change remote state, it does not require unknown secrets, it aligns with the repository language and package manager, and it materially improves release readiness.

Consider linting, formatting checks, unit tests, type checks, build checks, security or dependency checks, documentation checks, and matrix testing for supported versions. If CI is not added, explain why.

---

## Schema Validation

Throughout the review, identify and validate schemas and data contracts when applicable. Record schema findings in `schema-validation.md` and the registers.

Validate representative examples, fixtures, golden files, sample configs, or test data against schemas (JSON Schema, OpenAPI, database schemas, etc.) using repository-native commands. Check for drift, backward compatibility risks, missing validation, or stale generated schema artifacts.

---

## Validation Expectations

Use repository-native commands when available. Prefer commands documented in README, package scripts, Makefiles, task runners, CI files, or contribution docs. Do not invent unsafe commands or install heavy new tooling just to validate unless the repository clearly requires it.

---

## Non-Applicable Handling

Some repositories will not have APIs, CLIs, UIs, packaging, deployment, docs, tests, or CI. Do not force findings. Mark non-applicable checks explicitly, explain why, and continue.

---

## Final Report Requirements

Save the final report to `repository-review/<RUN_ID>/12-final-response.md`, then present the same content to the user.

The final report must begin with two tables:

### Completed actions

| Unique ID | Description of what was done | Files changed | Commit | Validation |
|---|---|---|---|---|

### Identified but not addressed

| Unique ID | Description of what was not done | Reason | Recommended next step |
|---|---|---|---|

After the two tables, include a summary of changes, validations run, CI assessment summary, deprecated-code summary, documentation and artifact updates, remaining risks, push/no-push decision, GO/CONDITIONAL GO/NO-GO recommendation, and restart recommendation.

---

## Restart Assessment

At the end, decide whether a new review run should be started. Recommend a restart only when implementation changed enough that earlier audit results may be stale, substantial architecture or behavior was discovered late, validation exposed issues requiring another pass, or major CI, packaging, public contract, or security changes were made. Do not restart merely because minor fixes were made.

---

## Safety Rules

Do not run destructive commands unless clearly necessary and safe. Do not delete user data, generated artifacts, databases, or untracked files without explicit justification. Do not expose or commit secrets. Do not install unnecessary dependencies. Do not change license terms. Do not alter public APIs without compatibility analysis. Do not modify deployment or release automation to publish externally without explicit permission. Stop and record a blocker if a change cannot be made safely.
