# Plan Review — destructive-confirm helper (architecture) + clean-backups preview

- Run ID: 20260704-190800
- Target plans (reviewed jointly — tightly coupled):
  - `.agents/plans/pending/2026-07-04-assess-architecture-destructive-confirm-helper.md` (the abstraction)
  - `.agents/plans/pending/2026-07-04-assess-self-documentation-clean-backups-preview.md` (its first adopter)
- Reviewer: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us
- Verdict: **APPROVE WITH REVISIONS APPLIED**

## Step 0 — conventions discovered
- Guiding principles: none dedicated; universal fallback + ARCHITECTURE.md (KISS, consistency, honest docs).
- Plan lifecycle `.agents/plans/pending/` → `done/`. Validation `PYTHONPATH=. pytest`.
- Stack: Python CLI + Textual TUI; SQLite.
- **Domain invariant (safety-critical), verified against source:** every destructive op proceeds ONLY on a
  typed `yes`. `force` bypasses ONLY the running-`opencode` process-lock — NOT the prompt. The prompt is
  skipped only by the delete fns' separate `confirm=False` param (the TUI path). Confirmed at
  ocman.py:4596 (force=lock), 4696-4699 (dry_run returns pre-prompt), 4705 (confirm gates prompt), 6074 &
  7288 (cleanup/clean-backups always prompt).

## Findings

| ID | Severity | Scope | Area (rubric) | Finding | Rem. Risk | Decision | Resolution |
|----|----------|-------|---------------|---------|-----------|----------|------------|
| PR-1 (ARCH-9) | **BLOCKER** (if executed as first drafted) | — | D / B (safety) | `confirm_destructive(..., assume_yes)` invited mapping each op's `force` → `assume_yes`; but `force` never skips the prompt today. That mapping would silently drop destructive confirmations for `--force` users | Low | FIX | Design + steps now forbid `force→assume_yes`, specify `assume_yes=(not confirm)` for delete fns / `False` for cleanup; step-1 tests must assert "`--force` still prompts" |
| PR-2 (ARCH-9) | MEDIUM | — | D / F | Step-1 characterization wording "`force`/`confirm=False` bypasses" conflated the two — baking the PR-1 bug into the test spec | Low | FIX | Step 1 rewritten to pin: force does NOT skip prompt; confirm=False does (delete fns) |
| PR-3 (ARCH-10) | LOW | — | consistency | clean-backups sizing should reuse the existing `dir_usage()` helper, not re-walk | Low | FIX | Both IPDs now reference `dir_usage()` (ocman.py:6210) |
| PR-4 | LOW | over-scope | G / KISS | Renderer's "header labels via noun/column config" drifted toward the config-driven rendering the plan elsewhere defers | Low | FIX | Fixed column set; caller supplies only two header label strings |
| PR-5 | LOW | — | consistency | Two IPDs both specified the table format → drift risk | Low | FIX | Architecture IPD is source of truth for the renderer; clean-backups IPD now says it inherits the format + describes only its inputs |

No REJECT — the approach (small seam, characterization-first, incremental migration, CLI-first) is sound;
the one serious issue (PR-1) is a mapping trap, fixable in the plan.

## Edits applied (per plan)
Architecture IPD:
- Added ARCH-9 (the `force`/`assume_yes` safety trap) and ARCH-10 (`dir_usage` reuse).
- Confirm-seam design: added a SAFETY note specifying per-op `assume_yes` mapping; **never** `force`.
- Step 1: pin flag semantics incl. "`--force` still prompts"; step 4: specify the correct per-op mapping.
- Renderer: fixed column set (KISS), caller supplies only two label strings.
- Added Plan-review provenance.

Clean-backups IPD:
- Step 1: reuse `dir_usage()` instead of a fresh `os.walk`.
- Added a Sequencing note: the shared renderer (headers/right-align/DELETE-KEEP/warning) is owned by the
  architecture IPD; this plan supplies the clean-backups inputs and inherits the format (fixes PR-5 drift).

## Deferred / open (with reasons)
- ARCH-4 (unify CLI+TUI confirm I/O): Medium-High / functionality — sync prompt vs async modal; share only
  the pure render string. Unchanged.
- Config/plugin/i18n renderer generalization (ARCH-6): Medium-High / complexity. Unchanged.

## Next step
Human review/approval + answers to the architecture IPD's open questions (esp. Q2 `--clear-history` gating,
Q4 clean-backups supersede/keep). Execute architecture IPD first (characterization tests first; the ARCH-9
mapping is the thing to get right), with clean-backups as the first adopter. This workflow changed no app code.
