# Release Review Runbook

Treat this file as the controlling instruction for this repository review. Keep working until you have completed the required run artifacts, committed appropriate local changes, performed final validation, assessed whether to restart the review, made a push/no-push decision, and produced the final response in the required table-first format.

This runbook is intended for OpenCode or another modern coding agent operating inside a repository. It is designed for serious pre-release or pre-major-run review and hardening.

## OpenCode project commands

After installation (via `install-workflows.py` at the agent-workflows repo root, which copies the workflows from the source directory and generates the command shims), OpenCode or Claude Code can invoke the generated command shims:

```text
/release-review
```

Runs the full workflow, including audit, implementation, validation, final report, and push/no-push decision.

```text
/release-review-plan
```

Runs the audit and planning phases only. It completes Sections 1 through 6, creates the consolidated implementation plan, and stops before Section 7 implementation.

The command wrappers are convenience entry points. `release-review/README.md` remains the controlling instruction.

## Invocation

From the repository root, execute:

```text
Read and execute release-review/README.md
```

Do not require the user to run each section manually. Execute the full sequence autonomously unless a safety blocker prevents progress.

## Primary objective

Perform a robust repository and code review that improves release readiness while minimizing the risk of unintended damage.

The subject is the **target project**, not this framework. Exclude `release-review/` (the runbook) and `workflow-artifacts/` (run records) from the review scope, and never modify `release-review/` during a run; see the review scope exclusions in `00-run-protocol.md`. (You still create and commit `workflow-artifacts/release-review/<RUN_ID>/` as the run's output.)

Maximize correctness, security, privacy, memory/resource safety, tests, documentation accuracy, schema validation, compatibility, packaging, CI readiness, maintainability, clear traceability, and clear final reporting. A central goal is to make the released project as **intuitive and self-documenting** as reasonably possible, so users can learn it as they go without reading a manual or taking a course.

A further central goal is **durable project knowledge for cold-start handoff**: a competent engineer or an LLM with zero prior context should be able to pick up the project and understand its intent, goals, philosophy, architecture, approach, and the rationale behind significant decisions - from the project's own tracked documentation. This review establishes and maintains that knowledge (creating missing intent/architecture/decision docs by default under the Fix Bar), mining the current conversation for intent as a guarded secondary source. See `00-run-protocol.md` ("Durable project knowledge and LLM cold-start orientation").

Minimize speculative changes, formatting churn, broad refactors, public contract breakage, unjustified deletion, remote side effects, secret exposure, and instruction drift.

## Review through eight expert personas

Conduct every audit section and the final review while deliberately reasoning from each of these perspectives in turn (defined in detail in `00-run-protocol.md`):

1. QA/QC engineer.
2. Testing and regression-testing expert.
3. UI/UX expert engineer.
4. Systems and software architect (abstraction, extensibility, simplification, elegant design, future-proofing without bloat).
5. Software engineer.
6. Sophisticated power user.
7. Complete novice with no domain knowledge.
8. Stakeholder in the project's goals and outcomes.

A finding obvious to one persona is often invisible to another. Hunt long and hard, from every angle, for bugs, memory/resource issues, security issues, usability issues, documentation issues, and anything that would make the released project harder to learn, trust, or maintain.

## Cross-cutting requirements

This review must also, on every run:

- **Reconcile any `TODO.md`/backlog/roadmap and `TODO`/`FIXME` code markers** against the release: triage each item, fix or escalate the ones that should not ship, update `TODO.md` to stay honest, and record the triage in `todo-reconciliation.md`.
- **Loudly warn about pending agent plans and staged prompts**: discover any prepared-but-unexecuted plans/IPDs (`.agents/plans/pending/`, IPDs marked pending) or queued prompt files, and surface in-scope pending items as a prominent WARNING in the Go/No-Go and summary. Such items block a clean GO until the user decides on them; the review never auto-executes them.
- **Honor the repository's guiding principles** (`GUIDING_PRINCIPLES.md` or equivalent) as a binding contract, or apply the universal fallback principles in `00-run-protocol.md`; record per-principle adherence in `guiding-principles-assessment.md`.
- **Hold the self-documenting / learn-as-you-go bar**: file and, where safe, fix anything that forces a user to read the manual to do a basic task.
- **Ensure durable cold-start knowledge exists**: establish/maintain intent, philosophy, architecture, and design-decision rationale in the project's own docs (respecting its existing convention), so a no-context LLM or engineer can orient. Recover intent from the current conversation as a guarded secondary source; verify material claims with the user or mark them as assumptions.
- **Treat memory/resource and live-interaction-surface correctness as first-class** per `00-run-protocol.md`.
- **Produce a mandatory per-phase report** for each section covering what was done, why, and what was considered but deliberately not done.

## Optional controlled parallel audit mode

After Section 1 establishes the repository baseline, the agent may use controlled parallel read-only audit lanes for parts of Sections 2 through 6 when the repository is large, unfamiliar, or has multiple independent surfaces such as code, tests, docs, schemas, packaging, and CI.

Parallelism is optional. Use it only when it improves review quality.

Rules:

1. Section 1 remains serial and is performed by the main agent.
2. Parallel audit lanes are read-only and honor the review scope exclusions in `00-run-protocol.md` (do not audit `release-review/` or `workflow-artifacts/`).
3. Parallel audit lanes must not edit tracked files, update official registers directly, commit, push, or make final release decisions.
4. Each lane should produce an audit-lane report using `templates/audit-lane-report.md`.
5. The main agent owns synthesis, deduplication, severity decisions, official run-specific IDs, finding/action registers, implementation planning, local commits, validation, final report, and push/no-push decision.
6. Section 7 implementation remains serial.
7. Section 8 final review remains serial.
8. Section 9 release execution remains serial.

## Required execution order

Read and follow `00-run-protocol.md` first (and `fix-decision-policy.md`, the fix-decision policy it references; `reference.md` holds look-up tables you consult on demand, not up front). Then execute the section files in order:

1. `01-current-state.md`
2. `02-quality-security-edge-cases.md`
3. `03-tests-regression.md`
4. `04-docs-specs-examples.md`
5. `05-feature-usability-maintainability.md`
6. `06-compatibility-packaging-release.md`
7. `07-implementation.md`
8. `08-final-ship-review.md`
9. `09-release-execution.md` (only after a GO/CONDITIONAL GO and explicit user approval to release)

Do not begin Section 7 implementation before completing Sections 1 through 6 and creating `workflow-artifacts/release-review/<RUN_ID>/implementation-plan.md`.

Do not begin Section 9 release execution until Section 8 produces a GO or CONDITIONAL GO and the user has explicitly approved performing the release.

## Per-section execution loop (mandatory)

This is a long, multi-step run. Do not work from memory of a section file you read earlier. For each section in order, run this exact loop:

1. **Open and read the full section file** (`0N-*.md`) at the start of that section. Re-read it even if you think you remember it; the section file is the authority for that phase, not your recollection.
2. **Set the section's TodoWrite item to in_progress** (if TodoWrite is available).
3. **Do the section's work**, applying the shared rules in `00-run-protocol.md` (personas, Fix Bar, memory/live-surface, self-documenting bar, TODO triage) as that section directs.
4. **Update the registers and artifacts** named in the section's "Required outputs".
5. **Write the section's per-phase report** to `section-summaries/<NN>-<short-name>.md` using `templates/per-phase-report.md` (what was done, why, what was considered but not done).
6. **Record the section checkpoint** in `08-checkpoints.md` and reconcile it against the registers.
7. **Commit** the section's tracked changes and run artifacts (see commit policy), then mark the TodoWrite item complete.
8. **Only then proceed** to the next section.

Do not batch multiple sections before writing reports or committing. If you discover you skipped a step for a prior section, stop and complete it before continuing.

Each section file opens with a **context contract** (read these / produce these / done when) and ends with an **exit gate** (a checklist of MUST items). Treat the exit gate as the definition of "done" for that section. `00-run-protocol.md` defines the MUST vs SHOULD tiers, the context-assembly ordering (front = rules + contract; middle = reference + registers; end = active section + exit gate), the model-capability expectation, and an optional phase-isolated execution mode for fast/small models or very large repositories (Sections 7 and 8 stay continuous).

## Run setup

At the start:

1. Confirm you are operating from the repository root.
2. Determine whether the repository uses Git.
3. Record the initial branch, head commit, remotes, and working tree status.
4. Create a run ID using local time in this format: `YYYYMMDD-HHMMSS`.
5. Create `workflow-artifacts/release-review/<RUN_ID>/`.
6. Ensure `workflow-artifacts/` is NOT git-ignored; remove any stale `workflow-artifacts/` ignore line so the run artifacts can be tracked as committed deliverables.
7. Create the required run artifacts defined in `00-run-protocol.md`.
8. Create `workflow-artifacts/release-review/<RUN_ID>/02-execution-plan.md` after enough initial inspection to understand the project type.
9. Use TodoWrite if running in OpenCode and the tool is available.

If the repository is not a Git repository, continue the review and record local commit and push steps as not applicable.

## TodoWrite use

If TodoWrite is available, use it for live progress visibility. Create todos for run setup, each review section, implementation planning, each coherent implementation batch, final validation, and the final report.

Do not create a TodoWrite item for every file inspected or every tiny edit. The authoritative record is always `workflow-artifacts/release-review/<RUN_ID>/`, not TodoWrite.

## Local commits and remote pushes

Use local commits for meaningful tracked repository changes when safe and possible. Commit only files changed by this run. Do not accidentally include unrelated pre-existing user changes. The `workflow-artifacts/release-review/<RUN_ID>/` artifacts are committed deliverables by default; commit them with the run (keep them local only if the user explicitly asks for local-only artifacts).

Apply the Fix Bar (see `00-run-protocol.md`): fix findings by default and defer only when the Remediation Risk of the fix itself is Medium-High or higher; severity is for reporting, not for deciding; never silently drop a finding.

Remote pushes are prohibited until the final stage and only allowed if the user has explicitly permitted pushing. If permission is absent, produce a push/no-push recommendation in `workflow-artifacts/release-review/<RUN_ID>/11-push-plan.md` and in the final report.

## Final response requirement

The final response must be saved to:

```text
workflow-artifacts/release-review/<RUN_ID>/12-final-response.md
```

Then present the same content to the user.

The final response must begin with:

1. A table of completed actions.
2. A table of identified but not addressed items.

The second table must include audit findings that were identified but intentionally not implemented, not only attempted actions that were left incomplete.

## Completion standard

The run is not complete until Sections 1 through 8 have been completed or explicitly marked not applicable with rationale, every section has a per-phase report, findings and actions have unique run-specific IDs, the `TODO.md`/backlog reconciliation and guiding-principles adherence assessment are recorded, the eight-persona review is reflected in findings, completed and unaddressed items are reconciled, validation results are recorded, local commits are recorded or explained, CI and deprecated-code assessments are recorded, push/no-push and restart decisions are recorded, and the final response is saved and presented. Section 9 is completed only if release execution was explicitly approved and performed.
