# Evidence - assess-testing 20260704-143424

Read-only assessment. No code changed.

## Inspected
- All test files read in full: `tests/test_ocman.py` (631 lines), `tests/test_core.py`
  (127), `tests/test_export_import.py`, `tests/test_move.py`,
  `tests/test_config_backup_restore.py`, `tests/test_tui.py`, `tests/test_perf.py`.
- `pytest --collect-only` → 66 tests collected.
- Cross-referenced each core `ocman.py` function against test references:
  functions with **0** direct test references: `call_compaction_api`, `find_turns`,
  `filter_conversation_turns`, `write_export_to_temp`, `load_export_file`,
  `recover_from_export`, `render_transcript`, `render_restart_context`,
  `render_compact_prompt`, `normalize_sessions`, `extract_session_objects`,
  `estimate_tokens`, `estimate_cost`, `parse_json_text`, `_read_file_ref`,
  `strip_jsonc_comments`. (`_remap_ids_in_json`/`_safe_extract_zip`/`_rebased_dir` show 0
  direct refs but ARE exercised indirectly — verified and excluded from gaps.)

## TEST-1 verification (the shipped bug)
- `ocman.py:787` `def call_compaction_api(model, prompt, verbosity) -> str` and
  `ocman.py:893` `return content` (a str, from `choices[0]["message"]["content"]`).
- `ocman_tui/app.py:1315` `result = call_compaction_api(model_info, prompt_content)`
  (2 args) and `:1316` `compacted_text = result["content"]`.
- The static type checker independently flags `app.py:1312` "Argument missing for
  parameter verbosity" and `app.py:1319`. Conclusion: TUI compaction raises `TypeError`
  at runtime; no test exercises it.

## Commands run
- `date +%Y%m%d-%H%M%S`, `git status --short` (clean), `pytest --collect-only -q`,
  targeted `grep` for function-vs-test references, and `Read` of the cited source ranges.

## Sampling / truncation notes
- `ocman.py` (~8100 lines) inspected at the function-signature and cited-range level, not
  line-by-line; test files read in full. No content truncated in a way that affects the
  findings.
