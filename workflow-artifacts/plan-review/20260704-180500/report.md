# Plan Review — 2026-07-04-assess-self-documentation-process-lock.md

- Run ID: 20260704-180500
- Target plan: `.agents/plans/pending/2026-07-04-assess-self-documentation-process-lock.md`
- Reviewer: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us
- Verdict: **APPROVE WITH REVISIONS APPLIED**

## Step 0 — conventions discovered
- Guiding principles: none dedicated; universal fallback + ARCHITECTURE.md. Concern = "errors that teach".
- Plan location/format: `.agents/plans/pending/`, IPD template.
- Stack: Python CLI + Textual TUI; SQLite (prod == test). Validation `PYTHONPATH=. pytest`.
- Domain invariants at-risk for this plan (the key ones): (i) **the process-lock is a safety gate on
  destructive ops** — it must keep refusing when a real opencode is running and not `--force`; (ii) the
  check currently **fails open** (proceeds if the check errors) — verified at ocman.py:4610-4613; (iii)
  timestamp display convention is `datetime.fromtimestamp(...).strftime('%Y-%m-%d %H:%M:%S')`.

## Findings

| ID | Severity | Scope | Area (rubric) | Finding | Rem. Risk | Decision | Resolution |
|----|----------|-------|---------------|---------|-----------|----------|------------|
| PR-1 (SD-8) | MEDIUM | — | A / reliability | Plan's "graceful degrade" under-specified vs the existing **fail-open** semantics (except→pass proceeds if check errors); detector must not raise into caller | Low | FIX | Added SD-8; step 4 requires fail-open preserved, detector never raises non-RecoveryError |
| PR-2 (SD-9) | MEDIUM | — | D / I | Changing a destructive-op **gate**; an over-tight plausibility filter → false negative → data loss. Missing regression guard that a real instance is still matched | Low | FIX | Added SD-9 + a regression test (genuine `opencode continue` line must match); gate errs toward inclusion |
| PR-3 (SD-10) | LOW | — | functionality | CWD→project used naive "prefix match" (`/a/b` vs `/a/bc` mismatch) | Low | FIX | Step 3 now uses resolved-path containment (`is_relative_to`), sibling-path test added |
| PR-4 | LOW | — | F | Detector tests could spawn real `ps`/depend on OS | Low | FIX | Require injectable command-runner + canned `ps` output; added timeout/fail-open tests |
| PR-5 | LOW | — | E / consistency | Timestamp formatting not tied to the existing convention | Low | FIX | PR-6 note: use the `db_show_info` strftime convention |

No BLOCKER. Approach is sound (enumerate + format + de-dup, no new dep, within time budget). Not a REJECT.

## Edits applied (per plan)
`.agents/plans/pending/2026-07-04-assess-self-documentation-process-lock.md`:
- Findings table: added **SD-8** (fail-open safety semantics), **SD-9** (filter-direction is
  safety-critical), **SD-10** (path-aware CWD→project match).
- Step 3: naive prefix → resolved-path containment (`is_relative_to`) with a sibling-path test.
- Step 4: explicitly preserve gate semantics + **fail-open** (detector returns []/PIDs-only on
  error, never raises into caller; timeout → fail-open) and gate-strength (err toward inclusion).
- Required tests: injectable runner (no real `ps`), SD-9 regression guard (genuine match not dropped),
  fail-open + timeout cases, SD-10 sibling-path case; PR-6 timestamp-consistency note.
- Open questions: added Q4 (confirm gate errs toward inclusion).
- Added a "Plan-review provenance" section.

## Deferred / open (with reasons)
- SD-4 (per-process **session id**): Remediation Risk Medium-High / functionality — not reliably derivable;
  a guess on a destructive screen would mislead. Best-effort project (by CWD) substituted. Unchanged.
- SD-5 (true **last-activity**): Medium / functionality — not cheap/reliable; start+elapsed substituted. Unchanged.

## Next step
Human review/approval, then execution. The crux is step 4: enrich the message **without weakening the
safety gate** (fail-open preserved, real instances never filtered out). This workflow changed no app code.
