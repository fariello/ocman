# Release execution log (Section 9)

Rung: C (FULL RELEASE), maintainer-approved.

## Step 2 - push main: DONE
- `git push origin main` -> 42057d8..1f0467c (50 commits, incl. v1.2.0 commit 2554395).

## Step 3 - push-then-verify CI: FAILED (blocker)
- secret-scan job: SUCCESS (gitleaks baseline effective remotely).
- CI job (run 29699322013, commit 1f0467c): FAILED on every matrix cell.
- Root cause (S9-REL2): pytest collection aborts at `import ocman -> import vistab`;
  `vistab.py:2617` annotates `-> Set[int]` without importing `Set`, raising
  `NameError: name 'Set'` on Python 3.12 (eager annotation eval). This is a bug in the
  PUBLISHED vistab 1.2.0 (PyPI latest). ocman requires vistab.set_color() (added in 1.2.x;
  absent in 1.1.3), so it cannot pin down to 1.1.3 (6 table tests fail with AttributeError).
  The fixed vistab is 1.2.1 (present in the local dev venv) but is NOT published to PyPI.
- Consequence: no published vistab satisfies BOTH "has set_color" AND "imports on py3.12".
  A clean `pip install ocman` fails import on py3.12; CI cannot go green as-is.

## Steps 4-7 (build/tag/GitHub Release/publish/smoke): NOT PERFORMED
- Halted per the runbook: CI is red; do not tag/build/publish until green.
- main is already pushed (public) but NO tag, NO GitHub Release, NO PyPI publish was done.

## Required handoff
- Publish vistab 1.2.1 to PyPI (maintainer owns vistab), then bump ocman's dep to
  `vistab>=1.2.1` and re-run CI. Resume Section 9 (tag/release) once CI is green.
