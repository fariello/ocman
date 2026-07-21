# CI Assessment

## Current CI
- `.github/workflows/ci.yml`: `test` matrix ubuntu/macos/windows x py3.10-3.14 (15 cells,
  fail-fast default) + non-gating `coverage` job (pytest --cov + report-only benchmarks). 16 jobs.
- `.github/workflows/secret-scan.yml`: gitleaks full-history (fetch-depth 0). Green.
- Dependency Graph workflow present.

## Published-version check (MANDATORY)
- Registry: PyPI (distribution `ocman`).
- Currently-published latest: **1.2.0** (releases: 1.0.0-1.0.6, 1.1.0, 1.2.0).
- Proposed this release: **1.3.0** (final). VALID bump: 1.3.0 > 1.2.0. No rc was ever published
  (rc1-rc4 are git tags only). PKG check PASSES.

## Build / packaging validation (run this section)
- `python -m build` succeeds: produced ocman-1.3.0rc4.tar.gz + wheel (will be 1.3.0 post-bump).
- `twine check` PASSED for both sdist and wheel (metadata valid).
- Console script `ocman = "ocman:main"` works (prints "ocman 1.3.0rc4").
- New-feature symbols importable via ocman.__getattr__ delegation.

## CI recommendations
- No CI change recommended. The matrix + coverage + secret-scan already cover the release
  surface; the last push (6913d1a) was 16/16 green first try. Adding more would not materially
  improve readiness and risks churn. (S2-S01 gitleaks baseline is a .gitleaksignore edit, not a
  CI-workflow change.)
- NOTE: local full-history gitleaks reports 3 non-baselined hits in a PRIOR run's artifacts
  (S2-S01); CI is currently green because the action's default scan range does not reach them,
  but baselining the 3 fingerprints keeps a future full-history run clean.
