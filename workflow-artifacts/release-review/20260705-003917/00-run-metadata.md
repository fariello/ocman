# 00 Run metadata

- Run ID: 20260705-003917
- Timestamp (local): 2026-07-05 00:39:17
- Agent / model: OpenCode — its_direct/pt3-claude-opus-4.8-1m-us
- Repository path: /home/gfariello/VC/ocman
- Git: repo=yes, branch=`main`, head=`9a7c1b5c05df8038d87b658a22525be6f279f026`
- Remote: `origin git@github.com:fariello/ocman.git`
- Initial working tree: clean (no uncommitted changes at run start)
- `.gitignore`: does NOT ignore `workflow-artifacts/` (OK; artifacts are committed deliverables)
- Environment: Python 3.14.4; Linux; pytest available (`PYTHONPATH=. pytest`)
- Prior runs: `20260703-134213`, `20260704-154024` (both shipped/prepared 1.0.4; GO for 1.0.4)

## Scope of this run

Pre-release review of the **1.0.4 → next** delta. 34 commits since tag `v1.0.4`, all on top of released 1.0.4,
committed locally, NOT pushed. Version is still `1.0.4` in code/pyproject (deliberately un-bumped; user will
bump AFTER a successful review). Target version to be decided with the user (user referred to 1.0.5).

Unreleased delta (from CHANGELOG `[Unreleased]` + git log): disk-usage reporting (`info` Backups section +
`--by-project`/`disk`), `--clear-history` typed-yes confirm, `--clean-backups` KEEP/DELETE preview, fractional
`--days`, process-lock detailed report + shared helper, unified destructive-confirmation seam, and the
compacted→project-prompts recovery feature (corrected this session from restart→compacted).

## Standing user constraints (this session)

- User will run the bump + PyPI publish AFTER a successful review with explicit sign-off. This run STOPS
  before Section 9 (no bump, no push, no publish) and presents Go/No-Go for approval.
- 1.0.4 is already published to PyPI, so the version MUST be advanced before any re-publish.
- Positioning note from user: ocman is a competitor to `ocgc`, whose key weakness is that it fails to reclaim
  ~95% of the space sessions occupy (DB and filesystem). ocman actually reclaims that space. The README should
  make this value proposition clear (feed into Section 4/5 docs review).
- Pending `docs` assessment IPD sits in `.agents/plans/pending/` — must be surfaced as a loud WARNING per the
  pending-plans rule.

## Review scope exclusions

`.agents/workflows/` (framework) and `workflow-artifacts/` (run records) are OUT of review scope. Subject is
the ocman project (`ocman.py`, `ocman_tui/`, `tests/`, docs, `pyproject.toml`, `.github/`).
