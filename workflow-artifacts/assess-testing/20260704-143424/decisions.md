# Decisions and assumptions - assess-testing 20260704-143424

## Concern / scope
- Concern: testing rigor and completeness. Lens: testing.md.
- Scope: whole project; no `$ARGUMENTS` narrowing.
- Lead personas: testing/regression expert + QA, with the software engineer on testability.

## Project conventions discovered
- Test command `PYTHONPATH=. pytest`; 66 tests (2 opt-in benchmarks skipped). anyio for
  async TUI tests via `run_test()`. SQLite prod == test (no dialect drift). CI matrix.
- No pre-existing `tests/fixtures/`; no coverage tooling.
- Out of scope (framework): `.agents/workflows/`, `workflow-artifacts/`.

## Key decisions / findings
- Verdict **needs work**: the admin/move/export-import/backup-restore surfaces are well
  tested, but the recovery/compaction pipeline (the product's headline feature) is
  essentially untested end-to-end.
- **TEST-1 is a real shipped bug found via the testing lens:** the TUI CompactionScreen
  calls `call_compaction_api(model_info, prompt_content)` (2 args; signature needs 3:
  model, prompt, verbosity) and then does `result["content"]` although the function
  returns a `str`. Verified by reading ocman.py:787/893 vs ocman_tui/app.py:1315-1316;
  the type checker independently flags app.py:1312 ("Argument missing for parameter
  verbosity") and app.py:1319. The proposed TUI compaction test (step 4) will be red on
  current code and force the fix during execution.
- Indirectly-covered functions were NOT re-proposed as gaps: `_remap_ids_in_json`
  (collision import test), `_safe_extract_zip` (Zip-Slip test), `_rebased_dir` (move
  tests), `consolidate_turns`/`truncate_*` (test_core.py) are already exercised.
- Test additions are low Remediation Risk (no product behavior change) and proposed by
  default; the sole behavior change (TEST-1 product fix) is desirable and low-risk.

## What was intentionally NOT proposed (and why)
- Coverage gating (TEST-10): deferred — Medium-High functionality/complexity risk; gating
  on a number forces low-value tests and can flake on a large single-file module.
- Property-based / load / real-opencode e2e suites: over-scope for a single-user local
  tool (KISS). Not proposed.
- A mocking framework: stdlib monkeypatch/unittest.mock suffices. Not proposed.

## Open questions for the user
1. Hand-authored `opencode_export.json` fixture vs a real sanitized export?
2. Confirm intended TUI compaction contract (write `.compacted.md` + notify) for TEST-1.
3. One `tests/test_recovery.py` vs split files? (Assumed one.)
