# Plan Review — 2026-07-04-assess-testing.md

- Run ID: 20260704-144500
- Target plan: `.agents/plans/pending/2026-07-04-assess-testing.md`
- Reviewer: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us
- Verdict: **APPROVE WITH REVISIONS APPLIED**

## Step 0 — conventions discovered
- Guiding principles: none dedicated; universal fallback + `ARCHITECTURE.md` principles.
- Plan location/format: `.agents/plans/pending/`, IPD template.
- Contributor contract: `AGENTS.md`; README documents `PYTHONPATH=. pytest`.
- Stack: Python CLI (`ocman.py`) + Textual TUI; SQLite (prod == test store). pytest +
  anyio; CI matrix. Prod runtime == test runtime; no dialect drift.
- Domain invariants at-risk for this plan: (i) the recovery parser yields the same turns
  for a given export (regression guard target); (ii) `call_compaction_api` returns a
  content **string** (contract the TUI caller violates); (iii) renderer call signatures
  (`turns, source_name, session`).

## Findings

| ID | Severity | Scope | Area (rubric) | Finding | Rem. Risk | Decision | Resolution |
|----|----------|-------|---------------|---------|-----------|----------|------------|
| PR-1 | HIGH | — | F / D | Step 4 proposed **mocking `call_compaction_api`**, which hides the bug and would pass on broken code — defeating the red→green anti-regression purpose | Low | FIX | Rewrote step 4 to mock only the network so the real render/API calls execute and the bugs surface |
| PR-2 | HIGH | UNDER-SCOPE | I / F | TEST-1 understated the defect: `render_compact_prompt` is *also* called with wrong arity (app.py:1279,1303) and fails before the API call; `dummy_sess` is not a `SessionInfo`. Fix must cover all three | Low | FIX | Expanded TEST-1 finding + step 4 to enumerate and fix all three app.py bugs |
| PR-3 | MEDIUM | — | accuracy | TEST-1 implied a runtime crash; the worker catches the exception and shows "Compaction failed" (non-functional, not crashing); line 1279 fails before the worker | Low | FIX | Corrected wording in the finding |
| PR-4 | MEDIUM | — | D | Step 1 didn't frame the parser fixture as a golden/regression guard with a named invariant | Low | FIX | Reframed step 1 as golden/characterization with the named parser invariant + documented provenance |
| PR-5 | LOW | — | F | Step 5 e2e test should mock the export subprocess at its boundary and not depend on an `opencode` binary | Low | FIX | Specified patching `run_command`/`subprocess.run` + network |
| PR-6 | LOW | — | H | Fixture provenance/shape should be documented for cold-start regeneration | Low | FIX | Added to step 1 validation + open question 1 emphasis |

No BLOCKER; approach is sound. Not a REJECT — the plan's direction (test the untested
recovery/compaction pipeline, TDD the TUI bug) is correct; the key flaw was the mocking
strategy in step 4, now fixed.

## Edits applied (per plan)
`.agents/plans/pending/2026-07-04-assess-testing.md`:
- Findings table: rewrote TEST-1 to enumerate all three app.py bugs (render_compact_prompt
  arity at 1279/1303, call_compaction_api arity at 1315, str-as-dict at 1316, dummy_sess
  vs SessionInfo) and to correct "crash" → "caught, non-functional".
- Step 1: reframed as golden/characterization regression guard with named invariant +
  fixture provenance documentation.
- Step 2: call renderers with real signatures + a real `SessionInfo` (documents the
  correct shape for the step-4 fix).
- Step 3: assert the `str` return contract.
- Step 4: **mock only the network, not the ocman functions**; enumerate the full set of
  app.py fixes the red→green test forces; explicit "do NOT mock call_compaction_api" note.
- Step 5: mock the export subprocess at its boundary; deterministic, no `opencode` binary.
- Spec/doc sync: CHANGELOG entry must cover all three bugs.
- Open questions: emphasized fixture fidelity; added Q4 (app.py edits during a testing IPD).
- Added "Plan-review provenance" section.

## Deferred / open (with reasons)
- None newly deferred. TEST-10 (coverage gating) remains deferred by the IPD — Medium-High
  Remediation Risk on functionality/complexity; unchanged and justified.

## Next step
Human review/approval, then execution. Step 1 (fixture + golden parser tests) and step 4
(network-only-mocked TUI compaction test that forces the app.py fix) are the crux. This
workflow changed no application code.
