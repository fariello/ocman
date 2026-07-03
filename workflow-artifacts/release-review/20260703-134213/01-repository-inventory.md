# 01 Repository Inventory

## Project state summary
`ocman` (OpenCode Manager) v1.0.3 — a CLI + Textual TUI administration suite for the OpenCode
agentic ecosystem. It browses/recovers/compacts opencode SQLite sessions and performs DB admin
(cleanup, orphan pruning, vacuum), backup/restore, session move/export/import, and LLM-based
compaction. Published on PyPI as `ocman`.

## Project type and scope
- Python 3.10+ application; single-file CLI (`ocman.py`, ~8040 lines) + `ocman_tui/` Textual package.
- Public contract: the `ocman` console entry point (CLI flags + positional `info/help/ui/gui`),
  the `.ocbox` export bundle format (schema `export_version: 2.0`), the backup ZIP format, and
  `ocman.toml` config schema.
- Distribution: `pyproject.toml` (hatchling), wheel includes `ocman_tui` package + force-includes `ocman.py`.

## Intended outcome / audience
- **Users:** OpenCode users who need to recover crashed/bloated sessions, migrate/relocate projects,
  export/import sessions, and maintain their opencode SQLite DB.
- **Operators:** same individuals administering their own opencode install (single-user, local).
- **Stakeholders:** the maintainer (Greg Fariello) and the OpenCode community.

## Guiding-principles document
- **None found** as a dedicated file (`GUIDING_PRINCIPLES.md`, `PRINCIPLES.md`, etc. absent; `AGENTS.md`
  points only to `.agents/workflows/index.md`). The universal fallback principles from `00-run-protocol.md`
  apply (intuitive/self-documenting, general-case/configurable-over-hardcoded, KISS, honest documentation).
  See `guiding-principles-assessment.md`.

## Backlog / TODO sources
- No `TODO.md`, `BACKLOG.md`, `ROADMAP.md`, `KNOWN_ISSUES.md`.
- No `TODO`/`FIXME`/`HACK`/`XXX` markers in `ocman.py` (only `XXXX` placeholder text in docstrings) or TUI.
- Result: no backlog to reconcile beyond this review's own findings. Recorded in `todo-reconciliation.md`.

## Public contract summary
- CLI: flat argparse (`parse_args`), natural-language preprocessing (`preprocess_argv`), positional
  `command` in {info, help, ui, gui}, `-V/--version`.
- Data contracts: `.ocbox` bundle (ZIP: meta.json export_version 2.0, db_data/<table>.jsonl,
  session_diffs/<sid>.json), backup ZIP (db family + config + history + storage diffs), `ocman.toml`.

## Artifact summary
- `ocman.py` (CLI, 8040 lines), `ocman_tui/{__init__,app,core}.py` + `widgets/{database,sidebar,models}.py`.
- `orsession/`, `agents/`, `prompts/` present; `orsession` referenced optionally by ocman.py.
- `README.md`, `CHANGELOG.md`, `LICENSE` (BSD-3-Clause), `pyproject.toml`, `.github/workflows/ci.yml`.

## Test and validation inventory
- `tests/`: test_ocman.py (631), test_export_import.py (297), test_move.py (265),
  test_config_backup_restore.py (206), test_tui.py (350), test_core.py (127).
- Validation command: `PYTHONPATH=. pytest`. **Result on this run: 56 passed in ~12s.**
- CI: `.github/workflows/ci.yml` — matrix (ubuntu/macos/windows × py3.10-3.14), `pip install -e .[dev]`, `pytest`.

## Documentation inventory
- `README.md` (243 lines): capabilities, quickstart, install, TUI tabs, full argument reference, config
  template, backup/restore internals, test instructions.
- `CHANGELOG.md`: entries up to **[1.0.2]** only — **DRIFT: no [1.0.3] entry** though version is 1.0.3.
- No `ARCHITECTURE.md`/`DESIGN.md`/`DECISIONS.md`/ADRs — durable cold-start knowledge is thin (see `cold-start-orientation.md`).

## Build/packaging/CI/deployment/release inventory
- Build: hatchling. Deps: textual>=3.0, rich>=13.0, pysqlite3-binary (linux only). Dev: pytest, anyio.
- CI present (tests only; no lint/type-check; no publish). Deployment: n/a (local tool). Release: PyPI (manual).

## Recent changes (git log)
- e6c5943 install agent-workflows (this framework) — out of review scope.
- 34dcd65 log prefix [INFO]; verbose import progress. 6bc12f8 export progress. 5ae133a Windows paths + JSONL streaming.
- 88c6b6d cross-platform + CI matrix. bc85e4d import security validation + v1.0.2. 26da227 move + export/import.

## Drift / inconsistencies (IDs)
- `20260703-134213-S1-A1` CHANGELOG.md missing [1.0.3] entry (version bumped to 1.0.3 in code/pyproject). DRIFT.
- `20260703-134213-S1-A2` README install says `git clone https://github.com/fariello/ocman.git` but the
  actual remote is `github.com:fariello/opencode-recover.git`. Possible clone-URL drift (needs confirmation).
- `20260703-134213-S1-A3` Two independent hardcoded `__version__` strings: `ocman.py:191` and
  `ocman_tui/__init__.py:5` — must be manually kept in sync (release risk).
- `20260703-134213-S1-A4` README mentions TUI package as source of `orsession` history log path in prose;
  package is now `ocman_tui`. Minor naming residue ("Orsession" in TUI docstrings/class `OrsessionApp`).

## Key ambiguities (IDs)
- `20260703-134213-S1-Q1` Is the intended public clone/repo URL `ocman` or `opencode-recover`? (README vs remote).
- `20260703-134213-S1-Q2` Is 1.0.3 already released to PyPI, or pending? Affects CHANGELOG expectations.

## Visible release-quality concerns (seeded; detailed in later sections)
- Zip-Slip in `cli_restore` `zipf.extractall` (ocman.py:6786, 6923) — security (Section 2).
- Connection leak on error path in `bundle_session_data` 2nd connection (ocman.py:~5456) — MEM (Section 2).
- TUI `call_from_thread` crash on Move/Export/Import modals (app.py) — LIVE bug, fix in-run (already fixed).

## Deprecation candidates
- `orsession/` package and `agents/`, `prompts/` dirs: unclear if still part of the shipped product or
  legacy. Recorded in `deprecation-candidates.md` for assessment.

## Recommended next actions
- Proceed to Section 2 (quality/security/edge/MEM/LIVE). Trace Zip-Slip and connection-leak paths in code.

## Out-of-scope directories (per 00-run-protocol.md)
- `.agents/workflows/` (this framework), `.opencode/`, `.claude/` command shims, `workflow-artifacts/` (run records).
  Present but NOT reviewed as project code.
