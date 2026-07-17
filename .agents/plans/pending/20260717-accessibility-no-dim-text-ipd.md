# IPD: remove low-contrast dim/grey text (accessibility)

- Date: 2026-07-17
- Concern: accessibility (contrast / readability)
- Scope: all user-facing output in `ocman/cli.py` and `ocman_tui/` that uses the
  ANSI faint attribute or a "dim" style for secondary text.
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-17 created (its_direct/pt3-claude-opus-4.8): from maintainer directive to
  stop using grey/dim for text (non-accessibility-compliant); render as normal, and
  optionally add readable color where it aids comprehension.
- 2026-07-17 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED; PR-001 (FIXED, keep helper names as shims + fix docstrings), PR-002 (FIXED, tests must force color-enabled path), PR-003 (FIXED, no overloading semantic colors), PR-004 (FIXED, name both helpers). Open questions resolved with maintainer: A=plain text, B=included (concrete spots), D=FORCE_COLOR included (NO_COLOR wins). Evidence re-verified against cli.py.

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

DECISION (maintainer, 2026-07-17): render as **plain default-foreground text**.
`color_dim(text)` returns `text` unchanged (no ANSI); `_h_dim(text, enabled)`
returns `text` (drop the `\033[2m`/`\033[0m` wrap). Highest contrast, simplest,
WCAG-safe. Secondary meaning is carried by the wording/parentheses that already
exist at every call site (e.g. "(Note: ...)", "(global; not attributable per
project)"). NOT a de-emphasis color (rejected to avoid overloading an existing
semantic color and to keep contrast maximal).

Doing it at the TWO helper definitions -- `color_dim` (`cli.py:167`) AND `_h_dim`
(`cli.py:5152`), the two independent color systems -- fixes all 38 call sites at
once with no call-site churn, which is the KISS choice and keeps the change
auditable. (Verified during review: `\033[2m` appears ONLY in these two helpers,
so nothing else emits faint text.)

Keep the helper NAMES (`color_dim`/`_h_dim`) as now-neutral compat shims to avoid
churning 38 call sites and to leave a single obvious edit point; but UPDATE their
docstrings so they no longer claim to "dim/mute" (a `color_dim` that does not dim
would be a lying docstring). If review prefers a rename, that is a separate
mechanical follow-up, not required for the accessibility fix.

### B. Add readable color where it AIDS comprehension (INCLUDED, per maintainer)

DECISION (2026-07-17): include a small, conservative set of readable-color
additions in this IPD, using only the existing high-contrast helpers
(`color_bold`/`color_cyan`/`color_green`/`color_yellow`), applied so color is never
the SOLE carrier of meaning (text still conveys it; safe under `NO_COLOR` and for
colorblind users). Concrete, bounded spots (the executor may trim, not expand):

- **Section/label emphasis with `color_bold`** on report headers that are currently
  plain, for scannability: e.g. the "Note:" / disclaimer lead-ins previously dimmed
  now read as plain text but their leading label may be bolded; `db info` /
  `spend` section titles already use `color_bold` (keep).
- **Status coloring where a state exists but is uncolored:** success lines green,
  warnings yellow (reuse `color_green`/`color_yellow`); do not introduce red except
  for genuine errors/irreversible warnings (already the convention).
- Do NOT recolor IDs/paths/counts that were dim into a new color (they become plain
  text per A); adding color there would just re-encode secondary-ness by color,
  which is what we are moving away from.

Constraint: every colored element must remain fully meaningful with color stripped
(`NO_COLOR`), and no NEW meaning may depend on hue alone. Keep the diff small; this
is polish layered on the accessibility fix, not a re-theme.

### C. TUI: replace `style="dim"`

In `ocman_tui/widgets/sidebar.py`, replace the 6 `style="dim"` / `"dim italic"`
usages. Options: drop the style (default foreground), or use the theme's readable
subtext color already in the CSS (`#a6adc8`, Catppuccin subtext, used elsewhere in
`ocman_tui/css/style.css`) rather than Rich `dim`. Prefer a defined theme color
over `dim` so contrast is controlled by the palette. Keep `italic` only if it does
not reduce legibility.

### D. Accessibility guardrails + FORCE_COLOR (make the fix durable)

- Add a brief note in `ARCHITECTURE.md` (or a CONTRIBUTING/style note): do NOT use
  the ANSI faint attribute or Rich `dim` for text; secondary info is conveyed by
  wording and, at most, a readable color; color is never the sole signal.
- **`FORCE_COLOR` (INCLUDED, per maintainer 2026-07-17):** honor `FORCE_COLOR` for
  symmetry with `NO_COLOR` in BOTH gates: `_COLOR_SUPPORTED` (`cli.py:128`) and
  `_help_color_enabled()` (`cli.py:5129`). Semantics (match the common convention):
  `NO_COLOR` set (any value, per no-color.org) => color OFF and takes precedence;
  else `FORCE_COLOR` set and not "0"/""/"false" => color ON even when not a TTY;
  else the existing isatty + `TERM!=dumb` logic. Precedence must be identical in
  both gates. Test the matrix (NO_COLOR wins over FORCE_COLOR; FORCE_COLOR forces on
  a non-TTY; neither => isatty behavior).

## Findings (as an assessment table)

| ID | Severity | Area | Finding | Evidence |
|----|----------|------|---------|----------|
| A1 | HIGH | accessibility/contrast | Secondary text uses ANSI faint `\033[2m`, low-contrast/near-invisible on some terminals | `color_dim` `cli.py:167`, 27 calls; `_h_dim` `cli.py:5152`, 11 calls |
| A2 | MEDIUM | accessibility/contrast | TUI uses Rich `dim`/`dim italic` for ids/tags/empty-states | `ocman_tui/widgets/sidebar.py:33,49,60,75,97,107` |
| A3 | LOW | robustness | No `FORCE_COLOR`; color cannot be forced in pipes. INCLUDED in scope (Design D) per maintainer, with NO_COLOR-wins precedence in both gates | `_COLOR_SUPPORTED` `cli.py:128`, `_help_color_enabled` `cli.py:5129` |

## Required tests / validation

- Unit (MUST force the color-ENABLED path): `color_dim`/`_h_dim` are gated by
  `_COLOR_SUPPORTED` (`cli.py:128`) / `_help_color_enabled()` (`cli.py:5129`); under
  pytest there is no TTY, so they ALREADY emit plain text and a naive "no `\033[2m`"
  assertion passes trivially and proves nothing. The test MUST enable color first
  (monkeypatch `_COLOR_SUPPORTED = True`, or call `_ansi` / `_h_dim(..., enabled=True)`
  directly) and THEN assert the faint code `\033[2m` is absent. If option A1, assert
  the enabled-path output equals the input (no ANSI at all); if A2 (color), assert it
  is the chosen readable code and never `2`.
- Characterization: existing tests that assert on rendered text still pass. Verified
  during review: NO test currently asserts on `\033[2m` or `color_dim` output
  (`grep` of `tests/` found none), so the regression surface is small; still, re-run
  the whole suite. Human-visible WORDING of notes/disclaimers is unchanged (only the
  styling changes).
- Full suite green: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` (paste
  real output).
- TUI: a smoke check that the sidebar renders without the `dim` style (manual or a
  widget test if feasible).
- No-color path unchanged: with `NO_COLOR` set, output is already plain; confirm no
  regression.
- `FORCE_COLOR` matrix (Design D): with `FORCE_COLOR=1` and no TTY, color helpers
  emit ANSI; with `NO_COLOR` set alongside `FORCE_COLOR`, `NO_COLOR` wins (plain);
  with neither, behavior matches isatty. Assert for BOTH gates (`_COLOR_SUPPORTED`
  and `_help_color_enabled`) so precedence is identical.
- Added-color (Design B): any element given a color remains fully meaningful with
  `NO_COLOR` set (strip color, assert the text/label is still present and unambiguous).

## Spec / documentation sync

- ARCHITECTURE.md / style note: the "no dim/faint text; color never the sole
  signal" rule (D).
- CHANGELOG under Unreleased: accessibility change (secondary text no longer dim).

## Open questions

RESOLVED in plan-review 2026-07-17 (maintainer):
- A rendering: **plain default-foreground text** (former dim text carries no color;
  option A1). Not a de-emphasis color.
- B (extra readable color): **included in THIS IPD** (see the firmed Design B below
  for the specific, conservative spots).
- D (`FORCE_COLOR`): **included in THIS IPD** (see the firmed Design D below).

No open questions remain.

## Approval and execution gate

This IPD is a proposal; it must be human-approved before execution and is not
auto-run. Scope fence: implement A (neutralize the two dim helpers + docstrings)
and C (TUI sidebar); B (extra readable color) and D (FORCE_COLOR) only if review
opts in, else deferred to a follow-up so the accessibility fix is not entangled
with taste. On approval: decide the A rendering (plain vs color) and B/D scope,
implement, add/adjust tests (forcing the color-enabled path), paste the real pytest
output, sync docs (ARCHITECTURE note + CHANGELOG), commit path-scoped (never push,
never tag), then move this IPD to `.agents/plans/executed/`. Recommended: run
`/plan-review` first (accessibility lens) to settle the rendering choice and the
color-scope question.
