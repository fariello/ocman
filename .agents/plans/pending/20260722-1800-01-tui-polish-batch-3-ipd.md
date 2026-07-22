# IPD: TUI polish batch 3 (footer label format, transcript-missing fix, Esc-cancel, layout)

- Date: 2026-07-22
- Concern: UI/UX + one correctness regression (transcript pane collapsed to ~0 height)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{spend,models}.py`,
  `tests/test_tui.py`. No `ocman/cli.py` change. No DB schema change. No new dependency.
- Status: PROPOSED (not yet executed)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused; a delta
  release-review must cover all the TUI work before rung C).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-22 (its_direct/pt3-claude-opus-4.8): third round of maintainer hand-test feedback
  (11 items) after batch 2 (20260721-2230-01).

## Itemized requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| B3-01 | Footer labels must be `[key][space][glyph-if-any][no space][label]` for EVERY button | Rewrite all footer button labels + `_sidebar_footer_label` to `"[b]^u[/b] ↻Update"` form (space after the bold key, no space before the label). Buttons with no glyph: `"[b]^q[/b] Quit"`. | app.py:1319-1325 (currently `^u↻Update`, no space after key); `_sidebar_footer_label` app.py |
| B3-02 | Details: transcripts are MISSING | REGRESSION: `#details-top` (metadata+FORMAT CONTROLS) is `height: auto` and grows to ~34/40 rows, squeezing `#transcript-container` (1fr) to height 2. Cap `#details-top` (e.g. `height: auto; max-height: 12` or a fixed small height) so the transcript gets the remaining space. Verify transcript region height is substantial at 120x40. | render shows details-top h=34, transcript-container h=2, transcript-md h=0 |
| B3-03 | ALL dialogs with a Cancel option must cancel on Esc | Add `BINDINGS=[Binding("escape","<cancel-action>")]` (or a shared base) to every ModalScreen that has a Cancel/No button: RestoreBackupModal, ClearHistoryModal, BatchDeleteModal, DeletionSafetyModal, ProjectDeletionSafetyModal, MoveProjectModal, MoveSessionModal, FilterModal, ExportSessionModal, ReclaimConfirmModal (+ any others). Esc dismisses with the same result as Cancel. | modal classes app.py:78+; storage.py ReclaimConfirmModal |
| B3-04 | `⚠` buttons need a space after: `⚠ LABEL` | Change all `[b red]⚠[/]LABEL` to `[b red]⚠[/] LABEL` (space after the closing tag). | 18 destructive buttons (app/database/storage) |
| B3-05 | If a non-`⚠` char was used, switch to `⚠` | Verified the char is already U+26A0 (⚠) everywhere; NO change needed beyond B3-04 spacing. Recorded for completeness. | xxd confirms e2 9a a0 = U+26A0 |
| B3-06 | Spend bottom pane does not fill the space | The `#spend-table` has `height: 1fr` but its parent `SpendWidget` (a `Static`) / container may not expand. Ensure SpendWidget + its DataTable container are `height: 1fr` so the table fills below the top controls. | spend.py:18 SpendWidget(Static); css #spend-table:400 |
| B3-07 | Models pane does not fill the space | Same as B3-06 for ModelsWidget / `#models-table`. | models.py:14 ModelsWidget(Static); css #models-table:403 |
| B3-08 | Search input must be 1 row, not 3 | `#input-session-search { height: 3 }` -> `height: 1`. | css style.css:33 height: 3 |
| B3-09 | Label the command-palette widget ("Commands") | The Header shows a command-palette icon with no label. Add a labeled affordance: either a footer/header "Commands" button, or set the Header icon's tooltip/label. Textual `Header` has a fixed command-palette dot; a clean approach is a small header title tweak OR a footer "Commands" button that calls `action_command_palette`. DECIDE in review (Header customization is limited). | app.py:1198 Header(show_clock=True) |
| B3-10 | Remove the extra padding line between the top Header row and content | The Header is height 3 with a `border-bottom: double` adding a visible gap line. Reduce Header height/border so there is no blank padding line under it. | css Header block:8 (border-bottom double #313244) |
| B3-11 | Set the app title to "OCMan (OpenCode Manager) v1.3.0" | `self.title = f"OCMan (OpenCode Manager) v{__version__}"`. | app.py:1345 currently "Ocman TUI Controller v..." |

## Design decisions to settle in plan-review (OPEN)
- B3-02 cap value: what is the right `#details-top` height so metadata + the 8 FORMAT CONTROLS
  fit without eating the transcript? The controls need ~9 rows; propose `#details-top { height: 11 }`
  (or auto + max-height 11). Confirm the metadata (7-8 lines) also fits in 11.
- B3-09: how to label the command palette. Textual's built-in Header renders a fixed palette
  dot with no caption. Options: (a) add a footer "Commands" button that triggers
  `action_command_palette`; (b) a custom header. RECOMMEND (a) - a `⌘ Commands` footer button
  (consistent with the new footer command bar), leaving the built-in palette dot as-is.
- B3-10: exact Header height/border. RECOMMEND drop `border-bottom` (the "double" line is the
  extra padding line the maintainer sees) and keep height 1 or 3; confirm no clock/title clipping.

## Non-goals
- No CLI/DB/dependency change. Not restyling beyond the listed items.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. TUI tests isolate OCMAN_CONFIG_PATH.
- New/updated tests: B3-02 (transcript region height is large at 120x40; regression guard),
  B3-08 (search input height == 1), B3-06/07 (spend/models table region fills, height > controls),
  B3-03 (each cancelable modal dismisses on Esc), B3-01/04 (footer label format; warn glyph has a
  trailing space), B3-11 (title string).
- Headless render at 120x40 for the visual/layout items (do not rely on DOM-presence alone; the
  batch-2 legend bug proved DOM-presence != visible).
- No em/en dash in authored prose.
- Maintainer hand-test acceptance gate for the visual items.

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one item per B3-*) BEFORE coding.
- Open questions: B3-02 cap, B3-09 approach, B3-10 header (resolve in plan-review).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output.
- Config safety: TUI tests set an isolated OCMAN_CONFIG_PATH; never touch the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off, git mv pending/ -> executed/.
- Release: 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- The 3 OPEN decisions above are resolved in plan-review before execution.
