# IPD: TUI polish batch (keybinding, status colors, layout, readability, transcript truncation)

- Date: 2026-07-21
- Concern: UI/UX + accessibility (TUI refinements from maintainer hand-testing)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{spend,models,database}.py`
  (layout heights), `tests/test_tui.py`. No `ocman/cli.py` change. No DB schema change. No new
  dependency.
- Status: PROPOSED (not yet executed)
- Target version: rides the in-flight 1.3.0 line (final 1.3.0 promotion is paused; a delta
  release-review must cover this + the footer/overlay work before rung C resumes).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-21 (its_direct/pt3-claude-opus-4.8): 10 refinements raised by the maintainer after
  hand-testing the footer/overlay work (IPD 20260721-1925-01). Captured here as one polish batch.

## Goal / itemized requirements

Each maintainer item mapped to a requirement with evidence and approach:

| ID | Maintainer item | Approach | Evidence |
|----|-----------------|----------|----------|
| PB-01 | Replace `^m` (Main): `^m`==Enter (CR) in many terminals, risks hijacking Enter | Rebind Main to a safe key (proposal: `^o` for "hOme"/back, or `escape`-only + a footer button). DECIDE key in review. Remove the priority `ctrl+m` binding and the overlay `ctrl+m` binding. | app.py:1165 `ctrl+m`; overlay BINDINGS app.py:1033-1034 |
| PB-02 | Color TUI status messages like the CLI (green info / yellow warn / red error) | Add Toast CSS keyed by severity (`Toast.-information`/`.-warning`/`.-error`) matching CLI colors (green #a6e3a1 / yellow #f9e2af / red #f38ba8). CLI uses green=info, yellow=warn, red=error. | style.css has NO toast rules; cli.py:162/167/172 |
| PB-03 | Spend list fills the space below the top controls | `#spend-table { height: 1fr; }` and make the SpendWidget container expand | spend.py:30 DataTable#spend-table |
| PB-04a | Models list fills available space | `#models-table { height: 1fr; }` | models.py:24 DataTable#models-table |
| PB-04b | Rename "Models Library" -> "Models" | TabPane title string | app.py TabPane "Models Library" |
| PB-05a | Details & Transcript transcript fills space | transcript area height 1fr | app.py transcript-area/#transcript-md |
| PB-05b | Rename "Details & Transcript" -> "Details" | TabPane title string | app.py:1068 |
| PB-06 | Transcript shows CLI-style TRUNCATED lines unless user toggles "Full lines"; warn if >5000 lines | Add a "Full lines" Checkbox (default off). Off => apply the CLI per-line truncation the CLI uses (`truncate_turns_by_lines`, already imported in core). On => full; if resulting transcript >5000 lines, show a warning notify. | render_current_transcript app.py:1714; core imports truncate_turns_by_lines |
| PB-07a | "Database Admin" -> "Database" | TabPane title | app.py:1271 "Database Admin" |
| PB-07b | Database rows less separated | reduce vertical margins/padding on the admin metric rows | database.py Horizontal rows |
| PB-08 | Text boxes hard to read in dark mode (accessibility) | Raise Input text/background contrast: brighter text (#cdd6f4 on a lighter field, or a higher-contrast pairing), placeholder contrast too. Applies to Input AND Select AND cfg-* fields. This is a GUIDING-PRINCIPLE (accessibility) fix. | style.css:85-92 Input |
| PB-09 | Details -> Session Metadata: model should be just the model id, not JSON | `s['model']` is a JSON blob (`{"id":...,"providerID":...}`); parse like the CLI does and show the id only. | app.py:1658 raw s.get('model'); CLI parses at cli.py:12903-12905 |
| PB-10 | All buttons + text boxes: no top/bottom padding, at most 1 space left/right | Global rule: `Button, Input, Select { padding: 0 1; margin: 0; }` (audit for height:3 defaults on Button). Reconcile with the footer buttons (already height 1). | style.css Input/Button/Select |

## Design decisions to settle in plan-review (OPEN)

- **PB-01 key choice:** what replaces `^m`? Candidates: `^o`, `^space`, or "Esc + footer button only"
  (no dedicated key). MUST avoid CR-collision keys (`^m`, `^j`) and existing binds
  (q/b/u/s/d/r/g). RECOMMEND: keep `escape` to dismiss + relabel the footer button to `Esc Main`
  (drop a dedicated ^-key entirely), which sidesteps the whole CR problem. Decide in review.
- **PB-06 threshold:** ">5000 lines" warning is on the FULL (untruncated) render; confirm the
  5000 constant and whether it should reuse an existing threshold constant.
- **PB-10 vs PB-08:** zero vertical padding on Inputs must not reduce the contrast/legibility fix
  in PB-08; verify the two do not fight (a 1-row input with a border may clip text).

## Non-goals
- No `ocman/cli.py` change; no DB or serialized-format change; no new dependency.
- Not changing WHAT the Spend/Models/Doctor/Running data shows, only sizing/labels/legibility.
- Not touching the Details/Actions tab CONTENT beyond transcript truncation + model-id + height.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL runner output). Isolate config via
  `OCMAN_CONFIG_PATH` in any TUI test so the REAL user config is never written (a prior run
  clobbered `~/.config/opencode/ocman.toml`; do not repeat).
- New/updated tests: PB-01 (new Main key works, Enter NOT hijacked), PB-06 (truncated by default,
  full-lines toggle, >5000 warning), PB-09 (metadata shows model id not JSON), PB-05b/04b/07a
  (tab titles), PB-03/04a/05a (table/transcript height 1fr present).
- Headless pilot smoke of the renamed tabs + overlays still open/close.
- No em/en dash in authored prose.
- Manual accessibility check (PB-08/PB-10): maintainer hand-test confirms text is readable and
  spacing is tight (this is the acceptance gate, see below).

## Gate / execution contract (MUST, per AGENTS.md)
Before coding, create a step-granular TodoWrite checklist (one item per PB-01..PB-10 sub-step).
- Open questions: PB-01 key, PB-06 threshold (resolve in plan-review before execution).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py` ONLY. No `ocman/cli.py`, no DB, no dep.
- Honesty rule: paste the ACTUAL pytest output; never claim an unrun result.
- Config safety: every TUI test MUST set an isolated `OCMAN_CONFIG_PATH`; never write the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off (PB-08/PB-10 are visual), `git mv`
  pending/ -> executed/ and re-add.
- Release: the paused 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- None beyond the two OPEN decisions above.
