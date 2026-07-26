RETIRED 2026-07-26: root-cause theory (unstyled scrollbar/gutter seam) was wrong for the "black
boxes"; superseded by .agents/plans/executed/20260724-2354-01-checkbox-border-render-fix-ipd.md
(the real cause was the Textual 8.x Checkbox border). Its only correct part, the BG-01 `.log-area`
scrollbar-color fix, already shipped in commit 0e19b4e and remains in effect.

# IPD: fix black scrollbar/gutter boxes + focus-border color in the TUI

- Date: 2026-07-24
- Concern: UI/UX (TUI). In two captured renders the right inner edge of several panels/inputs shows
  a column of PURE-BLACK (`#000000`) cells that clash with the control background:
    - `tmp/ocman-v130-20260724.01.svg` (Log tab): black column at x=1988.6 down the LIVE OPERATIONS
      LOG panel and the DATABASE OPERATIONS `.captioned-input` fields (bg `#11111b` / `#45475a`).
    - `tmp/ocman-v130-20260724.02.svg` (Details tab): SAME symptom, black column at x=1842.2. Re-
      verified during plan-review: this is NOT `#input-session-search` (that filter box is the
      LEFT-sidebar input at x~36, SVG "ilter tree + transcript"). The x=1842.2 column is inside the
      RIGHT-side FORMAT CONTROLS panel (SVG "FORMAT CONTROLS" at x=1549.4), one cell OUTSIDE a
      `.captioned-input` right border (the `╮`/`│` border glyph `#6c7086` is at x=1830, field bg
      `#45475a` ends at x=1830, black `#000000` begins at x=1842.2). So `.02` is the SAME
      `.captioned-input` class as `.01`'s DATABASE OPERATIONS fields, just a different panel.
  Same defect in both: the cell just OUTSIDE a control's right border (or a scroll region's edge)
  is left unpainted and renders black.
  Separately, the maintainer expected a focused input to show a BLUE border, but
  `.captioned-input:focus` uses mauve (`#cba6f7`); the only blue (`#0178d4`) in `.01` is Textual's
  default accent on the SYSTEM METRICS sparkline, not on the input.
- Scope: `ocman_tui/css/style.css` (`.log-area`, `.captioned-input`) and `tests/test_tui.py`. Pure
  styling; no Python logic change. (Plan-review PR-001 removed the earlier `#input-session-search`
  / `.search-bar-row` widening: the `.02` black box is a `.captioned-input`, not the search input,
  so no shared class needs adding to `app.py`/`widgets/*.py`.)
- Status: superseded (see RETIRED header; scrollbar theory replaced by the checkbox-border IPD; BG-01 shipped in 0e19b4e)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused).
- Approval: awaiting plan-review + maintainer approval
- Author: its_direct/pt3-claude-opus-4.8

## Evidence (from the captured SVG)
- SVG color classes: `r17 = #000000` (used for the black edge cells AND for button text),
  `r16 = #0178d4` (blue), `r13 = #6c7086` (dim border), `r8 = #313244`.
- Black cells at x=1988.6 recur down the Log panel rows (y~928-1200) and the DATABASE OPERATIONS
  input rows: an unstyled 1-cell scrollbar/gutter column defaulting to `#000000`.
- CSS today: `.log-area` (style.css:264) sets `background #11111b`, `border round #313244`,
  `overflow-y: scroll`, but NO `scrollbar-background`/`scrollbar-color` and NO
  `scrollbar-gutter: stable` -> the scrollbar track renders default black.
- `.captioned-input` (style.css:478) `background #45475a`, `border round #6c7086`, `padding 0 1`,
  `width 1fr`; `:focus` (style.css:486) border `#cba6f7` (MAUVE), background `#585b70`. No blue.
- For contrast, `.transcript-area` (style.css:301) DOES set `scrollbar-gutter: stable` and reads
  clean; the log/inputs do not.

## Root cause (hypothesis to CONFIRM in a live render, not just the SVG)
Plan-review (PR-002) tightened this. The earlier "unstyled scrollbar track" theory is only partly
right and is CONTRADICTED for the captioned inputs:
- `.captioned-input` is `height: 3` (style.css:480) - one text row plus its top/bottom border. It
  does NOT scroll, and the `.02` capture shows NO scrollbar thumb at x=1842.2 (only `#000000` and
  `#181825`). So for the inputs the black cell is NOT a scrollbar; it is the cell just OUTSIDE the
  field's right `round` border, inside the panel body, left UNPAINTED (defaulting to black). Likely
  the field's `width: 1fr` + `padding 0 1` + `round` border leaves a 1-col unpainted seam between
  the border and the panel edge.
- `.log-area` (style.css:264) DOES scroll (`overflow-y: scroll`) and sets no `scrollbar-*` colors,
  so THERE the black edge may genuinely be an unstyled scrollbar track.
So there may be TWO distinct causes wearing the same symptom. Both MUST be confirmed in a live
120x40 harness (focus each widget, re-capture) before choosing the fix, because a static SVG cannot
prove which element painted a given cell. Q2 below is the gating first step.

## Requirements
| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| BG-01 | The scrolling `.log-area` right edge is no longer black | AFTER confirming (Q2) the `.log-area` black edge is its scrollbar track: set `scrollbar-background`, `scrollbar-background-hover`, `scrollbar-color`, `scrollbar-color-hover` to the panel palette (track ~`#11111b`/`#313244`, thumb ~`#585b70`) and add `scrollbar-gutter: stable`. Confirm the right-edge cells render the panel bg, not `#000000`. | style.css:264; SVG .01 x=1988.6 |
| BG-02 | The `.captioned-input` fields no longer show a black cell just outside their right border | AFTER confirming (Q2) these fields do NOT scroll: the fix is to PAINT the seam, not recolor a scrollbar. Options to choose per the live finding: ensure the containing panel background covers the seam, or drop the field's right-edge gutter (e.g. adjust `width`/`padding`/`margin` so the `round` border sits flush against the panel bg). Confirm the cell right of the field border is the panel/field bg, not `#000000`, in BOTH `.01` (DATABASE OPERATIONS) and `.02` (FORMAT CONTROLS). Do NOT add scrollbar colors to a non-scrolling field. | style.css:478-489; SVG .01 x=1988.6 and .02 x=1842.2 (border `#6c7086` at x=1830) |
| BG-03 | The focus border stays the app's consistent mauve | RESOLVED with maintainer 2026-07-24: KEEP `.captioned-input:focus` border MAUVE `#cba6f7` (no change). The "blue" observed in the capture was Textual's accent on the SYSTEM METRICS sparkline, not an input border. This requirement is effectively a NO-OP + a one-line comment in the CSS noting the blue belongs to the sparkline, so a future reader does not "fix" it. | style.css:486; SVG r16 (#0178d4) only on sparkline |
| BG-04 | No regression to other scroll areas or the 1-row inputs | Do not alter `.transcript-area` (already clean, style.css:301) or the global border-less `Input` (style.css:95, `height: 1`, does not scroll, not implicated); scope every rule to `.log-area` / `.captioned-input`. | style.css:301, 95 |

## Open questions
- Q1 (focus border color): RESOLVED with maintainer 2026-07-24 = KEEP MAUVE `#cba6f7`. The blue in
  the capture is the sparkline accent, not an input border. BG-03 is a no-op + a clarifying comment.
- Q2 (verification, deferred to execution by design): the FIRST execution step MUST live-confirm,
  per widget, which cause produces the black cell: for `.log-area` (which scrolls) it is expected to
  be an unstyled scrollbar track (-> BG-01 recolor); for `.captioned-input` (`height: 3`, no scroll,
  no thumb seen in `.02`) it is expected to be an unpainted seam just outside the right border
  (-> BG-02 paint/flush the seam, NOT scrollbar colors). A static SVG cannot prove which element
  painted a cell, so this is confirmed live before the fix is chosen. This is not a human decision;
  it is an execution-time verification, correctly left OPEN-for-execution rather than asked here.

## Non-goals
- No change to widget structure, Python rendering, or the sparkline/SYSTEM METRICS accent.
- No new dependency. Linux/macos/windows unaffected (pure CSS).

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output).
- TUI test at 120x40 with an isolated `OCMAN_CONFIG_PATH`: open the Log tab AND a captioned-input
  panel (Database / FORMAT CONTROLS), await workers, focus the log and a captioned input; assert
  (a) the widget `.region` is non-empty and (b) via the app's captured render there is no `#000000`
  cell in the column just right of the panel/field right border. If a render-color assertion is
  impractical headlessly, at minimum assert the applied style (scrollbar-background for `.log-area`;
  the seam-fix property for `.captioned-input`) on the focused widget.
- Re-capture BOTH scenes the maintainer captured and eyeball: (a) the `.01` Log tab + DATABASE
  OPERATIONS, and (b) the `.02` Details tab `#input-session-search` filter box. Neither may show a
  `#000000` right-edge column.
- No em/en dash in authored prose.

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one per BG-*) BEFORE coding.
- Open questions: Q1 (focus color) resolved with maintainer (see Open questions). Q2 (live-confirm
  the per-widget cause: scrollbar for `.log-area` vs unpainted seam for `.captioned-input`) MUST be
  done as the first execution step, before choosing the BG-01/BG-02 fix.
- Scope fence: `ocman_tui/css/style.css`, `tests/test_tui.py`. Nothing else. (No `app.py`/`widgets`
  edit; PR-001 removed that need.)
- Honesty rule: paste ACTUAL pytest output; this is a VISUAL fix, so a maintainer hand-check (or a
  fresh SVG capture) is required before git mv to executed/.
- Commits: path-scoped, never `git add -A`, never push.
- Release: rides 1.3.0; covered by the eventual delta release-review.

## Execution record
- 2026-07-24 (its_direct/pt3-claude-opus-4.8-1m-us): executed after maintainer approval.
  Q2 live-verified in a 120x40 harness: `.log-area` (RichLog) has `show_vertical_scrollbar=True`
  with `scrollbar_background=Color(0,0,0)` (a GENUINE unstyled scrollbar track); `.captioned-input`
  has `show_vertical_scrollbar=False` (height 3, no scroll) and the headless compositor already
  paints the seam with the panel bg, so its black cell is real-terminal default-bg bleed through a
  reserved gutter. BG-01: added `scrollbar-background/-hover/-active`, `scrollbar-color/-hover/
  -active` (panel palette) + `scrollbar-gutter: stable` to `.log-area` -> scrollbar_background now
  `#11111b`. BG-02: pinned `.captioned-input` `scrollbar-background`/`scrollbar-color` to `#45475a`
  + `overflow: hidden hidden` -> scrollbar_background now `#45475a`, no reserved black gutter.
  BG-03: kept `:focus` mauve `#cba6f7` + added a clarifying CSS comment (blue = sparkline). BG-04:
  only `.log-area`/`.captioned-input` touched; `.transcript-area` and global `Input` untouched.
  Added 2 tests (no-black-scrollbar-gutter; focus-border-is-mauve). Full suite: 519 passed,
  2 skipped (perf benchmarks gated on OCMAN_BENCHMARK=1). No em/en dashes. AWAITING maintainer
  visual re-capture (per gate) before git mv pending -> executed.

## Workflow history
- 2026-07-24 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PR-001..PR-004. Re-verified the `.02` capture: the x=1842.2 black column is a `.captioned-input`
  in the FORMAT CONTROLS panel (border glyph `#6c7086` at x=1830), NOT `#input-session-search`
  (PR-001) - dropped the search-input widening and narrowed scope to CSS+tests. The
  "unstyled scrollbar" root cause holds only for the scrolling `.log-area`; `.captioned-input` is
  `height: 3` (no scroll, no thumb) so its black cell is an unpainted seam outside the right border
  (PR-002) - reshaped BG-01/BG-02 and made Q2 a gating live-verification first step. Reconciled the
  gate scope fence with the scope block (PR-003) and pointed the headless test at a captioned-input
  panel (PR-004). Q1 (focus border) resolved with maintainer = keep mauve `#cba6f7` (the blue was
  the sparkline accent). Verdict: APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL.
