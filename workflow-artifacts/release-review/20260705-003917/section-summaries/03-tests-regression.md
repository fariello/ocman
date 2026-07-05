# Per-Phase Report

## Section
- Section: 3 — Tests & regression protection
- Run ID: 20260705-003917
- Status: complete

## Personas applied
- Testing/regression expert (2): confirmed the delta's live surfaces have regression tests; identified the
  few genuine gaps (all Low).
- QA/QC (1): confirmed the restart→compacted correction carries explicit regression tests and the old test
  file was renamed (not dropped).

## What I did
- Counted tests per file (128 test functions across 10 files) and mapped each new delta function to its tests.
- Confirmed strong coverage of the delta's live/destructive surfaces:
  - Process lock: `test_process_lock_refuses_when_opencode_running`, `_force_bypasses`,
    `_fails_open_on_detector_error`, `test_detect_running_opencode_filter_and_self_exclusion`, `_fails_open`,
    `test_render_running_opencode_lists_each_process`.
  - Destructive preview: `test_render_destructive_preview_days_column`, `_no_days_when_disabled`,
    `_right_aligned_size`.
  - `cli_clean_backups`: `test_clean_backups`, `_cancel_on_non_yes`, `_dry_run_deletes_nothing`,
    `_preview_shows_keep_and_delete`, `_all_deleted_warning`.
  - `dir_usage`: `test_dir_usage`. Compacted-copy: 11 tests in test_compacted_project_prompt.py.
- Identified gaps: `_per_project_disk_usage` (T1), focused `confirm_destructive`/`_project_for_cwd` (T2).
- Re-checked carry-in S3-R1 (bare pytest → installed pkg): mitigated here (editable install) + CI sets
  PYTHONPATH; residual only for fresh non-editable installs; documented.
- Ran the suite: 126 passed, 2 skipped (opt-in perf).

## Why I did it
Green tests are not proof for live surfaces, but the presence of *targeted* tests for the refuse/force/
fail-open/cancel/dry-run paths is exactly the regression protection those surfaces need; I verified those
exist rather than assuming.

## What I considered but did NOT do (mandatory)

| Considered item | Why not done | Recommended next step |
|---|---|---|
| Adding tests now | Section 3 is audit-only; test writing is Section 7 | Add T1 (+ optionally T2) in S7 |
| A coverage tool run | Not configured in the repo; would add tooling | Manual mapping used instead |
| Treating S3-R1 as a blocker | Low severity; mitigated by editable install + CI PYTHONPATH + README | Optional pytest.ini in S7 |

## Key findings

| ID | Type | Severity | Remediation Risk | Title | Status | Next step |
|---|---|---|---|---|---|---|
| 20260705-003917-S3-T1 | T | Low | Low | No unit test for `_per_project_disk_usage` | identified | Add in S7 |
| 20260705-003917-S3-T2 | T | Low | Low | No focused test for `confirm_destructive`/`_project_for_cwd` | identified | Optional in S7 |
| 20260705-003917-S3-R1 | R | Low | Low | Bare pytest may resolve installed pkg | identified | Keep documented; optional pytest.ini |

## Actions created or updated
Planned for S7: T1 (add `_per_project_disk_usage` unit test). T2/R1 optional.

## Deferrals (Fix Bar)
None deferred on risk grounds — T1/T2/R1 are Low remediation risk and will be fixed/addressed in S7 by
default (T1 firmly; T2/R1 optional, low value).

## Guiding-principles / self-documenting notes
Test suite reflects the honest-documentation principle (tests assert the actual confirm/preview behavior).

## TODO / backlog items touched
None.

## Non-applicable checks
No integration/e2e harness beyond the existing subprocess-mocked flows; not required for this delta.

## Validation or commands
`PYTHONPATH=. pytest -q` → 126 passed, 2 skipped. See 10-validation-results.md.

## Handoff to next section
Section 4 (docs): fold the pending docs-IPD fixes (dead `default_model` key, incomplete arg table,
preprocess_argv commands, TUI css/) and add the ocman-vs-ocgc reclaim positioning (verified against the
vacuum/orphan/delete reclaim paths before any claim ships).
