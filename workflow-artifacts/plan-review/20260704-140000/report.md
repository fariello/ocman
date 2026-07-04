# Plan Review — 2026-07-04-assess-performance.md

- Run ID: 20260704-140000
- Target plan: `.agents/plans/pending/2026-07-04-assess-performance.md`
- Reviewer: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us
- Verdict: **APPROVE WITH REVISIONS APPLIED**

## Step 0 — conventions discovered
- Guiding principles: none dedicated; universal fallback + `ARCHITECTURE.md` principles.
- Plan location/format: `.agents/plans/pending/`, IPD template (goal, findings, ordered
  changes, deferred, scope check, tests, spec sync, open questions, approval gate).
- Contributor contract: `AGENTS.md` (workflows index); README user-facing; CHANGELOG per release.
- Project type/stack: Python CLI (`ocman.py`) + Textual TUI; SQLite (pysqlite3/stdlib). Prod
  data store == test data store (SQLite) — no dialect drift risk.
- Domain invariants (at-risk for this plan): (i) id remap maps every occurrence of an old
  session id to its new id and alters nothing else; (ii) a session `directory` is rebased iff
  it equals or is nested under the old prefix; (iii) cumulative history totals are never lost.

## Findings

| ID | Severity | Scope | Area (rubric) | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|---------------|---------|------------------|----------|------------|
| PR-1 | MEDIUM | — | F (precision) | IPD `file:line` anchors wrong: PERF-3 `5195-5209` (actual 5227-5232 / 5285-5292), PERF-5 `5497-5518` (actual 5504-5519) | Low | FIX | Anchors corrected against source |
| PR-2 | HIGH | UNDER-SCOPE | D / G | PERF-3 omitted `db_rebase_paths` (5363-5368), which shares the identical unscoped-scan + per-row `resolve()` pattern | Low | FIX | Step 3 now covers all three functions via one shared helper |
| PR-3 | HIGH | — | D (anti-regression) | No characterization tests pinning current output before the PERF-1/PERF-3 logic changes | Low | FIX | Added step 0 (baseline tests) + named at-risk invariants |
| PR-4 | MEDIUM | — | D / I | PERF-1's current substring `str.replace` is a latent correctness bug; plan framed it as pure perf ("preserves output") | Low | FIX | Reframed as perf + latent correctness fix; test asserts corrected mapping; CHANGELOG note |
| PR-5 | MEDIUM | — | A / C | PERF-3 SQL `LIKE` scoping matches raw stored strings, but current code compares `resolve()`-canonicalized paths → could miss non-canonical rows | Low | FIX | Clarified SQL is a candidate pre-filter; authoritative match stays in Python; added non-canonical-path test |
| PR-6 | LOW | — | F | Timing benchmark could become a flaky pass/fail gate | Low | FIX | Marked informational-only, never a CI gate |
| PR-7 | LOW | — | E / H | PERF-4 didn't specify trim-on-read vs on-save for existing over-cap files | Low | FIX | Specified trim on save only (never mutate on read) |

No BLOCKER findings. No REJECT-level unsoundness — the plan's approach is sound; edits harden it.

## Edits applied (per plan)
`.agents/plans/pending/2026-07-04-assess-performance.md`:
- Findings table: corrected PERF-3/PERF-5 anchors; expanded PERF-3 to name all three
  functions incl. `db_rebase_paths`; added PERF-1 latent-substring-bug note.
- Proposed changes: inserted **step 0** (characterization tests + named invariants);
  expanded step 3 to all three functions via a shared helper and clarified SQL pre-filter
  semantics; reframed step 2 as perf+correctness with a substring-collision test; marked
  the benchmark informational-only (step 1); specified PERF-4 trim-on-save (step 4);
  refreshed step-5 anchor.
- Scope check: recorded the `db_rebase_paths` under-scope catch and the characterization
  addition.
- Open questions: added the PERF-1 correctness-confirmation question.
- Added a "Plan-review provenance" section documenting the hardening.

## Deferred / open (with reasons)
- None deferred. PERF-2 was already correctly deferred by the IPD (Medium-High Remediation
  Risk on functionality — streaming rewrite of the core recovery pipeline). Left as-is;
  its deferral is justified and unchanged.

## Next step
Human review/approval of the revised IPD, then execution (step 0 characterization tests
first). This workflow did not execute the plan and changed no application code.
