# Implementation Plan (consolidated, Sections 1-6 -> Section 7)

## Scope summary
Apply low-Remediation-Risk fixes under the Fix Bar: 1 High LIVE bug (already fixed), 1 High security
(Zip-Slip), 1 Medium MEM leak, 1 Medium edge-case crash, 2 regression tests, and doc/packaging honesty +
cold-start knowledge. Defer only the export-loader streaming refactor (Medium-High functionality risk).

## Non-goals
- No modularization of `ocman.py`. No public API/CLI/schema removal. No streaming rewrite of `load_export_file`.
- No CI lint/type-check additions. No push/publish. No changes to out-of-scope framework dirs.

## Change batches

### Batch A — LIVE/correctness fixes (product code)
- **S7-A1 / S2-B1 (High LIVE, done):** `self.call_from_thread` -> `self.app.call_from_thread` in Move/Export/
  Import modals. Already applied to `ocman_tui/app.py`; commit in this batch.
- **S7-A2 / S2-S1 (High security):** Add `_safe_extract_zip(zipf, dest)` helper in `ocman.py` that rejects any
  member whose resolved path escapes `dest` (absolute or `..`), then replace the two `zipf.extractall(...)`
  calls (6786, 6923) with it. Preserve existing error messages/behavior.
- **S7-A3 / S2-MEM1 (Medium MEM):** Wrap the second connection in `bundle_session_data` in try/finally so it
  closes on the error path (ocman.py ~5456-5491).
- **S7-A6 / S2-E1 (Medium bug):** Initialize `session_title`/`time_created_str`/`time_updated_str` to safe
  defaults before the metadata-fetch try in `_do_delete_session_worker` (app.py ~1379).

### Batch B — Regression tests
- **S3-T1:** Test that `cli_restore` rejects/contains a ZIP containing a `../` traversal member.
- **S3-T2:** Test that TUI `_do_delete_session_worker` does not crash when the session metadata row is absent
  (exercise the helper's summary construction, or refactor summary building into a testable function).

### Batch C — Docs + packaging honesty (KD/A/U/M)
- **S7-A4 / S1-A1:** Add `[1.0.3]` CHANGELOG entry.
- **S7-A5 / S1-A3:** `ocman_tui/__init__.py` imports `__version__` from `ocman` (single source), keeping a
  literal fallback if the import fails.
- **S1-A2:** Align README clone URL — since canonical URL is unconfirmed (Q1), set it to the actual remote
  (`opencode-recover`) OR leave a note; will ask/keep conservative. (Marked needs-confirmation.)
- **S4-U1:** Fix README rollback filename to `rollback-before-restore-<timestamp>.zip`.
- **S4-KD1:** Create concise `ARCHITECTURE.md` (entry points, TUI-reuses-CLI, data contracts, DB model,
  rollback-safety pattern, short design-principles section).

## Files likely to change
- `ocman.py` (S2-S1, S2-MEM1), `ocman_tui/app.py` (S2-B1 done, S2-E1), `ocman_tui/__init__.py` (S1-A3),
  `tests/` (T1, T2), `CHANGELOG.md`, `README.md`, `ARCHITECTURE.md` (new).

## Risk / public behavior
- All Low remediation risk. No public behavior change except: malicious/corrupt restore ZIPs now rejected
  (intended), and TUI ops now complete cleanly (bug fix). No API/CLI surface change.

## Required validation
- `PYTHONPATH=. pytest` must stay green (56 + new tests). `python -c "import ocman, ocman_tui"` import sanity.
  `python -c "ast.parse"` syntax.

## Local commit grouping
- Commit A (product fixes) referencing S7-A1/A2/A3/A6. Commit B (tests) T1/T2. Commit C (docs/version) A4/A5/U1/KD1.
- Run artifacts committed at the Section 7 boundary.

## Deferred / blocked
- **S2-MEM2** streaming refactor: DEFER (Medium-High functionality risk). Document limitation in README instead (S7-A7).
- **S1-A2** repo URL: needs user confirmation (Q1); apply conservative fix + flag.

## Deprecated-code / CI decisions
- No deprecations acted on (DEP1-4 left as-is, evidence insufficient/rename risky). No CI changes (see ci-assessment.md).
