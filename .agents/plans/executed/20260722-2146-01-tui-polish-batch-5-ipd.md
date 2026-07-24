# IPD: TUI polish batch 5 (table fill/scroll, doctor colors, transcript toggle placement, copy fallback, tab highlight)

- Date: 2026-07-22
- Concern: UI/UX + several regressions/incompletes from batch 4 (things reported done that the
  maintainer finds not working: model copy, format-control labels, running refresh placement)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{storage,running,models}.py`,
  `tests/test_tui.py`, and `TODO.md` (item 3 deferral). No `ocman/cli.py` change. No DB/dep change.
- Status: executed (maintainer authorized move to executed/ 2026-07-24; code committed + pushed, CI green)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused).
- Approval: maintainer approved 2026-07-22 ("approved. Go.")
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-22 (its_direct/pt3-claude-opus-4.8): fifth round of maintainer hand-test feedback
  (13 sub-items) after batch 4 (20260722-2026-01). Several items are re-reports of batch-4 work
  that does not work in the maintainer's terminal; diagnoses below.
- 2026-07-22 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-501..PR-504. Verified: Collapsible(title, collapsed, collapsed_symbol='▶', expanded_symbol=
  '▼') matches the ask; doctor status is add_row column 1; TRANSCRIPT LOG title is a movable
  Label; only 2 refs to #activity-audit-log. Revisions: B5-02 use Rich Text cell not markup
  (PR-501); B5-07 pin async remove+remount + contained ripple (PR-502); fill tests must await
  the worker before asserting (PR-503); "Last copied" is a 1-row line (PR-504). Decisions
  resolved (B5-07 collapsible per-run, fill=full height, B5-06b Last-copied fallback).
  Status -> reviewed; GO - PENDING HUMAN APPROVAL. NOTE: this is the 5th consecutive TUI
  hand-test batch; consider a consolidated real-terminal hand-test pass after execution.

## Diagnoses (done before writing requirements)
- Model row-copy (item 6b): the handler IS correct and FIRES in a headless pilot (a real click
  copies the Provider/ID). The failure is almost certainly OSC-52 clipboard not honored by the
  maintainer's terminal/SSH. => add a visible FALLBACK (show the copied value so it can be
  hand-selected) rather than only a toast that may lie.
- Running Refresh (item 4): the button EXISTS but renders off-screen at x=112..128 on a 120-col
  screen (the count Static pushed it past the right edge). => fix the row layout so Refresh is
  visible immediately right of the count.
- Table fill (items 1,3,6a): `DataTable { height: 1fr }` is set, but a Textual DataTable fills
  its region as background yet only DRAWS rows at the top; the maintainer reports BOTH "half
  empty" AND "must scroll" for Doctor, which implies the table region is NOT actually getting
  the full height at load (layout computed before the worker populates rows -> item 1's "needs
  refresh after load" hypothesis). => force a layout refresh after rows load and ensure the
  table region truly fills.
- Doctor status color (item 2): `_status_label` intentionally emits plain uppercased text with a
  comment "Textual styles cells itself", but no cell styling was ever added. => color the status
  cell green/yellow/red per OK/WARN/ERROR like the CLI.

## Itemized requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| B5-01 | Doctor table: fills only after scroll / half-empty pane | After the checkup worker populates `#doctor-table`, call a layout refresh (`table.refresh(layout=True)` / `self.refresh(layout=True)`) so the 1fr region is recomputed with rows present; verify the table region fills and no scroll is needed when rows fit. | storage.py worker update; item-1 hypothesis |
| B5-02 | Doctor status values need red/yellow/green like CLI | In `add_row`, pass the status as a Rich `Text(label, style=...)` (NOT a `[markup]` string - DataTable cells need a renderable, and markup is not parsed in a plain-string cell). Map ERROR/vulnerable->red, WARN/exposed->yellow, OK->green, UNKNOWN/other->default. Verify by asserting the cell is a Text with the mapped style. | storage.py:39 _status_label / :176 add_row (status is column index 1) |
| B5-03 | Running table < 50% pane (5 rows) | Same root cause as B5-01 (region/refresh). Apply the same layout-refresh after load. If it still cannot fill with few rows (accepted earlier), DEFER to TODO.md per maintainer. | running.py refresh_running |
| B5-03-TODO | If B5-03 not fully fixable, record in TODO.md | Add a TODO.md entry: "TUI tables (Running/Models/Doctor) do not always paint full-height background with few rows." | TODO.md |
| B5-04 | Running: Refresh button missing (off-screen) | Fix the count/Refresh Horizontal so Refresh renders on-screen immediately right of the "N running instance(s)" status (size the status Static so the button fits within the pane width). | running.py:24 count row; render x=112..128 overflow |
| B5-05a | Details: add a not-truncated toggle immediately right of "TRANSCRIPT LOG" | MOVE the "Expanded" checkbox out of FORMAT CONTROLS into a Horizontal with the "TRANSCRIPT LOG" title (id kept `check-full-lines`); toggling re-renders. | app.py:1244 checkbox (in controls); :1255 TRANSCRIPT LOG title |
| B5-05b | FORMAT CONTROLS inputs still show no labels | The Labels exist but are clipped/lost in the 30-col controls pane. Put the description INSIDE each Input via `border_title` (Textual renders it on the top border) AND/OR widen the guidance; ensure "Max interactions" / "Max lines" are visibly attached to their fields. Verify at render that the border_title text is present. | app.py:1247-1250 |
| B5-06a | Models table < 50%, lots of scroll (77 rows) | Same fill fix as B5-01 (Models is a tab): ensure `#models-table` region fills its tab area; refresh layout after load. With 77 rows this is real scrolling, so the region MUST be as tall as possible. | models.py load_models |
| B5-06b | Model click-to-copy not working | Code is correct + fires in-harness (OSC-52 terminal limitation). Add a FALLBACK: on row select, ALSO put the Provider/ID into a selectable Static (e.g. a "Last copied: <spec>" line) so the maintainer can grab it even if the clipboard escape is ignored; keep the toast + copy_to_clipboard attempt. | models.py:81 handler; OSC-52 dependency |
| B5-07 | Logs: collapsible per-run entries (▶ collapsed / ▼ expanded on click) | RESOLVED (new scope). Replace the flat `#activity-audit-log` RichLog with a `VerticalScroll` of Textual `Collapsible` widgets, one per run (verified `Collapsible` is available). Each Collapsible `title` = `<timestamp> <reason> RUN:` (Collapsible renders the ▶/▼ itself); its body = the current per-run detail lines that `load_audit_trail` builds. Collapsed by default. Keep the prune controls (B2-12) below. See "B5-07 design". | app.py:1326 RichLog; :1413 load_audit_trail builds per-run text |
| B5-08 | Selected tab: blue background so the active tab is obvious | Add `Tab.-active { background: <blue>; color: <contrast> }` (Textual's active tab class) to style.css. | css:67 Tab; no Tab.-active rule |

## Design decisions (RESOLVED with maintainer 2026-07-22)
- B5-07: RESOLVED = collapsible per-run log entries. Each run header shows a disclosure
  triangle: collapsed `▶ 2026-07-10 20:37:31 DELETE RUN:` and, when clicked, expands to
  `▼ 2026-07-10 20:37:31 DELETE RUN:` revealing that run's details (what was done). This is NEW
  scope (not previously in an IPD). See "B5-07 design" below - it requires replacing the flat
  RichLog activity view with a collapsible structure (Textual `Collapsible` per run, or a Tree),
  driven by the `runs[]` records in the history ledger.
- B5-01/03/06a: RESOLVED = target is table region == FULL available pane height; scroll only
  when the row count exceeds that height. Items 1 and 6a are genuine fill/layout bugs to fix.
- B5-06b: RESOLVED = add a "Last copied:" selectable Static line under the models table as the
  clipboard fallback (plus keep the copy attempt + toast).

- 2026-07-22 (its_direct/pt3-claude-opus-4.8): EXECUTED B5-01..B5-08 (commit bbba3a7). Full
  suite 509 passed, 2 skipped. Notes: B5-01/03/06a add table.refresh(layout=True) after the load
  worker so 1fr tables fill; B5-02 status via Rich Text cell (green/yellow/red); B5-04 running
  status set to width:1fr so Refresh stays on-screen; B5-05a Expanded toggle moved beside the
  TRANSCRIPT LOG title with auto-re-render on toggle; B5-05b inputs use border_title; B5-06b
  "Last copied" selectable fallback added (clipboard still OSC-52-dependent); B5-07 replaced the
  RichLog with per-run Collapsibles (▶/▼) via async remount, grand totals in a Static below;
  B5-08 Tab.-active blue background. Real config untouched. B5-03-TODO not needed (fill fix
  applied). CAVEATS for hand-test: table fill in the real terminal, doctor colors, collapsible
  expand/collapse, model copy landing in the clipboard vs the fallback line. Plan stays in
  pending/ until maintainer hand-test sign-off, then git mv -> executed/.

## Plan-review findings (2026-07-22)
| ID | Sev | Scope | Area | Evidence | Finding | Decision |
|----|-----|-------|------|----------|---------|----------|
| PR-501 | MEDIUM | UNDER-SCOPE | A/correctness | storage.py:176 | B5-02 must pass a Rich `Text(label, style=...)` cell; a `[markup]` string is NOT parsed in a DataTable cell | FIXED |
| PR-502 | MEDIUM | UNDER-SCOPE | C/anti-regression | app.py:1326,1415 | B5-07 swaps RichLog->Collapsibles: `load_audit_trail` must remove old Collapsibles then async-mount new ones; only 2 refs to #activity-audit-log (ripple contained) | FIXED (design pins it) |
| PR-503 | MEDIUM | UNDER-SCOPE | E/testing | batch-4 fill bug | The "table fills full height" tests MUST await the load worker before asserting region height, or they pass while reality fails (as in batch 4) | FIXED |
| PR-504 | LOW | UNDER-SCOPE | F/UX | B5-06b | The "Last copied" Static must be a 1-row line that does not steal table height | FIXED |

## B5-07 design (collapsible per-run log; NEW scope)
- Today `load_audit_trail` (app.py:1413) reads `runs[]` from the history ledger and writes one
  flat text block per run into a `RichLog#activity-audit-log`.
- New: the Log tab hosts a `VerticalScroll#activity-log-scroll` that `load_audit_trail` clears
  and repopulates with one `Collapsible` per run (newest first), `title = "<timestamp> <reason>
  RUN:"`, `collapsed=True`, containing `Static`(s) with that run's existing detail lines. Textual
  `Collapsible` provides the ▶/▼ disclosure + click-to-toggle natively (no custom key handling).
- `load_audit_trail` must MOUNT new Collapsibles (async) into the scroll container, not write
  text; on refresh it FIRST removes the old ones (`scroll.remove_children()` or query+remove),
  then mounts fresh ones. Guard for the not-yet-mounted case (contextlib.suppress). Only two refs
  to `#activity-audit-log` exist (compose + load_audit_trail), so the ripple is contained; no
  other code reads that RichLog (PR-502).
- The B2-12 prune controls row + legend stay docked below the scroll.
- Empty state: a single "No activity recorded yet." Static when `runs` is empty.

## Non-goals
- No CLI/DB/dependency change. Not restyling beyond the listed items.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. TUI tests isolate OCMAN_CONFIG_PATH.
- ON-SCREEN render assertions at 120x40: B5-04 Refresh button fully on-screen (x+width <= width);
  B5-01/03/06a table region height ~= available pane height AFTER awaiting the load worker
  (PR-503: poll until rows are present / worker done, THEN assert region height, so the test
  fails if the fill is only correct at mount but not after data loads); B5-05a Expanded toggle
  is a sibling of the TRANSCRIPT LOG title (same Horizontal); B5-05b each FORMAT CONTROLS input
  has a non-empty border_title; B5-02 an ERROR/WARN/OK row renders the status cell with the
  mapped color markup; B5-06b row-select sets the "Last copied" Static; B5-08 Tab.-active rule
  present with a blue background.
- No em/en dash in authored prose.
- Maintainer hand-test acceptance gate for the visual items (esp. the terminal-dependent copy).

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one item per B5-*) BEFORE coding.
- Open questions: none (B5-07 = collapsible per-run entries via Textual Collapsible; fill target
  = full available height; B5-06b = "Last copied" selectable fallback - all resolved).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py`, `TODO.md` (only for the B5-03 deferral note). Nothing else.
- Honesty rule: paste the ACTUAL pytest output; and do NOT claim a terminal-dependent behavior
  (clipboard) works without saying it depends on the terminal.
- Config safety: TUI tests set an isolated OCMAN_CONFIG_PATH; never touch the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off, git mv pending/ -> executed/.
- Release: 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- None. All 3 prior open decisions resolved (B5-07 collapsible per-run, fill=full height,
  B5-06b "Last copied" fallback).
