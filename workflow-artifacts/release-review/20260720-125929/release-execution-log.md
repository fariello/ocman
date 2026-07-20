# Release Execution Log - v1.2.0 (rung C, full release)

Preconditions: Section 8 = GO; user explicitly approved FULL RELEASE (rung C) in this
conversation; no CONDITIONAL prerequisites; no LIVE/High findings; working tree clean and in
sync with origin/main.

## Step 1 - Finalize/version/commit

- Version consistent: `pyproject.toml` = 1.2.0, `ocman/cli.py:208 __version__` = 1.2.0,
  CHANGELOG `## [1.2.0] - 2026-07-20`. No derived VERSION-file artifact in this project.
- Release commit: `039951c` (already committed; working tree clean).

## Step 2-3 - Push + CI verify

- Release commit `039951c` pushed to `origin/main` (`bebb520..039951c`).
- CI run `29764588646`: initial run had 1 genuine failure (`ubuntu-latest 3.12`:
  transient `sqlite3.OperationalError: disk I/O error`, 407/408 in-cell) + 6 CANCELLED cells
  (fail-fast:true cancelled the rest). Re-ran failed jobs (`gh run rerun --failed`) -> ALL 15
  cells GREEN. Not a code regression (transient runner disk hiccup).
- Timeout used for polling: `gh run watch` bounded, completed well under 15 min.

## Step 4 - Build artifacts

- `python -m build` (isolated) -> `ocman-1.2.0.tar.gz` + `ocman-1.2.0-py3-none-any.whl`.
- Version 1.2.0 embedded; wheel contains `ocman`, `ocman_tui`, migrate script. Verified.

## Step 5 - Tag + push + GitHub Release (each a separate action)

- Annotated tag: `git tag -a v1.2.0 039951c -m "Release v1.2.0"` -> tag points at 039951c.
- Push tag: `git push origin v1.2.0` -> confirmed on remote (refs/tags/v1.2.0).
- GitHub Release: `gh release create v1.2.0 --draft --title v1.2.0 --notes-file <CHANGELOG [1.2.0]>`
  -> DRAFT created (isDraft: true). Attached both built artifacts (whl + sdist).
  NOT published; the human publishes the draft deliberately.

## Step 6 - Publish to PyPI (rung C) - HANDED OFF TO USER

- This run holds NO PyPI credentials (no TWINE_PASSWORD, no ~/.pypirc). twine is installed in
  the venv. Per the runbook, publishing is handed off with exact commands (see below); the
  agent does NOT guess credentials.

  Hand-off commands (run by the user with a PyPI token):
    /home/gfariello/venv/p3.14/bin/twine check /tmp/opencode/ocman-rel/*
    /home/gfariello/venv/p3.14/bin/twine upload /tmp/opencode/ocman-rel/ocman-1.2.0*
  (Artifacts also attached to the draft GitHub Release.)

## Step 7 - Post-release smoke test

- Local CLI smoke (release commit): `ocman --version` -> 1.2.0; import OK; full suite green
  (408 passed / 2 skipped). Published-artifact smoke test deferred until after the user runs
  the PyPI upload (install-from-PyPI check is part of the hand-off).

## Status

- Done by agent: tag v1.2.0 (annotated, pushed), draft GitHub Release with artifacts, CI green.
- Awaiting user: (1) `twine upload` to PyPI, (2) publish the draft GitHub Release.
