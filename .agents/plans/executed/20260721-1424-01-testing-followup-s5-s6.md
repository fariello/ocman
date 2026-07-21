# IPD: testing follow-up (assess-testing S5-S6 + the Storage-tab worker flake)

- Date: 2026-07-21
- Concern: testing (follow-up to `20260721-0111-01-assess-testing.md`, which executed Steps 1-4
  and deferred 5-6)
- Scope: `tests/*.py`, a small pure-seam refactor in `ocman/cli.py` (`_gather_git_decisions`),
  and possibly a small hardening of the Storage widget's worker + `.github/workflows/ci.yml`
  (one perf step). Tests + a testability seam + a widget-mount guard only; no user-facing
  behavior change.
- Status: executed (2026-07-21)
- Target version: rides the 1.3.0 line (test/infra + a pure seam; no user-facing change).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-21 created (its_direct/pt3-claude-opus-4.8): follow-up carrying the deferred Steps 5-6
  from the assess-testing IPD, plus the concrete Storage-tab worker-mount flake observed while
  executing that IPD.
- 2026-07-21 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED.
  Verified all anchors against code (storage.py:143 unguarded `query_one("#doctor-table")`;
  the `is_mounted` guard precedent at database.py:299; the interleaved `_menu` calls in
  `_gather_git_decisions` cli.py:9413-9508). PR-001 (TF-01 seam: the interleaving means the pure
  cut MUST be a choices-provider shape, not a single function containing menus; Step 2 now
  commits to it), PR-002 (TF-02 needs a DETERMINISTIC mutation-checked guard test, not only a
  probabilistic stress loop). Remaining open questions are non-blocking preferences with safe
  defaults. No unfixed BLOCKER/HIGH. GO - PENDING HUMAN APPROVAL.
- 2026-07-21 approved by maintainer; executed (its_direct/pt3-claude-opus-4.8). All 5 steps done.

## Post-execution summary

- TF-02 (Step 1): guarded `StorageWidget._do_checkup_worker`'s `update_ui` callback with
  `if not self.is_mounted: return` + `try/except NoMatches` around the `#doctor-table` query
  (imported `NoMatches`), matching the `DatabaseAdminWidget.refresh_metrics` precedent. Added a
  DETERMINISTIC test (`test_storage_checkup_worker_skips_when_unmounted`) that drives the worker
  on an unmounted widget and asserts no raise; MUTATION-CHECKED (removing the guard makes it fail
  with NoMatches). Stress-loop of storage+models TUI tests: 0 failures across the completed runs.
- TF-01 (Steps 2-3): extracted pure `_git_decisions_for_state(gs, *, dirty_choice, divergence_choice)`
  from `_gather_git_decisions`; the orchestrator now resolves all `_menu` choices up front
  (non-interactive defaults preserved byte-identically: divergence defaults to 1, dirty
  non-interactive still `die`s) then delegates. Added 9 pure-seam unit tests (not-a-repo, clean
  in-sync, clean-no-upstream, ahead push/skip, ahead+behind push/pull/pull-only/none, dirty
  abort-raises/commit-staged/add-all/no-commit). All 26 move tests pass (17 existing unchanged).
- TF-03/04 (Step 4): added `test_tui_prune_worker_error_is_surfaced_not_crashed` covering the
  `_do_prune_worker` except branch (db_run_cleanup raises -> error notify, no crash). Happy path
  already covered by `test_tui_prune_duration_and_scope`.
- TF-04 (Step 5): added a non-gating "Benchmarks" step to the CI coverage job
  (`OCMAN_BENCHMARK=1 pytest tests/test_perf.py -s || true`); verified locally it prints timings
  (2 passed, report-only). Never gates the build.
- Validation: full suite **473 passed, 2 skipped** (was 462; +11 new tests).
- Release: rides the 1.3.0 line; NOT promoted to final 1.3.0.

## Goal

Finish the testing-rigor work deferred from `20260721-0111-01`:
1. **S5:** give `_gather_git_decisions` a pure, unit-testable seam and test its branch logic
   (remote-move/git-decision code is the least-covered risky area).
2. **S6a (concrete, priority):** fix the Storage-tab worker-mount flake: under full-suite load
   the doctor worker queries `#doctor-table` before it is reliably mounted, raising
   `NoMatches("No nodes match '#doctor-table' on StorageWidget()")` (a `WorkerFailed`). Same
   TIMING CLASS as the modal-mount flake fixed in S1, but in a worker query, so the
   modal-only `await_screen` helper does not cover it. Observed intermittently on
   `test_tui_models_widget`/`test_tui_storage_*` under load; passes on rerun.
3. **S6b:** add focused TUI worker/error-path tests (widgets/database.py mutating actions +
   off-thread worker error handling), and make ONE perf check CI-runnable in report-only mode so
   gross hot-path regressions surface.

## Project conventions discovered (Step 0)

- Universal fallback principles. Plans `.agents/plans/pending/` -> `executed/`; Status born
  `to-review`. No em/en dashes. Path-scoped commits, never push. Coverage tooling now exists
  (pytest-cov + `[tool.coverage]`, added in the prior IPD) and a non-gating CI coverage job.
- `_gather_git_decisions(source_dir: Path, interactive: bool) -> tuple[list[list[str]], list[str], bool]`
  (cli.py): calls `git_state(source_dir)` (the IO), then builds `(git_cmds, labels, needs_bulk)`
  via interactive `input()` menus interleaved with the decision logic.
- Storage widget: `StorageWidget._do_checkup_worker(deep)` runs via `run_worker(..., thread=True)`
  (ocman_tui/widgets/storage.py:128) and does `self.query_one("#doctor-table", DataTable)`
  (storage.py:143) from the worker; `#doctor-table` is composed at storage.py:81. Exercised by
  `test_tui_storage_doctor_renders_and_totals` (tests/test_tui.py:691) and touched by others.
- `await_screen(pilot, app, screen_cls)` helper exists in tests/test_tui.py (modal-mount poll).

## Findings / requirements

| ID | Requirement | Evidence |
|----|-------------|----------|
| TF-01 | `_gather_git_decisions` needs a pure seam: separate the decision logic (git-state dict + choices -> cmds/labels/needs_bulk) from the `git_state()` IO and the `input()` prompts, so branches are unit-testable with fabricated state. | cli.py `_gather_git_decisions`; coverage 53/95 missed (prior run) |
| TF-02 | Storage worker `#doctor-table` mount race: worker queries the table before it is reliably mounted under load -> NoMatches/WorkerFailed. | storage.py:128/143; observed on test_tui_models_widget under full-suite load |
| TF-03 | Missing focused tests for TUI worker/error paths (database.py mutating actions, off-thread worker error handling). | coverage: widgets/database.py 53% |
| TF-04 | Perf tests never run in CI (skip-by-default), so hot-path regressions are uncaught. | test_perf.py skipif OCMAN_BENCHMARK!=1 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | TF-02 | Fix the Storage worker mount race FIRST (concrete CI annoyance). Options, pick the least-invasive that works: (a) in `_do_checkup_worker`/its UI-update callback, guard the `query_one("#doctor-table")` with an `is_mounted`/`try: ... except NoMatches` and re-schedule/skip if the table is not yet mounted (mirror the pattern already used elsewhere, e.g. database.py `refresh_metrics` guarded with `if not self.is_mounted: return`); OR (b) ensure the widget does not launch the checkup worker until after `on_mount`/compose has mounted `#doctor-table`. Prefer the guard that matches the existing `is_mounted` convention. Add BOTH (a probabilistic stress loop is not enough on its own): (i) a DETERMINISTIC unit test that drives `_do_checkup_worker`'s `update_ui` path when `#doctor-table` is absent / the widget is not mounted (e.g. call the guarded update after simulating unmount, or monkeypatch so the table query would raise) and assert it does NOT raise `WorkerFailed`/`NoMatches` (it skips/re-schedules); AND (ii) a stress loop to confirm the race is gone in practice. | ocman_tui/widgets/storage.py, tests/test_tui.py | Medium | (i) the deterministic guard test passes and FAILS if the guard is removed (mutation-check); (ii) stress loop (storage + models TUI tests 20x) shows 0 `WorkerFailed`/`NoMatches`; full suite green |
| 2 | TF-01 | Extract the PURE decision function from `_gather_git_decisions`. IMPORTANT (verified against cli.py:9413-9508): the current function INTERLEAVES `_menu(...)` interactive prompts BETWEEN decision branches (dirty/staged/detached), so a pure function that still contains the menus is impossible. Commit to the CHOICES-PROVIDER shape: (a) keep `_gather_git_decisions(source_dir, interactive)` as the thin orchestrator that calls `git_state()`, then resolves ALL interactive menus UP FRONT into a plain `choices` dict/dataclass (each menu -> a resolved int/enum; non-interactive defaults preserved exactly as today), then (b) delegate to a NEW pure `_git_decisions_for_state(gs: dict | None, choices) -> (git_cmds, labels, needs_bulk)` that has NO IO and NO `input()`/`_menu`. The set of choice keys must cover every branch currently reached by a `_menu` call. Product behavior unchanged (pure refactor; the non-interactive default path must produce byte-identical output). | ocman/cli.py | Medium | existing move/remote-move tests unchanged/green; new unit tests call `_git_decisions_for_state` with fabricated git states x choice combinations (clean / dirty-staged / dirty-unstaged / not-a-repo / detached) and assert the cmds/labels/needs_bulk |
| 3 | TF-01 | Unit-test `_git_decisions_for_state` across the branches: no-repo -> needs_bulk True + "bulk file copy" label; clean committed -> push cmds, needs_bulk False; dirty -> needs_bulk semantics; each choice path. Mutation-check at least one (flip a branch -> test fails). | tests/test_move.py | Low | new tests exercise the decision branches; coverage of the seam rises |
| 4 | TF-03 | Add focused async tests for widgets/database.py worker/error paths: a mutating action's happy path AND its off-thread worker ERROR path (the worker must surface the error via notify without touching a widget off the UI thread / after unmount). Reuse `await_screen`/`is_mounted` patterns; monkeypatch the underlying db_* call to raise and assert graceful handling (no crash, error surfaced). | tests/test_tui.py | Low | new tests pass; database.py coverage rises on the worker/error branches |
| 5 | TF-04 | Make ONE perf check CI-runnable in REPORT-ONLY mode: either a tiny CI step that runs `OCMAN_BENCHMARK=1 pytest tests/test_perf.py -s || true` (prints timings, never gates) in the existing non-gating coverage job or its own non-gating job; OR convert one benchmark into a bounded, generous assertion (e.g. import of N sessions < X s on CI) that only catches gross regressions. Prefer report-only to avoid CI-timing brittleness. | .github/workflows/ci.yml (and/or test_perf.py) | Low | CI shows perf timings; no new gating red |

## Deferred / out of scope

- A hard coverage-% gate: still deferred (same Medium-High usability/functionality axis rationale
  as the prior IPD; measurement stays visible-only).
- Broad TUI coverage beyond the specific worker/error paths in Step 4: not a blanket push.
- Any product behavior change beyond the TF-01 mount guard (a defensive guard, not a feature) and
  the TF-02 pure seam (a pure refactor).

## Anti-regression / invariants

- `_gather_git_decisions` keeps its public signature and behavior; the extracted pure function is
  an internal seam. Existing move/remote-move tests must pass unchanged.
- The Storage worker guard must not change what the checkup renders when the table IS mounted
  (only avoid the pre-mount NoMatches); existing `test_tui_storage_*` assertions unchanged.
- No new runtime (non-dev) dependency. Perf step is report-only (non-gating).
- The modal `await_screen` helper and the prior flake fixes remain intact.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE ACTUAL output (must stay
  462+ passed, 2 skipped, plus the new tests).
- TF-02: a LOCAL STRESS LOOP (e.g. the storage + models TUI tests run 20x) shows zero
  `WorkerFailed`/`NoMatches` failures (the checkable criterion, mirroring S1's approach).
- TF-01 pure-seam tests mutation-checked (flip a decision branch -> a test fails).
- Cross-platform: TUI/`await_screen` tests already run everywhere; perf step is Linux CI only.

## Spec / documentation sync

- None user-facing. If the perf step is added, a one-line note in CONTRIBUTING/README dev section
  on how to read the report-only perf output.

## Open questions

- RESOLVED (PR-001, from repo evidence cli.py:9413-9508): TF-01 MUST use the choices-provider
  shape (orchestrator resolves all `_menu` choices up front, then a pure
  `_git_decisions_for_state(gs, choices)` builder), because the menus are interleaved with the
  decision branches and cannot live inside a pure function. Step 2 now specifies this.
- NON-BLOCKING (maintainer preference, safe default): TF-05 perf = report-only (default) vs a
  bounded assertion. Plan defaults to report-only; confirm at approval.
- NON-BLOCKING (preference): after TF-02 (highest, the CI flake), do S5 (TF-01) or S6b next?
  Default: TF-02 -> TF-01 -> TF-03/04 -> perf. Confirm at approval.

## Approval and execution gate

- This IPD is a PROPOSAL and is NOT auto-executed. A human approves (optionally via
  `plan-review`) before execution.
- Execution checklist (MUST): before coding, create a TodoWrite step-granular checklist tracking
  each step, the new tests + the TF-02 stress loop, the full-suite run with PASTED output, any
  docs sync, the path-scoped commit(s), and the Status-executed + `git mv` to `executed/`.
- Scope fence: tests + the `_gather_git_decisions` pure seam + the Storage worker mount guard +
  a report-only perf CI step. No user-facing behavior change; no new runtime dependency; no hard
  coverage gate.
- Honesty rule (hard MUST): paste ACTUAL `pytest -q` output; never claim a pass not run. TF-01
  and TF-02 tests must be mutation-checked / stress-verified, not vacuous.
- Commits: path-scoped, NEVER push without approval, NEVER tag.
- Lifecycle: on completion set `Status: executed` and `git mv` this IPD to `executed/`.

Next: human review (optionally `/plan-review`) sets `Status: approved`; then execute per the above.
