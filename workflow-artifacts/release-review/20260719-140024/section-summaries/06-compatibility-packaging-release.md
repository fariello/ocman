# Section 6 - Compatibility, packaging, CI, release

## What I did
- Built the wheel locally (`python -m build --wheel`): `ocman-1.1.0-py3-none-any.whl` built
  cleanly; contains `ocman/` + `ocman_tui/` + the force-included
  `scripts/migrate_recovery_names.py`; console entry point `ocman = ocman:main`.
- Checked the published PyPI version: latest is 1.1.0, so the proposed 1.2.0 is a valid
  (strictly-greater) bump. Recorded in ci-assessment.md.
- Reviewed CI: ci.yml (matrix ubuntu/macos/windows x py3.10-3.14, `pip install -e .[dev]`,
  pytest) is solid; secret-scan.yml runs gitleaks over full history. No CI change
  recommended (no repo-native linter to wire; a wheel-build job is a future nice-to-have).
- Assessed compatibility: this cycle is additive (parity + tooling) with NO breaking
  changes; the removed `--show-models`/`--list-projects` flags predate v1.1.0. Minor bump.
- Assessed schemas (schema-validation.md): the `--json` envelope, `.ocbox` bundle, and
  `ocman.toml` are stable/unchanged; tested; no drift, no SCH finding.

## Why
- Packaging/version/CI correctness is the gate between "code is good" and "can be shipped";
  the published-version check prevents a version collision, and the wheel build confirms the
  artifact installs with the right entry point.

## What I considered but did NOT do
- Adding a lint/type-check or wheel-build CI job: declined - no repo-native linter exists
  (speculative), and the build is verified locally; not release-blocking.
- Publishing / uploading anything: prohibited outside Section 9 after a GO.
- Filing R/P/O/SCH findings: none warranted. The only packaging-adjacent action is the
  S2-S1 gitleaks baseline (so the secret-scan CI stays green) plus the version bump.
