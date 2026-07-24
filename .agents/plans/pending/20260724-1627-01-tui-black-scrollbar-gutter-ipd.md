# IPD: fix black scrollbar/gutter boxes + focus-border color in the TUI

- Date: 2026-07-24
- Concern: UI/UX (TUI). In two captured renders the right inner edge of several panels/inputs shows
  a column of PURE-BLACK (`#000000`) cells that clash with the control background:
    - `tmp/ocman-v130-20260724.01.svg` (Log tab): black column at x=1988.6 down the LIVE OPERATIONS
      LOG panel and the DATABASE OPERATIONS `.captioned-input` fields (bg `#11111b` / `#45475a`).
    - `tmp/ocman-v130-20260724.02.svg` (Details tab): SAME symptom, black column at x=1842.2 down
      the right edge of the `#input-session-search` "Filter tree + transcript" box (a PLAIN global
      `Input`, bg `#45475a`, NOT a `.captioned-input`). Verified: x=1830 is `#45475a`, x=1842.2 is
      46 `#000000` cells.
  Same root cause in both: an unstyled right-edge scrollbar/gutter column defaulting to black.
  Separately, the maintainer expected a focused input to show a BLUE border, but
  `.captioned-input:focus` uses mauve (`#cba6f7`); the only blue (`#0178d4`) in `.01` is Textual's
  default accent on the SYSTEM METRICS sparkline, not on the input.
- Scope: `ocman_tui/css/style.css` (`.log-area`, `.captioned-input`, `#input-session-search`, and
  the `.search-bar-row` inputs in models/running/spend that share the pattern), `ocman_tui/app.py`
  and `ocman_tui/widgets/*.py` ONLY if a shared class must be added to the search inputs,
  `tests/test_tui.py`. No Python logic change expected. Pure styling.
- Status: PROPOSED (not yet executed; awaiting plan-review then maintainer approval)
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
The black column is an UNSTYLED SCROLLBAR TRACK / gutter cell. Textual paints a scrollbar (or a
reserved gutter) on the right inner edge; because `.log-area` (and the captioned inputs' scroll
region) never set `scrollbar-background`/`scrollbar-background-hover`/`scrollbar-color`, the track
defaults to black and clashes with the panel. `.transcript-area` avoids this by reserving a stable
gutter and sitting flush. This must be VERIFIED by focusing each widget in a live 120x40 harness
and re-capturing, because a static SVG cannot prove which element painted the cell.

## Requirements
| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| BG-01 | The Log panel right edge is no longer black | On `.log-area`, set `scrollbar-background`, `scrollbar-background-hover`, `scrollbar-color`, `scrollbar-color-hover` to the panel palette (track ~`#11111b`/`#313244`, thumb ~`#585b70`), and add `scrollbar-gutter: stable`. Confirm the x=right-edge cells render the panel bg, not `#000000`. | style.css:264; SVG x=1988.6 black run |
| BG-02 | The captioned inputs AND the search/filter inputs no longer show a black right-edge cell | Give `.captioned-input`, `#input-session-search`, and the `.search-bar-row` inputs (models/running/spend) matching `scrollbar-*` colors (or remove the reserved gutter if the field is single-line and does not scroll). If several share the fix, add ONE shared class rather than duplicating. Confirm each field's right edge is `#45475a`, not black, in BOTH the `.01` (Database) and `.02` (Details filter) renders. | style.css:478; app.py:1224 `#input-session-search`; SVG .02 x=1842.2 |
| BG-03 | The focus border reads as intended (RESOLVE with maintainer: blue vs current mauve) | If the maintainer wants BLUE: set `.captioned-input:focus` border to the accent `#0178d4` (or the theme `$accent`). If mauve was intended and the SVG blue is just the sparkline accent, leave `:focus` as `#cba6f7` and instead document that the blue belongs to SYSTEM METRICS. DO NOT guess; this is an OPEN question below. | style.css:486; SVG r16 only on sparkline |
| BG-04 | No regression to other scroll areas | Do not alter `.transcript-area` (already clean) or the global border-less Inputs; scope every rule to `.log-area` / `.captioned-input`. | style.css:301, 98 |

## Open questions (MUST resolve before executing BG-03)
- Q1: For a FOCUSED captioned input, do you want a BLUE border (`#0178d4`, matching the app accent)
  or keep the current MAUVE (`#cba6f7`)? The SVG's blue is currently only on the SYSTEM METRICS
  sparkline, not on any input.
- Q2 (verification): confirm the black cell is a scrollbar track (not, e.g., a border cell) by
  re-capturing after the CSS change; if a scrollbar is not actually present on these widgets, BG-02
  becomes "remove the reserved gutter" instead of "recolor the scrollbar."

## Non-goals
- No change to widget structure, Python rendering, or the sparkline/SYSTEM METRICS accent.
- No new dependency. Linux/macos/windows unaffected (pure CSS).

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output).
- TUI test at 120x40 with an isolated `OCMAN_CONFIG_PATH`: open the Log tab, await workers, focus
  the log and each captioned input; assert (a) the widget `.region` is non-empty and (b) via the
  app's captured render there is no `#000000` cell inside the panel's right border column. If a
  render-color assertion is impractical headlessly, at minimum assert the CSS rule is applied
  (styles.scrollbar_background / border color) on the focused widget.
- Re-capture BOTH scenes the maintainer captured and eyeball: (a) the `.01` Log tab + DATABASE
  OPERATIONS, and (b) the `.02` Details tab `#input-session-search` filter box. Neither may show a
  `#000000` right-edge column.
- No em/en dash in authored prose.

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one per BG-*) BEFORE coding.
- Open questions: Q1 (focus color) and Q2 (verify scrollbar) MUST be resolved first.
- Scope fence: `ocman_tui/css/style.css`, `tests/test_tui.py`. Nothing else.
- Honesty rule: paste ACTUAL pytest output; this is a VISUAL fix, so a maintainer hand-check (or a
  fresh SVG capture) is required before git mv to executed/.
- Commits: path-scoped, never `git add -A`, never push.
- Release: rides 1.3.0; covered by the eventual delta release-review.
