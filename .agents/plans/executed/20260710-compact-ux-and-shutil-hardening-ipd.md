# Implementation Plan - Multi-session compact UX + import-hygiene hardening

Status: EXECUTED

Follow-up to the executed gap-closure work
(`.agents/plans/executed/20260710-gap-closure-ipd-01-05-followup.md`). Verification
confirmed that gap-closure fully executed and the suite is green (275 passed, 2
skipped). This plan addresses issues that were NOT visible to the test suite,
surfaced from real CLI runs of `ocman session compact` on multiple/large
sessions.

Evidence lines are `ocman.py:<line>` verified on 2026-07-10; re-verify before
editing (line numbers drift).

---

## Important: three reported crashes were a stale shadow copy, not repo bugs

The user reported an `UnboundLocalError: cannot access local variable 'shutil'`
(both at the batch-cleanup `finally` and during single-session compaction) and a
non-graceful `KeyboardInterrupt` traceback on Ctrl-C. All three tracebacks
referenced `/home/gfariello/venv/.../site-packages/ocman.py`, a STALE COPY that
shadows the editable install. Verified against the current repo:

- `main()` imports `shutil` at the top (`ocman.py:10525`), before any
  `shutil.` use, so the `UnboundLocalError` cannot occur in the repo.
- Ctrl-C at the batch prompt: `handle_signal` raises `KeyboardInterrupt`
  (`ocman.py:3841`), the batch `finally` cleans temp dirs, and the outer
  `except KeyboardInterrupt` (`ocman.py:11995`) prints "Recovery cancelled." and
  exits 130. Graceful in the repo.

So those are ENVIRONMENT artifacts of the recurring shadow copy, addressed by G3
below (make it structurally impossible), not by re-fixing already-correct code.

The remaining items (G1, G2) ARE real repo issues found in the same runs.

---

## Gaps to fix

### G1 (HIGH, UX) - verbose transcript preview floods the batch-compact estimate table

`ocman session compact` first prints an "LLM Compaction Estimates" table with a
row per session. But building each row calls `recover_from_export`
(`ocman.py:11779`) inside the estimate loop, and `recover_from_export`
UNCONDITIONALLY prints "Extracted turns: N Session tail preview:" plus a
multi-line per-turn preview (`ocman.py:3797`, and the per-turn prints at
`1599-1601`). Result (from a real run): the estimate table is interrupted
mid-render by hundreds of lines of transcript preview for each session, so the
table is unreadable and the batch looks like it is "compacting everything
together" when it is only estimating.

This also mildly misleads the user about what compact does: it DOES process one
session at a time, writing one `*.compacted.md` per session (the per-session loop
at `ocman.py:11894-11977` copies each session's generated files and calls
`run_compaction` individually). Only the noisy estimate output makes it look
batched.

Fix:
- Suppress the transcript preview during the ESTIMATE pass. Preferred: add a
  `quiet: bool = False` (or `preview: bool = True`) parameter to
  `recover_from_export` that gates the `print` at `ocman.py:3797` and the
  per-turn preview block; the batch estimate loop passes quiet=True. The actual
  per-session compaction pass may keep a concise per-session header
  ("Compacting session X ...", already at `ocman.py:11894`).
- Do NOT change the transcript preview for the single-session `recover`/`show`
  paths (it is useful there); only the compact-estimate pass goes quiet.
- Keep the estimate table contiguous: print the header, then one clean row per
  session, then GRAND TOTAL / AVERAGE, then the single confirm.

Test: a batch-compact estimate over >=2 sessions (with `recover_from_export`
stubbed or the preview asserted absent) produces a contiguous table and no
"Session tail preview" lines before the prompt.

### G2 (MEDIUM, robustness) - `main()` relies on a redundant top-of-function `import shutil`

`shutil` is imported at module scope (`ocman.py:91`), but `main()` and ~12 other
functions each do a local `import shutil` (`ocman.py:10525` and others). Because
`main()` contains a local `import shutil`, Python treats `shutil` as a LOCAL for
the whole function; the only reason `shutil.rmtree` in the batch `finally`
(`ocman.py:11992`) works is that the top-of-`main` import (`10525`) runs first.
Delete or move that one line and every compaction/backup path in `main()` breaks
with the exact `UnboundLocalError` the shadow copy exhibited. This is a latent
footgun sitting one edit away from a real outage.

Fix:
- Remove the scattered function-local `import shutil` statements and rely on the
  single module-level import (`ocman.py:91`). Grep every `import shutil` inside a
  function body and delete it; confirm `shutil` is still module-imported.
- This makes `shutil` unambiguously the module global in every function, so no
  code path can hit `UnboundLocalError` regardless of edit order.
- Optional: apply the same cleanup to other redundantly re-imported stdlib
  modules in `main()` if any exist (check `import sys`, `import json`, etc.), but
  `shutil` is the one with a demonstrated failure mode; keep scope tight.

Test: a unit test that, for `main` (and ideally all module functions), asserts no
function body contains `import shutil` (AST or source scan), so the footgun
cannot be reintroduced.

### G3 (HIGH, environment) - permanently stop the site-packages shadow copy

Root cause of the three false bug reports (and prior sessions'): hatchling's
`force-include` of `ocman.py` copies it into `site-packages` on `pip install`,
where it shadows the editable `.pth` redirect and goes stale. `scripts/dev-
editable-install.sh` mitigates it but only if run. `RECORD` still lists
`ocman.py`, so any reinstall recreates the shadow.

Fix (make it structurally impossible, not just documented):
- Convert the top-level module to an editable-friendly layout OR change the
  hatchling config so editable installs do NOT copy `ocman.py`. Options to
  evaluate during execution (pick the simplest that keeps `console_scripts`
  working and the wheel correct):
  1. Move `ocman.py` into a package (`ocman/__init__.py` re-exporting, or
     `ocman/cli.py` with `console_scripts = ocman = "ocman.cli:main"`), so the
     editable install uses a normal package `.pth` with no stray top-level file.
  2. Keep the single module but use hatchling's editable "redirect" mode /
     `[tool.hatch.build.targets.wheel] sources`/`packages` config so editable
     does not force-include the file into site-packages.
- Whatever is chosen: a fresh `pip install -e .` must leave NO
  `site-packages/ocman.py`, and `python -c "import ocman; print(ocman.__file__)"`
  must resolve to the repo working tree.
- Update `scripts/dev-editable-install.sh` / ARCHITECTURE notes accordingly.

Test / verification (documented, since it is packaging):
- After a clean editable reinstall, assert `site-packages/ocman.py` does not
  exist and `import ocman` resolves under the repo path. A CI/smoke check or a
  documented manual step in the walkthrough.
- The distributable wheel still contains `ocman.py` (or the package) and the
  `ocman` console script still runs (existing e2e/CLI tests cover this).

---

## Execution order

1. G1 (user-facing readability of the flow they actually run).
2. G2 (removes the latent `shutil` outage; small, mechanical).
3. G3 (packaging change; validate wheel + editable install + console script).
4. Full `PYTHONPATH=. pytest` green; plus a clean-editable-install smoke check
   for G3.

---

## Non-goals

- Re-fixing the `shutil`/Ctrl-C crashes as if they were repo bugs (they are
  shadow-copy artifacts; G2 hardens the latent risk, G3 removes the shadow).
- Changing the per-session-one-file compaction behavior (it is correct as
  designed; only the estimate-pass output is noisy).
- Reworking the estimate/actual cost accounting (delivered and green).
