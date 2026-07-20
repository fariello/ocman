# Section 9 - Release Execution (per-phase report)

## What I did

- Confirmed all hard preconditions (GO, explicit rung-C approval, no conditions, no LIVE/High,
  clean tree in sync with origin).
- Rebuilt and verified release artifacts (`ocman-1.2.0` sdist + wheel) from the release commit.
- Created the annotated tag `v1.2.0` on `039951c` and pushed it to `origin`.
- Verified CI green for the release commit (after re-running a transient flaky cell).
- Created a DRAFT GitHub Release `v1.2.0` from the CHANGELOG `[1.2.0]` notes and attached both
  built artifacts. Left it as a draft for the human to publish deliberately.
- Ran a local CLI smoke (`--version` = 1.2.0, import OK, suite green).
- Wrote `release-execution-log.md`.

## Why

- Rung C is a full release, executed as separate, named actions (tag, push tag, draft Release,
  publish) rather than one bundled "yes", per the runbook. The GitHub Release is a DRAFT and
  PyPI is a hand-off because publishing must be a deliberate human act and this run holds no
  PyPI credentials.

## What I considered but did NOT do (and why)

- **PyPI publish:** handed off. No PyPI token is available to this run; the runbook forbids
  guessing credentials. Exact `twine check`/`twine upload` commands are provided in the log.
- **Publishing the GitHub Release:** left as a DRAFT deliberately; the human publishes it (the
  runbook says never auto-publish).
- **Force-anything / signed tags:** the project does not sign tags (no `tag.gpgSign`); used a
  standard annotated tag consistent with prior `vX.Y.Z` releases. No force-push, no history
  rewrite.
- **Install-from-PyPI smoke test:** deferred until after the user runs the upload (cannot smoke
  a published artifact before it is published).
