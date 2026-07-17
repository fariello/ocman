# IPD: remove low-contrast dim/grey text (accessibility)

- Date: 2026-07-17
- Concern: accessibility (contrast / readability)
- Scope: all user-facing output in `ocman/cli.py` and `ocman_tui/` that uses the
  ANSI faint attribute or a "dim" style for secondary text.
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-17 created (its_direct/pt3-claude-opus-4.8): from maintainer directive to
  stop using grey/dim for text (non-accessibility-compliant); render as normal, and
  optionally add readable color where it aids comprehension.

## Goal

Stop rendering secondary information (notes, disclaimers, IDs, paths, counts,
search context) in low-contrast dim/grey text, which fails accessibility contrast
expectations and is near-invisible on some terminals. Convey "this is secondary"
through wording/placement (and optionally a readable color), NOT through reduced
contrast.

## Project conventions discovered (Step 0)

- Guiding principles (`AGENTS.md` + fallback): intuitive/self-documenting, honest
  docs, KISS; no em/en dashes in authored prose.
- Plan lifecycle: `.agents/plans/pending/` -> `executed/`; `Status:` front matter.
- Stack: single-file CLI `ocman/cli.py` + a Textual TUI in `ocman_tui/`; pytest.

## What "dim/grey" is here (verified 2026-07-17)

There is no grey color code; the "grey" is the ANSI FAINT attribute `\033[2m`:

- CLI system 1: `_ansi(code, text)` (`ocman/cli.py:135`) wraps `\033[{code}m...`;
  `color_dim` (`cli.py:167`) = `_ansi("2", text)`. Called at **27 sites**.
- CLI system 2 (help text): `_h_dim(text, enabled)` (`cli.py:5152`) emits `\033[2m`.
  Called at **11 sites**.
- TUI: Textual `style="dim"` (and `"dim italic"`) at `ocman_tui/widgets/sidebar.py`
  lines 33, 49, 60, 75, 97, 107 (session id short-hashes, project-dir tags, empty
  states).
- Color gating: `_COLOR_SUPPORTED` (`cli.py:128`) and `_help_color_enabled()`
  (`cli.py:5129`) already honor `NO_COLOR` / `TERM=dumb` / isatty. There is NO
  `FORCE_COLOR` handling.

Note: this faint attribute is the ONLY de-emphasis mechanism; no `\033[90m`
(bright-black/grey) or `\033[37m` is used.

## Design

### A. CLI: neutralize the faint attribute (primary fix)

Make `color_dim` and `_h_dim` STOP emitting `\033[2m`. Two viable renderings
(decide in review; default to the first):

1. **Plain default-foreground text** (recommended): `color_dim(text)` returns
   `text` unchanged (no ANSI). Highest contrast, simplest, WCAG-safe. Secondary
   meaning is carried by wording/parentheses that already exist at every call site
   (e.g. "(Note: ...)", "(global; not attributable per project)").
2. **A readable de-emphasis color**: repurpose the helper to a high-contrast color
   (e.g. cyan, matching the existing `color_cyan`) so secondary text stays visually
   distinct without the contrast loss. Only if review wants a visual signal.

Doing it at the two helper definitions fixes all 38 call sites at once with no
call-site churn, which is the KISS choice and keeps the change auditable.

### B. Add readable color where it AIDS comprehension (optional, per directive)

The maintainer allowed "maybe use more color for other things." Candidates, all
using the existing high-contrast helpers (`color_cyan`/`color_green`/`color_yellow`/
`color_bold`), applied sparingly so color is never the SOLE carrier of meaning:
- Column headers / labels in reports (bold).
- Positive/success vs warning states (green/yellow) where not already colored.
Keep this minimal and additive; propose specific spots in review rather than
recoloring broadly. Do NOT make any information depend on color alone (a
colorblind/no-color user must still get the full meaning from text).

### C. TUI: replace `style="dim"`

In `ocman_tui/widgets/sidebar.py`, replace the 6 `style="dim"` / `"dim italic"`
usages. Options: drop the style (default foreground), or use the theme's readable
subtext color already in the CSS (`#a6adc8`, Catppuccin subtext, used elsewhere in
`ocman_tui/css/style.css`) rather than Rich `dim`. Prefer a defined theme color
over `dim` so contrast is controlled by the palette. Keep `italic` only if it does
not reduce legibility.

### D. Accessibility guardrails (make the fix durable)

- Add a brief note in `ARCHITECTURE.md` (or a CONTRIBUTING/style note): do NOT use
  the ANSI faint attribute or Rich `dim` for text; secondary info is conveyed by
  wording and, at most, a readable color; color is never the sole signal.
- Consider (open question) honoring `FORCE_COLOR` for symmetry with `NO_COLOR`, so
  color can be forced on in pipes; not required by this accessibility fix.

## Findings (as an assessment table)

| ID | Severity | Area | Finding | Evidence |
|----|----------|------|---------|----------|
| A1 | HIGH | accessibility/contrast | Secondary text uses ANSI faint `\033[2m`, low-contrast/near-invisible on some terminals | `color_dim` `cli.py:167`, 27 calls; `_h_dim` `cli.py:5152`, 11 calls |
| A2 | MEDIUM | accessibility/contrast | TUI uses Rich `dim`/`dim italic` for ids/tags/empty-states | `ocman_tui/widgets/sidebar.py:33,49,60,75,97,107` |
| A3 | LOW | robustness | No `FORCE_COLOR`; color cannot be forced in pipes (minor; not blocking) | `_COLOR_SUPPORTED` `cli.py:128` |

## Required tests / validation

- Unit: `color_dim("x")` and `_h_dim("x", True)` do NOT contain `\033[2m` (assert
  the faint code is gone); if option A1, assert output equals input; if A2 (color),
  assert it is the chosen readable code, never `2`.
- Characterization: existing tests that assert on rendered text still pass; any test
  matching on dim-wrapped substrings is updated to the new rendering. Human-visible
  wording of notes/disclaimers is unchanged (only the styling changes).
- Full suite green: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` (paste
  real output).
- TUI: a smoke check that the sidebar renders without the `dim` style (manual or a
  widget test if feasible).
- No-color path unchanged: with `NO_COLOR` set, output is already plain; confirm no
  regression.

## Spec / documentation sync

- ARCHITECTURE.md / style note: the "no dim/faint text; color never the sole
  signal" rule (D).
- CHANGELOG under Unreleased: accessibility change (secondary text no longer dim).

## Open questions

- Rendering choice for A: plain text (recommended) vs a readable de-emphasis color?
- Scope of the optional "more color" (B): do it in this IPD (propose exact spots) or
  a separate follow-up? Lean: keep this IPD focused on removing dim; add color as a
  small, explicit follow-up so the accessibility fix is not entangled with taste.
- Add `FORCE_COLOR` handling now or defer (A3)?

## Approval and execution gate

This IPD is a proposal; it must be human-approved before execution and is not
auto-run. On approval: implement A (and C), decide B/D scope, add/adjust tests,
paste the real pytest output, sync docs, commit path-scoped (never push), then move
this IPD to `.agents/plans/executed/`. Recommended: run `/plan-review` first
(accessibility lens) to settle the rendering choice and the color-scope question.
