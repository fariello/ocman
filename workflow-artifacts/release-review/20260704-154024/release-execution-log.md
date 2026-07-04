# Release Execution Log — v1.0.4 (run 20260704-154024, Section 9)

Preconditions: Section 8 = GO; user explicitly approved steps 1-4 (push, tag, PyPI publish, GitHub release);
no unaddressed LIVE/High; working tree clean with only intended release changes.

## Steps

| # | Step | Command | Result |
|---|---|---|---|
| 1 | Finalize/version/commit | (done in Section 7) | 1.0.4 in ocman.py/pyproject/ocman_tui; CHANGELOG [1.0.4]; commit 8c2aee9 |
| 2 | Push release commit | `git push origin main` | b5b902c..38f42c2; origin/main == HEAD == 38f42c2 |
| 3 | Verify remote CI | `gh run watch 28719980194 --exit-status` | **success** for headSha 38f42c2; full matrix ubuntu/macos/windows × py3.10-3.14 |
| 4 | Build artifacts | `python -m build` | ocman-1.0.4-py3-none-any.whl + ocman-1.0.4.tar.gz; `twine check` PASSED both |
| 5 | Tag release | `git tag -a v1.0.4 -m ...` + `git push origin v1.0.4` | tag b44c0cc -> commit 38f42c2; confirmed on remote |
| 6 | Publish to PyPI | `twine upload dist/ocman-1.0.4*` | **NOT performed — handed off.** No PyPI credentials available to this run (no ~/.pypirc, no TWINE_* env). Runbook prohibits publishing with unauthorized/unavailable credentials. |
| 7a | GitHub release | `gh release create v1.0.4 --title "ocman v1.0.4" --notes-from-tag` | Published (not draft/prerelease): https://github.com/fariello/ocman/releases/tag/v1.0.4 |
| 7b | Attach artifacts to GH release | `gh release upload v1.0.4 dist/ocman-1.0.4*` | wheel + sdist attached |
| 8 | Smoke test | `python ocman.py --version` / import | 1.0.4 (see below) |

## Release identifiers
- Release commit: 38f42c20ed8c941b0cc64046bd799febfc4d7fb8
- Tag: v1.0.4 (annotated, unsigned — consistent with prior tags)
- Remote: git@github.com:fariello/ocman.git (main + v1.0.4 pushed)
- CI run: 28719980194 (success)
- GitHub Release: https://github.com/fariello/ocman/releases/tag/v1.0.4 (wheel + sdist attached)
- PyPI: **pending user upload** (artifacts built + twine-checked in dist/)

## Handoff to user — PyPI publish (step requiring credentials)
Artifacts are built and validated in `dist/`. To publish 1.0.4 to PyPI with your token:
```
twine upload dist/ocman-1.0.4-py3-none-any.whl dist/ocman-1.0.4.tar.gz
```
(Provide the token via `~/.pypirc`, `TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-...`, or interactive prompt.)
Do a `twine upload --repository testpypi ...` dry run first if desired. `dist/` is gitignored; rebuild with
`python -m build` if needed.

## Post-release verification
Local smoke test passed (see Section 9 report). Full end-user verification (pip install from PyPI) is pending
the PyPI upload.
