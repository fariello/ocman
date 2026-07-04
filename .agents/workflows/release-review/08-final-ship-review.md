# 08 Final Ship Review

## Context contract

- **Read:** `00-run-protocol.md`, `fix-decision-policy.md`, this file, all run artifacts, the Section 7 changes/diffs, registers, validation results. Personas: all eight (produce the sign-off). `templates/final-response.md` defines the report shape.
- **Produce:** `final-bug-security-audit.md`, finalized `persona-review.md`/`todo-reconciliation.md`/`guiding-principles-assessment.md`/`cold-start-orientation.md`, `10-validation-results.md`, `11-push-plan.md`, `12-final-response.md`; per-phase report `section-summaries/08-final-ship-review.md`.
- **Done when:** the Exit gate at the bottom of this file is satisfied.
- **Continuity:** runs continuous with Section 7 (shares the implementation evidence).

## Purpose

Assess whether the current project is ready to ship as a robust, well-written, well-documented, stable, secure, maintainable, feature-complete project for its intended scope.

Be practical but conservative. The goal is not to claim perfection. The goal is to determine whether the project is as close to release-ready as reasonably possible for its intended scope.

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

Read all run artifacts, current Git status, local commits made during the run, validation results, CI assessment, schema validation assessment, deprecation candidates, findings and action registers, implementation plan, and Section 7 results.

## Allowed actions

Allowed: run final validation commands, inspect final diffs, update final artifacts, make final small cleanup edits if necessary and safe, create a final local commit if tracked files changed, prepare push/no-push plan, and write final report.

Not allowed unless explicitly permitted: remote push, publish/deploy/release/upload/change remote state, start a new review run automatically, or make broad new implementation changes that should have gone through Section 7 planning.

## Final review checks

Review project purpose/scope, feature completeness, correctness, stability, security/privacy, memory/resource safety, edge cases, performance, test coverage, regression protection, docs/specs/examples, API/CLI/UI/config/schema/storage/integration consistency, packaging/build, deployment/operations, installation/first-run, versioning/changelog/release notes, backward compatibility/migration, developer and operator experience, user-facing rough edges, documented limitations, deprecation candidates, CI readiness, and release blockers.

Conduct the final review through all eight personas (`00-run-protocol.md`) and produce an eight-persona sign-off (one line per persona, including the novice and stakeholder views) in the final report and in `persona-review.md`.

## Eight-persona sign-off, TODO, principles, and self-documenting reconciliation (mandatory)

Before writing the final report:

1. **Persona sign-off.** For each of the eight personas, state whether the project is acceptable from that viewpoint and list any blocking concerns with IDs.
2. **TODO/backlog reconciliation.** Finalize `todo-reconciliation.md`: confirm every `must-before-release` item is fixed or escalated as a release blocker, every `should-` item is fixed or consciously deferred, stale items are removed/marked, and `TODO.md` itself is honest. Summarize in the report.
3. **Guiding-principles adherence.** Finalize `guiding-principles-assessment.md` with a per-principle verdict and any unresolved `GP` findings.
4. **Self-documenting / learn-as-you-go.** State whether a novice could learn the project as they go without a manual or course, and list any remaining `U` blockers.
5. **Pending agent plans and staged prompts (loud warning).** Review the pending-plans/staged-prompts inventory from Section 1. For each pending IPD or queued prompt that is not clearly out-of-scope for this release, raise a prominent WARNING. If ANY in-scope pending plan or staged prompt exists, the final report's Go/No-Go and its summary MUST call it out loudly (a bold `WARNING: N pending plan(s)/prompt(s) not executed` line naming each item and its path), and the recommendation may not be a clean GO - it is at most CONDITIONAL GO with those items listed as explicit prerequisites or decisions for the user. Also flag any status/location mismatch (a plan in `done/` still marked pending, or a `pending/` plan marked executed) as a WARNING to resolve. Do not execute the plans or prompts; surface them for a human decision. If none exist, state that explicitly ("no pending plans or staged prompts").
6. **Cold-start orientation verdict (`KD`).** Judge whether a competent engineer or an LLM with zero prior context could, from the project's own tracked docs alone, understand its intent, goals, philosophy, architecture/approach, and the rationale behind major decisions. Score each of the four knowledge areas (intent/overview, principles, architecture, decision rationale) as adequate / thin / missing, and list remaining `KD` findings. Note any orientation-doc passages still marked "inferred, needs confirmation" so the user can verify them. This is a scored assessment, not a hard release blocker: gaps are findings (fixed under the Fix Bar); only an egregious absence of orientation knowledge should weigh on the GO/CONDITIONAL-GO recommendation, and then as a documented condition, not an automatic NO-GO.

## Final bug/security sanity audit

Before writing the final report, create or update:

```text
workflow-artifacts/release-review/<RUN_ID>/final-bug-security-audit.md
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

Use the `verify` workflow (`verify/tools/run_checks.py`) to run the repo's own checks and produce machine-checkable evidence (`workflow-artifacts/verify/<RUN_ID>/verify-results.json`): actual commands, exit codes, metrics, and logs. `10-validation-results.md` should CITE that evidence rather than assert results from reading the code.

**Evidence gate on the recommendation.** The GO / CONDITIONAL GO / NO-GO recommendation must be backed by this evidence. If a relevant test/lint/build/type-check could not be verified (no runnable setup, needs services/credentials, or blocked by the safety denylist), the recommendation may not be a clean GO: downgrade to CONDITIONAL GO with the unverified checks listed as explicit prerequisites, and state plainly which claims are unverified. Never issue a GO whose basis is the agent's self-report where deterministic evidence was available but not produced. "Could not verify" must appear as prominently as "verified".

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

By the time Section 8 runs, the Fix Bar should already have driven every finding to fixed or explicitly deferred-with-justification. For any finding still open, do not categorize by "if time allows" (effort is not a Fix-Bar reason). Categorize remaining findings as: must fix before release (release blocker), deferred because the fix carries Medium-High or higher Remediation Risk (name the axis), acceptable known limitation if documented, or nice to have after release.

For each final finding, include ID, title, severity (impact if left alone), Remediation Risk and the at-risk axis if deferred, affected area, why it matters, recommended fix, affected audiences, public behavior change assessment, required artifact updates, and whether it blocks release.

Use `REL` IDs for final release decisions and blockers. Preserve earlier IDs when referring to unresolved items.

## Push/no-push plan

Create or update `workflow-artifacts/release-review/<RUN_ID>/11-push-plan.md` with current branch, local commits, Git status, whether the user explicitly permitted pushing, push recommendation, risks, suggested command if permitted, and no-push rationale if permission is absent.

Do not push unless explicitly permitted.

## Restart assessment

Decide whether a new review run should be started. Recommend restart only when implementation changed enough that earlier audit results may be stale, substantial architecture or behavior was discovered late, validation exposed issues requiring another broad pass, or major CI/packaging/public contract/security changes were made. Do not restart merely because minor fixes were made. Do not start a new run automatically. Apply the loop guard in `00-run-protocol.md`: recommend at most one restart, with an enumerated list of what the next run must re-examine; if this run is itself a recommended follow-up, do not recommend a third broad pass.

## Final report

Save the final report to `workflow-artifacts/release-review/<RUN_ID>/12-final-response.md`, then present the same content to the user.

Create or update `section-summaries/08-final-ship-review.md` with the Section 8 final ship review summary.

Follow the exact structure in `templates/final-response.md`; it is the single canonical definition of the report (including the table columns). Do not redefine the columns here.

The report begins with the two tables from the template: **Completed actions** and **Identified but not addressed**. The second table must include audit findings identified but not implemented, not only actions that were attempted and left incomplete, and must carry the Remediation Risk + axis for each unaddressed item. Any `LIVE`/High data-integrity finding that was not fixed MUST appear here, flagged `LIVE - needs user decision`, never silently moved to `TODO.md`.

After the tables, include every remaining section the template lists (summary of changes, Fix Bar summary, tests/validations, CI, schema validation, deprecated-code, final bug/security/memory sanity audit, TODO/backlog reconciliation, pending plans / staged prompts, guiding-principles adherence, eight-persona sign-off, self-documenting / learn-as-you-go assessment, documentation/artifact updates, remaining risks, push/no-push decision, GO/CONDITIONAL GO/NO-GO recommendation, restart recommendation, and Section 9 readiness).

**Live-surface / data-integrity gate.** If any `LIVE`/High data-integrity finding (Section 2) is unaddressed, the recommendation may not be a clean GO: it is at most CONDITIONAL GO with that finding listed as an explicit prerequisite, or NO-GO if it can overwrite/destroy verified data, spend uncontrolled money, corrupt shared state, or exhaust production resources. Hermetic tests passing does not satisfy this gate.

**Pending-plans / staged-prompts gate.** If any in-scope pending agent plan (IPD) or staged prompt was found (Section 1 inventory), the recommendation may not be a clean GO: it is at most CONDITIONAL GO with each pending item named as an explicit prerequisite or user decision. The Go/No-Go section and the summary must both carry a loud, bold `WARNING` naming the pending items and their paths - never bury them or silently proceed to GO. A status/location mismatch (e.g. a plan in `done/` still marked pending) is itself a WARNING to resolve before a clean GO.

## TodoWrite guidance

If TodoWrite is available, reconcile all todos against the findings and action registers, mark statuses accurately, and do not leave stale in-progress todos.

## Judgment guidance

Be honest. Do not claim release readiness if validation failed, critical tests are missing, security blockers remain, or public contract risk is unresolved.

A CONDITIONAL GO is appropriate when the project is mostly ready but has limited, clearly documented prerequisites. A NO-GO is appropriate when unresolved blockers would likely harm users, operators, developers, integrations, maintainers, security, or release reliability.

## Non-applicable guidance

If release concepts do not apply to the repository, provide a readiness assessment for the nearest equivalent, such as major run readiness, internal adoption readiness, or handoff readiness.

## Section 9 handoff

If the recommendation is GO or CONDITIONAL GO and the user explicitly approves performing the release, proceed to `09-release-execution.md`. Do not begin release execution automatically or without that approval. If the recommendation is NO-GO, do not proceed to Section 9.

## Exit gate

The run is complete only when all are true (MUST):

- [ ] `final-bug-security-audit.md` written; final validation run and recorded in `10-validation-results.md`.
- [ ] Eight-persona sign-off completed in `persona-review.md` and the report.
- [ ] TODO/backlog reconciliation, guiding-principles assessment, self-documenting assessment, and cold-start orientation verdict finalized.
- [ ] Live-surface / data-integrity gate applied to the GO/CONDITIONAL GO/NO-GO recommendation.
- [ ] Pending-plans / staged-prompts gate applied: any in-scope pending IPD or staged prompt (or status/location mismatch) is loudly WARNED in the Go/No-Go and summary and blocks a clean GO; absence stated explicitly.
- [ ] `11-push-plan.md` and restart assessment (with loop guard) recorded.
- [ ] `12-final-response.md` saved per `templates/final-response.md` (both tables + all sections) and presented to the user.
- [ ] Per-phase report written; checkpoint recorded and committed.
