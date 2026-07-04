# 06 Commands

| # | Command | Purpose | Result |
|---|---|---|---|
| 1 | git rev-parse/status/log/remote | Baseline | main @ 4b34802; clean; 1 ahead of origin; remote fariello/ocman |
| 2 | git log v1.0.3..HEAD | Identify delta | 3 product commits (280cfc8, 428aaf7, 2cfd3d2) + docs/plan commits |
| 3 | git show --stat b5b902c | Check framework update | tooling only (agent-workflows 20260704-01); no product code |
| 4 | PYTHONPATH=. pytest | Baseline test state | 91 passed, 2 skipped |
| 5 | grep __version__ / TODO markers | Version sources + backlog | 1.0.3 in ocman.py/pyproject/ocman_tui fallback; no TODO/FIXME in product |
| 6 | git diff --stat v1.0.3..HEAD | Delta size | +979/-127 across ocman.py, ocman_tui, tests, docs |

Working dir: /home/gfariello/VC/ocman. No secrets in output.

## Section 2
| # | Command | Purpose | Result |
|---|---|---|---|
| 7 | scan_secrets.py --repo . --format json --out .../secrets-scan.json | Mandatory secret scan (tree+history) | 1582 candidates (all FPs: entropy IDs/hashes/timestamps/test data) |
| 8 | gitleaks detect --no-banner --redact | Mature scanner cross-check | 156 commits scanned, NO LEAKS FOUND |

## Section 9 (release execution)
| # | Command | Purpose | Result |
|---|---|---|---|
| 9 | git push origin main | Push release commit | 38f42c2 on origin/main |
| 10 | gh run watch 28719980194 | Verify CI | success (full matrix) |
| 11 | python -m build; twine check | Build+validate artifacts | ocman-1.0.4 whl+sdist PASSED |
| 12 | git tag -a v1.0.4; git push origin v1.0.4 | Tag release | b44c0cc -> 38f42c2, on remote |
| 13 | gh release create v1.0.4 + upload | GitHub release | published + artifacts attached |
| 14 | twine upload | PyPI publish | NOT run — no credentials; handed off |
