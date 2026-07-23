# IPD: TUI polish batch 6 (root-cause fixes: table fill, unlabeled inputs, doctor colors == CLI)

- Date: 2026-07-22
- Concern: UI/UX correctness. Three root causes found by investigation (batch-5 hand-test):
  a single unconstrained-Horizontal layout bug (tables small + Database inputs mislaid), a
  border_title-needs-a-border bug (FORMAT CONTROLS labels invisible), and a doctor status color
  map that does NOT match the CLI (NOTICE not yellow).
- Scope: `ocman_tui/css/style.css`, `ocman_tui/app.py`, `ocman_tui/widgets/{storage,models,spend,running,database}.py`,
  `tests/test_tui.py`. No `ocman/cli.py` change (mirror its existing `_DOCTOR_TAGS`). No DB/dep change.
- Status: reviewed (plan-review applied 2026-07-22; awaiting maintainer approval to execute)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-22 (its_direct/pt3-claude-opus-4.8): investigation-first round after batch-5 hand-test.
  Maintainer asked to investigate (not fix) the small tables, the unlabeled FORMAT CONTROLS /
  DATABASE OPERATIONS inputs, and doctor colors. Root causes found (below); now IPD'd to fix.

## Root-cause diagnoses (verified at render, 120x40)
- TABLES SMALL (all tabs/overlays except TRANSCRIPT LOG): every table sits under a controls
  `Horizontal` with `classes="search-bar-row"`, and `.search-bar-row` has NO CSS rule, so it
  defaults to Textual's `height: 1fr` and SPLITS the vertical space ~50/50 with the table.
  Measured (Models tab): panel content 32 rows -> search row 15, table 16, last-copied 1. The
  TRANSCRIPT LOG is the lone exception because its title row is `#transcript-title-row { height:1 }`.
- FORMAT CONTROLS "no labels": batch-5 set `Input.border_title` on the Max-interactions/Max-lines
  fields, but `Input { border: none }` (from PB-10). `border_title` ONLY renders when the widget
  has a border, so the titles are invisible; the blue edge on click is the `:focus`
  `border-left: thick` style.
- DATABASE OPERATIONS "3 unlabeled black boxes": the inputs DO have sibling `Label`s
  ("Clean Older Than:", "Project scope...", "Prune backups older than (days):"), but each
  `Horizontal(Label, Input)` is unconstrained; the Label expands and pushes the Input far right
  or OFF-SCREEN (measured: `#input-prune-project` at x=131 on a 120-col screen).
- DOCTOR COLORS != CLI: the TUI `_STATUS_STYLE` maps only ok/error/warn/vulnerable/exposed, so
  NOTICE/INFO/DEBUG/UNKNOWN fall through to grey. The CLI's authoritative map is `_DOCTOR_TAGS`
  (cli.py:13677): INFO green, OK bold green, NOTICE yellow(33), WARN bold yellow, DEBUG teal(36),
  ERROR bold red, UNKNOWN white(37), SKIPPED plain. NOTICE must be YELLOW, exactly like the CLI.

## Itemized requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| B6-01 | Tables fill full height (Models/Spend/Running/Doctor) | Give `.search-bar-row` `height: auto` so the controls row takes its natural (1-row) height and the `1fr` table gets the rest. Also give `.horizontal-buttons` `height: auto` (same latent 1fr issue in dialogs/action rows; 10 uses in app.py). Audit confirmed: all `.search-bar-row` uses are single control rows, so `auto` is correct. Verify each table region ~= pane height after load. | style.css: no .search-bar-row rule (defaults 1fr); measured 50/50 split; .horizontal-buttons 10 uses |
| B6-02 | DOCTOR status colors EXACTLY like the CLI (esp. NOTICE=yellow) | DERIVE the TUI status style from the CLI `_DOCTOR_TAGS` (importable from ocman) rather than a hand-copied dict, so they CANNOT drift again (this map has been wrong 3x). Build a `{status: (hex, bold)}` from `_DOCTOR_TAGS`' ANSI codes via a small fixed ANSI->hex table (32->green #a6e3a1, 33->yellow #f9e2af, 31->red #f38ba8, 36->teal #94e2d5, 37->white #cdd6f4, None->default). Render the status as a Rich `Text(label, style=hex + (" bold" if bold))`. NOTICE=33=yellow, OK=32 bold=bold green, etc. | storage.py:40 _STATUS_STYLE (missing NOTICE etc.); cli.py:13677 _DOCTOR_TAGS (importable, verified) |
| B6-03 | FORMAT CONTROLS inputs must show a visible label | border_title is invisible without a border. FIX: put a visible inline `Label` immediately before each input (e.g. "Max interactions:" / "Max lines (when Expanded):") in the narrow controls pane, OR give ONLY these inputs a 1-line border so their border_title renders. DECIDE approach in review; RECOMMEND visible Labels (simpler, always shows, no height cost beyond 1 row each). | app.py:1244-1250; Input border:none style.css:98 |
| B6-04 | DATABASE OPERATIONS inputs must be clearly labeled + on-screen | Constrain each label+input `Horizontal` to `height: auto` and give the Label an explicit width (or stack Label above Input) so the Input is not pushed off-screen; ensure all three (Clean Older Than, Project scope, Prune backups older-than) show their label and the field is fully visible. | database.py:241-254,283-286; measured off-screen x=131 |

## Design decisions (RESOLVED in plan-review 2026-07-22)
- B6-03: RESOLVED = visible inline `Label` before each FORMAT CONTROLS input (Label above Input,
  each 1 row), NOT border_title (invisible on a border-less input). "Max interactions:" and
  "Max lines (when Expanded):".
- B6-02: RESOLVED = mirror the CLI bold treatment too (OK/WARN/ERROR bold), derived from
  `_DOCTOR_TAGS` for full parity + no drift.
- B6-01: RESOLVED = `.search-bar-row` + `.horizontal-buttons` -> `height: auto`; audit confirms
  all uses are single control/button rows.

## Plan-review findings (2026-07-22)
| ID | Sev | Scope | Area | Evidence | Finding | Decision |
|----|-----|-------|------|----------|---------|----------|
| PR-601 | MEDIUM | UNDER-SCOPE | A/anti-regression | cli.py:13677 | The color map has been wrong 3x; DERIVE the TUI map from cli._DOCTOR_TAGS (importable) so they cannot drift, not a hand-copied dict | FIXED |
| PR-602 | LOW | UNDER-SCOPE | F/UX | style.css .horizontal-buttons | `.horizontal-buttons` (10 uses) has the same latent 1fr issue; give it height:auto too | FIXED |
| PR-603 | LOW | UNDER-SCOPE | F/UX | Input border:none | B6-03 resolved to visible inline Labels (border_title cannot show without a border) | FIXED |

## Workflow history
- 2026-07-22 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-601..PR-603. Verified: `.search-bar-row` has no CSS (defaults 1fr) -> measured 50/50 table
  split; Input border:none makes border_title invisible; Database label+input Horizontals push
  inputs off-screen (x=131); cli._DOCTOR_TAGS is importable with ANSI codes + bold (NOTICE=33
  yellow). Revisions: derive doctor colors from _DOCTOR_TAGS (PR-601); also fix .horizontal-buttons
  (PR-602); FORMAT CONTROLS uses visible inline Labels (PR-603). Decisions resolved. Status ->
  reviewed; GO - PENDING HUMAN APPROVAL.

## Non-goals
- No CLI/DB/dependency change. Mirror the CLI color map; do not re-derive a new palette.

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. TUI tests isolate OCMAN_CONFIG_PATH
  and read files with `encoding="utf-8"` (Windows-safe; the batch-5 CI lesson).
- ON-SCREEN render assertions at 120x40 (await the load worker before asserting):
  B6-01 each table region height is close to its pane content height (e.g. table >= pane - 4),
  and the controls `.search-bar-row` is height 1; B6-04 each Database input's region is fully
  on-screen (x+width <= 120) and its sibling Label is present; B6-03 each FORMAT CONTROLS input
  has a visible sibling Label.
- B6-02 UNIT: assert the TUI status map matches the CLI for every DOCTOR_* value, especially
  `_status_cell("notice")` -> yellow (#f9e2af) and OK -> bold green; ideally derive the expected
  set from cli._DOCTOR_TAGS so the two can never drift again.
- No em/en dash in authored prose.
- Maintainer hand-test acceptance gate (esp. NOTICE renders yellow, tables fill).

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one item per B6-*) BEFORE coding.
- Open questions: B6-03 approach, B6-02 bold parity, B6-01 class-audit (resolve in plan-review).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output.
- Config safety: TUI tests set an isolated OCMAN_CONFIG_PATH; never touch the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off, git mv pending/ -> executed/.
- Release: 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- None. All open decisions resolved (see Design decisions).
