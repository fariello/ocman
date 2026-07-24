# IPD: TUI polish batch 7 (self-describing input fields: bordered + inline caption)

- Date: 2026-07-23
- Concern: UI/UX. The FORMAT CONTROLS and DATABASE OPERATIONS text fields still read as
  unlabeled "black boxes": the inputs are border-less dark rectangles, their dim separate
  Labels do not associate, some labels clip in the narrow cards, and empty fields look blank.
- Scope: `ocman_tui/css/style.css`, `ocman_tui/app.py`, `ocman_tui/widgets/database.py`,
  `tests/test_tui.py`. No `ocman/cli.py` change. No DB/dep change.
- Status: reviewed (plan-review applied 2026-07-23; awaiting maintainer approval to execute)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-23 (its_direct/pt3-claude-opus-4.8): batch-6 hand-test signed off items 1-4 (Doctor,
  Running, Models, Log all perfect). Item 5 (the unlabeled input "black boxes") remained;
  investigation found the root factors below. Maintainer prefers INLINE labels (not mandatory).

## Workflow history
- 2026-07-23 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-701..PR-702. Verified a bordered Input renders border_title at height 3 (pilot). Revisions:
  concise captions to avoid truncation in narrow panes + render-verify with same-row fallback
  (PR-701); scope the border via a `.captioned-input` class, not per-id, leaving global
  Input/border:none untouched (PR-702). Decisions resolved (thin border, keep legend, same-row
  fallback). Status -> reviewed; GO - PENDING HUMAN APPROVAL.

## Root-cause diagnosis (verified at render)
The "black boxes" are `Input` fields (`background #45475a`, `border: none`, height 1). They DO
have sibling Labels, but:
1. `border: none` -> no visible field outline, so the box does not read as an editable field
   until focused (focus adds `border-left: thick`).
2. Separate Labels are dim (`.info-label` #a6adc8) and sit above -> weak caption-to-field
   association; the prominent dark box dominates.
3. In DATABASE OPERATIONS the cards are a 2-col grid (~half width); long labels like
   "Project scope (optional; blank = all projects):" (47 cols) CLIP in the narrow card.
4. Empty inputs (e.g. project scope) show only a dim placeholder -> look blank.

## Decision (maintainer): inline captions preferred
Textual renders an Input's `border_title` ON its top border when the input HAS a border. So a
single approach fixes all four factors: give these specific inputs a visible border + a concise
`border_title`, and drop the now-redundant separate Label. The caption then sits inline on the
field, the field reads as a field, and there is no separate dim label to clip or mis-associate.

## Itemized requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| B7-01 | FORMAT CONTROLS fields are self-describing (inline caption) | Give `#input-max-interactions` and `#input-max-lines` a visible `border: round`/`tall` + a concise `border_title` ("Max interactions", "Max lines (Expanded)"); REMOVE the two separate `Label`s above them. A bordered Input is height 3, which is fine in this pane. | app.py:1243-1247 (Labels + border-less Inputs) |
| B7-02 | DATABASE OPERATIONS fields are self-describing (inline caption) + no clipping | Give `#input-retention-duration`, `#input-prune-project`, `#input-backup-clean-days` a visible border + concise `border_title` ("Clean older than", "Project (blank=all)", "Prune backups older than (days)"); REMOVE the separate `Label`s. Keep the h/d/w/mo/y legend line. Concise titles fit the ~half-width card without clipping. | database.py:242-248,277-278 |
| B7-03 | Fields must read as editable even when empty | With a visible resting border (B7-01/02) an empty field is clearly a field; ensure the placeholder stays legible (raise `.input--placeholder` contrast if needed). | css:110 input--placeholder #bac2de |
| B7-04 | Restore a visible resting border on these captioned inputs without regressing the 1-row inputs elsewhere | Scope the border to ONLY the captioned fields (by id, or a shared class e.g. `.captioned-input`), so the search box and other 1-row inputs keep `border: none`. Do NOT change the global `Input { border: none }`. | css:95 Input border:none (global, keep) |

## Design decisions (RESOLVED with maintainer 2026-07-23)
- B7-01/02 border style: RESOLVED = a THIN border (`border: round <accent>` at thin weight; not
  Textual's heavier `tall`). Verify it does not overflow the 30-col controls pane / ~half-width
  DB card (a bordered Input is +2 cols, +2 rows).
- Legend: RESOLVED = KEEP the h/d/w/mo/y legend as a separate line (the "Clean older than"
  border_title is the caption; the legend still explains the unit letters).
- Fallback: RESOLVED = if `border_title` does not render reliably at these widths, fall back to a
  brightened Label on the SAME row as the field (Horizontal with a fixed-width label), not above.

## Plan-review findings (2026-07-23)
| ID | Sev | Scope | Area | Evidence | Finding | Decision |
|----|-----|-------|------|----------|---------|----------|
| PR-701 | LOW | UNDER-SCOPE | F/UX | pilot: bordered Input renders border_title, truncates if title > field width | Keep captions CONCISE so they do not truncate in the narrow panes: FORMAT CONTROLS "Max interactions" / "Max lines (Expanded)"; DB "Clean older than" / "Project (blank=all)" / "Prune backups older-than (days)". If any still clips at render, apply the same-row-label fallback for that field. | FIXED (short captions pinned + render-verify) |
| PR-702 | LOW | UNDER-SCOPE | C/maintainability | css:95 global Input | Scope the resting border via ONE shared class `.captioned-input`, not per-id rules, so the global `Input { border: none }` and other 1-row inputs are provably untouched. | FIXED |

## Non-goals
- No change to the inputs' behavior/ids/handlers (only their border + caption + the removed Labels).
- Do not alter the global Input style or other 1-row inputs (search box, cfg-* fields).

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. TUI tests isolate
  OCMAN_CONFIG_PATH and read files with encoding="utf-8".
- ON-SCREEN render at 120x40: each captioned input has a non-empty `border_title`; the field
  region is fully on-screen (x+width <= 120) in both FORMAT CONTROLS and DATABASE OPERATIONS;
  the separate Labels for these fields are gone (no orphan dim label). Update the batch-6 tests
  test_tui_format_controls_have_visible_labels and test_tui_database_ops_inputs_on_screen_and_labeled
  to assert the border_title caption instead of a sibling Label.
- No em/en dash in authored prose.
- Maintainer hand-test acceptance gate (can you now tell what each box is?).

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one item per B7-*) BEFORE coding.
- Open questions: border style, legend retention, fallback (resolve in plan-review).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output; verify the caption renders on-screen, do not
  claim a visual result from DOM presence alone (the batch-5 border_title lesson).
- Config safety: TUI tests set an isolated OCMAN_CONFIG_PATH; never touch the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off, git mv pending/ -> executed/.
- Release: 1.3.0 rung-C needs a delta release-review covering all TUI batches.

## Deferred / open
- None. All open decisions resolved (thin border, keep legend, same-row fallback).
