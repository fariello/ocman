# Release Review Runbook (Antigravity Edition)

Treat this file as the controlling instruction for this repository review. Keep working until you have completed the required run artifacts, committed appropriate local changes, performed final validation, assessed whether to restart the review, made a push/no-push decision, and produced the final response in the required table-first format.

This runbook is designed specifically for Gemini-powered Antigravity agents operating in the repository workspace.

---

## Primary Objective

Perform a robust repository and code review that improves release readiness while minimizing the risk of unintended damage.

- **Maximize**: Correctness, security, privacy, tests, documentation accuracy, compatibility, packaging, CI readiness, maintainability, clear traceability, and clear final reporting.
- **Minimize**: Speculative changes, formatting churn, broad refactors, public contract breakage, unjustified deletion, remote side effects, secret exposure, and instruction drift.

---

## Tooling and Agent Behavior Guidelines

As an Antigravity agent, you must execute the review using the standard tools at your disposal:
1. **File Reading & Editing**: Use `view_file` to inspect code and configs. Use `replace_file_content` or `multi_replace_file_content` to make surgical modifications.
2. **Commands**: Propose commands using `run_command` to execute tests, linters, builds, and git queries.
3. **Workspace Paths**: Ensure all work remains inside the repository workspace. Do not write or execute files outside it.

---

## Required Execution Order & Expected Outcomes

Read and follow `00-run-protocol.md` first. Then execute the section files sequentially. Do not proceed to a section until the preceding section's artifact generation and verification are complete.

### Step 1: Run Setup & Baseline
- **Instructions**: Follow [01-current-state.md](file:///home/gfariello/VC/pubrun/release-review/01-current-state.md).
- **Execution**: Check git status, current branch, HEAD commit hash, remotes, and verify that the working tree is clean. Generate a run ID in the format `YYYYMMDD-HHMMSS`.
- **Expected Outputs**:
  - Create run directory: `repository-review/<RUN_ID>/`
  - Create baseline artifacts:
    - `00-run-metadata.md`
    - `01-repository-inventory.md`
    - `02-execution-plan.md`
    - `03-findings-register.csv` (initialized)
    - `04-action-register.csv` (initialized)
    - `05-decisions.md` (initialized)
    - `06-commands.md` (initialized)
    - `07-commits.md` (initialized)
    - `08-checkpoints.md` (initialized)
  - Add `repository-review/` to `.gitignore`.

### Step 2: Quality, Security, and Edge Cases Audit
- **Instructions**: Follow [02-quality-security-edge-cases.md](file:///home/gfariello/VC/pubrun/release-review/02-quality-security-edge-cases.md).
- **Execution**: Inspect imports, file handling, path manipulation, subprocess execution, credential usage, error handling, and memory/resource usage.
- **Expected Outputs**:
  - Create/update: `repository-review/<RUN_ID>/final-bug-security-audit.md` (initialized)
  - Record findings in the register (`03-findings-register.csv`).

### Step 3: Tests, Coverage, and Regression Audit
- **Instructions**: Follow [03-tests-regression.md](file:///home/gfariello/VC/pubrun/release-review/03-tests-regression.md).
- **Execution**: Check for missing test suites, run tests locally, verify coverage configurations, and look for flaky or disabled tests.
- **Expected Outputs**:
  - Record test gaps or coverage actions in the findings and action registers.

### Step 4: Documentation, Specifications, and Examples Audit
- **Instructions**: Follow [04-docs-specs-examples.md](file:///home/gfariello/VC/pubrun/release-review/04-docs-specs-examples.md).
- **Execution**: Check README correctness, verify installation/usage commands, check JOSS/CFF metadata files, check changelog correctness, and test example scripts.
- **Expected Outputs**:
  - Record any docs issues or outdated command instructions in findings.

### Step 5: Feature Usability and Maintainability Audit
- **Instructions**: Follow [05-feature-usability-maintainability.md](file:///home/gfariello/VC/pubrun/release-review/05-feature-usability-maintainability.md).
- **Execution**: Inspect CLI interfaces, argument parsing, interactive modes, help screens, error reporting formatting, and overall code legibility/organization.
- **Expected Outputs**:
  - Record usability/maintainability findings in the register.

### Step 6: Compatibility, Packaging, and CI Audit
- **Instructions**: Follow [06-compatibility-packaging-release.md](file:///home/gfariello/VC/pubrun/release-review/06-compatibility-packaging-release.md).
- **Execution**: Check Python version compatibility, packaging configurations (e.g. `pyproject.toml`, build hooks), dependencies (pinning and versions), and GitHub Actions workflows.
- **Expected Outputs**:
  - Create: `repository-review/<RUN_ID>/ci-assessment.md`
  - Create: `repository-review/<RUN_ID>/deprecation-candidates.md`
  - Create: `repository-review/<RUN_ID>/schema-validation.md`

### Step 7: Implementation Planning & Execution
- **Instructions**: Follow [07-implementation.md](file:///home/gfariello/VC/pubrun/release-review/07-implementation.md).
- **Execution**: 
  1. Synthesize all findings from Sections 1-6.
  2. Create the consolidated implementation plan: `repository-review/<RUN_ID>/09-implementation-plan.md`.
  3. **DO NOT start making edits** until the plan is created.
  4. Perform surgical, atomic code changes in batches. Verify each batch locally with pytest or linting. Make clean local git commits referencing findings/actions.
- **Expected Outputs**:
  - Populate implementation plan `09-implementation-plan.md`.
  - Create local git commits for verified changes. Update `07-commits.md`.

### Step 8: Final Ship Review & User Gate Approval
- **Instructions**: Follow [08-final-ship-review.md](file:///home/gfariello/VC/pubrun/release-review/08-final-ship-review.md).
- **Execution**: Run the full validation suite, perform a post-implementation bug/security sanity audit, and compile the final report.
- **Expected Outputs**:
  - Finalize: `repository-review/<RUN_ID>/10-validation-results.md`
  - Finalize: `repository-review/<RUN_ID>/11-push-plan.md`
  - Write final report: `repository-review/<RUN_ID>/12-final-response.md` (MUST begin with Completed Actions and Unaddressed Findings tables).
  - **MANDATORY USER GATE**: Present the final report and explicitly ask the user for a **GO** or **CONDITIONAL GO** approval. **DO NOT push to origin or proceed to Section 9 until approval is received.**

### Step 9: Post-Go Release Execution
- **Instructions**: Follow [09-release-execution.md](file:///home/gfariello/VC/pubrun/release-review/09-release-execution.md).
- **Execution**: Push code, verify remote CI, build final distribution packages, verify embedded commit metadata in built artifacts, tag the release with an annotated tag, run twine check, and hand off PyPI publishing to the user (manual upload).
- **Expected Outputs**:
  - Code pushed to `origin/main`.
  - Passing remote CI run.
  - Built distribution packages with baked git HEAD commit hash.
  - Annotated tag pushed to remote.
  - Distribution files handed off to the user for manual PyPI publication.

---

## Local Progress Tracking

Use the following artifacts in your App Data directory `/brain/` folder for live progress visibility:
- **`task.md`**: Live checklist of all tasks and subtasks using markdown checkboxes (e.g. `- [x]`). Keep this updated.
- **`walkthrough.md`**: Summary of concrete changes made, validations run, and output results.

The authoritative run record remains under `repository-review/<RUN_ID>/`. Reconcile your `task.md` checklist with the run registers before producing the final report.
