# Release Review Runbook Manifest

This directory contains a modular, executable repository review runbook for use with Google Antigravity or other modern coding agents.

---

## How to Use

To run the repository review, the agent must sequentially read and execute the instructions under the `release-review/` directory:

1. Start by reading [README.md](file:///home/gfariello/VC/pubrun/release-review/README.md) and [00-run-protocol.md](file:///home/gfariello/VC/pubrun/release-review/00-run-protocol.md) to understand the operating guidelines, unique ID rules, and checkpoints.
2. Proceed section by section, starting with [01-current-state.md](file:///home/gfariello/VC/pubrun/release-review/01-current-state.md).
3. Do not proceed to the implementation section ([07-implementation.md](file:///home/gfariello/VC/pubrun/release-review/07-implementation.md)) until all preceding sections have been completed and the consolidated implementation plan is saved under the run directory.
4. Stop and request explicit user approval before executing any post-Go release steps ([09-release-execution.md](file:///home/gfariello/VC/pubrun/release-review/09-release-execution.md)).

---

## Files

| File | Purpose |
|---|---|
| `README.md` | Main orchestrator and entry point for the review workflow. |
| `00-run-protocol.md` | Global operating protocol, safety rules, unique ID rules, artifacts, commit/push policies, and reporting requirements. |
| `01-current-state.md` | Repository inventory, current-state assessment, public contract discovery, drift analysis, and early deprecation signals. |
| `02-quality-security-edge-cases.md` | Bugs, correctness, security, privacy, error handling, resource handling, reliability, and edge-case audit. |
| `03-tests-regression.md` | Test coverage, regression protection, fixtures, CI test behavior, and missing critical tests. |
| `04-docs-specs-examples.md` | Documentation, specification, examples, README, help text, and behavior-documentation alignment. |
| `05-feature-usability-maintainability.md` | Feature completeness, usability, developer experience, operator experience, maintainability, and stale-code impact. |
| `06-compatibility-packaging-release.md` | Compatibility, packaging, build, CI, deployment, versioning, changelog, migration, and release artifacts. |
| `07-implementation.md` | Consolidated implementation plan and execution of safe, significant-value fixes. |
| `08-final-ship-review.md` | Final release readiness assessment, post-implementation bug/security sanity audit, validation reconciliation, final report, push plan, and user-approval gating. |
| `09-release-execution.md` | Post-Go release execution checklist (commit/push, CI validation, package build hook validation, git tagging, and PyPI publishing). |

---

## Expected Run Artifacts

The agent creates and maintains all review artifacts under the designated run directory:
```text
repository-review/<RUN_ID>/
  00-run-metadata.md
  01-repository-inventory.md
  02-execution-plan.md
  03-findings-register.csv
  04-action-register.csv
  05-decisions.md
  06-commands.md
  07-commits.md
  08-checkpoints.md
  09-implementation-plan.md
  10-validation-results.md
  11-push-plan.md
  12-final-response.md
  deprecation-candidates.md
  ci-assessment.md
  schema-validation.md
  final-bug-security-audit.md
  section-summaries/
    01-current-state.md
    02-quality-security-edge-cases.md
    03-tests-regression.md
    04-docs-specs-examples.md
    05-feature-usability-maintainability.md
    06-compatibility-packaging-release.md
    07-implementation.md
    08-final-ship-review.md
```

`repository-review/` should be ignored by Git. The review artifacts are for local accountability and should not be committed unless the user explicitly asks.
