# Repository inventory (Section 1)

## Project identity

- Name: ocman. Purpose (from pyproject/README): "Administer, maintain, and repair your
  OpenCode agentic environment: sessions, database, and config." A CLI + Textual TUI that
  manages the local OpenCode SQLite database, sessions, storage, backups, and recovery.
- Audience: OpenCode power users / operators and a single maintainer; technically comfortable.
- Type: Python package (>=3.10), console script `ocman = "ocman:main"`, hatchling build.

## Structure (project scope)

- `ocman/` - the CLI + all core logic (`cli.py`, ~16.3k lines; `__init__.py` dynamic
  `__getattr__` delegation exposing the CLI symbols).
- `ocman_tui/` - the Textual TUI: `app.py`, `core.py` (re-export shim), `widgets/`
  (`sidebar`, `database`, `models`, `storage`, `spend`, `running`), `css/`.
- `tests/` - `test_ocman.py`, `test_tui.py`, `test_core.py`, `test_perf.py`, plus
  `test_config_backup_restore.py`; `conftest.py`.
- `scripts/migrate_recovery_names.py` (packaged via force-include).
- Docs: `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `AGENTS.md`, `CITATION.cff`,
  `LICENSE` (Apache-2.0), `NOTICE`.
- CI: `.github/workflows/ci.yml`, `.github/workflows/secret-scan.yml`.

## Out of review scope (present but excluded per 00-run-protocol)

- `.agents/workflows/` (the workflow framework itself, incl. release-review/plan-review).
- `workflow-artifacts/` (run records; this run creates its own here).
- Agent tooling wrappers: `.opencode/`, `.claude/`, `.agents/` command shims.

## Guiding principles

- No dedicated GUIDING_PRINCIPLES.md. ARCHITECTURE.md has a "Design principles" / KISS
  section (intuitive/self-documenting, general-case/configurable, KISS, honest docs) that
  matches the universal fallback in 00-run-protocol. AGENTS.md carries the contributor
  contract + prose rule (no em/en dashes; sanctioned "not available" glyph exception).
- Assessment: use ARCHITECTURE.md's principles + the universal fallback (recorded in
  guiding-principles-assessment.md).

## Backlog / TODO sources

- `TODO.md`: an informal backlog. Current content = two SHIPPED notes (chunking, spend)
  plus one explicitly-deferred stretch goal (forked/shared-spend de-duplication). NO
  `must-`/`should-before-release` items.
- In-code TODO/FIXME/HACK/XXX markers: 2 grep hits, both FALSE POSITIVES (`ses_XXXX`
  example text at cli.py:5372; `[XXXXX]` doc glyph at cli.py:13056). No real code markers.

## Pending agent plans / staged prompts

- `.agents/plans/pending/`: NONE (only README). All this cycle's IPDs are in
  `.agents/plans/executed/`. No staged prompts dir. No status/location mismatch found.
- Section-8 pending-plans WARNING: not triggered (nothing pending).

## Public contract

- Console script `ocman` (noun-based subcommands + top-level verbs). JSON output envelope
  `{schema_version, command, <command>: payload}` for `--json` commands (spend, doctor,
  running, list). `.ocbox` bundle format (meta.json + db_data/*.jsonl). Config `ocman.toml`.

## Tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`; last full run: 407 passed,
  2 skipped (the 2 skips = perf benchmarks gated on OCMAN_BENCHMARK=1). Textual TUI tests
  use `run_test()`.

## Recent changes (this release cycle, all committed)

See 00-run-metadata.md context: docs accuracy, extract-on-delete, full TUI parity (5
phases), FU-01 config fix, TUI docs, self-documentation fixes. 40 commits ahead of
origin/main; last tag v1.1.0.

## Drift / release-quality concerns (with IDs)

- 20260719-140024-S1-REL1: version is 1.1.0 in BOTH pyproject.toml and ocman/cli.py:208,
  but 40 feature/fix commits have landed since the v1.1.0 tag. The release needs a version
  bump (proposed 1.2.0, minor: new features, no breaking changes) and a CHANGELOG cut of
  `[Unreleased]` -> `[1.2.0]`. Expected release-prep, handled in Sections 6/7.
- No other drift found in this pass; artifacts (README/ARCHITECTURE/CHANGELOG) were synced
  earlier this cycle.

## Deprecation candidates

- None new. (`--show-models`/`--list-projects` were already removed as user flags; the
  remaining references are historical docstrings/comments, intentional.)

## Recommended next actions

- S6/S7: bump version 1.1.0 -> 1.2.0 (pyproject + cli.py) and cut the CHANGELOG.
- S3: re-run the full suite as the regression gate.
- S6: verify packaging (wheel builds, entry point, deps) and CI config.
