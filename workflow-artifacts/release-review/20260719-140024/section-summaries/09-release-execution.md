# Section 9 - Release execution (rung C) - HALTED at CI verify

## What I did
- Pushed `main` to origin (42057d8..1f0467c), as authorized (action 1).
- Verified CI via `gh run watch`: the secret-scan job passed (gitleaks baseline works
  remotely), but the CI matrix job FAILED on every cell.
- Diagnosed the failure to root cause by reading the CI log and reproducing on a local
  Python 3.12: pytest collection aborts at `import ocman -> import vistab`; the PUBLISHED
  `vistab 1.2.0` has `def _get_spanned_boundaries(self, row) -> Set[int]:` without importing
  `Set`, raising `NameError: 'Set'` under Python 3.12's eager annotation evaluation.
- Established that ocman cannot pin down to `vistab 1.1.3`: it uses `vistab.Vistab.set_color`
  (added in 1.2.x; absent in 1.1.3), and 6 table tests fail with AttributeError on 1.1.3.
- Confirmed the fixed vistab is 1.2.1 (in the local dev venv) but is NOT on PyPI (latest 1.2.0).
- Filed S9-REL2 (Blocker). HALTED before tag/build/GitHub-Release/publish per the
  runbook's red-CI rule.

## Why
- The runbook forbids tagging/building/publishing on red CI. The blocker is an external
  dependency (vistab), and its fix (publishing 1.2.1) requires maintainer action on the
  sibling vistab project, so I cannot resolve it in this repo alone.

## What I considered but did NOT do
- Pin `vistab==1.1.3` or `!=1.2.0`: rejected - 1.1.3 lacks set_color (breaks ocman); no
  other published 1.2.x exists, so a constraint alone cannot yield a working install on 3.12.
- Vendoring/patching vistab or dropping Python 3.12 from the matrix: out of scope and
  user-facing; not an agent decision.
- Tagging v1.2.0 / creating the GitHub Release / publishing to PyPI: NOT done - CI is red.
- main IS pushed (public), but nothing is tagged/released/published, so the release is not
  cut; it is recoverable by fixing the dependency and re-verifying CI.
