# Assessment run report - testing (whole project)

- Date / run ID: 20260704-143424
- Concern: testing (rigor and completeness)
- Scope: whole project; emphasis on recovery/compaction pipeline + TUI compaction
- IPD written: .agents/plans/pending/2026-07-04-assess-testing.md
- Verdict: **needs work** for testing — the DB/admin/move/export-import/backup surfaces are
  well tested (66 tests), but the product's headline recovery/compaction pipeline is
  essentially untested, and that gap has already let a real bug ship (TEST-1).

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| TEST-1 | High | Low | QA / regression | TUI compaction calls `call_compaction_api` with wrong arity + treats returned str as dict → `TypeError`; untested so it shipped (app.py:1315-1316) |
| TEST-2 | High | Low | testing expert | Core recovery parser `find_turns`/`extract_opencode_turns` has no fixture-based test |
| TEST-3 | High | Low | testing expert | No end-to-end recovery/compaction flow test (`recover_from_export`/`main()`) |
| TEST-4 | Medium | Low | software engineer | `call_compaction_api` branches (HTTPS refusal, errors, success) untested |
| TEST-5 | Medium | Low | software engineer | Output renderers unasserted |

(Full list incl. TEST-6..TEST-10 in `findings.csv`.)

## Proposed plan (summary)

1. Add a realistic opencode-export fixture + `find_turns`/`extract_opencode_turns` tests (TEST-2).
2. Assert the three output renderers' contracts (TEST-5).
3. Unit-test `call_compaction_api` with a mocked `urlopen` (TEST-4).
4. Add a TUI compaction test that is red on current code and forces the app.py fix (TEST-1).
5. Add an end-to-end recovery integration test (mocked subprocess + API) (TEST-3).
6. Unit-test the config-parsing helpers (TEST-6) and the pure estimators (TEST-7).
7. Positive legacy `db_data.json` import round-trip (TEST-8); document benchmark opt-in (TEST-9).

## Deferred (with reason)

- TEST-10 (coverage gating): Remediation Risk **Medium-High** on **functionality/complexity**
  — gating merges on a coverage number tends to force low-value tests and can flake on a
  large single-file module. Optional local-only coverage tool suggested instead. (Effort
  is not the reason.)

## Out-of-repo / organizational notes

- None. All proposed tests are runnable in-repo with stdlib mocking (no network, no
  `opencode` binary required).

## Next step

Review the IPD (optionally run the `plan-review` workflow on it) and approve before
execution. This workflow does not execute the plan. Note: TEST-1 documents a real,
currently-shipped bug in the TUI compaction path that this testing work will fix.
