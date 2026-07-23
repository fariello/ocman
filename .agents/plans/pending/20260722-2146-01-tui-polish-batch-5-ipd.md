# IPD: TUI polish batch 5 (table fill/scroll, doctor colors, transcript toggle placement, copy fallback, tab highlight)

- Date: 2026-07-22
- Concern: UI/UX + several regressions/incompletes from batch 4 (things reported done that the
  maintainer finds not working: model copy, format-control labels, running refresh placement)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{storage,running,models}.py`,
  `tests/test_tui.py`, and `TODO.md` (item 3 deferral). No `ocman/cli.py` change. No DB/dep change.
- Status: PROPOSED (not yet executed)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-22 (its_direct/pt3-claude-opus-4.8): fifth round of maintainer hand-test feedback
  (13 sub-items) after batch 4 (20260722-2026-01). Several items are re-reports of batch-4 work
  that does not work in the maintainer's terminal; diagnoses below.

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
| B5-02 | Doctor status values need red/yellow/green like CLI | In the doctor row loader, style the status cell: ERROR->red, WARN->yellow, OK->green, else default. Use a Rich `Text`/markup cell so the DataTable renders color. | storage.py:39 _status_label / :176 add_row |
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

## B5-07 design (collapsible per-run log; NEW scope)
- Today `load_audit_trail` (app.py:1413) reads `runs[]` from the history ledger and writes one
  flat text block per run into a `RichLog#activity-audit-log`.
- New: the Log tab hosts a `VerticalScroll#activity-log-scroll` that `load_audit_trail` clears
  and repopulates with one `Collapsible` per run (newest first), `title = "<timestamp> <reason>
  RUN:"`, `collapsed=True`, containing `Static`(s) with that run's existing detail lines. Textual
  `Collapsible` provides the ▶/▼ disclosure + click-to-toggle natively (no custom key handling).
- `load_audit_trail` must MOUNT new Collapsibles (async) into the scroll container, not write
  text; on refresh it removes the old ones first. Guard for the not-yet-mounted case.
- The B2-12 prune controls row + legend stay docked below the scroll.
- Empty state: a single "No activity recorded yet." Static when `runs` is empty.

## Non-goals
- No CLI/DB/dependency change. Not restyling beyond the listed items.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. TUI tests isolate OCMAN_CONFIG_PATH.
- ON-SCREEN render assertions at 120x40: B5-04 Refresh button fully on-screen (x+width <= width);
  B5-01/03/06a table region height ~= available pane height after load; B5-05a Expanded toggle
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
