# 01 Repository Inventory

## Project state summary

`ocman` (OpenCode Manager) is a single-user, local CLI + Textual TUI administration suite
for the OpenCode ecosystem: browse/recover/compact opencode sessions in a local SQLite DB,
and manage that DB, its config, and related on-disk state (backup/restore, cleanup,
project/session move, portable export/import, spend accounting, doctor health checkup).

- HEAD: 6913d1a on `main`, clean, in sync with origin.
- Last final release: v1.2.0 (tag + PyPI + GH Release).
- Current version string: **1.3.0rc4** (candidate). CHANGELOG already carries a released
  `[1.3.0] - 2026-07-20` heading with an empty `[Unreleased]`. Promotion to final 1.3.0 is
  the subject of this review.
- 27 commits since v1.2.0 (whole 1.3.0 cycle). Product surface changed:
  `ocman/cli.py` (+863/-... net large), `ocman_tui/widgets/storage.py`, `pyproject.toml`,
  README, CHANGELOG, and tests (test_ocman.py +748, test_tui.py, test_move.py).

## Project type and scope

Python 3.10-3.14 package. Console entry point `ocman = "ocman:main"`. Single large CLI module
`ocman/cli.py` (~17k lines) + `ocman/__init__.py` (dynamic `__getattr__` re-export) + a Textual
TUI package `ocman_tui/`. Deps: textual, rich, vistab>=1.3.0, pysqlite3-binary (linux).

## Intended outcome / audience

Users: individual developers using OpenCode who need to inspect, recover, clean up, move,
back up, and account for their local opencode session database. Operators/stakeholders: the
maintainer (single-user tool, local-only, no server component). Success = safe, reversible,
self-documenting administration of opencode state without data loss.

## Guiding-principles document

No standalone `GUIDING_PRINCIPLES.md`. Principles live in `ARCHITECTURE.md` "Design principles"
(line ~248). Substantive per-principle adherence is Section 5's job; universal fallback
principles (00-run-protocol) also apply. Recorded location for `guiding-principles-assessment.md`.

## Durable-knowledge docs (cold-start)

Present and maintained: `README.md` (intent + full command reference), `ARCHITECTURE.md`
(components, entry points, design principles), `DECISIONS.md` (ADR log), `CHANGELOG.md`
(Keep-a-Changelog), plus 58 executed IPDs under `.agents/plans/executed/`. Strong cold-start
posture already; Section 4/8 verify currency.

## Backlog / TODO sources

- `TODO.md` (33 lines): 2 SHIPPED-annotated items (chunk-large-sessions, spend) + 1 genuinely
  deferred stretch goal (forked/shared-spend de-duplication). Full triage -> Section 5.
- In-code `TODO`/`FIXME`/`HACK`/`XXX` markers in shipped source: **none** (0). Two `XXX` hits
  are literal placeholder text in help/docstrings, not markers.

## Pending agent plans / staged prompts (for Section 8 warning)

- `.agents/plans/pending/`: only `README.md`. **No pending IPDs.**
- `.agents/prompts/pending/` and `.../not-executed/`: only `.gitkeep` + `README.md`. **No staged prompts.**
- No status/location mismatch found (grep hits for "pending" prose are all inside executed/ or README bodies).
- Comms inboxes (`.agents/comms/{local,shared}/inbox/`): empty. Prior comms all archived/sent.
- => Clean. No in-scope pending work blocks a GO.

## Public contract summary

CLI commands (README-documented): list/lp/ls/lr, running, doctor, spend, session
(recover/compact/rename/...), move, backup, export/import, reconnect, kill, TUI. All 5 new
1.3.0 commands (lr+filters, session rename, reconnect, kill, doctor server check) are
documented in README command reference. `--json` on scriptable commands.

## Test and validation inventory

- pytest suite: **473 passed, 2 skipped** (skips = benchmarks gated on `OCMAN_BENCHMARK=1`),
  ~132s. Command: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`.
- tests/: test_ocman.py, test_tui.py, test_move.py, test_export_import.py, conftest.py
  (cross-platform helpers: abs_path/norm_real/make_symlink/SYMLINKS_SUPPORTED, real_process_detection skip).
- Coverage tooling (pytest-cov) added this cycle; baseline ~70% overall (no hard gate).

## Build / packaging / CI / release inventory

- `pyproject.toml`: version 1.3.0rc4, deps, `[tool.coverage]` config, pytest-cov dev extra.
- CI (`.github/workflows/ci.yml`): `test` matrix ubuntu/macos/windows x py3.10-3.14 (15 cells,
  fail-fast default) + non-gating `coverage` job (coverage + report-only benchmarks). 16 jobs.
  `secret-scan.yml` (gitleaks) green. Last push 6913d1a was 16/16 green first try.
- `CITATION.cff`: cff-version 1.2.0 (schema, OK) but software `version: "1.1.0"` -- STALE.

## Drift / inconsistencies (findings)

- **F-01** version string `1.3.0rc4` while CHANGELOG heading is released `[1.3.0]` (promotion bump).
- **F-02** `CITATION.cff` software version `1.1.0` (2 releases behind; should track release).
- **F-03** `AGENTS.md` references `RELEASING.md` and `CONTRIBUTING.md`; neither file exists in repo.

## Out-of-scope (per 00-run-protocol exclusions)

`.agents/workflows/` (installed framework copy) and `workflow-artifacts/` (run records) are
present but NOT reviewed as project code/docs. `.agents/` plans/prompts/comms are project
process artifacts and ARE inventoried above for the pending-work gate, but not audited for
code quality.

## Recommended next actions

Proceed to audit Sections 2-6. Primary release action is the version bump (F-01) + CITATION
sync (F-02) + fix broken AGENTS.md refs (F-03), all low remediation risk.
