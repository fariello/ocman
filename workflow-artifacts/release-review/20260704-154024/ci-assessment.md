# CI Assessment (follow-up run)

## Existing CI
`.github/workflows/ci.yml`: matrix (ubuntu/macos/windows × py3.10-3.14); `pip install -e .[dev]` +
`PYTHONPATH: .`; `pytest`. Confirmed this run: the editable install + PYTHONPATH means CI tests the working
tree correctly (unlike a bare local `pytest` against an installed copy — see S3-R1). Safe, no publish steps.

## Delta impact
- No CI change required for the delta; the new tests run under the existing matrix. The opt-in benchmarks
  (`OCMAN_BENCHMARK`) are correctly skipped by default in CI.

## Optional hardening considered (S2-S1)
- **Add gitleaks to CI.** gitleaks is available and ran clean this review. A secret-scan CI step is low risk
  (read-only, no secrets needed, no remote state) and would catch future accidental commits.
  - Decision: **recommend but do not add in this run.** Rationale: it is a nice-to-have hardening, not a
    release blocker for 1.0.4, and adding a CI action + pinning a scanner version is a small scope expansion
    better decided deliberately by the maintainer. Flagged as a follow-up (CI1), not implemented.

## Decision
No CI changes this run. Existing CI is safe and adequate for 1.0.4. gitleaks-in-CI recommended as a future
follow-up (CI1).
