# Release Review - ocman 1.1.0 (run 20260707-004045)

## Completed actions

| Unique ID | Description of what was done | Files changed | Commit | Validation |
|---|---|---|---|---|
| S6-C1 / S6-A1 | Ship `scripts/migrate_recovery_names.py` in the wheel (force-include) so `pip install` users have the documented upgrade tool | pyproject.toml | 3e24c76 | wheel rebuilt (script present); twine check PASSED |
| S2-E1 / S2-A1 | `cli_filter` rejects an oversized input by `st_size` BEFORE `read_text` (respects `--force`); test asserts read not called on rejection | ocman.py, tests/test_file_tools.py | 3e24c76 | pytest 174 passed |
| S5-U1 / S5-A1 | `--force` help text now notes it also overrides the filter/--compact size cap | ocman.py | 3e24c76 | `ocman --help` shows updated text |
| S4-D1 / S4-A1 | README NOTE pointing upgraders to `scripts/migrate_recovery_names.py` (`--dry-run` first) | README.md | 3e24c76 | manual read |
| S3-T1 / S3-A1 | `test_tui.py` pins TUI/CLI naming parity (canonical full-sid name), honoring `default_out_dir`, and the compacted-copy call | tests/test_tui.py | 3e24c76 | pytest 174 passed (+2) |

## Identified but not addressed

| Unique ID | Description of what was not done | Remediation Risk + axis | Reason | Recommended next step |
|---|---|---|---|---|
| CI-1 | Add a gitleaks secret-scan step to CI | Low (complexity) - not deferred for risk | Left advisory: it is an infra/workflow change and the user holds release timing; not a release blocker | Add a gitleaks job to `.github/workflows/ci.yml` when convenient |

(No audit finding was deferred for remediation-risk reasons: all five findings were Low RR and were
fixed in-run. CI-1 is a recommendation this review chose not to commit as infra, not a deferred
finding.)

## Summary of changes
This review independently re-verified the ocman 1.1.0 delta (the `filter` command, canonical
recovery filenames + migration script, egress guards, collision safety, TUI parity, prose) that
had already been assessed, plan-reviewed, and executed earlier this session. It found five small
gaps, all Low remediation risk, and fixed them all: the wheel now ships the migration script; the
filter size cap is enforced before reading; `--force` help and README are complete; and TUI naming
parity is pinned by tests.

## Fix Bar summary
5 findings, all Remediation Risk Low -> all fixed by default; 0 deferred. No High/BLOCKER/LIVE/MEM.

## Validations run
- `PYTHONPATH=. pytest`: 172 -> **174 passed, 2 skipped** after fixes.
- `python -m build --wheel` + inspection: migration script now in the wheel. `twine check`: PASSED.
- `ocman --help`: `--force` text verified.
- gitleaks (tree + 229 commits): **0 leaks**; built-in scanner candidates triaged as false positives.

## CI assessment
Existing CI (ubuntu/macos/windows x Python 3.10-3.14 pytest) is adequate and mirrors validation.
Advisory: add a gitleaks step (CI-1). Not changed in this run.

## Schema validation
No `.ocbox`/backup-ZIP format change in 1.1.0. Recovery filename scheme reads legacy + canonical
(back-compat, tested). New config keys default safely (old ocman.toml loads). No schema drift.

## Deprecated-code
None. `copy_restart_to_project_prompts` legacy key intentionally retained + documented.

## Final bug/security/memory sanity audit
No unsafe change introduced. 0 secrets. Secret-scan egress guard redacts values. No leaks in the
delta; size cap bounds both read and egress. Release-safe.

## TODO / backlog reconciliation
`TODO.md`: one item (`ocman spend`), explicitly informal/future -> out-of-scope-for-release, left
tracked. No in-code TODO/FIXME markers.

## Pending plans / staged prompts
**NONE.** `.agents/plans/pending/` is empty; all 1.1.0 IPDs are executed. No release blocker.

## Guiding-principles adherence
All four ARCHITECTURE design principles HELD (intuitive/self-documenting, configurable-over-
hardcoded, KISS, honest documentation).

## Eight-persona sign-off
All eight PASS (see persona-review.md). No persona blocks the release.

## Self-documenting / learn-as-you-go
`--help` shows filter/`--scope`/`--allow-secrets` with examples; README documents the config keys +
the upgrade/migration path (D1 fixed); `--force` help complete (U1 fixed).

## Documentation / artifact updates
README (migration NOTE), `--force` help, and the run record (this directory). CHANGELOG already
carried the 1.1.0 entry incl. the `--compact` behavior-change note.

## Remaining risks
Minimal. Pre-existing static-analysis (LSP) noise (`pysqlite3.connect`, `str|None`, TUI
duck-typing) is cosmetic; the runtime suite is green. Advisory CI-1 remains open (user's call).

## Push / no-push decision
**No push** this run (no permission; user holds pushes/tags). Recommendation: push + tag `v1.1.0` +
build + upload + GitHub release when the user approves (Section 9 not run).

## GO / NO-GO
**GO for ocman 1.1.0.**

## Restart recommendation
**No restart.** Fixes were small and Low-risk; no late architectural discovery; convergence reached.

## Section 9 readiness
Ready on explicit approval: tag `v1.1.0` at the reviewed HEAD, `python -m build`, user uploads to
PyPI, GitHub release marked Latest. Not executed (requires user go-ahead).
