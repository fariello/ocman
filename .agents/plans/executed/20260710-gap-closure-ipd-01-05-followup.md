# Implementation Plan - Gap closure for executed IPDs 01-05

Status: EXECUTED

Post-execution verification of the five executed IPDs
(`.agents/plans/executed/20260709-01..05`) found the core features are largely
implemented, but two changed function return shapes were not propagated to all
callers/tests, one CLI dispatch has a keyword-argument typo, and a few smaller
gaps remain. The test suite is currently RED: **14 failed, 256 passed, 2
skipped** (`PYTHONPATH=. pytest`, Python 3.14). This plan closes those gaps and
returns the suite to green.

Evidence lines are `ocman.py:<line>` verified against the current tree on
2026-07-10; re-verify before editing (line numbers drift).

---

## How this was verified

- Ran the full suite: 14 failures (listed below), all traceable to two return
  shape changes plus one typo.
- Read the executed code for each IPD deliverable and confirmed feature presence
  with `ocman.py:line` evidence.
- Independently reproduced the CRITICAL `backup restore` break against the repo
  module (after removing a stale `site-packages/ocman.py` shadow copy that was
  masking it): `cli_restore(source=...)` raises
  `TypeError: unexpected keyword argument 'source'. Did you mean 'sources'?`.

Note (environment hazard): a stale `ocman.py` had reappeared in
`.../site-packages/` and shadowed the editable install. It was removed during
verification. Anyone validating this work must confirm `python -c "import
ocman; print(ocman.__file__)"` points at the repo, or run with `PYTHONPATH=.`.

---

## What is CORRECT (no action needed)

Recorded so the gap list is not mistaken for "IPDs failed".

- IPD 01: `list models` word-order rewrite to `["models", ...]`
  (`ocman.py:5369-5370`), `resolve_model_spec` (`ocman.py:713`),
  `db_get_session_stats` + `~msgs/~interactions/~parts` columns
  (`ocman.py:3976`, `11108-11129`). Tests present.
- IPD 02: `resolve_targets` with once-per-batch candidate fetch
  (`ocman.py:4737-4746`), kind-qualified `session:/project:/model:` prefix
  (`4755`), bare-integer-ambiguity guard (`4788`), interactive-vs-non-TTY
  ambiguity handling.
- IPD 03: variadic `specs` on compact/recover/show/delete; model-by-resolution
  (no `model` positional); exactly-one-model rule; estimate table + batch
  confirm + actuals summation; project expansion with `-A` added to
  compact/recover; `backup create` scoped bundles.
- IPD 04: `--show-secrets[=masked|raw]`, `--expunge-secrets`,
  allow/expunge mutual-exclusion, `finditer` spans + overlap-merge redaction,
  `-y` not bypassing the secret guard.
- IPD 05: multi-file batch-atomic restore CORE (`cli_restore(sources)` with one
  pre-batch backup + all-or-nothing rollback + up-front validation); import
  `--new-session-id` generation + remap + project-bundle refusal.

---

## Gaps to fix (ranked)

### G1 (BLOCKER) - `ocman backup restore` is dead on the CLI

`main()` dispatch calls `cli_restore(source=args.restore)` (`ocman.py:10603`),
but the function parameter is `sources` (`ocman.py:10172`). Every real
`ocman backup restore ...` raises `TypeError` before doing anything. Not caught
because tests call `cli_restore([...])` positionally, never through the CLI
dispatch.

Fix: change the call site to `cli_restore(args.restore)` (positional).
`_normalize` already sets `out["restore"]` to a single path (str) or a list
(`ocman.py:6164-6169`), and `cli_restore` accepts `list[str] | str`.

Test: an end-to-end/subprocess test that runs `ocman backup restore FILE`
(and `FILE1 FILE2`) through the real entry point and asserts success (guards the
dispatch path, not just the function). Extend `tests/test_ocman.py` e2e block or
`tests/test_config_backup_restore.py`.

### G2 (BLOCKER) - TUI compaction passes a tuple where a str is expected

`call_compaction_api` now returns `(content, usage_info)` (`ocman.py:857`,
`948-965`), but the TUI still does
`compacted_text = call_compaction_api(...)` (`ocman_tui/app.py:1331`; the stale
comment at 1329-1330 still says it returns a str). Writing `compacted_text`
then fails ("data must be str, not tuple"). Fails
`tests/test_tui.py::test_tui_compaction_end_to_end_network_mocked` and
`::test_tui_compaction_honors_out_dir_and_copies_to_project`.

Fix: unpack in the TUI: `compacted_text, _usage = call_compaction_api(...)` and
update the stale comment. Confirm no other `ocman_tui/*` caller uses the old
shape.

### G3 (HIGH) - stale tests + mocks not updated for the two changed return shapes

The `call_compaction_api` (str -> `(str, usage)`) and `run_compaction`
(Path -> `(path, usage, did_expunge)`) contract changes were not propagated to
existing tests/mocks. Failing (10):
- `tests/test_recovery.py::test_call_compaction_api_success_returns_content_string`
  asserts `== "COMPACTED"`; now returns a tuple.
- `tests/test_recovery_naming.py::test_run_compaction_uses_local_canonical`
  mocks a bare-string API and treats the return as a single Path.
- 8 x `tests/test_file_tools.py::test_filter_*`: `fake_api` returns a bare
  string; `filter` unpacks a tuple (`ocman.py:6917`), so the mock breaks with
  "too many values to unpack".

Decision: the PRODUCTION `filter` path is correct (it unpacks `text, _`); the
FIX is to update the tests/mocks to the new contract (mocks return
`("text", None)`; assertions expect the tuple / new `run_compaction` shape).
Do NOT revert the return-shape change (IPD 03 relies on it for actuals). Where a
test only cares about the text, unpack `text, _`.

### G4 (HIGH) - `session delete` re-prompts per session on a TTY

Multi-session delete shows one batch preview + one `confirm_destructive(...,
assume_yes=args.yes)` (`ocman.py:11283-11300`), but then calls
`db_delete_session_recursive(session_id=..., ...)` WITHOUT `confirm=False`
(`ocman.py:11304-11309`); its default `confirm=True` (`ocman.py:7103`) triggers a
SECOND typed-'yes' prompt per session (`ocman.py:7213-7216`). This contradicts
IPD 03's "single typed confirm" and is only hidden because
`test_multi_session_delete` mocks `input` to always return "yes".

Fix: pass `confirm=False` to `db_delete_session_recursive` in the batch loop
(the batch already performed the single confirm / honored `-y`). Add a test that
asserts exactly ONE confirmation prompt is issued for an N-session delete (e.g.
count `input`/`confirm_destructive` invocations), so the regression cannot recur.

### G5 (LOW) - restore leaves the pre-batch rollback ZIP on success

`cli_restore` creates `rollback-before-restore-*.zip` (`ocman.py:10199`) but
never deletes it after all files succeed (IPD 05 spec step 4). Over time these
accumulate in the backups dir.

Fix: on the success path (after the final summary, `ocman.py:10395-10400`),
`rollback_file.unlink(missing_ok=True)`. Do NOT delete on the failure path (it
is the recovery artifact). Add an assertion to a restore-success test that the
rollback ZIP is gone.

### G6 (LOW) - `test_restore_rollback_safety` assertion drift

The test expects `match="Restoration failed and rolled back"`, but the code now
raises `"Restoration failed for {name} and rolled back: {e}"` (`ocman.py:10389`).
The behavior (rollback) is correct; the regex is stale.

Fix: update the test regex to `r"Restoration failed.*rolled back"` (tolerant of
the `for {name}` insertion), keeping it meaningful.

### G7 (MEDIUM) - missing tests for behaviors that currently have none

These IPD 03/04 behaviors are implemented but untested, so they are unprotected
against regression. Add:
- compact: a mid-batch per-session failure is reported and the batch CONTINUES
  (IPD 03 #5).
- compact: the estimate table shows per-session + grand total + average, and the
  post-run actuals are summed (and reported "unavailable" when the API omits
  `usage`) (IPD 03 #4).
- `--show-secrets=masked` end-to-end: the matched line is shown with the value
  masked and the raw value is absent from output.
- `--show-secrets=raw`: requires the TTY typed "reveal" confirm; without it the
  value is not printed.
- `-y` with a detected secret and neither `--allow-secrets` nor
  `--expunge-secrets`: still REFUSES (IPD 04 #5).

### G8 (LOW / hardening) - redaction re-scan relies on placeholder string-mangling

`redact_secrets` avoids re-triggering keyword detectors by mangling the kind in
the placeholder (e.g. `key` -> `k_e_y`, `ocman.py:6575`) so the re-scan yields no
hits. This works for the current detector set but is fragile if patterns change.

Fix (low-risk): use a placeholder that structurally cannot match any detector
(e.g. `[REDACTED]` with no secret-like keyword and no token-shaped value), and
keep the existing "re-scan yields no hits" property test as the guard. Confirm
against all current `_SECRET_PATTERNS`.

---

## Execution order

1. G1, G2 (BLOCKERs: broken CLI restore + broken TUI compaction).
2. G3, G4 (stale-test propagation; delete double-confirm).
3. G5, G6, G7, G8 (cleanup, assertion drift, missing tests, hardening).
4. Full `PYTHONPATH=. pytest` must be GREEN (target: 0 failures; only the 2
   intentional perf-benchmark skips remain).

---

## Tests / verification (summary)

- Suite returns to green (14 -> 0 failures).
- New guards: CLI-dispatch restore success (G1), TUI compaction tuple-unpack
  (G2), single-confirm delete (G4), rollback-ZIP cleanup (G5), and the G7 set.
- Re-run confirms `import ocman` resolves to the repo (no shadow copy).

---

## Docs

- Update `ocman_tui/app.py` stale comment (G2).
- No user-facing behavior change beyond fixing broken `backup restore`; note in
  the changelog that `backup restore` and TUI compaction were fixed.

---

## Non-goals

- Reverting the `call_compaction_api` / `run_compaction` return-shape changes
  (IPD 03's actual-cost summation depends on them).
- New features beyond closing the verified gaps above.
