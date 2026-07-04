# IPD: Assess testing - close the recovery/compaction test gaps

- Date: 2026-07-04
- Concern: testing (rigor and completeness)
- Scope: whole project; emphasis on the recovery/compaction pipeline and the TUI
  compaction path, which are currently untested
- Status: PENDING (awaiting human approval; not executed)
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
| TEST-1 | High | Low | QA / regression | TUI compaction | `call_compaction_api(model_info, prompt_content)` passes 2 args (needs 3: model, prompt, verbosity) and treats the returned `str` as `result["content"]` → `TypeError` at runtime. Untested, so it shipped. | ocman_tui/app.py:1315-1316 vs ocman.py:787,893 |
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
| 1 | TEST-2 | Add a small realistic opencode-export JSON **fixture** (`tests/fixtures/opencode_export.json`) and tests asserting `find_turns` extracts expected user/assistant turns, honors `include_tools`, and falls back for raw text / unknown formats. | tests/fixtures/, tests/test_recovery.py (new) | Low | New tests pass; document the fixture's shape |
| 2 | TEST-5 | Test `render_transcript`, `render_restart_context`, `render_compact_prompt` on a small `Turn` list: assert headings/turn text/structure present (output-contract characterization). | tests/test_recovery.py | Low | New tests pass |
| 3 | TEST-4 | Unit-test `call_compaction_api` by monkeypatching `urllib.request.urlopen`: (a) non-HTTPS + non-localhost URL raises; (b) success payload → returns content; (c) empty choices / empty content / HTTPError → `RecoveryError`. | tests/test_recovery.py | Low | New tests pass without network |
| 4 | TEST-1 | Add a TUI compaction test (mock `call_compaction_api`) that drives the compaction worker and asserts it is called with the correct arity and a `.compacted.md` file is written. **This test will fail against current code**, forcing the app.py:1315-1316 fix (pass `verbosity`, use the returned string) as part of execution. Record the fix in the plan's outcome. | tests/test_tui.py, ocman_tui/app.py | Low | Test red before fix, green after; note the product fix in the execution outcome + CHANGELOG |
| 5 | TEST-3 | Add an integration test of the CLI recovery flow: feed the step-1 fixture through `recover_from_export` (or `main()` with `-s` and mocked `opencode` subprocess + mocked API), asserting restart/transcript files are produced with expected content. | tests/test_recovery.py | Low | New test passes with subprocess+API mocked |
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
- If step 4 changes TUI compaction behavior (from "crashes" to "works"), add a CHANGELOG
  entry under Fixed.

## Open questions

1. Is a hand-authored `opencode_export.json` fixture acceptable, or do you have a real
   (sanitized) export to use as the golden fixture? (Assumption: hand-author a minimal
   realistic one; confirm its shape matches your opencode version.)
2. For TEST-1, confirm the intended TUI compaction behavior is "write a `.compacted.md`
   and notify success" (assumed from the code) so the test encodes the right contract.
3. Should the new recovery tests live in one `tests/test_recovery.py` or be split? (Assumption: one file.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered steps; step 4 forces the TUI compaction fix (red→green).
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
