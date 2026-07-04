# Evidence - assess-performance 20260704-135426

Read-only assessment. No code changed.

## Files inspected (ocman.py)
- Import path: `extract_and_import_session` / `process_and_insert_row` and the
  collision remap — lines ~5508-5769; the O(diffs × ids) string-replace loop at
  **5748-5758** (esp. 5750-5755).
- Export path: `bundle_session_data` — batched `fetchmany(1000)` streaming to per-table
  temp JSONL at **5497-5518** (fixed temp filenames in `gettempdir()`).
- Move metadata: `db_move_project_metadata` **5171-5259** and `db_move_session_metadata`
  **5261-5287** — per-row `Path().resolve()`; move-session `SELECT id, directory FROM
  session` (unscoped) at ~5286.
- Recovery load: `load_export_file` **1642** (`read_text`), `load_prior_context_files`
  **3087** (`read_text` per file, concatenated).
- Rendering: `render_transcript` **2538+** — uses a `lines` list + join (efficient).
- History: `_load_history`/`_save_history` **6201-6260** — whole-file JSON load + atomic
  rewrite; `cumulative` precomputed; `runs` list unbounded.
- Delete/cleanup: chunking at 999 (`4581-4582`, `5864`, `6221`) — already scale-safe.

## Commands run
- `grep`/`Read` over the paths above (needle inspection; no execution of ocman itself).
- Prior release-review (run 20260703-134213) explore-agent map of `ocman.py` used as a
  secondary index; all performance claims here were re-verified against current source.
- No profiler was run (no benchmark harness exists — that gap is PERF-6). Findings are
  grounded in complexity arguments read from the code, per the lens ("reason from the
  code, do not guess").

## Sampling / truncation notes
- `ocman.py` is ~8074 lines; inspection targeted the hot paths above rather than a full
  line-by-line read. TUI (`ocman_tui/`) was reviewed for worker/threading perf in the
  prior release-review; no new performance hot path there (UI-bound, backgrounded).
