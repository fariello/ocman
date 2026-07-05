# IPD: Assess architecture - shared destructive-confirmation / preview helper

- Date: 2026-07-04
- Concern: architecture and extensibility
- Scope: NARROWED (user request) to designing a **shared destructive-confirmation / preview
  abstraction** so ocman's destructive CLI ops can uniformly (a) preview the full outcome
  (keep vs remove), (b) warn forcefully on total/irreversible loss, and (c) confirm — instead
  of each op hand-rolling its own prompt.
- Status: EXECUTED (approved by user 2026-07-04; implemented across two runs — see Execution outcome)
- Author: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us

## Goal

Introduce the smallest structural seam that removes the duplicated/inconsistent destructive
confirmation logic and gives the KEEP/DELETE-preview + "you're deleting everything" warning a
single home. This is the abstraction the `--clean-backups` preview request needs to plug into
so that improvement (and future ones) is uniform rather than bespoke per command.

## Project conventions discovered (Step 0)

- Intent/audience: single-user local opencode admin tool; CLI (`ocman.py`) + Textual TUI.
- Guiding principles: none dedicated; universal fallback + `ARCHITECTURE.md` (**KISS**, consistency,
  self-documenting, honest docs). The architecture lens warns explicitly against over-engineering.
- Plan lifecycle: `.agents/plans/pending/` → `.agents/plans/executed/` (terminal dir).
- Validation: `PYTHONPATH=. pytest`.
- **Current state (verified):** four near-identical typed-`yes` confirmation blocks exist —
  `db_delete_session_recursive` (ocman.py:4705-4714), `db_delete_project_recursive` (4960-4967),
  `db_run_cleanup`/clean-orphans (6074-6079), `cli_clean_backups` (7287-7295). Styles diverge
  (`Type 'yes'` vs `[Y/n]` vs `[y/N]`); irreversibility warnings are ad hoc (delete prints a red
  "IRREVERSIBLE" line at 4702; clean-backups does not); **`--clear-history` (7607-7624) has NO
  confirmation at all.** The TUI has its own separate typed-`yes` modals (`DeletionSafetyModal`
  app.py:136, `ProjectDeletionSafetyModal` app.py:257).
- **Invariant (safety-critical):** for every destructive op, the confirm gate must keep proceeding
  ONLY on a typed `yes` (and bypass under force/confirm=False/dry-run exactly as today).

## Findings

Architecture changes carry blast radius — Remediation Risk is rated accordingly.

| ID | Severity | Rem. Risk | Persona | Finding | Evidence |
|----|----------|-----------|---------|---------|----------|
| ARCH-3 | High | Medium (functionality) | architect / stakeholder | No preview/outcome abstraction — each op hand-rolls its "what's affected" view; KEEP/DELETE + total-loss warning has no home (the driver) | ocman.py:4666-4712, 4920-4967, 6007-6079, 7262-7295 |
| ARCH-1 | Medium | Low | architect / software engineer | Four duplicated typed-`yes` confirmation blocks | ocman.py:4705-4714, 4960-4967, 6074-6079, 7287-7295 |
| ARCH-2 | Medium | Low | architect / novice | Inconsistent confirmation UX; `--clear-history` has none | ocman.py:4702, 4707/4962/6074/7288, 7442/7526, 7607-7624 |
| ARCH-4 | Medium | Medium-High (functionality) | architect | CLI/TUI confirmation duplication; forcing one abstraction across sync CLI + async Textual risks over-abstraction | ocman_tui/app.py:136, 257 |
| ARCH-5 | Low | Low | software engineer | dry_run/force/confirm interpreted per-op | ocman.py:4582, 4596, 5822, 7224 |
| ARCH-6 | Low | Medium-High (complexity) | architect | Risk of over-generalizing into a "framework" | KISS / scale |
| ARCH-7 | Medium | Low | architect / QA | Refactor must preserve exact confirm behavior (safety-critical) | ocman.py:4705-4714 etc. |
| ARCH-8 | Low | Low | stakeholder | Sequence vs the standalone clean-backups IPD (avoid two renderers) | .agents/plans/pending/20260704-assess-self-documentation-clean-backups-preview.md |
| ARCH-9 | **Blocker (if executed as first drafted)** | Low | architect / QA (security) | **`assume_yes` must NOT be wired to `force`.** In every current op, `force` bypasses only the running-`opencode` process-lock — never the typed-`yes` prompt (delete-session prompt is gated by the separate `confirm` param at ocman.py:4705; `db_run_cleanup`/`cli_clean_backups` always prompt, 6074/7288). Mapping `force`→`assume_yes` during migration would silently skip destructive confirmations for `--force` users. | ocman.py:4596 (force=lock only), 4705 (confirm gates prompt), 6074, 7288 |
| ARCH-10 | Low | Low | software engineer | clean-backups size should reuse the existing `dir_usage()` helper (added by the executed disk-usage feature) rather than re-walking dirs, for consistency | ocman.py:6210 `dir_usage` |

## Proposed design (the abstraction)

Two small, pure pieces + one thin I/O seam, all in `ocman.py` (no new module/package/dependency):

1. **A preview data model** (a small `@dataclass`, e.g. `DestructivePreview`):
   - `remove: list[PreviewItem]` and `keep: list[PreviewItem]` where `PreviewItem` holds
     `label` (name), optional `size_bytes`, optional `detail` (e.g. modified date / row counts).
   - `action_verb` (e.g. "delete", "prune", "overwrite"), `noun` ("backups", "sessions"),
     `irreversible: bool`.
2. **A pure renderer** `render_destructive_preview(preview) -> str`: builds the color-independent
   table with **column headers** (e.g. `Item` / `Size` / `Detail` / `Action`, adapted to the op's noun —
   for backups: `Backup` / `Size` / `Modified` / `Action`) and a separator rule; per item a row with the
   label (left), **size right-aligned** in its column, detail, and an `Action` cell holding the literal
   `DELETE`(red)/`KEEP`(green) word (words carry meaning; color is enhancement). Column widths are computed
   from plain-text content and **plain text is padded before coloring** so alignment holds with color on/off.
   Then totals and a **forceful warning when `keep == []` and `remove != []`** ("this will <verb> ALL
   <N> <noun> — nothing will remain"). Size column is right-aligned. **KISS (ARCH-6):** the column set is
   FIXED (Item / Size / Detail / Action); the caller supplies only two label strings — the item-column header
   (from `noun`, e.g. "Backup") and the detail-column header (e.g. "Modified"). No general column-config /
   pluggable-column mechanism. Pure (returns a string) so both CLI and TUI can use it.
3. **A confirm seam** `confirm_destructive(preview, *, dry_run, assume_yes, interactive=True) -> bool`:
   prints the rendered preview; if `dry_run` → print "(dry run)" and return False (no action); if
   `assume_yes`/`not interactive` → return True (bypass); else prompt `Type 'yes' to confirm <verb>:` and
   return `input().strip() == "yes"`, treating EOF/KeyboardInterrupt as a cancel. This is the single home for
   the typed-`yes` logic (ARCH-1/2/5).

   > **SAFETY — how `assume_yes` maps at each call site (do NOT get this wrong; see ARCH-9).** In the current
   > code, the per-op `force` flag bypasses ONLY the running-`opencode` **process-lock** check — it does
   > **not** skip the typed-`yes` prompt. The prompt is skipped only by the delete functions' separate
   > `confirm=False` parameter (used by the TUI, which runs its own modal). Therefore each migrated call site
   > MUST pass `assume_yes` derived from its **existing prompt-skip condition** — i.e. `assume_yes = (not
   > confirm)` for `db_delete_session_recursive`/`db_delete_project_recursive`, and `assume_yes = False`
   > (always prompt) for `db_run_cleanup` and `cli_clean_backups`. **Never map `force` → `assume_yes`** — doing
   > so would silently drop the confirmation for `--force` users (a safety regression). `force` continues to
   > gate only the process-lock, unchanged.

## Proposed changes (ordered, validatable)

| Step | Source IDs | Change | Files | Rem. Risk | Validation |
|------|-----------|--------|-------|-----------|------------|
| 1 | ARCH-7, ARCH-9 | **Characterization tests first** for the current confirm behavior of the four ops, pinning the exact flag semantics: typed `yes` proceeds; any other input / EOF / KeyboardInterrupt cancels; `dry_run` returns before prompting and deletes nothing; **`force` does NOT skip the typed-`yes` prompt** (it only bypasses the process-lock) — assert `--force` still prompts; and for the delete fns, `confirm=False` skips the prompt (the TUI path). These tests LOCK IN the correct mapping so the migration (steps 3-5) cannot silently drop a confirmation (ARCH-9). Green before any refactor. | tests/ | Low | New tests pass against current code, incl. an explicit "`force=True` still requires typed 'yes'" case |
| 2 | ARCH-3, ARCH-6 | Add the `PreviewItem`/`DestructivePreview` dataclass + `render_destructive_preview()` (pure) + `confirm_destructive()` (I/O seam) in `ocman.py`. Column **headers** + separator; **Size column right-aligned**; color-independent DELETE/KEEP `Action` column; forceful all-affected warning; pad-before-color. No config-driven rendering; no new dependency. | ocman.py | Low | Unit tests (color forced off): header row present; Size right-aligned (shared right edge); DELETE per remove, KEEP per keep; all-affected warning iff keep==[]; confirm seam returns True only on typed 'yes', respects dry_run/assume_yes |
| 3 | ARCH-1, ARCH-8 | **First adopter — `cli_clean_backups`:** build a `DestructivePreview` (remove=old backups, keep=retained), call `render_destructive_preview` + `confirm_destructive`. This realizes the clean-backups KEEP/DELETE request through the shared helper (supersedes the bespoke renderer in the clean-backups IPD; cross-reference it). | ocman.py:7224-7331 | Low | Characterization test (step 1) still green; clean-backups shows KEEP/DELETE + all-deleted warning |
| 4 | ARCH-1, ARCH-2, ARCH-5, ARCH-9 | Migrate the other three CLI confirmations to `confirm_destructive` **one at a time**, each behind its own characterization test: delete-session (4705-4714), delete-project (4960-4967), clean-orphans prune (6074-6079). **Map `assume_yes` from the op's existing prompt-skip condition — `assume_yes = (not confirm)` for the delete fns, `assume_yes = False` for cleanup; leave `force` wired to the process-lock only (ARCH-9).** Keep each op owning WHAT to delete; only the confirm/preview I/O moves to the helper. | ocman.py | Low | Per-op characterization tests green before+after each migration, including the "`force` still prompts" assertion |
| 5 | ARCH-2 | Bring `--clear-history` under the helper: add a `confirm_destructive` gate ("erase all N runs and reset grand totals"), currently unconfirmed. | ocman.py:7607-7624 | Low | Test: non-'yes' cancels; 'yes' clears; dry-run/force respected if applicable |
| 6 | ARCH-4 | **TUI reuse of the PURE parts only:** have the TUI deletion modals import `render_destructive_preview` for their scope/summary text where useful. Do NOT unify the confirm I/O (sync prompt vs async Textual modal). | ocman_tui/app.py:136, 257 | Low | TUI tests still pass; modal shows the shared summary string |
| 7 | docs | ARCHITECTURE.md: document the destructive-confirmation seam (data model + renderer + confirm) as the one way to do destructive confirmations. README/CHANGELOG note the standardized prompts + all-affected warning. | ARCHITECTURE.md, README.md, CHANGELOG.md | Low | Docs only |

## Deferred / out of scope (with reason)

| Finding ID | Rem. Risk | Axis | Reason | Recommended later step |
|------------|-----------|------|--------|------------------------|
| ARCH-4 (unify CLI+TUI confirm I/O) | Medium-High | functionality | A synchronous `input()` prompt and an async Textual `ModalScreen` are different interaction models; forcing one confirm mechanism across both adds complexity and risk for little gain. Only the *pure* render/summary is shared. | If the TUI later needs identical wording, share only the string; keep the I/O separate. |
| (config-driven / pluggable renderers, i18n, styles) | Medium-High | complexity | Over-generalization for a single-maintainer local tool (ARCH-6). | Not planned. |

## Scope check

- **Over-scope (avoid):** No new module/package/dependency; one dataclass + two functions in `ocman.py`.
  Do not change WHICH items each op removes, the cutoff/selection logic, or the typed-`yes` semantics.
  Do not unify CLI and TUI confirmation I/O.
- **Under-scope (add):** the shared preview data model + renderer + confirm seam (ARCH-3/1), the
  `--clear-history` confirmation (ARCH-2), and characterization tests (ARCH-7) are the core and are proposed.

## Required tests / validation

- `PYTHONPATH=. pytest` stays green throughout. Characterization tests (step 1) pin each op's current
  proceed/cancel/dry-run/force behavior and must stay green across every migration (steps 3-5). New unit
  tests for the renderer (color-forced-off assertions) and the confirm seam (typed-'yes' only; dry_run;
  assume_yes). The clean-backups adopter reuses/extends `test_clean_backups`.
- Determinism: force NO_COLOR in renderer assertions; monkeypatch `input`/`default_backup_dir`.

## Spec / documentation sync

- ARCHITECTURE.md: add the "destructive-confirmation seam" as the canonical pattern.
- README + CHANGELOG: standardized destructive prompts + all-affected warning; `--clear-history` now confirms.

## Open questions

1. **Blast-radius sequencing.** Proposed: land the seam + clean-backups adopter first, then migrate the other
   three ops one-at-a-time behind characterization tests, then `--clear-history`. OK to do this incrementally
   across commits rather than all at once? (Assumption: yes — safest.)
2. **`--clear-history` gating.** It has no `--force`/`--dry-run` today. Add a plain typed-`yes` confirm (with a
   `--force` bypass for scripts)? (Assumption: add typed-`yes` + honor a force/`--yes` bypass if one exists.)
3. **TUI scope.** Confirm we should NOT unify CLI+TUI confirm I/O (only share the render/summary string).
   (Assumption: correct — keep them separate.)
4. **Relationship to the clean-backups IPD.** This IPD supersedes that IPD's bespoke renderer (clean-backups
   becomes the first adopter here). Should the clean-backups IPD be marked superseded, or kept as the
   detailed spec for the renderer's clean-backups-specific rows? (Assumption: keep it, but note it now builds
   on this helper.)

## Plan-review provenance (2026-07-04)

Hardened by the `plan-review` workflow (run 20260704-190800), reviewed jointly with the clean-backups IPD,
after re-reading the four confirm sites (ocman.py:4696-4714, 4960-4967, 6066-6081, 7283-7295) and the flag
semantics. Changes applied:

- **Added ARCH-9 (Blocker-if-executed-as-first-drafted):** verified that `force` bypasses ONLY the
  process-lock at every call site, never the typed-`yes` prompt (which is gated by the delete fns' separate
  `confirm` param, and is unconditional for cleanup/clean-backups). The design/steps now forbid mapping
  `force → assume_yes` and specify the correct per-op mapping; step 1 tests must assert "`--force` still
  prompts". This closes a silent-confirmation-drop safety trap the first draft's `assume_yes`/`force`
  conflation invited.
- **Added ARCH-10:** clean-backups sizing should reuse the existing `dir_usage()` helper (ocman.py:6210,
  from the executed disk-usage feature) rather than re-walking.
- **Tightened the renderer (ARCH-6/KISS):** FIXED column set; caller supplies only two header label strings
  (item + detail), not a general column-config.

Verdict: APPROVE WITH REVISIONS APPLIED.

## Execution outcome (2026-07-04, PARTIAL — stays pending)

Executed with explicit user approval, scope = **helper + clean-backups first adopter only** (user chose
incremental sequencing; the other confirm-site migrations + `--clear-history` remain for a follow-up
execution, so this IPD stays in `pending/`).

Done this run:
- **Step 1:** characterization tests for `cli_clean_backups` confirm behavior (typed-`yes` proceeds,
  non-`yes`/dry-run cancel) — `test_clean_backups_cancel_on_non_yes`, `test_clean_backups_dry_run_deletes_nothing`.
- **Step 2:** added `PreviewItem`/`DestructivePreview` + pure `render_destructive_preview()` (headers,
  right-aligned Size, color-independent DELETE/KEEP, all-affected warning, pad-before-color) +
  `confirm_destructive()` (typed-`yes`; dry_run/assume_yes) in `ocman.py`. `assume_yes` is NOT wired to
  `force` (ARCH-9); mapped from the caller's prompt-skip condition.
- **Step 3:** converted `cli_clean_backups` to build a `DestructivePreview` (remove=old, keep=retained),
  reuse `dir_usage()` for dir sizes (ARCH-10), summarize KEEP rows beyond 20 (full under `-v`), and confirm
  via the seam. Verified live on the real backups dir (22 delete / 5 keep, 7.23 GB, right-aligned).
- **Docs:** ARCHITECTURE.md "Destructive-confirmation seam"; README `--clean-backups` section; CHANGELOG.
- Tests added: renderer right-align, KEEP/DELETE preview, all-deleted warning. Validation: `PYTHONPATH=.
  pytest` → 102 passed, 2 skipped.

### Follow-up execution (2026-07-04, steps 4-6 — COMPLETES this IPD)

User approved the follow-up batch (all 3 sites + `--clear-history`; `--force` reused as the bypass;
delete/project use a remove-only preview). Done:

- Added `DestructivePreview.warn_if_all_removed` (True for collection prunes like backups; the delete/prune
  ops don't render via the seam so it does not apply there) and made `confirm_destructive(preview=None,
  render=False, action_verb=...)` able to own just the dry-run/irreversible/typed-`yes` tail while the op
  keeps printing its own detailed row/file listing.
- **Step 4 (migrations):** `db_delete_session_recursive`, `db_delete_project_recursive`, and
  `db_run_cleanup`/clean-orphans now confirm via `confirm_destructive(..., render=False)`. Per ARCH-9,
  `assume_yes` is the existing prompt-skip condition (`not confirm` for the delete fns; `False` for cleanup)
  — **never `force`**. Characterization tests pin: cancel-on-non-`yes`, `confirm=False` skips (TUI),
  and **`force=True` still prompts** (`test_delete_session_force_still_prompts`).
- **Step 5 (`--clear-history`):** now prints how many run records will be erased + "cannot be undone" and
  requires typed `yes`; `--force` bypasses. Tests: `test_clear_history_requires_confirmation`,
  `test_clear_history_force_bypasses_prompt`.
- **Step 6 (TUI):** left the TUI's own async safety modals as-is (they already display their deletion scope);
  no forced reuse of the render string — kept CLI/TUI I/O separate per the decision. Minimal by design.
- Docs: ARCHITECTURE.md adopters list; CHANGELOG entries.

Validation across the full follow-up: `PYTHONPATH=. pytest` → 107 passed, 2 skipped. All prior tests
(delete/cleanup/TUI) stayed green — behavior preserved.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT
auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered steps (characterization tests first; incremental migration).
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
