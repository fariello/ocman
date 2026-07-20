# 11 Push Plan

- Branch: `main`
- Remote: `origin` git@github.com:fariello/ocman.git
- Local commits made this run (NOT pushed):
  - `4ee6928` ci: restore fail-fast default; changelog date -> 2026-07-20 (product/config)
  - Section commits `c263925`..`7e93ee6` (run artifacts, 8 commits)
- Working tree: clean. Local is ahead of origin/main by this run's commits.

## Permission status

- The user requested this release-review and previously authorized a full release (rung C)
  for v1.2.0 in the prior cycle. However, per the runbook, the push/tag/publish decision is
  RE-CONFIRMED at the end of THIS run via the DECISION block. Nothing is pushed automatically.

## Recommendation

- Push recommended once the user picks a consent rung (A/B/C). The primary reason to push is
  to let CI re-validate the fail-fast restore (A1) across the matrix before any tag.
- Suggested command on approval: `git push origin main`
- Then, on rung C (full release), proceed to Section 9: annotated `v1.2.0` tag -> push tag ->
  draft GitHub Release from CHANGELOG [1.2.0] -> hand off PyPI twine steps (no PyPI token in
  this run). Each externally-visible action separately confirmed, default-NO.

## No-push rationale (until approval)

- Push policy is hold-by-default; the user drives push/tag/publish. All work is committed
  locally and fully recoverable.
