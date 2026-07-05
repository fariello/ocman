# 11 Push / no-push plan

- Branch: `main`
- Remote: `origin git@github.com:fariello/ocman.git`
- Local commits this run: S1–S8 artifact commits + 2 product commits (docs; code/packaging/version) +
  run-setup. All local; nothing pushed.
- Working tree: clean.
- User push permission: **NOT granted for this run** (user explicitly performs the bump/push/publish after a
  successful review + sign-off).

## Recommendation
**No push during this run.** Present Go/No-Go and stop. On the user's approval, the release sequence
(Section 9) is:

1. `git push origin main`
2. Tag: `git tag -a v1.0.5 -m "ocman 1.0.5" && git push origin v1.0.5`
3. Build: `python -m build` (produces `dist/ocman-1.0.5.tar.gz` + wheel)
4. Publish: `twine upload dist/ocman-1.0.5*` (1.0.4 is already on PyPI; 1.0.5 is the new version — verified
   bumped in ocman.py + pyproject.toml)
5. Optional: `gh release create v1.0.5 --notes-from-tag`

## Risks
- Low. Delta is backward-compatible; version correctly bumped so no PyPI collision with 1.0.4.
- Prerequisite before a clean release: resolve the pending docs IPD (move
  `.agents/plans/pending/20260705-assess-documentation.md` → `.agents/plans/executed/`, since this run
  executed its findings). Housekeeping, not a code risk.
