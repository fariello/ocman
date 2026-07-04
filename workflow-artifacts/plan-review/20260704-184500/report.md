# Plan Review — 2026-07-04-assess-functionality-restart-to-project-prompts.md

- Run ID: 20260704-184500
- Target plan: `.agents/plans/pending/2026-07-04-assess-functionality-restart-to-project-prompts.md`
- Reviewer: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us
- Verdict: **APPROVE WITH REVISIONS APPLIED**

## Step 0 — conventions discovered
- Guiding principles: none dedicated; universal fallback + ARCHITECTURE.md (KISS, honest docs, self-documenting).
- Plan location/format: `.agents/plans/pending/`, IPD template. Validation `PYTHONPATH=. pytest`.
- Stack: Python CLI + Textual TUI; SQLite (prod == test).
- Domain invariants at-risk for this plan: (i) recovery's **primary outputs must not be broken** by the new
  copy side-effect (fail-soft); (ii) writes must stay **inside** the target project's `.agents/prompts/pending`;
  (iii) the requested backup scheme (`.restart.bu.NNN.md`, 001+) differs from the existing `_backup_if_exists`.

## Findings

| ID | Severity | Scope | Area (rubric) | Finding | Rem. Risk | Decision | Resolution |
|----|----------|-------|---------------|---------|-----------|----------|------------|
| PR-1 (RSP-9) | MEDIUM | — | G / plumbing | Plan glossed that `recover_from_export` has **no project-dir param**; needs threading through the signature + **both** call sites (8150, 8184) where `opencode_cwd` is in scope | Low | FIX | Step 5 now specifies the signature + both-call-site threading |
| PR-2 (RSP-10) | MEDIUM | UNDER-SCOPE (disclosure) | I / stakeholder | Feature is **CLI-only** — the TUI "write restart" button (app.py:1274) uses a separate path and would NOT copy; user may expect parity | Low | FIX | Documented as a scope boundary + open Q5; TUI parity deferred |
| PR-3 (RSP-11) | LOW | — | A / correctness | Placeholder `SessionInfo` has `raw={}` → `session.raw["directory"]` would KeyError | Low | FIX | Step 1 uses `.get("directory")`; no-KeyError test added |
| PR-4 (RSP-12) | LOW | — | accuracy | `recover_from_export` returns a literal `[transcript, restart, compact]`, not `generated_paths`; whether to list the copied path is a UX choice | Low | FIX | Step 5 corrected; listing decision routed to open Q5 |

No BLOCKER. The approach is sound (write point, name/date, backup scheme, fail-soft, path containment were all
correct in the draft — I verified them against source). Not a REJECT.

## Edits applied (per plan)
`.agents/plans/pending/2026-07-04-assess-functionality-restart-to-project-prompts.md`:
- Findings table: added RSP-9 (plumbing), RSP-10 (CLI-only scope), RSP-11 (KeyError safety), RSP-12 (return shape).
- Step 1: `session.raw.get("directory")` + no-KeyError test.
- Step 5: thread `project_dir` + `copy_to_project_prompts` params through the signature and BOTH call sites
  (pass `opencode_cwd`); corrected the return-shape wording; routed "list the copied path?" to open Q5.
- Scope check + Deferred: recorded the CLI-only boundary and TUI-parity deferral.
- Open questions: added Q5 (CLI-only vs TUI parity).
- Added a "Plan-review provenance" section.

## Deferred / open (with reasons)
- Copy transcript/prompt/compacted too: out of scope — request is restart-only (RSP-8). Unchanged.
- TUI parity (RSP-10): deferred (scope) — separate code path + TUI thread; open Q5 lets the user opt in.
- SD-style deferrals from the assess run (session id / last-activity) do not apply to this plan.

## Next step
Human review/approval + answers to the 5 open questions (esp. Q1 project-dir precedence, Q5 CLI-only vs TUI),
then execution. The crux: thread the project dir cleanly and keep the copy **fail-soft** so it never breaks the
primary recovery output. This workflow changed no application code.
