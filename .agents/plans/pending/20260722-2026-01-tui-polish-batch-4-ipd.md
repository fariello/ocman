# IPD: TUI polish batch 4 (overlay sizing/titles, transcript truncation+search-lines, copy, Main removal)

- Date: 2026-07-22
- Concern: UI/UX + two transcript-rendering correctness bugs (search line breaks lost;
  per-line truncation never applied)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{storage,running,models,spend}.py`,
  `tests/test_tui.py`. No `ocman/cli.py` change (reuse `collapse_to_preview`). No DB/dependency change.
- Status: PROPOSED (not yet executed)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused; delta
  release-review must cover all TUI work before rung C).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-22 (its_direct/pt3-claude-opus-4.8): fourth round of maintainer hand-test feedback
  (13 sub-items across Doctor/Running/Main/Models/Spend/Details) after batch 3 (20260722-1800-01).

## Itemized requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| B4-01a | Doctor: checkup table fills all available space | Make the StorageWidget's checkup table (`#doctor-table`) + its parent chain `height: 1fr` inside the overlay. | storage.py doctor table; overlay app.py:1110 |
| B4-01b | "STORAGE CHECKUP (read-only)" -> "CHECKUP RESULTS (read-only)" | Rename the label in StorageWidget. | storage.py checkup title Label |
| B4-01c | "Run / Refresh Checkup" -> "Run Checkup", placed immediately right of "CHECKUP RESULTS (read-only)" | Rename button + move it into a Horizontal with the title label. | storage.py run-checkup button |
| B4-01d | Doctor overlay title -> "OCMAN DOCTOR (Esc to return)" (drop `^m`) | Change DoctorOverlay.title_text; remove the "^m" mention everywhere (^m no longer bound). | app.py:1105 |
| B4-01e | Click outside the Doctor pane returns (like Esc) | RESOLVED: add `on_click` to `_FooterOverlay` that dismisses ONLY when the click target is the modal backdrop (the screen itself), NOT when clicking inside `.overlay-panel`. Shared by Doctor + Running. | app.py:1060 _FooterOverlay |
| B4-02a | Running overlay title -> "RUNNING OPENCODE INSTANCES (Esc to return)" | Change RunningOverlay.title_text (drop `^m`). | app.py:1117 |
| B4-02b | Running has 3 nested boxes; keep only 2 (controls + table) | RESOLVED: drop the RunningWidget's OUTER `panel-card` wrapper; the overlay's `.overlay-panel` is the single surrounding box, leaving (controls/count row) + (table). | running.py compose |
| B4-02c | "Refresh" goes to the right of the running-instances count | Put the count Label + Refresh button in one Horizontal. | running.py Refresh button + count label |
| B4-02d | Running table fills space | `#running-table` (or the RunningWidget table) + parents `height: 1fr`. | running.py table |
| B4-02e | Click outside Running pane returns (like Esc) | Same `_FooterOverlay.on_click` as B4-01e (shared). | app.py:1060 |
| B4-03 | Remove "Main" (footer button + overlay close button) | Delete the `foot-main` footer button + its handler, and the `#overlay-close-row`/`btn-overlay-close` button in each overlay. Esc + click-outside now cover it. | app.py:1313 foot-main; 1098 btn-overlay-close |
| B4-04a | Models table fills space | Same as batch-3 attempt but verify at render; models.py table + parents 1fr in the OVERLAY context (the widget is now shown in an overlay, not a tab, so overlay-panel must be 1fr too). | models.py; overlay |
| B4-04b | Clicking a model row copies Provider/ID to clipboard + says so | ModelsWidget: on `DataTable.RowSelected`, read the Provider/ID cell, `app.copy_to_clipboard`, toast. | models.py models-table |
| B4-05 | Spend table still does not fill | RESOLVED (acceptable if few rows): ensure the `1fr` chain reaches `#spend-table` INSIDE the Spend tab so the table REGION fills; do NOT add synthetic empty-row styling. "Container fills, rows are few" is accepted. Verify the table region height at render. | spend.py; css:403-410 |
| B4-06a | Search: transcript matching lines lost their line breaks; "Showing 15" should show 14 lines | The matching lines are joined with single `\n` into MARKDOWN, which collapses soft breaks into one paragraph. Render matches as a fenced code block or join with hard breaks (two spaces + `\n`, or `\n\n`), and make the "Showing N" count equal the number of lines actually shown. | app.py:1820-1823 |
| B4-06b | Transcripts must show each U:/A: line TRUNCATED (CLI-style) unless Expanded | RESOLVED: when NOT expanded, render each turn as a one-line `collapse_to_preview(turn.text, max_chars=100)` preview (line breaks collapsed, ~100 chars + ellipsis) with its role label; Expanded = current full `render_transcript`. RENAME the "Full lines" checkbox (id `check-full-lines`) label to "Expanded". Import collapse_to_preview from ocman; graceful fallback if unavailable. | app.py:1799 truncate_turns_by_lines; cli.py:1617 collapse_to_preview; checkbox app.py:1250 |
| B4-06c | FORMAT CONTROLS text fields have no labels | The "Max interactions"/"Max lines" inputs have labels ABOVE (batch-2), but the maintainer wants them clearer; put the label inside via Input `placeholder`/border-title, or keep a tight inline label. Ensure every input in FORMAT CONTROLS is self-describing. | app.py:1251-1256 |

## Design decisions (RESOLVED with maintainer 2026-07-22)
- B4-06b: RESOLVED = reuse the CLI's `collapse_to_preview(text, max_chars=100)` (100-char parity)
  for non-expanded turn previews, AND rename the checkbox "Full lines" -> "Expanded". Fall back
  to the current behavior gracefully if collapse_to_preview cannot be imported.
- B4-02b: RESOLVED = drop the RunningWidget's OUTER `panel-card` wrapper so only (opts/controls
  row) + (table) remain; the overlay's `.overlay-panel` is the single surrounding box.
- B4-05: RESOLVED = "table container fills, rows are few" is ACCEPTABLE. Ensure the `1fr` chain
  reaches `#spend-table` so the table region fills; do not add synthetic empty-row styling.
- B4-01e/B4-02e: RESOLVED = click-outside dismisses ONLY when the click target is the modal
  backdrop (the screen itself), NOT when clicking inside `.overlay-panel`.

## Non-goals
- No CLI/DB/dependency change (reuse existing `collapse_to_preview`). Not restyling beyond the list.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. TUI tests isolate OCMAN_CONFIG_PATH.
- ON-SCREEN render assertions at 120x40 (DOM-presence is not enough): B4-01a/02d/04a/05 table
  region heights fill; B4-06a matching lines render as N separate lines (count matches header);
  B4-06b non-expanded turns are single-line previews (<= ~100 chars); overlay titles (B4-01d/02a)
  have no "^m"; B4-03 no foot-main / no btn-overlay-close; B4-01e/02e click on the modal backdrop
  dismisses; B4-04b row-click copies Provider/ID (fires copy + toast).
- No em/en dash in authored prose.
- Maintainer hand-test acceptance gate for the visual items.

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one item per B4-*) BEFORE coding.
- Open questions: none (B4-06b=100/rename-to-Expanded, B4-02b=drop outer panel-card, B4-05=accept
  few-rows, B4-01e/02e=backdrop-only dismiss - all resolved).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output.
- Config safety: TUI tests set an isolated OCMAN_CONFIG_PATH; never touch the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off, git mv pending/ -> executed/.
- Release: 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- None. All 4 prior open decisions resolved (see Design decisions).
