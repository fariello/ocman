# IPD: TUI polish batch 3 (footer label format, transcript-missing fix, Esc-cancel, layout)

- Date: 2026-07-22
- Concern: UI/UX + one correctness regression (transcript pane collapsed to ~0 height)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{spend,models}.py`,
  `tests/test_tui.py`. No `ocman/cli.py` change. No DB schema change. No new dependency.
- Status: executed (maintainer authorized move to executed/ 2026-07-22; hand-tested across subsequent batches)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused; a delta
  release-review must cover all the TUI work before rung C).
- Approval: maintainer approved 2026-07-22 ("Approved. Go.")
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-22 (its_direct/pt3-claude-opus-4.8): third round of maintainer hand-test feedback
  (11 items) after batch 2 (20260721-2230-01).
- 2026-07-22 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-301..PR-304. Verified evidence against code: transcript regression root-caused (details-top
  h=34 squeezes transcript to h=2); search input height:3 (css:33); warn char is U+26A0 already;
  9+ cancelable modals with differing cancel dismiss values; spend/models Static->panel-card
  chain does not expand; Header border-bottom double (css:14). Revisions: B3-03 pinned to
  per-modal cancel value (PR-301), B3-06/07 pinned the full parent chain (PR-302), validation
  requires on-screen render assertions (PR-303), B3-01 _sidebar_footer_label format pinned
  (PR-304). Decisions resolved (B3-02 cap=11, B3-09 dropped, B3-10 drop header border).
  Status -> reviewed; GO - PENDING HUMAN APPROVAL.

## Itemized requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| B3-01 | Footer labels must be `[key][space][glyph-if-any][no space][label]` for EVERY button | Rewrite all footer button labels to `"[b]^u[/b] ↻Update"` (space after the bold key, glyph then label with no space between glyph and label). No-glyph buttons: `"[b]^q[/b] Quit"`, `"[b]␣[/b] Select"`. The dynamic `_sidebar_footer_label` helper MUST emit the same format: `"[b]^b[/b] 🗹Side[b]b[/b]ar"` / `"[b]^b[/b] ☐Side[b]b[/b]ar"`. | app.py:1319-1325 (currently `^u↻Update`, no space after key); `_sidebar_footer_label` app.py:1466 |
| B3-02 | Details: transcripts are MISSING | REGRESSION: `#details-top` (metadata+FORMAT CONTROLS) is `height: auto` and grows to ~34/40 rows, squeezing `#transcript-container` (1fr) to height 2. Cap `#details-top` (e.g. `height: auto; max-height: 12` or a fixed small height) so the transcript gets the remaining space. Verify transcript region height is substantial at 120x40. | render shows details-top h=34, transcript-container h=2, transcript-md h=0 |
| B3-03 | ALL dialogs with a Cancel option must cancel on Esc | Add an Esc binding to every cancelable ModalScreen. CRITICAL: each modal's cancel returns a DIFFERENT value (RestoreBackupModal -> `dismiss(None)` app.py:127; ClearHistoryModal -> `dismiss(False)` app.py:158; BatchDelete/Deletion/ProjectDeletion -> `dismiss(None)`; MoveProject/MoveSession/Filter/Export -> `dismiss(False)`). Esc MUST dismiss with that SAME cancel value (route Esc to an `action_cancel` that calls the exact same dismiss the Cancel button does), NOT a blanket `dismiss()`, so the screen callback receives the right type. Covers RestoreBackupModal, ClearHistoryModal, BatchDeleteModal, DeletionSafetyModal, ProjectDeletionSafetyModal, MoveProjectModal, MoveSessionModal, FilterModal, ExportSessionModal, and storage.py ReclaimConfirmModal. | modal classes app.py:79,130,163,208,338,482,653,710,796; storage.py ReclaimConfirmModal |
| B3-04 | `⚠` buttons need a space after: `⚠ LABEL` | Change all `[b red]⚠[/]LABEL` to `[b red]⚠[/] LABEL` (space after the closing tag). | 18 destructive buttons (app/database/storage) |
| B3-05 | If a non-`⚠` char was used, switch to `⚠` | Verified the char is already U+26A0 (⚠) everywhere; NO change needed beyond B3-04 spacing. Recorded for completeness. | xxd confirms e2 9a a0 = U+26A0 |
| B3-06 | Spend bottom pane does not fill the space | `#spend-table { height: 1fr }` only fills its PARENT, but the chain above it does not expand: `SpendWidget` (a `Static`, spend.py:18) wraps a `Vertical.panel-card` (spend.py:22) holding the title, a controls Horizontal, the DataTable, and a totals Static. Make `SpendWidget` AND its inner `.panel-card` `height: 1fr` so the table gets the remaining space below the controls. | spend.py:18/22 SpendWidget(Static)->Vertical.panel-card->#spend-table; css:400 |
| B3-07 | Models pane does not fill the space | Same chain as B3-06: `ModelsWidget` (Static, models.py:14) -> `Vertical.panel-card` -> `#models-table`. Make `ModelsWidget` + its `.panel-card` `height: 1fr`. | models.py:14/18 ModelsWidget(Static)->Vertical.panel-card->#models-table; css:403 |
| B3-08 | Search input must be 1 row, not 3 | `#input-session-search { height: 3 }` -> `height: 1`. | css style.css:33 height: 3 |
| B3-09 | Label the command-palette widget ("Commands") | DROPPED (maintainer 2026-07-22): Textual's built-in Header palette dot has no caption slot; the maintainer chose not to add a separate labeled affordance. No change. | app.py:1198 Header(show_clock=True) |
| B3-10 | Remove the extra padding line between the top Header row and content | The Header is height 3 with a `border-bottom: double` adding a visible gap line. Reduce Header height/border so there is no blank padding line under it. | css Header block:8 (border-bottom double #313244) |
| B3-11 | Set the app title to "OCMan (OpenCode Manager) v1.3.0" | `self.title = f"OCMan (OpenCode Manager) v{__version__}"`. | app.py:1345 currently "Ocman TUI Controller v..." |

## Design decisions (RESOLVED with maintainer 2026-07-22)
- B3-02: RESOLVED = cap `#details-top` at height 11 (fits metadata's 7-8 lines + the 8 FORMAT
  CONTROLS rows); the transcript takes the remaining `1fr`. Verify the transcript region height
  is substantial at 120x40.
- B3-09: RESOLVED = drop it (do NOT add a Commands label/button). The maintainer accepted that
  Textual's built-in Header palette dot has no caption slot and chose not to add a separate
  affordance. B3-09 becomes a no-op / removed from scope.
- B3-10: RESOLVED = drop the Header `border-bottom: double` (that double line is the extra
  padding line); keep the Header otherwise. Verify no clock/title clipping.

- 2026-07-22 (its_direct/pt3-claude-opus-4.8): EXECUTED B3-01..B3-11 (B3-09 dropped; commit
  b2fbfa9). Full suite 498 passed, 2 skipped. Notes: B3-02 transcript regression fixed by
  capping #details-top to 11 (transcript container now ~25 rows). B3-03 required BOTH a priority
  Esc binding AND an on_key handler on the modals (a focused child Input swallowed the plain
  binding); Esc now dismisses each dialog with its specific cancel value (None/False). B3-05
  confirmed the glyph was already U+26A0 (only B3-04 spacing needed). B3-06/07 fixed by making
  the SpendWidget/ModelsWidget Static + inner .panel-card `height: 1fr`. Real config untouched.
  CAVEATS for hand-test: all visual items (footer format, header line removal, transcript space,
  spend/models fill, 1-row search, ⚠ spacing) plus Esc-cancel on each dialog type. Plan stays in
  pending/ until maintainer hand-test sign-off, then git mv -> executed/.

## Plan-review findings (2026-07-22)
| ID | Sev | Scope | Area | Evidence | Finding | Decision |
|----|-----|-------|------|----------|---------|----------|
| PR-301 | MEDIUM | UNDER-SCOPE | A/correctness | app.py:127,158 | B3-03 Esc must dismiss with each modal's SPECIFIC cancel value (None vs False), not a blanket dismiss(), or the callback gets the wrong type | FIXED (route Esc to the same dismiss the Cancel button uses) |
| PR-302 | LOW | UNDER-SCOPE | F/UX | spend.py:18/22 | B3-06/07 vague; the Static widget + inner .panel-card must be 1fr, not just #spend-table | FIXED (pinned the full parent chain) |
| PR-303 | LOW | UNDER-SCOPE | E/testing | batch-2 legend bug | Visual items need ON-SCREEN render assertions (region h/w at 120x40), not DOM-presence | FIXED (validation plan pins render checks) |
| PR-304 | LOW | UNDER-SCOPE | F/UX | app.py:1466 | B3-01 must pin the dynamic _sidebar_footer_label output format | FIXED (exact string specified) |

## Non-goals
- No CLI/DB/dependency change. Not restyling beyond the listed items.
- B3-09 (command-palette label) is out of scope per the maintainer decision above.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. TUI tests isolate OCMAN_CONFIG_PATH.
- New/updated tests: B3-02 (transcript region height is large at 120x40; regression guard),
  B3-08 (search input height == 1), B3-06/07 (spend/models table region fills, height > controls),
  B3-03 (each cancelable modal dismisses on Esc), B3-01/04 (footer label format; warn glyph has a
  trailing space), B3-11 (title string).
- Headless render at 120x40 for the visual/layout items (do not rely on DOM-presence alone; the
  batch-2 legend bug proved DOM-presence != visible). PR-303: the tests MUST assert widget
  `.region` height/width on a rendered 120x40 app for B3-02 (transcript region height is large,
  e.g. > 8), B3-06/07 (spend/models table region height > the controls above it), B3-08 (search
  input region height == 1), and B3-10 (Header has no double-border gap line / content starts
  directly under it). B3-03 tests press Escape on each cancelable modal and assert dismissal with
  the correct cancel result.
- No em/en dash in authored prose.
- Maintainer hand-test acceptance gate for the visual items.

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one item per B3-*) BEFORE coding.
- Open questions: none (B3-02 cap=11, B3-09 dropped, B3-10 drop Header border-bottom - all resolved).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output.
- Config safety: TUI tests set an isolated OCMAN_CONFIG_PATH; never touch the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off, git mv pending/ -> executed/.
- Release: 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- None. All 3 prior open decisions resolved (B3-02 cap=11, B3-09 dropped, B3-10 drop Header border).
