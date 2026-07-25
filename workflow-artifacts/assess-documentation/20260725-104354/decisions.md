# Decisions and assumptions - assess documentation (20260725-104354)

## Concern / scope assessed
- Concern: documentation (alias `docs` -> documentation).
- Scope: whole project, README.md primary; CHANGELOG.md cross-checked; ARCHITECTURE.md scanned for
  user-facing version drift. All doc claims verified against ocman/cli.py (the argparse surface and
  the config/env code paths), not inferred from names.

## Project conventions discovered (Step 0)
- Plan lifecycle: `.agents/plans/pending/` -> `.agents/plans/executed/`; filename
  `YYYYMMDD-HHMM-NN-<slug>.md`; front-matter `Status:` readiness. New IPD born `to-review`.
- Guiding contract: AGENTS.md (no em/en dashes in authored prose; sanctioned glyph exceptions).
- Stack: Python 3.10+ CLI + Textual TUI; version 1.3.0 (pyproject.toml:7 == ocman/cli.py:208).
- Review-scope exclusions honored: did NOT assess `.agents/workflows/` or `workflow-artifacts/` as
  project docs.

## Key decisions
- Verdict: adequate. The README is accurate and current; findings are one High accuracy fix plus
  small navigation/reference/hygiene gaps. No Blocker.
- Fix-by-default: all 7 findings are Low Remediation Risk, so all are proposed (none deferred on
  risk grounds).
- Verified the two highest-impact findings from source directly (not just the sub-agent report):
  - AD-01: README.md:444 shows `[PATTERN]`; parser metavar is `PID|PATTERN` (ocman/cli.py:6458) and
    the PID branch/enriched preview exist (12446-12453, 12500-12514). Confirmed stale.
  - AD-02: `OCMAN_CONFIG_PATH` is a module constant (ocman/cli.py:224); grep of ocman/ finds no
    `os.environ`/`getenv` read for it. The README env-override claim is false. Confirmed.

## What was intentionally NOT proposed (and why)
- Implementing an actual `OCMAN_CONFIG_PATH` environment override in code (AD-02 code option): OUT
  OF SCOPE for a documentation assessment. It is a behavior change requiring its own decision and
  tests. The docs-side correction (remove the false claim) is proposed and removes the inaccuracy.
  This is a scope boundary, not a Remediation-Risk deferral.
- No new sections/expansions beyond the seven targeted corrections (Complexity axis; the README is
  already thorough, so bloat would harm it).

## Assumptions (to confirm)
- AD-02 resolution defaults to the DOCS fix (remove the row). If the maintainer instead wants the
  env override to work, that is a separate code plan.

## Open questions for the user
- AD-02: docs fix (remove the row) or implement the env override in code?
