# Release Review Runbook

Treat this file as the controlling instruction for this repository review. Keep working until you have completed the required run artifacts, committed appropriate local changes, performed final validation, assessed whether to restart the review, made a push/no-push decision, and produced the final response in the required table-first format.

This runbook is intended for OpenCode or another modern coding agent operating inside a repository. It is designed for serious pre-release or pre-major-run review and hardening.

## OpenCode project commands

If this zip is expanded into the repository root, OpenCode can invoke the included command wrappers:

```text
/release-review
```

Runs the full workflow, including audit, implementation, validation, final report, and push/no-push decision.

```text
/release-review-plan
```

Runs the audit and planning phases only. It completes Sections 1 through 6, creates the consolidated implementation plan, and stops before Section 7 implementation.

## Installing or activating OpenCode commands

The zip includes optional OpenCode project commands:

```text
.opencode/commands/release-review.md
.opencode/commands/release-review-plan.md
```

OpenCode discovers per-project Markdown commands from `.opencode/commands/` when OpenCode is run from that project. The Markdown file name becomes the slash command name. Therefore:

- `.opencode/commands/release-review.md` becomes `/release-review`.
- `.opencode/commands/release-review-plan.md` becomes `/release-review-plan`.

To install the commands for a repository:

1. Download `release-review.zip`.
2. From the repository root, unzip it so these paths exist at the repository root:

   ```text
   release-review/README.md
   .opencode/commands/release-review.md
   .opencode/commands/release-review-plan.md
   ```

3. Start or restart OpenCode from the repository root.
4. In the OpenCode TUI, type `/release-review` to run the full workflow, or `/release-review-plan` to run the audit and planning workflow only.

The command wrappers are convenience entry points. `release-review/README.md` remains the controlling instruction.

If the slash commands do not appear:

1. Confirm the files are under `.opencode/commands/`, not `.opencode/command/` and not inside a nested extracted folder.
2. Confirm OpenCode was started from the repository root or from a child directory inside the same Git repository.
3. Restart OpenCode so it reloads project command files.
4. Use the manual fallback prompt:

   ```text
   Read and execute release-review/README.md
   ```

For user-wide installation instead of per-project installation, copy the command Markdown files to `~/.config/opencode/commands/`. Keep the `release-review/` directory in each repository where the command should operate, because the command wrappers reference `@release-review/README.md`.

## Invocation

From the repository root, execute:

```text
Read and execute release-review/README.md
```

Do not require the user to run each section manually. Execute the full sequence autonomously unless a safety blocker prevents progress.

## Primary objective

Perform a robust repository and code review that improves release readiness while minimizing the risk of unintended damage.

Maximize correctness, security, privacy, tests, documentation accuracy, compatibility, packaging, CI readiness, maintainability, clear traceability, and clear final reporting.

Minimize speculative changes, formatting churn, broad refactors, public contract breakage, unjustified deletion, remote side effects, secret exposure, and instruction drift.

## Optional controlled parallel audit mode

After Section 1 establishes the repository baseline, the agent may use controlled parallel read-only audit lanes for parts of Sections 2 through 6 when the repository is large, unfamiliar, or has multiple independent surfaces such as code, tests, docs, schemas, packaging, and CI.

Parallelism is optional. Use it only when it improves review quality.

Rules:

1. Section 1 remains serial and is performed by the main agent.
2. Parallel audit lanes are read-only.
3. Parallel audit lanes must not edit tracked files, update official registers directly, commit, push, or make final release decisions.
4. Each lane should produce an audit-lane report using `templates/audit-lane-report.md`.
5. The main agent owns synthesis, deduplication, severity decisions, official run-specific IDs, finding/action registers, implementation planning, local commits, validation, final report, and push/no-push decision.
6. Section 7 implementation remains serial.
7. Section 8 final review remains serial.

## Required execution order

Read and follow `00-run-protocol.md` first. Then execute the section files in order:

1. `01-current-state.md`
2. `02-quality-security-edge-cases.md`
3. `03-tests-regression.md`
4. `04-docs-specs-examples.md`
5. `05-feature-usability-maintainability.md`
6. `06-compatibility-packaging-release.md`
7. `07-implementation.md`
8. `08-final-ship-review.md`

Do not begin Section 7 implementation before completing Sections 1 through 6 and creating `repository-review/<RUN_ID>/09-implementation-plan.md`.

## Run setup

At the start:

1. Confirm you are operating from the repository root.
2. Determine whether the repository uses Git.
3. Record the initial branch, head commit, remotes, and working tree status.
4. Create a run ID using local time in this format: `YYYYMMDD-HHMMSS`.
5. Create `repository-review/<RUN_ID>/`.
6. Add `repository-review/` to `.gitignore` if it is not already ignored.
7. Create the required run artifacts defined in `00-run-protocol.md`.
8. Create `repository-review/<RUN_ID>/02-execution-plan.md` after enough initial inspection to understand the project type.
9. Use TodoWrite if running in OpenCode and the tool is available.

If the repository is not a Git repository, continue the review and record local commit and push steps as not applicable.

## TodoWrite use

If TodoWrite is available, use it for live progress visibility. Create todos for run setup, each review section, implementation planning, each coherent implementation batch, final validation, and the final report.

Do not create a TodoWrite item for every file inspected or every tiny edit. The authoritative record is always `repository-review/<RUN_ID>/`, not TodoWrite.

## Local commits and remote pushes

Use local commits for meaningful tracked repository changes when safe and possible. Commit only files changed by this run. Do not accidentally include unrelated pre-existing user changes. Do not commit `repository-review/` artifacts unless the user explicitly asks.

Remote pushes are prohibited until the final stage and only allowed if the user has explicitly permitted pushing. If permission is absent, produce a push/no-push recommendation in `repository-review/<RUN_ID>/11-push-plan.md` and in the final report.

## Final response requirement

The final response must be saved to:

```text
repository-review/<RUN_ID>/12-final-response.md
```

Then present the same content to the user.

The final response must begin with:

1. A table of completed actions.
2. A table of identified but not addressed items.

The second table must include audit findings that were identified but intentionally not implemented, not only attempted actions that were left incomplete.

## Completion standard

The run is not complete until all eight sections have been completed or explicitly marked not applicable with rationale, findings and actions have unique run-specific IDs, completed and unaddressed items are reconciled, validation results are recorded, local commits are recorded or explained, CI and deprecated-code assessments are recorded, push/no-push and restart decisions are recorded, and the final response is saved and presented.
