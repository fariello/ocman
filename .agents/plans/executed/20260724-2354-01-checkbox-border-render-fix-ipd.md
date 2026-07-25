# IPD: fix TUI checkboxes rendering as empty black bar-boxes (Textual 8.x border regression)

- Date: 2026-07-24
- Concern: UI/UX (TUI). Every `Checkbox` in the app renders as two empty block-drawing bars
  (`▊▔▔▔▔` over `▊▁▁▁▁`) with NO visible label or toggle glyph. On the Database tab these are the
  "4 selectable black boxes" under Project (blank=all); the same defect hits FORMAT CONTROLS,
  Config, Spend, and modal checkboxes. Separately, the DATABASE OPERATIONS action buttons had long
  labels and the third (Import Session) ran off-screen at moderate widths.
- This SUPERSEDES the root-cause theory in `20260724-1627-01-tui-black-scrollbar-gutter-ipd.md` for
  the "black boxes": that IPD blamed an unstyled scrollbar/gutter seam. That was WRONG for the
  boxes (its `.log-area` scrollbar fix, commit 0e19b4e, was correct for the LOG panel and stays).
- Status: EXECUTED (2026-07-24; maintainer confirmed on-screen; 521 passed / 2 skipped)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused).
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Why the previous ~8-10 attempts failed (and why this is different)
Every prior attempt (scrollbar colors, gutter, panel padding, container unwrap, button min-width)
targeted CONTAINERS around the checkboxes and was "verified" with widget-REGION checks, which
reported placement as fine while the actual painted output was broken. The defect is in the
`Checkbox` widget itself, and it is only visible in the RENDERED CELLS, not the region geometry.

Objective, reproducible evidence gathered this round (literal compositor text dump + `render_line`):
- Installed Textual is 8.2.8 (pin `textual>=3.0.0`; the app was written for Textual 3.x).
- In Textual 8.x a `Checkbox` (a `ToggleButton`) renders as a 3-row BORDERED widget:
  row0 `▊▔▔▎`, row1 `▊ ▐X▌ label ▎`, row2 `▊▁▁▎`.
- Our global rule `Checkbox { height: 1 }` (style.css:129) CLAMPS the widget to 1 row, which drops
  the middle content row (the one with `▐X▌ label`). `Checkbox.content_size.height` is 0; a direct
  `render_line(0)` returns only blank spaces. What remains on screen are the two border bars =
  the "black boxes".
- Proven fix: add `border: none` to the `Checkbox` rule. With it, `content_size.height` goes 0 -> 1
  and the widget renders `▐X▌ label` on a single row. Verified in the REAL app (not a toy) at 154x64
  AND 120x50, across the Details/Admin/Spend tabs (every visible checkbox is height 1).

This is different because the fix is on the widget whose rendering was actually broken, and the
verification is the literal rendered text, which reproduces the maintainer's exact symptom.

## Evidence
- Offending rule: `ocman_tui/css/style.css:129` `Checkbox { ... height: 1; ... }` (no `border`).
- Textual 8.x ToggleButton BUTTON constants `▐ X ▌`; bordered by default; needs 3 rows unless
  border removed. Confirmed via `Checkbox.render_line` returning blank at height 1.
- Checkbox definitions: `ocman_tui/widgets/database.py:257-266` (4 prune checkboxes, were wrapped in
  bare single-child `Horizontal(...)` that also added stray blank rows); `ocman_tui/app.py:1240-1257`
  (FORMAT CONTROLS), `1147-1149` (Config), modals.
- Buttons: `database.py:270-273` long labels; Import off-screen at ~120-154 cols.

## Requirements
| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| CB-01 | Checkboxes render their label + toggle glyph on one row | Add `border: none;` to the global `Checkbox` rule so `height: 1` no longer crushes the content row. Fixes ALL checkboxes app-wide. | style.css:129; render proof content_size 0->1 |
| CB-02 | DATABASE OPERATIONS checkboxes are direct children (no stray gap rows) | Yield the 4 checkboxes directly into `#ops-fields` (remove the per-checkbox `Horizontal` wrappers, which produced blank rows between them). Ids unchanged (`check-dry-run/force/sweep-orphans/prune-extracts`); prune logic unchanged. | database.py:256-267; render rows 16/19 gaps |
| CB-03 | Shorter checkbox labels (maintainer-specified) | `Dry Run (Preview...)`->`Dry Run`; `Force (Bypass...)`->`[b red]⚠[/] Force`; `Sweep orphaned rows/files too`->`Delete orphaned`; `Write recovery extracts before deleting`->`Backup Before`. Values/ids unchanged. | database.py:257-266 |
| CB-04 | Action buttons fit one row at moderate widths | Relabel `Run Prune / Clean`->`Prune`, `Inspect Orphans`->`Inspect`, `Import Session`->`Import`; add `.ops-button-row Button { width: auto; min-width: 0 }` so buttons shrink to labels (Textual default min-width 16 caused overflow). Buttons stay in a ROW (maintainer preference). Applied to DATABASE OPERATIONS and BACKUP rows. | database.py:270-273; verified all 6 on-screen at 120 and 154 |
| CB-05 | No behavior change | Only labels, container nesting, and CSS change. No id, value, handler, or query_one target changes; prune/backup/import logic untouched. | database.py handlers unchanged |
| CB-06 | The action buttons actually PAINT (were missing, not just clipped) | `#ops-fields` is a `VerticalScroll` defaulting to `height: 1fr`; it expanded to fill the panel and crushed the button row (placed below it) into the panel's last sliver so the buttons fell outside the painted area (proven: ops-fields height 25, button row at y=32; SVG export lacked the buttons). Set `#ops-fields { height: auto }` so it sizes to content and the buttons below get real space. Verified via compositor dump: row shows `⚠ Prune  Inspect  Import` on-screen at 154 and 120. | style.css #ops-fields; SVG export missing buttons pre-fix |
| CB-07 | Checkboxes are readable in dark mode | Give `Checkbox` a lighter `background: #45475a` (was transparent, near-invisible on the dark panel). Verified: the label row renders on a #45475a band. | style.css:129 Checkbox background |

## Non-goals
- Not pinning/downgrading Textual (the `border: none` fix is correct for 8.x and harmless on 3.x).
- Not changing the Log-tab scrollbar fix from 0e19b4e (that one was correct).
- No change to widget behavior or DB operations.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output).
- New regression test: mount the app, open the Admin tab, assert every visible `Checkbox` has
  `content_size.height == 1` (label row present) and that `#ops-fields` has no `Horizontal` child;
  assert the 3 ops buttons are on-screen at width 120.
- Manual/harness proof (this is a VISUAL fix the region-based tests historically missed): a literal
  compositor text dump at 154x64 must show `▐X▌ Dry Run`, `▐X▌ ⚠ Force`, `▐X▌ Delete orphaned`,
  `▐X▌ Backup Before` and `⚠ Prune  Inspect  Import` (all on-screen). Maintainer SVG re-capture
  before git mv to executed.
- No em/en dash in authored prose.

## Gate / execution contract (MUST, per AGENTS.md)
- Open questions: none (labels + row layout specified by maintainer; root cause proven).
- Scope fence: `ocman_tui/css/style.css`, `ocman_tui/widgets/database.py`, `tests/test_tui.py`.
- Honesty rule: paste ACTUAL pytest output; visual fix requires maintainer re-capture before executed.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on green tests + maintainer visual confirmation, git mv pending -> executed.

## Execution record (2026-07-24, its_direct/pt3-claude-opus-4.8-1m-us)
Root cause proven via literal compositor text dump + `Checkbox.render_line`: Textual 8.2.8 makes a
`Checkbox` a bordered 3-row `ToggleButton`; the global `Checkbox { height: 1 }` (no `border: none`)
crushed out the label row (`content_size.height` 0), rendering every checkbox as two empty bars.
Fix = `Checkbox { border: none }` (content_size 0 -> 1), verified in the REAL app on Details/Admin/
Spend. Scope grew during the session (all maintainer-directed and visually confirmed on-screen):
- CB-01 checkbox `border: none`; CB-07 checkbox `background: #45475a` for dark-mode readability.
- CB-02 unwrapped the 4 prune checkboxes from bare `Horizontal`; CB-03 short labels
  (`Dry Run` / `[b red]⚠[/] Force` / `Delete orphaned` / `Backup Before`).
- CB-04 buttons relabeled Prune/Inspect/Import + `.ops-button-row Button { width:auto; min-width:0 }`
  (row layout kept per maintainer); CB-06 `#ops-fields { height: auto }` so the trailing button row
  (below a VerticalScroll that defaulted to height:1fr) actually paints.
- Follow-on (maintainer requests after first confirmation): converted the FORMAT CONTROLS and all
  three DATABASE OPERATIONS/BACKUP boxed `.captioned-input` fields to plain `.field-caption` label +
  borderless Input (no box); removed panel interior padding scoped to `#metadata-panel`,
  `#controls-panel`, and `DatabaseAdminWidget .panel-card` (Database/Models/Spend `.panel-card`
  elsewhere untouched); `#details-top` height 11 -> 12. Removed now-dead `_captioned()` helper and
  the entire `.captioned-input` CSS block (no widget uses it app-wide).
- Verified through the SVG-export path (matches the real terminal), not just region checks, after
  earlier region-only checks proved unreliable.
- Tests: added checkbox-label-row / direct-children / buttons-fit-at-120 regressions; rewrote the
  two captioned-input tests to the labeled-borderless design; removed the dead mauve-border test.
- Full suite: 521 passed, 2 skipped (perf benchmarks gated on OCMAN_BENCHMARK=1). No em/en dashes.
- The `20260724-1627-01` scrollbar IPD's `.log-area` fix (commit 0e19b4e) remains correct and in place.
