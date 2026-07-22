# IPD: TUI polish batch (keybinding, status colors, layout, readability, transcript truncation)

- Date: 2026-07-21
- Concern: UI/UX + accessibility (TUI refinements from maintainer hand-testing)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{spend,models,database}.py`
  (layout heights), `tests/test_tui.py`. No `ocman/cli.py` change. No DB schema change. No new
  dependency.
- Status: approved (maintainer GO 2026-07-21; executing PB-01..PB-10)
- Target version: rides the in-flight 1.3.0 line (final 1.3.0 promotion is paused; a delta
  release-review must cover this + the footer/overlay work before rung C resumes).
- Approval: maintainer approved 2026-07-21 ("Approve. Go.")
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-21 (its_direct/pt3-claude-opus-4.8): 10 refinements raised by the maintainer after
  hand-testing the footer/overlay work (IPD 20260721-1925-01). Captured here as one polish batch.
- 2026-07-21 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-101..PR-104. Verified all path:line claims against code (no toast CSS; truncate_turns_by_lines
  imported-but-unused; CLI model-json parse; tab titles; table ids). Revisions: PB-06 now pins
  take-effect via the existing Refresh-View button (existing checkboxes do not auto-re-render,
  app.py:2515) + counts RENDERED-markdown lines; PB-09 pins bare id only (not the CLI providerID
  suffix) + non-JSON fallback; PB-08/PB-10 gain a CSS-presence regression-guard test. Both prior
  decisions resolved (PB-01 Esc, PB-06 2500). Status -> reviewed; GO - PENDING HUMAN APPROVAL.

- 2026-07-21 (its_direct/pt3-claude-opus-4.8): EXECUTED PB-01..PB-10 (commit f8cd333). Full
  suite 484 passed, 2 skipped. Notes: PB-08/PB-10 reconciled by dropping the `tall` border on
  Input/Select/Button (which forced height 3 and clipped text) in favour of a solid high-contrast
  field at height 1; PB-06 "Full lines" follows the existing Refresh-View pattern; the removed
  `ctrl+m` also required updating 3 test presses to `escape`. Config isolation held (real
  ~/.config/opencode/ocman.toml untouched this run). CAVEAT for hand-test: PB-08 (input
  readability) and PB-10 (spacing) are visual; the toast colors (PB-02) and tight rows (PB-07b)
  should be eyeballed. Plan stays in pending/ until maintainer hand-test sign-off, then
  git mv -> executed/.

## Plan-review findings
| ID | Sev | Scope | Area | Evidence | Finding | Decision |
|----|-----|-------|------|----------|---------|----------|
| PR-101 | MEDIUM | UNDER-SCOPE | F/UX | app.py:2515,1805 | PB-06 did not state how "Full lines" takes effect; existing transcript checkboxes only re-render on Refresh View | FIXED (pinned to Refresh-View pattern) |
| PR-102 | MEDIUM | UNDER-SCOPE | A/correctness | app.py:1747 | "2500 lines" unit ambiguous | FIXED (count rendered-markdown newlines) |
| PR-103 | LOW | IN-SCOPE | F/UX | cli.py:12905 | "id only" could accidentally copy CLI's `id (providerID)` + no non-JSON fallback | FIXED (bare id + fallback specified) |
| PR-104 | MEDIUM | UNDER-SCOPE | E/testing | style.css:85 | PB-08/PB-10 visual-only, no regression guard | FIXED (CSS-presence test added) |

## Goal / itemized requirements

Each maintainer item mapped to a requirement with evidence and approach:

| ID | Maintainer item | Approach | Evidence |
|----|-----------------|----------|----------|
| PB-01 | Replace `^m` (Main): `^m`==Enter (CR) in many terminals, risks hijacking Enter | DECIDED (maintainer): drop the dedicated key entirely. Remove the app `ctrl+m` priority binding AND the overlay `ctrl+m` binding; keep `escape` as the dismiss key; relabel the footer `foot-main` button to `Esc Main` (clickable). No CR-collision key remains. | app.py:1165 `ctrl+m`; overlay BINDINGS app.py:1033-1034; footer `foot-main` |
| PB-02 | Color TUI status messages like the CLI (green info / yellow warn / red error) | Add Toast CSS keyed by severity (`Toast.-information`/`.-warning`/`.-error`) matching CLI colors (green #a6e3a1 / yellow #f9e2af / red #f38ba8). CLI uses green=info, yellow=warn, red=error. | style.css has NO toast rules; cli.py:162/167/172 |
| PB-03 | Spend list fills the space below the top controls | `#spend-table { height: 1fr; }` and make the SpendWidget container expand | spend.py:30 DataTable#spend-table |
| PB-04a | Models list fills available space | `#models-table { height: 1fr; }` | models.py:24 DataTable#models-table |
| PB-04b | Rename "Models Library" -> "Models" | TabPane title string | app.py TabPane "Models Library" |
| PB-05a | Details & Transcript transcript fills space | transcript area height 1fr | app.py transcript-area/#transcript-md |
| PB-05b | Rename "Details & Transcript" -> "Details" | TabPane title string | app.py:1068 |
| PB-06 | Transcript shows CLI-style TRUNCATED lines unless user toggles "Full lines"; warn if >2500 lines | Add a "Full lines" Checkbox (default off) NEXT TO the existing Include-Tools/All-Roles checkboxes. It takes effect the SAME way those do: on the existing "Refresh View" button (they do NOT auto-re-render; see on_checkbox_changed app.py:2515 which only handles cfg-* config checkboxes). In render_current_transcript: OFF => apply `truncate_turns_by_lines(turns, <max_lines>)` (max_lines from the existing "Max Lines" input, default 2500); ON => render full, then if the rendered markdown line count (`transcript_markdown.count(chr(10))`) exceeds 2500, emit a warning notify. Line count is the RENDERED-markdown lines, matching what the user sees. | render_current_transcript app.py:1714; truncate_turns_by_lines imported core.py:41; checkboxes re-render only via btn-refresh-transcript app.py:1805 |
| PB-07a | "Database Admin" -> "Database" | TabPane title | app.py:1271 "Database Admin" |
| PB-07b | Database rows less separated | reduce vertical margins/padding on the admin metric rows | database.py Horizontal rows |
| PB-08 | Text boxes hard to read in dark mode (accessibility) | Raise Input text/background contrast: brighter text (#cdd6f4 on a lighter field, or a higher-contrast pairing), placeholder contrast too. Applies to Input AND Select AND cfg-* fields. This is a GUIDING-PRINCIPLE (accessibility) fix. | style.css:85-92 Input |
| PB-09 | Details -> Session Metadata: model should be just the model id, not JSON | Parse `s['model']` with a small helper: JSON dict => show ONLY `obj.get("id")` (NOT the CLI's `id (providerID)` form; maintainer wants the bare id); plain non-JSON string (older rows) => show as-is; empty => "N/A". Robust to malformed JSON. | app.py:1658 raw s.get('model'); CLI uses the providerID suffix (which we do NOT copy) at cli.py:12903-12905 |
| PB-10 | All buttons + text boxes: no top/bottom padding, at most 1 space left/right | Global rule: `Button, Input, Select { padding: 0 1; margin: 0; }` (audit for height:3 defaults on Button). Reconcile with the footer buttons (already height 1). | style.css Input/Button/Select |

## Design decisions (RESOLVED with maintainer 2026-07-21)

- **PB-01 key choice:** RESOLVED = drop the dedicated key; use `Esc` to dismiss overlays plus
  the clickable footer button relabeled `Esc Main`. No CR-collision key remains.
- **PB-06 threshold:** RESOLVED = 2500 lines. The warning fires when the FULL (untruncated,
  "Full lines" on) render exceeds 2500 lines. (Maintainer: "still too much, but we'll see how
  the TUI handles that" - revisit after hand-testing.)
- **PB-10 vs PB-08 (still to verify in execution, not an open decision):** zero vertical padding
  on Inputs must not reduce the PB-08 legibility fix; a bordered 1-row input can clip text, so
  during execution verify the two do not fight (may need `border: none` + a background instead of
  a `tall` border to keep 1-row height AND readable text).

## Non-goals
- No `ocman/cli.py` change; no DB or serialized-format change; no new dependency.
- Not changing WHAT the Spend/Models/Doctor/Running data shows, only sizing/labels/legibility.
- Not touching the Details/Actions tab CONTENT beyond transcript truncation + model-id + height.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL runner output). Isolate config via
  `OCMAN_CONFIG_PATH` in any TUI test so the REAL user config is never written (a prior run
  clobbered `~/.config/opencode/ocman.toml`; do not repeat).
- New/updated tests: PB-01 (Esc dismisses overlay; no `ctrl+m` binding remains; footer button
  relabeled), PB-06 (truncated by default; Full-lines checkbox exists; full render >2500 lines
  emits a warning notify), PB-09 (metadata shows bare model id, not JSON, and tolerates a plain
  string), PB-05b/04b/07a (tab titles renamed), PB-03/04a/05a (table/transcript height 1fr),
  PB-08/PB-10 (regression guard: assert the Input/Button contrast + zero-vertical-padding CSS
  rules are present, so a later edit cannot silently revert the accessibility fix).
- Headless pilot smoke of the renamed tabs + overlays still open/close.
- No em/en dash in authored prose.
- Manual accessibility check (PB-08/PB-10): maintainer hand-test confirms text is readable and
  spacing is tight (this is the acceptance gate, see below).

## Gate / execution contract (MUST, per AGENTS.md)
Before coding, create a step-granular TodoWrite checklist (one item per PB-01..PB-10 sub-step).
- Open questions: none (PB-01 = Esc-only + footer button; PB-06 = 2500; both resolved).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py` ONLY. No `ocman/cli.py`, no DB, no dep.
- Honesty rule: paste the ACTUAL pytest output; never claim an unrun result.
- Config safety: every TUI test MUST set an isolated `OCMAN_CONFIG_PATH`; never write the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off (PB-08/PB-10 are visual), `git mv`
  pending/ -> executed/ and re-add.
- Release: the paused 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- None. Both prior open decisions resolved (PB-01 Esc, PB-06 2500).
