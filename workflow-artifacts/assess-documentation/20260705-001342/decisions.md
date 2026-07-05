# Decisions & assumptions - assess documentation (20260705-001342)

## Concern & scope
- Concern: documentation (lens `.agents/workflows/assess/lenses/documentation.md`; alias `docs` → documentation).
- Scope: the whole project's written docs — `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `AGENTS.md` — assessed for **accuracy first**, then completeness, per the lens. Verified against source (`ocman.py`, `ocman_tui/`, `pyproject.toml`), not inferred from names.
- Explicitly out of scope per review-scope rules: `.agents/workflows/` (the framework itself) and `workflow-artifacts/` run records.

## Project conventions discovered
- No `GUIDING_PRINCIPLES.md`; principles live in ARCHITECTURE.md ("Design principles", incl. "Honest documentation"). Used those + universal fallback.
- Plans lifecycle: `.agents/plans/pending/` → `.agents/plans/executed/`, filenames `YYYYMMDD-<slug>.md` (existing repo convention; used it — did NOT impose the template's `YYYY-MM-DD-` form).
- CHANGELOG.md is the change record and has an active `[Unreleased]` section; version is 1.0.4 (unreleased changes pending).
- Package: console script `ocman = ocman:main`; TUI package `ocman_tui`.

## Key decisions
- **Verdict "needs work"** driven by one High-severity accuracy defect (D1, the dead config key). The rest of the docs are strong: install/config/run/backup/restore/limitations/testing are present and accurate, and many spot-checked claims verified TRUE (export_version 2.0, Python 3.10+, retention default 5, `disk`/`--by-project`, per-project session-diff-only caveat, entry points).
- **Fix-by-default:** all six findings are Low Remediation Risk to fix as docs (D6's *doc* is already accurate → no doc change; only the *code rename* is deferred). Proposed acting on D1-D5.
- Followed the lens's "accuracy before completeness" ordering: D1 (inaccuracy) is the priority; D2 (completeness gap) next.
- Followed the lens's anti-bloat guidance (Complexity axis): proposed only accuracy corrections and the specific missing rows — no prose rewrites, no new sections, no aspirational content.

## What was intentionally NOT proposed, and why
- **Removing the stale `Orsession`/`orsession` identifiers (D6):** Remediation Risk Medium-High on complexity/functionality — a code refactor across the public TUI export (`ocman_tui/__init__.py`), an event-handler name (`on_orsession_app_refresh_sidebar`), a temp-dir prefix, and tests. ARCHITECTURE.md:22 already names the class accurately, so no doc is wrong. Deferred to a possible future architecture assessment / rename IPD. Effort was never the reason.
- **No style/prose editing** of otherwise-accurate docs (out of the documentation-accuracy remit; would be the `prose` lens).

## Open questions for the user (also in the IPD)
1. README `default_compaction_model` value: show real default `""` (recommended) vs a commented example model string?
2. Argument Reference: add all 13 missing flags (recommended) vs only the high-value browsing/version subset?
3. D6: leave `OrsessionApp` reference exactly as-is (recommended) vs add a "(legacy name)" parenthetical?

## Assumptions made
- The `[Unreleased]` CHANGELOG changes are committed-but-unreleased on top of 1.0.4 (confirmed via CHANGELOG structure + `__version__`); the doc fixes will land under the same `[Unreleased]` section.
- `PYTHONPATH=. pytest` currently passes 126/2-skipped (from session context); doc-only edits must leave that unchanged.
