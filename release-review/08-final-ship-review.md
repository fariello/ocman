# 08 Final Ship Review

## Purpose

Assess whether the current project is ready to ship as a robust, well-written, well-documented, stable, secure, maintainable, feature-complete project for its intended scope.

Be practical but conservative. The goal is not to claim perfection. The goal is to determine whether the project is as close to release-ready as reasonably possible for its intended scope.

---

## Standing Constraints for this Section

- Preserve public behavior unless a change is clearly justified.
- Do not make speculative changes.
- Do not create broad refactors or formatting churn.
- Use run-specific unique IDs for every finding and action.
- Update the finding and action registers before leaving this section.
- Mark non-applicable checks explicitly rather than forcing findings.
- Prefer meaningful fixes, not checklist compliance.
- **REMOTE ACTIONS PROHIBITED**: Do not perform any remote push, tag push, or package publishing in this section.

---

## Required Inputs

Read all run artifacts, current Git status, local commits made during the run, validation results, CI assessment, deprecation candidates, findings and action registers, implementation plan, and Section 7 results.

---

## Allowed Actions

- **Allowed**: Run final local validation commands, inspect final diffs, update final artifacts, make final small cleanup edits if necessary and safe, create a final local commit if tracked files changed, prepare the push/no-push plan, and compile the final report.
- **Strictly Prohibited**: Pushing to a remote branch, pushing tags to origin, uploading to PyPI, or starting a new review run automatically.

---

## Final Ship Review Checklist

Evaluate and verify each of the following:
1. **Purpose and Scope**: Ensure the project is aligned with its target scope.
2. **Feature Completeness**: Confirm all planned outstanding features (e.g. TODO.md items) are fully implemented.
3. **Correctness & Stability**: Verify no new regression bugs exist.
4. **Security & Privacy**: Audit path handling, exception safety, and ensure zero credentials or secrets are exposed in code/logs.
5. **Test Coverage & Regression**: Run the full test suite locally. Verify test coverage is complete and configured properly.
6. **Documentation & Examples**: Confirm README, docstrings, citation metadata (`CITATION.cff`), and CLI help text are up-to-date and accurate.
7. **Packaging & Build**: Check `pyproject.toml` and ensure package builds cleanly locally.

---

## Final Bug/Security Sanity Audit

Before writing the final report, create or update:
```text
repository-review/<RUN_ID>/final-bug-security-audit.md
```
Perform a final post-implementation sanity audit focused on whether changes made during the run introduced or left unresolved material issues.

Review:
1. New or modified code paths.
2. New or modified tests.
3. New or modified configurations, CI, packaging, scripts, schemas, and documentation.
4. Changed file handling, path handling, subprocess use, serialization, and error handling.
5. Unresolved findings or residual risks.

---

## Final Validation Results

Run the repository-native validation commands locally (e.g. test suites, linter checks, schema validations). Record the exact command strings, their results, and logs in:
```text
repository-review/<RUN_ID>/10-validation-results.md
```

---

## Final Schema Validation Check

Before the final report, update:
```text
repository-review/<RUN_ID>/schema-validation.md
```
Confirm:
1. Discovered schemas and serialization formats were assessed.
2. Schema, implementation, documentation, and tests are synchronized.
3. Compatibility risks are evaluated and recorded.

---

## Compile Push Plan

Create or update:
```text
repository-review/<RUN_ID>/11-push-plan.md
```
Include:
- Current branch name.
- Local commits made during the run.
- Working tree status (must be clean).
- Push recommendation and any associated risks.
- **Explicit Push Gating Statement**: Declare that no push is executed until explicit user authorization is given.

---

## Compile Final Report

Save the final report to:
```text
repository-review/<RUN_ID>/12-final-response.md
```
Then present the same content to the user in the chat response.

The final report must begin with these two tables:

### Completed actions

| Unique ID | Description of what was done | Files changed | Commit | Validation |
|---|---|---|---|---|

### Identified but not addressed

| Unique ID | Description of what was not done | Reason | Recommended next step |
|---|---|---|---|

After the two tables, include:
- Summary of changes.
- Tests and validations run.
- CI assessment summary.
- Deprecated-code assessment summary.
- Schema validation summary.
- Documentation and artifact updates.
- Remaining risks.
- Push/no-push decision/plan.
- Final **GO**, **CONDITIONAL GO**, or **NO-GO** recommendation.
- Restart recommendation.

---

## MANDATORY USER GATING CHECKPOINT: GO/NO-GO Approval

> [!CAUTION]
> **STOP AND DO NOT PROCEED TO SECTION 9 (RELEASE EXECUTION).**
> Present the final report and tables to the user in your response. Explicitly ask the user to review the report and approve the release with a **GO** or **CONDITIONAL GO** decision.
> You must pause execution here and wait for the user's response. Do not perform any remote push, tag creation, or PyPI upload until the user explicitly responds with their approval to proceed with the release execution.
