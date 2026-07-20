# 00 Run Metadata

- Run ID: 20260720-125929
- Workflow: release-review (controlling instruction: `.agents/workflows/release-review/README.md`)
- Agent/model: OpenCode, its_direct/pt3-claude-opus-4.8-1m-us
- Repository path: /home/gfariello/VC/ocman
- Uses Git: yes
- Initial branch: main
- Initial HEAD: bebb5209b133136658e287cbcf43d84ba1e50295
- Remotes: origin git@github.com:fariello/ocman.git (fetch/push)
- Branch sync at start: in sync with origin/main (0 ahead / 0 behind)
- Initial working tree status: clean
- Run timestamp (local): 2026-07-20 12:59:29

## Purpose of this run

Full pre-release review for **v1.2.0**. This is a re-review requested after a large
batch of cross-platform CI-hardening changes landed since the prior release-review run
(`20260719-140024`, which issued GO for v1.2.0). The intervening work:

- macOS firmlink project-import rebase bug fix (`4cfcd18`) + OS-agnostic regression test.
- Windows/macOS test portability fixes (symlink guard capability probe, abs_path/norm_real
  helpers, TUI modal-mount timing) across `4adfa26`, `febda16`, `ef04c01`, `3fd934b`, `bebb520`.
- `vistab>=1.3.0` dependency floor (`58399fe`).
- `DECISIONS.md` created and backfilled (`3037abd`, `cf6267e`).
- CI `fail-fast: false` set TEMPORARILY for diagnosis (must be restored).

CI matrix at HEAD (`bebb520`): all 15 cells GREEN (ubuntu/macos/windows x py3.10-3.14).

## Environment summary

- Python venv: /home/gfariello/venv/p3.14/ (Python 3.14). Also /usr/bin/python3.12 present.
- Test command: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`
- Baseline (local Linux) prior to this run: 408 passed, 2 skipped (2 skips = perf benchmarks
  gated on OCMAN_BENCHMARK=1).

## Scope exclusions (per 00-run-protocol.md)

- `.agents/workflows/` (this framework + siblings) and its wrappers: OUT of review scope.
- `workflow-artifacts/`: run records, OUT of review scope (this run still writes its own).

## Prior run reference

- `workflow-artifacts/release-review/20260719-140024/` — GO for v1.2.0; findings S1-REL1
  (version bump, done) and S2-S1 (gitleaks baseline of 6 synthetic test fixtures, done).
