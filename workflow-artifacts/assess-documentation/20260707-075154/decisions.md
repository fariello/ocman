# Decisions and assumptions - assess documentation (20260707-075154)

## Concern / scope

- Concern resolved from the invocation argument `docs` -> `documentation` lens
  (`.agents/workflows/assess/lenses/documentation.md`). Note a sibling
  `self-documentation` lens exists (in-product clarity); this run is the repo-docs lens
  as the user asked for "docs".
- Scope: project-authored documentation only: README.md, ARCHITECTURE.md, CHANGELOG.md,
  CITATION.cff, AGENTS.md, TODO.md, plus a check of LICENSE/NOTICE references.
- Out of scope (per review-scope exclusions): `.agents/workflows/` (the framework),
  `workflow-artifacts/` run records, `.agent-workflows-installer-backups/`, `.claude/`,
  `.opencode/`, and `node_modules` README files.

## Project conventions discovered (Step 0)

- Guiding principles: `ARCHITECTURE.md` "Design principles" (incl. "Honest documentation").
- Pending-plans dir: `.agents/plans/pending/`; terminal dir `.agents/plans/executed/`;
  filename `YYYYMMDD-<slug>.md`; IPD carries a `Status:` line. Matches existing executed IPDs.
- Contributor contract: `AGENTS.md` (agent-workflows pointer + "no em dashes in authored
  prose" convention, advisory).
- A prior documentation assessment executed 2026-07-05
  (`.agents/plans/executed/20260705-assess-documentation.md`); this run targets drift
  introduced by the 1.1.0 release since then. Findings here are new, not stale re-proposals.

## Key decisions

- Verified doc claims against code rather than inferring from prose. Parsed every
  `add_argument` in `ocman.py` via AST to get the authoritative flag list and compared it
  to the README Argument Reference table.
- Applied the lens IPD emphasis: inaccuracies before gaps. DOC-1 (wrong published version)
  ranked High severity because it is machine-consumed citation metadata; DOC-2 (missing
  table row) Medium; DOC-3/DOC-4 Low.
- Fix-by-default: all four findings proposed for action (all Low Remediation Risk).

## What was intentionally NOT proposed (and why)

- Adding version numbers to README/ARCHITECTURE prose: deliberately not proposed
  (Complexity/maintenance axis). Those files currently carry no hardcoded version, which
  is the correct low-maintenance choice; keeping the single source of citation version in
  `CITATION.cff` avoids future drift.
- `-m/--use-model` absent from README: correct, it is `argparse.SUPPRESS`ed (deprecated).
- `--format` absent from README: correct, it is an opencode subprocess argument, not an
  ocman CLI flag.
- README "From PyPI (Recommended)" install: not flagged. 1.1.0 is not yet uploaded to
  PyPI, so `pip install ocman` currently yields 1.0.6, but that is a transient release-
  pipeline state, not a documentation defect.

## Open questions for the user - RESOLVED (2026-07-07, interactive)

1. DOC-3/DOC-1 dates: **use the git-tag/GitHub-release date 2026-07-07** (not the
   pending PyPI upload date). Confirmed by user.
2. DOC-3: **yes, correct the CHANGELOG 1.1.0 heading to 2026-07-07** to match the tag.
   Confirmed by user.

No open questions remain; the IPD's proposed changes are ready for execution on approval.
