# assess testing - evidence (reproducible)

## Commands run
- `PYTHONPATH=. pytest -q` -> 452 passed, 2 skipped in ~115s (Linux, py3.14).
- `python -m coverage run --source=ocman,ocman_tui -m pytest -q` then `coverage report --sort=cover`
  -> saved to `coverage-summary.txt` (TOTAL 70%).
- `coverage json` -> mapped missing cli.py lines to enclosing `def` to rank untested functions.
- grep of test names for delete/move/restore/import; grep of @pytest.mark.* usage; grep of the
  `assert isinstance(app.screen, ...)`-after-single-pause pattern in test_tui.py.

## Test inventory
- 13 test files, ~9.4k lines, 444 test functions. Largest: test_ocman.py (264), test_tui.py (32),
  test_recovery.py (24), test_import/export (21).
- Marks: 31 anyio, 13 real_process_detection (Linux-only skip off-Linux), 4 parametrize, 1 skipif.

## Coverage highlights (see coverage-summary.txt)
- ocman/cli.py 71% (2605/8910 missed); ocman_tui/app.py 65%; widgets/database.py 53%.
- Highest MISSED-line functions (miss/total): _run_main 468/1628 (dispatch tail; low concern),
  db_show_info 79/318, db_run_cleanup 71/392, _execute_move 63/193, extract_and_import_project
  59/199, _gather_git_decisions 53/95, db_delete_project_recursive 51/252,
  db_delete_session_recursive 42/225, cli_restore 29/240, detect_running_instances 27/56,
  db_delete_sessions_batch 25/199, cli_kill 22/71.

## Flake-pattern evidence (T-02)
- test_tui.py has 122 pilot.pause/poll-loop uses, but ~10 `assert isinstance(app.screen, XModal)`
  sit right after a single pause (lines 164,199,238,339,383,642,...). The same class already
  forced CI reruns (test_tui_clear_history/app_startup/app_pruning); clear_history was hardened
  with a poll loop, but the pattern persists elsewhere.

## Not run / limitations
- Coverage measured on Linux only; off-Linux (macOS/Windows) detector-path coverage understated
  (those tests skip on Linux). CI matrix cells cover them.
- Perf tests (test_perf.py) skipped (OCMAN_BENCHMARK unset), so hot-path timing not exercised here.
