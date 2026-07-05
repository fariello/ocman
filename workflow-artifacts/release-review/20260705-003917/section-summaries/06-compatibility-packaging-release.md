# Per-Phase Report

## Section
- Section: 6 — Compatibility, packaging, CI, release
- Run ID: 20260705-003917
- Status: complete

## Personas applied
- Operator/stakeholder (8): install/first-run path, version discipline, sdist contents.
- Software engineer (5): backward-compatibility of the delta, CI adequacy.

## What I did
- Reviewed `pyproject.toml`: hatchling; wheel force-includes `ocman.py` + packages `ocman_tui`;
  `requires-python >=3.10`; deps textual/rich/pysqlite3-binary(linux). Console script `ocman = ocman:main`.
- Confirmed the delta is **fully backward-compatible**: no flags removed/renamed (`git diff` shows no `-...
  add_argument`), `.ocbox` `export_version` unchanged (2.0), new config keys additive with defaults, history
  format back-compat. → semver **patch** (1.0.5) is appropriate.
- Found packaging issue P2: the `sdist` exclude still lists the old `repository-review/` name, so `.agents/`
  (996K) + `workflow-artifacts/` (3.0M) could bundle into the PyPI sdist. Wheel is unaffected.
- Confirmed version discipline R2: 1.0.4 is tagged + on PyPI; CHANGELOG `[Unreleased]` must be finalized and
  the version bumped before any re-publish.
- Wrote `ci-assessment.md` (CI adequate; optional build+secret-scan gate deferred) and `schema-validation.md`
  (no serialized-format drift; only the D1 docs-vs-config drift).

## Why I did it
1.0.4 is already published, so the single hard release gate is: bump the version and finalize the changelog.
The sdist cruft (P2) is a cheap, safe packaging hygiene fix. Backward-compat analysis justifies a patch bump.

## What I considered but did NOT do (mandatory)

| Considered item | Why not done | Recommended next step |
|---|---|---|
| Bumping the version now | Version choice is the user's; this run stops before Section 9 | User picks 1.0.5 (recommended) / 1.1.0; bump in S7 or at S9 |
| Adding build/secret-scan CI gates | Optional; adds maintenance for a single-maintainer tool; tests + local scan already gate | Defer (S6-CI1) |
| Adding `tests/` to sdist exclude | Shipping tests in sdist is common/benign; focus P2 on the ~4MB framework cruft | Optional |
| Building the sdist to verify contents | `python -m build` not run to avoid creating dist artifacts mid-review; inferred from hatchling default + config | Verify at S7/S9 build |

## Key findings

| ID | Type | Severity | Remediation Risk | Title | Status | Next step |
|---|---|---|---|---|---|---|
| 20260705-003917-S6-P2 | P | Medium | Low | sdist may ship ~4MB `.agents/`+`workflow-artifacts/` | identified | Fix exclude in S7 |
| 20260705-003917-S6-R2 | R | High | Low | Must bump version + finalize CHANGELOG before publish | identified | Bump S7; publish S9 |
| 20260705-003917-S6-CI1 | CI | Low | Medium | CI is tests-only (no lint/build/secret gate) | identified | Defer (optional) |

## Actions created or updated
Planned for S7: P2 (fix sdist exclude), R2 (bump version + finalize CHANGELOG — pending user version choice).

## Deferrals (Fix Bar)
S6-CI1 deferred (Medium remediation risk: CI maintenance surface; not release-blocking). Effort is not the
reason — the deferral is the added standing complexity for a single-maintainer tool where tests already gate.

## Guiding-principles / self-documenting notes
Honest-documentation: finalizing the CHANGELOG version heading at release keeps the change record honest.

## TODO / backlog items touched
None.

## Non-applicable checks
No deployment/containers/migrations (local single-user tool). No server/network release surface.

## Decisions and assumptions
Target version deferred to user (1.0.5 recommended — patch, since fully backward-compatible). This run does
NOT bump or publish.

## Validation or commands
`git diff v1.0.4..HEAD` public-contract check (no removed flags); pyproject/CI reads; du of framework dirs.

## Handoff to next section
implementation-plan.md consolidates the Section 7 fix set: D1/D2/D3/D4/U1/U2 (docs+prompt), T1 (test), P2
(sdist exclude), and R2 version-bump prep (CHANGELOG finalize; actual bump pending user version choice).
