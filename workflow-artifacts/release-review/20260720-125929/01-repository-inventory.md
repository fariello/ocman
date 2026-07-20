# 01 Repository Inventory

## Current project state summary

`ocman` is a single-user command-line + TUI tool to administer, maintain, and repair a local
OpenCode agentic environment: its SQLite database, sessions, projects, and config. Version
under review: **1.2.0** (`pyproject.toml:7`, `ocman/cli.py:208` both = "1.2.0"). Not yet
tagged/released; CHANGELOG `[1.2.0]` section is the pending release notes.

This is a RE-REVIEW. The prior run (`20260719-140024`) issued GO for v1.2.0. Since then, 16
commits landed (plus this run's setup commit): cross-platform CI hardening (macOS/Windows
test portability), one real product fix, a dependency-floor bump, DECISIONS.md creation, and
a temporary CI diagnostic setting. See "Recent changes / delta since prior GO" below.

## Project type and scope

- Python package (hatchling build). `requires-python >= 3.10`.
- Two importable packages: `ocman` (CLI core, `ocman/cli.py` ~16.4k lines + a thin
  `ocman/__init__.py` that delegates via `__getattr__`) and `ocman_tui` (Textual TUI:
  `app.py` ~2.3k lines + `widgets/`).
- Console script: `ocman = "ocman:main"` (`pyproject.toml:29`).
- Ships `scripts/migrate_recovery_names.py` via force-include.

## Intended outcome / audience

- Outcome: let an OpenCode user safely inspect, clean, repair, move, export/import, and
  reclaim space in their local OpenCode state, without hand-editing SQLite.
- Audience: OpenCode end users (novice to power user) on a personal machine. Single-user,
  local, no elevated privileges expected (see DECISIONS.md run-elevated entry).

## Guiding-principles document

- None found (`GUIDING_PRINCIPLES.md`/`PRINCIPLES.md`/AGENTS.md principles section all absent).
  The **universal fallback principles** from `00-run-protocol.md` apply (intuitive/
  self-documenting; general-case/configurable; KISS; honest docs). Recorded in
  `guiding-principles-assessment.md`.

## Durable-knowledge docs (cold-start)

- `README.md` (44 KB): intent, usage, command reference.
- `ARCHITECTURE.md` (21 KB): structure and approach.
- `DECISIONS.md` (17.6 KB): ADR-style decision log, created + backfilled this cycle
  (`3037abd`, `cf6267e`). Covers the v1.1->v1.2 cross-cutting decisions incl. the ones from
  the CI-hardening work reviewed here.
- `CHANGELOG.md` (40 KB): Keep-a-Changelog style; `[1.2.0]` populated.
- Convention: decision rationale = DECISIONS.md + executed-IPD trail (`.agents/plans/executed/`).

## Backlog / TODO sources

- `TODO.md`: informal backlog. Current content documents SHIPPED items (chunk-large-sessions,
  spend) and explicit deferrals (forked/shared-spend de-dup). No open release blockers.
- In-code `TODO`/`FIXME`/`HACK`/`XXX`: 2 matches, both FALSE POSITIVES (`ses_XXXX` example
  string at `cli.py:5372`, `[XXXXX]` docstring at `cli.py:13070`).

## Pending agent plans / staged prompts

- `.agents/plans/pending/`: only `README.md` + `.gitkeep`. **No pending IPDs.**
- `.agents/prompts/pending/`: absent (no staged prompts).
- `not-executed/`, `superseded/`: only READMEs.
- Status/location check: 4 executed plans matched a pending-ish regex, but all have
  `Status: EXECUTED`; the matches were workflow-history prose. **No status/location mismatch.**

## Public contract summary

- CLI surface: `ocman` subcommands (list/ls, session recover/compact/export, import, move,
  spend, doctor, reclaim, db cleanup, config, tui, etc.). `main()` wrapper -> `_run_main()`.
- TUI: 9 tabs (sidebar/sessions, storage, spend, running, database, models, config).
- Library: `import ocman` re-exports via `__getattr__` delegation to `ocman.cli`.

## Test & validation inventory

- pytest suite under `tests/` (test_ocman, test_tui, test_export_import, test_move,
  test_file_tools, test_recovery*, test_config*, test_migrate_recovery_names, test_core,
  test_compacted_project_prompt, test_perf).
- Command: `PYTHONPATH=. pytest -q`. Local Linux baseline (py3.14): 408 passed, 2 skipped
  (2 = perf benchmarks gated on OCMAN_BENCHMARK=1).
- conftest: autouse running-OpenCode guard neutralizer; `real_process_detection` marker =
  Linux-only skip off-Linux; cross-platform helpers `abs_path`/`norm_real`/`make_symlink`
  + capability probe `SYMLINKS_SUPPORTED`.

## Build / packaging / CI / release inventory

- `pyproject.toml`: hatchling; deps textual>=3, rich>=13, vistab>=1.3.0, pysqlite3-binary
  (linux only). dev extra: pytest, anyio.
- CI: `.github/workflows/ci.yml` matrix ubuntu/macos/windows x py3.10-3.14; **`fail-fast:
  false` set TEMPORARILY (diagnostic)** — must be restored to default (see finding S1-CI1).
  `.github/workflows/secret-scan.yml`: gitleaks full-history.
- `.gitleaksignore`: baselines 6 synthetic AWS-key test fixtures by fingerprint (from prior run).
- CI status at HEAD `bebb520`: all 15 cells GREEN (verified via `gh run watch`, exit 0).

## Recent changes / delta since prior GO (2554395..HEAD)

- `4cfcd18` fix(import): macOS firmlink project-import rebase (real product fix) + regression test.
- `bebb520`,`3fd934b`,`32d8559`,`4adfa26`,`febda16`,`ef04c01`: cross-platform TEST portability
  (symlink capability probe, abs_path/norm_real, TUI modal-mount timing, macOS realpath).
- `58399fe` fix(deps): vistab>=1.3.0 floor.
- `3037abd`,`215b321`,`cf6267e`: DECISIONS.md create + backfill + references.
- `ef04c01`: CI fail-fast:false (diagnostic).
- Net product-code change vs prior GO: essentially ONE function (`extract_and_import_project`
  rebase) + dependency floor + version already bumped. The rest is tests/docs/CI.

## Drift / inconsistencies (with IDs)

- 20260720-125929-S1-CI1 (finding): `ci.yml` `fail-fast: false` is a TEMPORARY diagnostic
  setting with an in-file comment saying to restore it once green. The matrix IS green now, so
  it should be restored. See findings register.

## Deprecation candidates

- None new. (See `deprecation-candidates.md`.)

## Recommended next actions

- Restore `fail-fast: true` (S1-CI1) in Section 7.
- Verify the delta's product fix + tests hold (Sections 2-3).
- Confirm CHANGELOG/docs reflect the delta (Section 4/6).
- Re-confirm release readiness for v1.2.0 (Section 8), then Section 9 on GO + approval.

## Out-of-scope directories (present, not reviewed as project)

- `.agents/workflows/` (this framework + siblings), `.opencode/`, `.claude/` command shims.
- `workflow-artifacts/` (run records). This run writes its own under `release-review/20260720-125929/`.
