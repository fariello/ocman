# 07 Implementation of Safe, Valuable Fixes

## Context contract

- **Read:** `00-run-protocol.md`, `fix-decision-policy.md`, this file, all section summaries and registers from Sections 1-6, `deprecation-candidates.md`, `ci-assessment.md`, `schema-validation.md`. MUST re-open the actual source files cited by High/`LIVE`/`MEM` findings.
- **Produce:** `implementation-plan.md`, the actual fixes (code/tests/docs/`KD` docs), updated `TODO.md`, register/commit/validation updates; per-phase report `section-summaries/07-implementation.md`.
- **Done when:** the Exit gate at the bottom of this file is satisfied.
- **Continuity:** keep this section continuous with Section 8; do not run it in an isolated fresh context that discards the implementation evidence.

## Purpose

Create a consolidated implementation plan from Sections 1 through 6, then implement safe, meaningful, significant-value fixes.

This is the primary change-making section. It should favor useful release hardening over minimalism, but it must avoid churn, speculative work, broad refactors, and unsafe changes.

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

Read the findings register, action register, all section summaries from Sections 1 through 6, `deprecation-candidates.md`, `ci-assessment.md`, `schema-validation.md`, decisions, validation results, and current Git status.

### Re-ground in the evidence before fixing (MUST for High/`LIVE`/`MEM`)

A register entry is a summary the audit wrote, not the lived reading of the code. Before implementing a fix for any High, `LIVE`, or `MEM` finding, **re-open the actual source files cited by that finding** and confirm the problem and the intended fix against the real code, not against the register text. This is mandatory whether the run is continuous or phase-isolated; in a phase-isolated run (fresh context) it is the only thing that restores real grounding, and in a continuous run it guards against drift across a long transcript. Record in `06-commands.md` (or the per-phase report) which files you re-opened. For lower-severity findings, re-open the source when the register lacks enough detail to fix safely.

## Required implementation plan

Before editing tracked project files, create `workflow-artifacts/release-review/<RUN_ID>/implementation-plan.md` (this is the consolidated plan; do not confuse it with `02-execution-plan.md`, the lightweight early plan, or with Section 9 release execution).

The implementation plan must include scope summary, non-goals, change batches, unique implementation action IDs, source finding IDs, files likely to change, risk level, public behavior change assessment, required tests, required artifact updates, validation method, local commit grouping, deferred findings, blocked findings, deprecated-code decisions, and CI decisions.

Do not start implementation until the plan exists.

## Selection criteria: apply the Fix Bar

Selection is governed by the Fix Bar defined in `00-run-protocol.md`. **Fix every finding by default.** Do not skip a fix because it is small, low-severity, or because it costs effort, time, or tokens. The only question is whether there is a strong enough reason NOT to fix it.

> FIX the finding unless the *Remediation Risk* of fixing it is Medium-High or higher (risk that the fix itself harms complexity, usability, security, or functionality, now or in the future). When unsure, prefer to fix and note the uncertainty.

For every finding, record its Remediation Risk (Low / Medium / Medium-High / High) on the action in the register:

- **Low or Medium Remediation Risk: implement now.** This includes bugs, nits, wording/polish, missing-but-required capabilities, usability/self-documenting gaps, and guiding-principles fixes.
- **Medium-High or High Remediation Risk: defer or mark wont-do**, but only with an explicit recorded justification naming which axis (complexity, usability, security, functionality) and why. Where possible, do the safe part now and defer only the risky remainder. Never silently drop a finding.
- **Over-scope findings:** the "fix" is to recommend removing or deferring the over-scoped feature/abstraction/dependency. This is usually low Remediation Risk, so do it.

Severity (Blocker / High / Medium / Low) is recorded for reporting only; it does not decide whether to fix. A Low/cosmetic finding is fixed by default; a High finding is deferred only if its *cure* clears the Medium-High Remediation-Risk bar (the `LIVE`/High data-integrity class below is never silently deferred regardless).

Legitimate high-Remediation-Risk reasons to defer include: the fix would add disproportionate architectural complexity (KISS/over-engineering), would degrade usability, would weaken security, would risk breaking current or planned behavior without enough evidence, requires product judgment or unavailable credentials, or requires a large refactor whose breakage risk is real. "It is hard to test" is not by itself a deferral reason; refactor for testability instead.

### Non-deferral threshold for `LIVE`/High data-integrity findings (mandatory)

A finding tagged `LIVE` or rated **High** by the Section 2 live-interaction-surface or memory/resource review (can overwrite/destroy completed/verified/paid-for output or user data; spend real money/quota on skippable work; decide on incompletely-retrieved or truncated input; signal/stop/coordinate the wrong process; block forward progress through a backlog; or exhaust memory/handles in production) **must be fixed in this run, or explicitly escalated to the user - it may NOT be silently deferred to `TODO.md`.** The defer reasons "cannot be validated (hard to test)" and "requires large refactoring" do NOT apply to this class. For each such finding:

1. Implement the fix; extract a testable helper if needed so it CAN be validated ("hard to test" is a prompt to refactor for testability, not to defer).
2. If a fix is genuinely out of scope for the run, surface it to the user in the Section 7 per-phase report AND the final report's "identified but not addressed" table as an explicit **High/`LIVE`, not fixed** item requiring a decision - never only as a `TODO.md` entry.
3. Add a regression test for the fixed behavior.

#### Medium and Low severity findings: fix them too

Under the Fix Bar, Medium- and Low-severity findings (live-surface, memory, usability/self-documenting, guiding-principles, polish, and nits alike) are fixed by default, not deferred. Low severity is not a deferral reason; only Medium-High-or-higher Remediation Risk is. This closes the recurring loophole where cheap, safe correctness/usability fixes were dropped as "not important enough". The active discipline here is the Complexity axis: do not let "it is cheap to add" turn into gold-plating or scope creep. If a fix would add disproportionate complexity, degrade usability, weaken security, or risk breaking behavior, defer it and name the axis; otherwise fix it now. Where a fix turns risky mid-way, stop, do the safe portion, and defer the risky remainder with a recorded reason.

### Self-documenting and guiding-principles fixes

Prefer fixes that make the product teach the user as they go - clearer command/flag/field names, better `--help`/usage output, helpful first-run guidance, actionable error messages, sensible defaults, inline hints - over adding documentation to compensate for an opaque interface. Implement `GP` (guiding-principles) fixes that move the project toward its stated principles; never implement a change that violates them.

### Durable knowledge / cold-start orientation docs (`KD`)

Implement the `KD` findings from Sections 4 and 5 by creating or improving the project's own orientation docs: intent/overview, guiding principles (create if absent), architecture/approach, and the design-decision rationale / decisions log. Under the Fix Bar, creating a missing orientation doc is normally low Remediation Risk and is done by default, not deferred. Respect the project's existing convention (extend an ADR directory or `docs/` tree rather than adding competing files); do not duplicate rationale across files - link instead.

When writing the "why" (intent, goals, rationale, alternatives, trade-offs), recover it from the current conversation as a guarded secondary source per `00-run-protocol.md`: code/tests are authoritative for behavior; verify material claims with the user or mark passages "inferred, needs confirmation" and log the assumption in `05-decisions.md`. Do not commit sensitive or ephemeral transcript content - capture durable conclusions only. If intent is missing and unrecoverable, ask the user a small set of high-value questions (the bounded exception in `00-run-protocol.md`) before finalizing, and if unanswered, commit a clearly-labeled inferred draft and list the open questions in the final report.

### TODO.md update policy

As items from `TODO.md`/backlog are completed, become obsolete, or change status during this run, update `TODO.md` (and related backlog files) so they stay honest. Record the final disposition of every triaged item in `todo-reconciliation.md`. Do not use `TODO.md` as a place to silently park findings this review should have fixed or escalated.

## Allowed actions

Allowed: edit code, add/update tests, update docs/examples/specs/schemas/changelog/release notes, update packaging/build metadata when safe, add/update low-risk CI workflows when justified, mark code/docs deprecated when evidence is strong, remove obsolete code only when evidence is strong and risk is low, and create local commits.

Not allowed without explicit user permission: remote push, publish/deploy/release/upload, rotate credentials, delete user data, rewrite major architecture, change license terms, or remove public APIs/CLI commands/schemas/config fields without compatibility analysis and strong justification.

## Implementation order

Prefer safety/correctness fixes, `LIVE`/memory data-integrity fixes, tests protecting those fixes, edge-case/reliability fixes, self-documenting/usability and guiding-principles fixes, docs/spec/example corrections, packaging/build/release metadata fixes, low-risk CI additions, deprecation markers, then small maintainability fixes that reduce real risk.

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

Update the implementation plan, registers, decisions, commands, commits, checkpoints, validation results, deprecation candidates, CI assessment, `todo-reconciliation.md`, and `guiding-principles-assessment.md`.

Record the Remediation Risk (Low / Medium / Medium-High / High) for every finding acted on or deferred. Every deferred finding must name the Remediation-Risk axis (complexity, usability, security, or functionality) that justifies the deferral.

Create the per-phase report `section-summaries/07-implementation.md` (what was done, why, what was considered but not done) covering implemented scope, intentionally unimplemented scope with its Remediation-Risk justification (including any `LIVE`/High finding escalated rather than fixed), change batches, source finding IDs addressed, self-documenting/usability and guiding-principles fixes made, durable-knowledge / cold-start orientation docs created or improved (`KD`) and any intent passages marked "inferred, needs confirmation", `TODO.md` items completed or re-classified, tests and validations, artifacts updated, local commits, remaining risks, and follow-up work.

## TodoWrite guidance

If TodoWrite is available, create todos for each implementation batch, mark each in progress before editing, mark complete only after validation/register updates/local commit decision, track deferred/blocked items at a high level, and reconcile TodoWrite with the action register before leaving Section 7.

## Judgment guidance

Fix by default; the diff size is not the metric. Apply the Fix Bar: address every finding unless its Remediation Risk is Medium-High or higher. Small precise fixes are preferred, and small does not mean skippable. Guard the Complexity axis so fix-by-default does not become over-engineering or scope creep.

## Non-applicable guidance

If no safe implementation work is found, do not fabricate changes. Record the rationale and proceed to final review.

## Exit gate

Do not proceed to Section 8 until all are true (MUST):

- [ ] `implementation-plan.md` complete; source files for High/`LIVE`/`MEM` findings were re-opened before fixing.
- [ ] Fix Bar applied: every finding fixed unless its Remediation Risk is Medium-High+ (each deferral names the axis); no finding silently dropped.
- [ ] Every `LIVE`/High data-integrity finding fixed or explicitly escalated to the user (never silently TODO'd).
- [ ] Medium/Low severity findings fixed by default; self-documenting and `GP` fixes applied.
- [ ] Durable-knowledge / cold-start `KD` docs created or improved by default; intent verified or clearly marked "inferred, needs confirmation".
- [ ] `TODO.md` updated to stay honest; `todo-reconciliation.md` finalized for this run.
- [ ] Validation run and recorded where possible; relevant artifacts synchronized.
- [ ] Local commits (including run artifacts) made or explained; actions + Remediation Risk reconciled.
- [ ] Per-phase report written; checkpoint recorded and committed.
