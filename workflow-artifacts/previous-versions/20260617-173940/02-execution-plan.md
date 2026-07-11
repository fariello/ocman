# Execution Plan - 20260617-173940

This execution plan guides the audit and review phases for the `ocman` repository.

## Audit Lanes

### Lane 1: Quality, Security & Edge Cases
- **Target**: `ocman.py` and `orsession/core.py`.
- **Focus**:
  - SQLite transaction safety, exception handling, and connection lifecycle.
  - File I/O safety (path traversal, clean deletion of session diff JSONs, directory traversal).
  - Safe subprocess invocations (any shell command executions).
  - Memory or file-descriptor leaks.

### Lane 2: Tests & Regression
- **Target**: Testing gaps.
- **Focus**:
  - Analyze the total lack of tests in the repository.
  - Propose unit testing setup or test cases for the core CLI logic (e.g., CTE recursive resolver, backup creator, validation).

### Lane 3: Docs, Specs & Examples
- **Target**: `README.md`, `SPEC-orsession.md`, and CLI `--help`.
- **Focus**:
  - Identify documentation drift now that the tool has been renamed from `opencode_recover_session.py` to `ocman` and has advanced database cleaning capabilities (`--clean`, `--clean-orphans`, `--days`, etc.).

### Lane 4: Packaging & Release
- **Target**: `pyproject.toml`.
- **Focus**:
  - Review dependencies (`textual`, `rich`, `pysqlite3-binary`).
  - Review python version compatibility (>= 3.10).
  - Review packaging targets (hatchling wheel build rules).

## Schedule & Milestones
1. **Audit (Sections 1-6)**: Execute serial audits for each lane and record findings in the findings register.
2. **Synthesis (Section 7)**: Combine all findings, assign unique run IDs, and create the implementation plan.
3. **Execution (Section 7)**: Implement changes in safe, validated batches.
4. **Final Review (Section 8)**: Run validation tests, check size reduction, perform final sanity audit, and compile final report.
