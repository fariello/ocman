# CI Assessment


## Section 6 assessment

- CI = `.github/workflows/ci.yml` (test matrix ubuntu/macos/windows x py3.10-3.14) +
  `secret-scan.yml` (gitleaks full-history). Both appropriate and low-risk; neither publishes.
- Current state at bebb520: all 15 test cells GREEN; secret-scan green.
- ACTION (S1-CI1 / S6-CI1): restore `fail-fast: true` (drop the temporary diagnostic override
  + its comment) now that the matrix is green. Low remediation risk. Done in Section 7, then
  re-run CI to confirm steady-state green.
- No new CI checks recommended: linting/type-checking are not part of the repo's native
  validation (adding them would be scope creep for this release); tests+secret-scan+matrix are
  the material gates and are present.

## Published-version check

- PyPI published latest: **1.1.0**. Proposed: **1.2.0**. Valid bump (1.2.0 >= 1.1.0). No PKG finding.

## Section 9 push+verify

- Ref pushed: main -> 039951c (bebb520..039951c). Run: 29764588646.
- Initial: 1 genuine failure (ubuntu 3.12, transient sqlite3 disk I/O error) + 6 cancelled
  (fail-fast:true). Rerun of failed jobs -> ALL 15 GREEN. Fail-fast restore validated.
- Tag v1.2.0 pushed; draft GitHub Release created.
