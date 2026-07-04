# IPD: Assess testing - close the recovery/compaction test gaps

- Date: 2026-07-04
- Concern: testing (rigor and completeness)
- Scope: whole project; emphasis on the recovery/compaction pipeline and the TUI
  compaction path, which are currently untested
- Status: EXECUTED (approved by user 2026-07-04; implemented — see Execution outcome below)
- Author: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us

## Goal

Give the test suite real confidence in ocman's **headline feature** — session recovery
and LLM compaction — which today is essentially untested end-to-end, while the DB
admin / move / export-import / backup-restore paths are well covered (66 tests). The
assessment already surfaced a concrete shipped bug in the untested TUI compaction path
(TEST-1), which is the clearest argument for the gap. Prioritize the highest-value
missing tests (critical paths, recently changed code, a real latent bug) over any
coverage number.

## Project conventions discovered (Step 0)

- Guiding principles: none dedicated; universal fallback + `ARCHITECTURE.md` principles.
- Pending-plans location/format: `.agents/plans/pending/` (existing), IPD template.
- Contributor/spec-sync contract: `AGENTS.md` (workflows index); README documents
  `PYTHONPATH=. pytest` as the test command.
- Stack/test setup: Python 3.10+, pytest; `anyio` for async TUI tests via `run_test()`;
  SQLite (prod == test store, no dialect drift). CI: matrix pytest, ubuntu/macos/windows
  × py3.10-3.14. Current: 66 tests (2 opt-in benchmarks skipped by default).
- Existing coverage (strong): config load/save, backup/restore incl. rollback + Zip-Slip,
  export/import incl. SQLi + traversal rejection + collision remap, move/rebase (+ non-
  canonical path), delete/cleanup + history metrics, CLI arg preprocessing, TUI startup/
  admin/delete/prune/config-tab, `_safe_call_from_thread`, model resolution, turn
  consolidate/truncate.
- Coverage gaps (this IPD): the recovery *parse* pipeline (`find_turns`/
  `extract_opencode_turns`), the end-to-end recovery/compaction flow, the API client
  (`call_compaction_api`), the output renderers, several parsing helpers, pure
  estimators, and the TUI compaction path (which is currently broken — TEST-1).

## Findings

Severity = impact if left alone; Remediation Risk = Fix-Bar gate. Test additions are
inherently low Remediation Risk (they do not change product behavior) — except where a
test forces a product fix (TEST-1), which is itself low-risk and desirable.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| TEST-1 | High | Low | QA / regression | TUI compaction | The TUI compaction path is **non-functional** (multiple untested arity/type bugs): (a) `render_compact_prompt(self.current_turns, dummy_sess)` passes 2 args but the fn needs `turns, source_name, session` (app.py:1279, 1303 vs ocman.py:3175) — fails *before* the API call; (b) `call_compaction_api(model_info, prompt_content)` passes 2 args (needs `model, prompt, verbosity`) and then does `result["content"]` on the returned **str** (app.py:1315-1316 vs ocman.py:787,893); (c) `dummy_sess` is a duck-typed object, not a `SessionInfo`. Exceptions are caught by the worker's `try/except` and surfaced as "Compaction failed: ...", so it does not crash the app — it simply never works. Untested, so it shipped. | ocman_tui/app.py:1279,1303,1315-1316 vs ocman.py:3175,2596,787,893 |
| TEST-2 | High | Low | testing expert / QA | recovery parser | `find_turns`/`extract_opencode_turns` (core export→Turns parser) has no fixture-based test | ocman.py:2106, 1948 |
| TEST-3 | High | Low | testing expert | e2e recovery | `recover_from_export` / CLI recovery+compaction `main()` flow untested end-to-end | ocman.py:3341, main() |
| TEST-4 | Medium | Low | software engineer | API client | `call_compaction_api` branches (HTTPS refusal, HTTP error, empty response, success) untested | ocman.py:787-892 |
| TEST-5 | Medium | Low | software engineer | renderers | `render_restart_context`/`render_compact_prompt`/`render_transcript` output unasserted | ocman.py:2538, 2596 |
| TEST-6 | Medium | Low | software engineer | config parsing | `strip_jsonc_comments`/`parse_json_text`/`_read_file_ref`/`expand_env_vars` under-tested at the ocman level | ocman.py:401,1165,465,486 |
| TEST-7 | Low | Low | software engineer | pure helpers | `estimate_tokens`/`estimate_cost` untested | ocman.py:732,749 |
| TEST-8 | Low | Low | testing expert | import back-compat | Legacy `db_data.json` import branch only exercised by rejection tests; no positive round-trip | ocman.py extract_and_import_session |
| TEST-9 | Low | Low | testing / CI | benchmark opt-in | Document the `OCMAN_BENCHMARK=1` opt-in so contributors know it exists (CI correctly skips it) | tests/test_perf.py, ci.yml |
| TEST-10 | Low | Medium-High (functionality) | testing expert | coverage tooling | No coverage tool; gating on a number would be noisy on a large single-file module | pyproject.toml |

## Proposed changes (ordered, validatable)

| Step | Source IDs | Change | Files | Rem. Risk | Validation |
|------|-----------|--------|-------|-----------|------------|
| 1 | TEST-2 | Add a small realistic opencode-export JSON **fixture** (`tests/fixtures/opencode_export.json`) and **golden/characterization** tests asserting `find_turns` extracts the expected ordered user/assistant turns, honors `include_tools` on/off, and falls back for raw text / unknown formats. Named invariant: *the parser yields the same turns for a given export*; this fixture is the regression guard for future parser changes. | tests/fixtures/, tests/test_recovery.py (new) | Low | New tests pass; fixture shape + provenance documented in the test/file header so it can be regenerated |
| 2 | TEST-5 | Test `render_transcript`, `render_restart_context`, `render_compact_prompt` on a small `Turn` list, **calling them with their real signatures** (`turns, source_name, session` for the latter two; construct a real `SessionInfo`). Assert headings/turn text/structure present (output-contract characterization). Constructing a real `SessionInfo` here also documents the correct call shape the TUI fix (step 4) must adopt. | tests/test_recovery.py | Low | New tests pass |
| 3 | TEST-4 | Unit-test `call_compaction_api` by monkeypatching `urllib.request.urlopen`: (a) non-HTTPS + non-localhost URL raises; (b) success payload → returns the content **string**; (c) empty choices / empty content / HTTPError → `RecoveryError`. Assert the return is a `str` (pins the contract the TUI caller violates). | tests/test_recovery.py | Low | New tests pass without network |
| 4 | TEST-1 | Add a TUI compaction test that drives `run_llm_compaction`/`compaction_worker` and **mocks ONLY the network** (`urllib.request.urlopen`), NOT the ocman functions — so the real `render_compact_prompt` and `call_compaction_api` calls execute and their arity/type bugs actually surface. Assert a `.compacted.md` file is written and a success (not "Compaction failed") notification occurs. **This test is red against current code** and forces fixing ALL of the app.py bugs in TEST-1: `render_compact_prompt(turns=..., source_name=..., session=<real SessionInfo>)` at 1279 & 1303, `call_compaction_api(model_info, prompt, verbosity=0)` at 1315, and using the returned string (drop `["content"]`) at 1316; replace the `dummy_sess` duck type with a real `SessionInfo`. (Mocking `call_compaction_api` itself would hide the bugs and let the test pass on broken code — do NOT do that.) | tests/test_tui.py, ocman_tui/app.py | Low | Test red before fix, green after; product fix noted in execution outcome + CHANGELOG |
| 5 | TEST-3 | Add an integration test of the CLI recovery flow: feed the step-1 fixture through `recover_from_export` (or `main()` with `-s`), mocking the export subprocess at its boundary (patch `run_command`/`subprocess.run` used by `write_export_to_temp`) and the network for the API. Assert restart/transcript files are produced with expected content. Do not depend on an installed `opencode` binary. | tests/test_recovery.py | Low | New test passes deterministically with subprocess+network mocked |
| 6 | TEST-6 | Unit-test `strip_jsonc_comments`, `parse_json_text` (lenient + strict-failure), `_read_file_ref`, and `expand_env_vars` incl. malformed input and the `{file:}/{env:}/${VAR}` forms directly against `ocman`. | tests/test_config_parsing.py (new) | Low | New tests pass |
| 7 | TEST-7 | Unit-test `estimate_tokens` (heuristic bounds) and `estimate_cost` (math; None-cost model → None). | tests/test_recovery.py | Low | New tests pass |
| 8 | TEST-8 | Add a positive legacy `db_data.json` import round-trip test asserting rows import correctly. | tests/test_export_import.py | Low | New test passes |
| 9 | TEST-9 | Document the benchmark opt-in (`OCMAN_BENCHMARK=1 PYTHONPATH=. pytest tests/test_perf.py -s`) in the README testing section. | README.md | Low | Docs only |

## Deferred / out of scope (with reason)

| Finding ID | Rem. Risk | Axis | Reason | Recommended later step |
|------------|-----------|------|--------|------------------------|
| TEST-10 | Medium-High | functionality | Coverage *gating* on a number tends to force low-value tests and can flake on a large single-file module; it would push scope toward chasing lines rather than behavior (KISS). | Optionally add `coverage` as an opt-in *local* tool (never a CI merge gate) to guide test authoring; decide separately. |

## Scope check

- **Over-scope (avoid):** Do not add property-based, load, or e2e-against-real-opencode
  suites — disproportionate for a single-user local tool (KISS). Do not chase a coverage
  percentage. Do not add a mocking framework; stdlib `monkeypatch`/`unittest.mock` suffices.
- **Under-scope (add):** The recovery/compaction pipeline is the product's headline
  feature and is essentially untested; the fixture + parser + e2e tests (steps 1-5) are
  the required additions. TEST-1 shows a real shipped bug the gap allowed.

## Required tests / validation

- `PYTHONPATH=. pytest` stays green and grows by the new tests. New async TUI test uses
  the existing `anyio` + `run_test()` pattern. All API/subprocess interactions are mocked
  (no network, no `opencode` binary needed) so tests stay deterministic and CI-safe.
- Step 4 is the one behavior-affecting change (fixes the TUI compaction call); it must be
  red-before/green-after and noted in the execution outcome.

## Spec / documentation sync

- Step 9 updates the README testing section (benchmark opt-in).
- Step 4 changes TUI compaction from "always fails" to "works": add a CHANGELOG entry
  under Fixed covering all three app.py bugs (render_compact_prompt arity,
  call_compaction_api arity, str-treated-as-dict).

## Open questions

1. Is a hand-authored `opencode_export.json` fixture acceptable, or do you have a real
   (sanitized) export to use as the golden fixture? This materially affects TEST-2/3
   fidelity — a real export is strongly preferred so the parser test reflects the actual
   opencode format. (Assumption: hand-author a minimal realistic one; confirm its shape.)
2. For TEST-1, confirm the intended TUI compaction behavior is "write a `.compacted.md`
   and notify success" (assumed from the code) so the test encodes the right contract.
3. Should the new recovery tests live in one `tests/test_recovery.py` or be split? (Assumption: one file.)
4. TEST-1 involves editing product code (`ocman_tui/app.py`) — confirm this IPD is
   allowed to change app.py during execution (it is a test-driven bug fix, not just test
   additions), or whether you want the app.py fix tracked as a separate change.

## Plan-review provenance (2026-07-04)

Hardened by the `plan-review` workflow (run 20260704-144500). Changes applied after
re-reading the cited source:

- **Corrected TEST-1** (verified against app.py:1279/1303/1315-1316 and ocman.py):
  it is not a single `call_compaction_api` arity bug — `render_compact_prompt` is *also*
  called with the wrong arity (and fails first), and `dummy_sess` is not a `SessionInfo`.
  The exception is *caught* by the worker (surfaced as "Compaction failed"), so it is
  non-functional rather than app-crashing; wording corrected.
- **Fixed step 4's method (was a real flaw):** the draft proposed mocking
  `call_compaction_api`, which would hide every bug and let the test pass on broken code.
  Revised to mock **only** the network (`urllib.request.urlopen`) so the real
  render/API calls execute and the arity/type bugs surface (true red→green), and to
  require fixing all three app.py bugs.
- **Tightened steps 2, 5:** call renderers with real signatures + a real `SessionInfo`
  (documents the correct shape for the step-4 fix); mock the export subprocess at its
  boundary (`run_command`/`subprocess.run`) for a deterministic e2e test.
- **Framed step 1 as a golden/regression guard** with a named parser invariant and
  documented fixture provenance.
- Added open question 4 (app.py edits during a testing IPD).

Verdict: APPROVE WITH REVISIONS APPLIED.

## Execution outcome (2026-07-04)

Executed with explicit user approval (including the app.py edits per open question 4). All
steps completed; TEST-10 (coverage gating) remained deferred as planned.

- **TEST-2 (step 1):** `tests/fixtures/opencode_export.json` fixture + golden
  `find_turns`/`extract_opencode_turns` tests (with/without tools, raw-text + unknown-dict
  fallbacks) in `tests/test_recovery.py`.
- **TEST-5 (step 2):** renderer contract tests calling `render_transcript`/
  `render_restart_context`/`render_compact_prompt` with real signatures + real `SessionInfo`.
- **TEST-4 (step 3):** `call_compaction_api` unit tests mocking only `urllib.request.urlopen`
  (success returns a str; non-HTTPS refusal; empty choices/content; HTTPError → RecoveryError).
- **TEST-1 (step 4):** `test_tui_compaction_end_to_end_network_mocked` mocks only the
  network. Verified **red on pre-fix code** (`TypeError: render_compact_prompt() missing 1
  required positional argument: 'session'`) and **green after the fix**. Fixed all three
  app.py bugs: `render_compact_prompt` now passes `source_name=` + a real `SessionInfo`
  (app.py:1303 and the sibling "write prompt" export action at ~1279); `call_compaction_api`
  now passes `verbosity=0`; the returned string is used directly (dropped `["content"]`).
  Added `SessionInfo` to `ocman_tui/core.py` re-exports and `app.py` imports.
- **TEST-3 (step 5):** end-to-end `recover_from_export` test using the fixture (no
  subprocess/network dependency) asserting restart + transcript files are written.
- **TEST-6 (step 6):** `tests/test_config_parsing.py` for `strip_jsonc_comments`,
  `parse_json_text` (strict/lenient), `_read_file_ref`, `expand_env_vars`.
- **TEST-7 (step 7):** `estimate_tokens`/`estimate_cost` unit tests.
- **TEST-8 (step 8):** positive legacy `db_data.json` import round-trip.
- **TEST-9 (step 9):** README documents the benchmark opt-in; CHANGELOG notes the compaction fix.

Validation: `PYTHONPATH=. pytest` → **91 passed, 2 skipped** (was 66). Commit: see git history.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered steps; step 4 forces the TUI compaction fix (red→green).
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
