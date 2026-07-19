# Implementation plan (Section 7)

Findings from Sections 1-6 are minimal (the project was reviewed change-by-change this
session). Two actions, both Low remediation risk, non-behavioral:

| Action | Source finding | Change | Files | RR | Validation |
|--------|----------------|--------|-------|----|------------|
| A1 | S1-REL1 | Bump version 1.1.0 -> 1.2.0 in pyproject.toml and ocman/cli.py:208; cut CHANGELOG `[Unreleased]` -> `## [1.2.0] - 2026-07-19`. | pyproject.toml, ocman/cli.py, CHANGELOG.md | Low | `ocman -V` shows 1.2.0; CHANGELOG has a [1.2.0] heading; full suite green |
| A2 | S2-S1 | Baseline the 6 confirmed-false-positive gitleaks fingerprints (synthetic AWS-key test fixtures) in `.gitleaksignore`. | .gitleaksignore | Low | `gitleaks detect` exits clean (0 leaks) |
| A3 | S1-REL1 | (Verify) rebuild the wheel as 1.2.0 locally (non-publishing) to confirm packaging after the bump. | (none) | Low | wheel builds as ocman-1.2.0 |

No B/MEM/LIVE/GP/KD/SCH findings to fix. No deprecation removals. No deferred findings
(nothing cleared the Medium-High deferral bar; everything found is fixed).

Order: A1 (bump + CHANGELOG cut) -> A2 (gitleaks baseline) -> re-run full suite -> A3
(wheel rebuild verify) -> commit.
