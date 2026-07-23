# IPD: TUI polish batch 4 (overlay sizing/titles, transcript truncation+search-lines, copy, Main removal)

- Date: 2026-07-22
- Concern: UI/UX + two transcript-rendering correctness bugs (search line breaks lost;
  per-line truncation never applied)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{storage,running,models,spend}.py`,
  `tests/test_tui.py`. No `ocman/cli.py` change (reuse `collapse_to_preview`). No DB/dependency change.
- Status: approved (maintainer GO 2026-07-22; executing B4-01..B4-06)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused; delta
  release-review must cover all TUI work before rung C).
- Approval: maintainer approved 2026-07-22 ("approved. Go!")
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-22 (its_direct/pt3-claude-opus-4.8): fourth round of maintainer hand-test feedback
  (13 sub-items across Doctor/Running/Main/Models/Spend/Details) after batch 3 (20260722-1800-01).
- 2026-07-22 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-401..PR-405. Verified evidence: run-checkup id is btn-run-doctor (storage.py:92);
  RunningWidget panel-card + #lbl-running-status count (running.py:23,30); collapse_to_preview
  importable from ocman (max_chars=100); models "Provider / ID" is column 1; FORMAT CONTROLS
  labels exist but read detached; transcript matches joined into Markdown (soft-break collapse).
  Revisions: keep btn-run-doctor id (PR-401), pin running box/count targets (PR-402), render
  search matches in a fenced code block with N==shown (PR-403), pin collapse_to_preview import +
  label rename (PR-404), add copy/click-outside behavioral tests (PR-405). Decisions resolved
  (B4-06b 100/Expanded, B4-02b drop outer panel-card, B4-05 accept few-rows, B4-01e/02e
  backdrop-only). Status -> reviewed; GO - PENDING HUMAN APPROVAL.

## Itemized requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| B4-01a | Doctor: checkup table fills all available space | Make the StorageWidget's checkup table (`#doctor-table`) + its parent chain `height: 1fr` inside the overlay. | storage.py doctor table; overlay app.py:1110 |
| B4-01b | "STORAGE CHECKUP (read-only)" -> "CHECKUP RESULTS (read-only)" | Rename the label in StorageWidget. | storage.py checkup title Label |
| B4-01c | "Run / Refresh Checkup" -> "Run Checkup", placed immediately right of "CHECKUP RESULTS (read-only)" | Rename the button LABEL only; KEEP its id `btn-run-doctor` (the on_button_pressed handler keys on it - storage.py). Move the title Label + this button into one Horizontal so the button sits immediately right of the title. | storage.py:90 title Label, :92 Button id=btn-run-doctor |
| B4-01d | Doctor overlay title -> "OCMAN DOCTOR (Esc to return)" (drop `^m`) | Change DoctorOverlay.title_text; remove the "^m" mention everywhere (^m no longer bound). | app.py:1105 |
| B4-01e | Click outside the Doctor pane returns (like Esc) | RESOLVED: add `on_click` to `_FooterOverlay` that dismisses ONLY when the click target is the modal backdrop (the screen itself), NOT when clicking inside `.overlay-panel`. Shared by Doctor + Running. | app.py:1060 _FooterOverlay |
| B4-02a | Running overlay title -> "RUNNING OPENCODE INSTANCES (Esc to return)" | Change RunningOverlay.title_text (drop `^m`). | app.py:1117 |
| B4-02b | Running has 3 nested boxes; keep only 2 (controls + table) | RESOLVED: remove the `classes="panel-card"` from the RunningWidget's outer `Vertical` (running.py:23) so it no longer draws a border; the overlay's `.overlay-panel` + the DataTable's own border are the 2 remaining boxes. | running.py:23 Vertical(classes="panel-card") |
| B4-02c | "Refresh" goes to the right of the running-instances count | The count/status is `#lbl-running-status` (running.py:30). Move the `Refresh` button (id btn-refresh-running) into a Horizontal with that status Static so Refresh sits to its right; the `All users` checkbox stays with them. | running.py:26 Refresh, :30 #lbl-running-status |
| B4-02d | Running table fills space | `#running-table` (or the RunningWidget table) + parents `height: 1fr`. | running.py table |
| B4-02e | Click outside Running pane returns (like Esc) | Same `_FooterOverlay.on_click` as B4-01e (shared). | app.py:1060 |
| B4-03 | Remove "Main" (footer button + overlay close button) | Delete the `foot-main` footer button + its handler, and the `#overlay-close-row`/`btn-overlay-close` button in each overlay. Esc + click-outside now cover it. | app.py:1313 foot-main; 1098 btn-overlay-close |
| B4-04a | Models table fills space | Same as batch-3 attempt but verify at render; models.py table + parents 1fr in the OVERLAY context (the widget is now shown in an overlay, not a tab, so overlay-panel must be 1fr too). | models.py; overlay |
| B4-04b | Clicking a model row copies Provider/ID to clipboard + says so | ModelsWidget: on `DataTable.RowSelected`, read the Provider/ID cell, `app.copy_to_clipboard`, toast. | models.py models-table |
| B4-05 | Spend table still does not fill | RESOLVED (acceptable if few rows): ensure the `1fr` chain reaches `#spend-table` INSIDE the Spend tab so the table REGION fills; do NOT add synthetic empty-row styling. "Container fills, rows are few" is accepted. Verify the table region height at render. | spend.py; css:403-410 |
| B4-06a | Search: transcript matching lines lost their line breaks; "Showing 15" should show 14 lines | Matches are joined with single `\n` into MARKDOWN (soft breaks collapse to one paragraph). FIX: render the matched lines inside a fenced code block (```), so every line is preserved verbatim and Markdown does not reinterpret `#`/`*`/etc. in matched content; put the "Showing N line(s) matching X" header ABOVE the fence, and make N == the number of matched lines rendered (currently the header text itself was miscounted). | app.py:1817-1825 |
| B4-06b | Transcripts must show each U:/A: line TRUNCATED (CLI-style) unless Expanded | RESOLVED: when NOT expanded, render each turn as a one-line `collapse_to_preview(turn.text, max_chars=100)` preview (line breaks collapsed, ~100 chars + ellipsis) with its role label; Expanded = current full `render_transcript`. RENAME the "Full lines" checkbox (id `check-full-lines`) label to "Expanded". Import collapse_to_preview from ocman; graceful fallback if unavailable. | app.py:1799 truncate_turns_by_lines; cli.py:1617 collapse_to_preview; checkbox app.py:1250 |
| B4-06c | FORMAT CONTROLS text fields have no labels | Labels DO exist above the inputs (app.py:1252/1254) but read as detached; make each input self-describing by setting its `border_title` (or placeholder) to the field name, and update "Max lines (when not Full)" -> "when not Expanded" to match the B4-06b rename. | app.py:1252-1255 |

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

- 2026-07-22 (its_direct/pt3-claude-opus-4.8): EXECUTED B4-01..B4-06 (commit b97c16d). Full
  suite 502 passed, 2 skipped. Notes: B4-01a doctor table fills via #doctor-checkup-card 3fr +
  #reclaim-log capped (table ~9 rows); B4-06a matches render in a code fence (line breaks kept,
  N==shown); B4-06b non-expanded turns use collapse_to_preview(100) with U:/A: prefixes;
  checkbox renamed "Full lines"->"Expanded"; B4-03 removed foot-main + action_show_main + overlay
  close buttons; B4-01e/02e click-backdrop-dismiss added to _FooterOverlay; B4-04b models
  row-click copies Provider/ID. Real config untouched. CAVEATS for hand-test: all visual/table
  sizing, click-outside dismiss, model-row copy (OSC-52 terminal-dependent), transcript preview
  vs Expanded, and search line breaks. Plan stays in pending/ until maintainer hand-test sign-off,
  then git mv -> executed/.

## Plan-review findings (2026-07-22)
| ID | Sev | Scope | Area | Evidence | Finding | Decision |
|----|-----|-------|------|----------|---------|----------|
| PR-401 | LOW | UNDER-SCOPE | A/correctness | storage.py:92 | B4-01c: button id is `btn-run-doctor` (handler keys on it); rename label only, keep id | FIXED |
| PR-402 | LOW | UNDER-SCOPE | F/UX | running.py:23,30 | B4-02b/c: name the exact box (panel-card class on Vertical:23) + the count is #lbl-running-status | FIXED |
| PR-403 | MEDIUM | UNDER-SCOPE | A/correctness | app.py:1820 | B4-06a: render matches in a fenced code block so lines survive + `#`/`*` not reinterpreted; N == lines shown | FIXED |
| PR-404 | LOW | UNDER-SCOPE | A/correctness | ocman.collapse_to_preview | B4-06b: import path verified (from ocman); pin role-label prefix + rename the "when not Full" label | FIXED |
| PR-405 | LOW | UNDER-SCOPE | E/testing | B4-04b/01e/02e | copy + click-outside need behavioral tests | FIXED (validation updated) |

## Non-goals
- No CLI/DB/dependency change (reuse existing `collapse_to_preview`). Not restyling beyond the list.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. TUI tests isolate OCMAN_CONFIG_PATH.
- ON-SCREEN render assertions at 120x40 (DOM-presence is not enough): B4-01a/02d/04a/05 table
  region heights fill; B4-06a matching lines render as N separate lines (count matches header);
  B4-06b non-expanded turns are single-line previews (<= ~100 chars); overlay titles (B4-01d/02a)
  have no "^m"; B4-03 no foot-main / no btn-overlay-close; B4-01e/02e click on the modal backdrop
  dismisses AND a click inside .overlay-panel does NOT dismiss (both asserted); B4-04b row-click
  copies the Provider/ID cell (assert copy_to_clipboard called with that value + toast);
  B4-06a a multi-line match renders N separate lines with N == the header count; B4-06b a
  non-expanded turn renders as a single <=~103-char preview line.
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
