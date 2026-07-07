# 01 Repository Inventory

## Project state summary
- **ocman** (OpenCode Manager) 1.1.0: a single-user, local CLI + Textual TUI to manage opencode
  session data (list/inspect, recover/compact sessions, disk-usage + cleanup/VACUUM, move,
  export/import `.ocbox`, backup/restore, and the new `filter` command).
- Version `1.1.0` (consistent: `ocman.py:__version__`, `pyproject.toml`). License Apache-2.0.
- Entry point: `ocman = "ocman:main"` (console script). Python `>=3.10`.

## Project type / scope
- Single-file stdlib CLI (`ocman.py`, ~9166 lines) + optional Textual TUI (`ocman_tui/`, ~1746
  lines) that reuses CLI logic. One-off migration script `scripts/migrate_recovery_names.py`.
- Audience: developers who use opencode and need to manage/reclaim its SQLite session store.
  Operators = the same single user locally. No network service, no multi-tenant surface.

## Intended outcome / stakeholders
- Goal (per README): actually reclaim opencode DB space (delete orphaned/old rows + on-disk
  session diffs, VACUUM, report reclaimed bytes) and safely recover/compact sessions.
- Stakeholder = the maintainer/author (Gabriele G. R. Fariello) and end users running it locally.

## Guiding-principles doc
- No dedicated `GUIDING_PRINCIPLES.md`. Principles are stated in `ARCHITECTURE.md` "Design
  principles": intuitive/self-documenting, configurable-over-hardcoded, KISS, honest
  documentation. `AGENTS.md` now also carries a prose convention (no em dashes). Universal
  fallback principles also apply. Recorded for the Section 5 per-principle assessment.

## Backlog / TODO sources
- `TODO.md`: 1 item (`ocman spend`), explicitly labeled "Informal backlog ... not yet promoted to
  an IPD". Clearly out-of-scope-for-this-release (a future feature idea, no committed work).
- In-code `TODO`/`FIXME`/`HACK`/`XXX`: none real. The only `XXXX` hits (ocman.py:4079-4133) are
  placeholder tokens in `--help`/`preprocess_argv` example text, not markers.

## Pending agent plans / staged prompts
- `.agents/plans/pending/`: **EMPTY**. All four 1.1.0-related IPDs are in `.agents/plans/executed/`
  (`20260706-compacted-restart-file-tools`, `-security-`, `-edge-cases-`, `-compatibility-`,
  `20260707-assess-prose`), each `Status: EXECUTED`. No staged prompt dir.
- **No pending-plan release blocker.** (Feeds the Section 8 Go/No-Go: clean on this axis.)

## Public contract summary
- CLI flags + the `filter`/`info`/`ui`/`gui` positional commands; `ocman.toml` config keys;
  on-disk recovery artifact names (`YYYYMMDD-HHMM-<sid>.<kind>.md`, new in 1.1.0); `.ocbox`
  export bundle format; backup ZIP format. 1.1.0 adds `filter`, `--allow-secrets`,
  `filter_max_bytes`, `filter_secret_scan`, and the canonical naming scheme (+ migration script).

## Test / validation inventory
- `PYTHONPATH=. pytest` -> **172 passed, 2 skipped** (verified this run). 13 test files incl. the
  1.1.0 additions (`test_file_tools`, `test_recovery_naming`, `test_migrate_recovery_names`).
- CI: `.github/workflows/ci.yml` matrix ubuntu/macos/windows x Python 3.10-3.14 running pytest.

## Documentation inventory
- `README.md` (usage, positioning, Argument Reference, config template), `ARCHITECTURE.md`
  (entry points, design principles, canonical naming, destructive-confirm seam), `CHANGELOG.md`
  (Keep-a-Changelog style, 1.1.0 entry present), `AGENTS.md`, `TODO.md`, `LICENSE`/`NOTICE`/
  `CITATION.cff` (Apache-2.0 set).

## Build / packaging / release
- `pyproject.toml` (version 1.1.0, license Apache-2.0, scripts entry, sdist excludes `.agents/` +
  `workflow-artifacts/` per prior release-review). PyPI: 1.0.6 live (1.0.0-1.0.5 yanked). `v1.1.0`
  not yet tagged (user holding the tag for after this review).

## Recent changes (this session, since v1.0.6)
- 1.1.0: `filter` command + canonical recovery filenames + migration script; egress guards
  (size cap + secret/PII scan) on `filter` and `--compact`; shared collision-safety helper;
  TUI naming/out-dir/compacted-copy parity; prose (em-dash) normalization.

## Drift / inconsistencies
- INV-1 (Low): pre-existing LSP/type-checker noise (`pysqlite3.connect`, `str|None`, TUI
  `NoSelection`/`DummySession`) is cosmetic static-analysis only; suite passes. Not a release
  blocker. Evidence: LSP diagnostics vs. green pytest.

## Deprecation candidates
- None new. (`copy_restart_to_project_prompts` config key name is legacy but intentionally kept
  for back-compat, documented; not a candidate.)

## Out of scope (per protocol)
- `.agents/workflows/` (this framework) and `workflow-artifacts/` (run records) are present but
  NOT reviewed as project code.

## Recommended next actions
- Sections 2-6 focus on the 1.1.0 delta (the shipped result of the executed IPDs), independently
  re-verifying rather than trusting the IPD text; confirm packaging/CHANGELOG/version for release.
