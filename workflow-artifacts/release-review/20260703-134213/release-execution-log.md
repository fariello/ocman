# Release Execution Log — v1.0.3 (run 20260703-134213, Section 9)

Preconditions: Section 8 = GO; user explicitly approved release execution ("go"); scope chosen by user =
push + tag + verify CI (NO PyPI publish); no unaddressed LIVE/High finding; working tree clean.

## Steps

| # | Step | Command | Result |
|---|---|---|---|
| 0 | Fix stale local remote | `git remote set-url origin git@github.com:fariello/ocman.git` | Was `opencode-recover.git` (redirects to ocman). Repointed to canonical. `git fetch` OK. |
| 1 | Confirm repo identity | `gh repo view fariello/opencode-recover` / `fariello/ocman` | Both resolve to `fariello/ocman` (rename + redirect). |
| 2 | Push release commit | `git push origin main` | e6c5943..c56e5eb; origin/main == HEAD == c56e5eb. |
| 3 | Verify remote CI | `gh run watch 28708205093 --exit-status` | **success** for headSha c56e5eb; matrix ubuntu/macos/windows × py3.10-3.14. |
| 4 | Build artifacts | `python -m build` | Built ocman-1.0.3.tar.gz + ocman-1.0.3-py3-none-any.whl; `twine check` PASSED both. |
| 5 | Tag release | `git tag -a v1.0.3 -m ...` + `git push origin v1.0.3` | Tag 53f34d0 -> commit c56e5eb; confirmed on remote via ls-remote. |
| 6a | GitHub Release | `gh release create v1.0.3 --notes-from-tag` | Published (not draft/prerelease) at https://github.com/fariello/ocman/releases/tag/v1.0.3 (after user granted token Contents:write). |
| 6b | PyPI publish | `twine upload dist/ocman-1.0.3*` (by maintainer) | **Done** — ocman 1.0.3 released to PyPI by the maintainer. |
| 7 | Smoke test | `ocman.py --version`; import ocman/ocman_tui; wheel contents | ocman 1.0.3 / tui 1.0.3; wheel contains ocman.py + ocman_tui package. PASS. |

## Release identifiers
- Release commit: c56e5eb3602dcd19f1540d9609c401a61822b5fe
- Tag: v1.0.3 (annotated, unsigned — project does not sign tags; prior tags v1.0.0-1.0.2 are also unsigned)
- Remote: git@github.com:fariello/ocman.git (main + v1.0.3 pushed)
- CI run: 28708205093 (success)
- GitHub Release: v1.0.3 published (https://github.com/fariello/ocman/releases/tag/v1.0.3)
- PyPI: ocman 1.0.3 published by maintainer

## Handoff to user (PyPI publish — not performed this run)
Artifacts are built and validated in `dist/`. To publish to PyPI when ready (requires your PyPI token):
```
twine upload dist/ocman-1.0.3*
```
(`dist/` is gitignored; rebuild with `python -m build` if needed.)

## Post-release verification
Local smoke test passed. No release incident. No rollback needed.
