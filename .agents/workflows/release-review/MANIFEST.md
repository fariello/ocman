# Release Review Runbook Manifest

This directory contains a modular, executable repository review runbook for use with OpenCode or another modern coding agent.

The framework is installed under `.agents/workflows/release-review/` (alongside the sibling `plan-review/`). The installer (`install-workflows.py`, at the agent-workflows repo root) also generates per-tool slash-command shims under `.opencode/commands/` and `.claude/commands/`, and adds a one-line pointer to `AGENTS.md`. See `.agents/workflows/index.md` for the workflow manifest.

## How to use

With OpenCode or Claude Code after installing, run:

```text
/release-review
```

For audit and implementation planning only, run:

```text
/release-review-plan
```

These commands are convenience shims. The controlling file remains this directory's `README.md`.

From the repository root, in any agent, tell it:

```text
Read and execute .agents/workflows/release-review/README.md
```

`README.md` is the controlling instruction. The agent should read `00-run-protocol.md`, then execute sections `01` through `08` in order. Section `09` (release execution) runs only after a GO/CONDITIONAL GO and explicit user approval.

The review is conducted through eight expert personas (QA/QC, testing/regression, UI/UX, architect, software engineer, power user, novice, stakeholder) and, on every run, reconciles any `TODO.md`/backlog against the release, honors the repository's guiding principles, holds a self-documenting / learn-as-you-go bar, treats memory/resource and live-interaction-surface correctness as first-class, and produces a mandatory per-phase report for each section.

## Slash commands (generated shims)

The installer generates these from the `.agents/workflows/index.md` manifest, into
both `.opencode/commands/` (OpenCode) and `.claude/commands/` (Claude Code). Each shim
just says "read and execute" the workflow body and accepts optional `$ARGUMENTS`.

| Command | Invokes | Purpose |
|---|---|---|
| `/release-review` | `release-review/README.md` | Full audit, implementation, validation, final report, and push/release decision. |
| `/release-review-plan` | `release-review/README.md` (planning-only) | Audit and consolidated implementation plan, stopping before implementation. |
| `/plan-review` | `plan-review/plan-review.md` | Pre-execution plan reviewer (reviews and revises a proposed plan before any code is written). |

The sibling `assess/` workflow adds a family of single-concern commands (e.g.
`/assess-security`, `/assess-performance`) that each assess one concern deeply and write
an IPD into the project's pending-plans directory for human approval (they do not
auto-execute). See `.agents/workflows/index.md` for the full, authoritative and current
command list; it is the source of truth, so this file does not enumerate the assess
commands.

## Files

| File | Purpose |
|---|---|
| `README.md` | Main orchestrator and single entry point for the full review. |
| `MANIFEST.md` | This file: what each release-review file is and how to invoke the workflow. |
| `00-run-protocol.md` | Global operating protocol, safety rules, ID rules, the Fix Bar, artifacts, TodoWrite use, commit and push policy, and final reporting requirements. |
| `fix-decision-policy.md` | Canonical fix-decision policy: fix by default; defer only when the Remediation Risk of the fix itself is Medium-High or higher. |
| `reference.md` | On-demand look-up material kept out of the always-read core: ID type codes, ID examples, schema/data-contract types, CI checks, register statuses. |
| `01-current-state.md` | Repository inventory, current-state assessment, public contract discovery, drift analysis, and early deprecation signals. |
| `02-quality-security-edge-cases.md` | Bugs, correctness, security, privacy, error handling, resource handling, reliability, and edge-case audit. |
| `03-tests-regression.md` | Test coverage, regression protection, fixtures, CI test behavior, and missing critical tests. |
| `04-docs-specs-examples.md` | Documentation, specification, examples, README, help text, behavior-documentation alignment, and durable cold-start knowledge (intent, architecture, decision rationale). |
| `05-feature-usability-maintainability.md` | Feature completeness, usability, developer/operator experience, maintainability, guiding-principles adherence, cold-start orientation, and stale-code impact. |
| `06-compatibility-packaging-release.md` | Compatibility, packaging, build, CI, deployment, versioning, changelog, migration, and release artifacts. |
| `07-implementation.md` | Consolidated implementation plan and safe, significant-value fixes, including mandatory handling of `LIVE`/High data-integrity findings and `TODO.md` updates. |
| `08-final-ship-review.md` | Final release readiness assessment, final bug/security/memory sanity audit, eight-persona sign-off, TODO/backlog and guiding-principles reconciliation, validation reconciliation, final report, push/no-push decision, and restart assessment. |
| `09-release-execution.md` | Project-agnostic post-GO release execution: push, CI verification, artifact build, annotated tagging, publish/deploy (credential-gated), and post-release smoke test. Runs only after a GO/CONDITIONAL GO and explicit user approval. |
| `templates/execution-plan.md` | Template for the early run execution plan. |
| `templates/implementation-plan.md` | Template for the implementation plan created after audit sections and before fixes. |
| `templates/audit-lane-report.md` | Template for optional controlled parallel read-only audit lanes used after the Section 1 baseline. |
| `templates/schema-validation.md` | Template for recording discovered schemas, schema validation commands, example validation, compatibility concerns, and schema drift. |
| `templates/final-bug-security-audit.md` | Template for the final post-implementation bug/security/memory sanity audit. |
| `templates/section-summary.md` | Legacy generic per-section summary template (superseded by `per-phase-report.md`). |
| `templates/per-phase-report.md` | Mandatory per-phase report template: what was done, why, and what was considered but not done. |
| `templates/todo-reconciliation.md` | Template for triaging every `TODO.md`/backlog/roadmap and in-code `TODO`/`FIXME` item against the release. |
| `templates/guiding-principles-assessment.md` | Template for per-principle adherence assessment against the repo's principles doc or the universal fallback. |
| `templates/cold-start-orientation.md` | Template for the cold-start orientation assessment: can a no-context engineer/LLM understand the project's intent, philosophy, architecture, and decision rationale from its own docs. |
| `templates/persona-review.md` | Template for the eight-persona review notes and final sign-off. |
| `templates/final-response.md` | Template for the saved final report and table-first final answer. |
| `templates/finding-register.csv` | CSV header template for durable finding tracking. |
| `templates/action-register.csv` | CSV header template for durable action tracking. |

## Expected run artifacts

The agent should create and maintain:

```text
workflow-artifacts/release-review/<RUN_ID>/
  00-run-metadata.md
  01-repository-inventory.md
  02-execution-plan.md
  03-findings-register.csv
  04-action-register.csv
  05-decisions.md
  06-commands.md
  07-commits.md
  08-checkpoints.md
  10-validation-results.md
  11-push-plan.md
  12-final-response.md
  implementation-plan.md     (consolidated plan, created after Sections 1-6; not Section 9)
  deprecation-candidates.md
  ci-assessment.md
  schema-validation.md
  final-bug-security-audit.md
  todo-reconciliation.md
  guiding-principles-assessment.md
  cold-start-orientation.md
  persona-review.md
  release-execution-log.md   (only if Section 9 is performed)
  section-summaries/         (mandatory per-phase reports for Sections 1-9)
  audit-lanes/               (optional parallel read-only audit lane reports)
```

The `workflow-artifacts/release-review/<RUN_ID>/` artifacts are committed deliverables of the review by default: the per-phase reports, registers, plans, and final report should be tracked and committed with the run so the project keeps a durable, auditable record. Do not git-ignore `workflow-artifacts/`. Keep artifacts local only if the user explicitly asks for local-only artifacts on a given run.

The review applies the Fix Bar (see `00-run-protocol.md`): findings are fixed by default and deferred only when the Remediation Risk of the fix itself is Medium-High or higher (complexity, usability, security, or functionality). Severity is for reporting; Remediation Risk is for deciding.
