# IPD: TUI footer command bar + sidebar-width fix + Doctor/Running/Config overlays

- Date: 2026-07-21
- Concern: UI/UX (TUI layout + discoverability of global views)
- Scope: `ocman_tui/app.py` (bindings, compose footer, actions, modal screens, tab removal),
  `ocman_tui/css/style.css` (sidebar-pane width, footer bar styling), `tests/test_tui.py`.
  No `ocman/cli.py` change. No DB schema change. No new dependency.
- Status: executed (maintainer authorized move to executed/ 2026-07-22; hand-tested across subsequent batches)
- Target version: rides the in-flight 1.3.0 line (final 1.3.0 promotion is paused pending this
  UI work; this rides along and re-triggers a release-review delta pass before promotion).
- Approval: maintainer approved 2026-07-21 ("Approved. Go.")
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-21 (its_direct/pt3-claude-opus-4.8): the maintainer surfaced two TUI problems while
  hand-testing during the paused 1.3.0 release-review Section 9, and proposed a footer command
  bar. Implementation of the width fix + footer bar + rebindings BEGAN before an IPD existed
  (a process miss). This IPD is written RETROACTIVELY to capture the plan, mark the already-done
  parts, and gate the remaining overlay-screen refactor through the normal lifecycle. Per
  AGENTS.md the correct closure of a process gap is a new plan, not a silent continuation.

## Workflow history
- 2026-07-21 (its_direct/pt3-claude-opus-4.8): EXECUTED TF-01..TF-15 (commits 6866b95 footer/
  width/pane-toggle; a0ea3bf overlays/tab-removal/tests). Full suite 479 passed, 2 skipped.
  During execution three things surfaced beyond the plan and were fixed: (a) footer command keys
  were swallowed by a focused Input (e.g. Input's own ^d), so the app command bindings were made
  priority=True; (b) ^m must run the overlay's save-on-dismiss, so App.action_show_main delegates
  to the overlay's action_dismiss_overlay; (c) removing tabs shifted mount ordering so
  DatabaseAdminWidget metrics were not populated on mount -> app on_mount now drives an explicit
  refresh_metrics(). CAVEAT for hand-test: in some terminals ^m and Enter share a byte (CR); watch
  whether ^m (priority) ever intercepts Enter. NOTE: during the first smoke run (before config
  isolation) the TUI wrote default_retention_days=7 to the REAL ~/.config/opencode/ocman.toml;
  reset to 5 and flagged to the maintainer. Plan stays in pending/ until maintainer hand-test
  sign-off (Acceptance gate), then git mv -> executed/.
- 2026-07-21 (its_direct/pt3-claude-opus-4.8): maintainer hand-testing found TF-15 (toggle
  hides only the tree, not the search box/results). Added as a requirement + fixed in the DONE
  edits (toggle `#sidebar-pane`). Small low-risk correction to already-in-tree TF-01/TF-04 work,
  so tracked in THIS IPD, not a new one.
- 2026-07-21 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-001..PR-006. Verified DONE claims (TF-01..06) and PENDING feasibility (config query_one
  whole-DOM save/load, storage/running self-load, TabbedContent.active) against code. Fixes
  applied in-place: transition-ordering MUST (TF-13), config save-on-dismiss to replace the lost
  tab-switch save (TF-10), migrate the 8 existing tab-based tests (TF-14), Esc/^m dismiss
  bindings not automatic (TF-08), ^c->^g Config rebind (UX; maintainer-approved), execution-
  contract gate added. Status -> reviewed; GO - PENDING HUMAN APPROVAL.

## Goal

Two maintainer-reported problems, one design:

1. **Sidebar/search eats ~half the screen.** The "Search sessions (content/title), Enter to
   run" input sat in a `#sidebar-pane` `Vertical` that had NO width, so the pane and the
   `#workspace` (width 1fr) split the row ~50/50, pushing the tabbed panes far left.
2. **Not enough discoverable, clickable commands.** The stock `Footer` showed only Quit /
   Toggle Sidebar / Refresh / Select and could not carry per-button styling or a live
   sidebar-visibility glyph.

Design (settled with maintainer):
- Replace the stock `Footer` with a custom `#footer-bar` row: non-clickable key hints
  (`Select`, `^q Quit`) plus clickable, distinctly-backgrounded command buttons.
- Footer/keys and their EXACT glyphs (from the maintainer's mockup):
  `space` Select, `^q` Quit, `^b` Sidebar (live checkbox glyph), `^u` ↻ Update (was `^r`
  Refresh), `^s` 🔎 Search (focus the search field; was Toggle Sidebar), `^d` 🩺 Doctor,
  `^r` ▶ Running, `^g` ⚙ Config, `^m` Main.
- Maintainer's ORIGINAL mockup used `^c` for Config; during plan-review this was rebound to
  `^g` (confiG) to avoid the `ctrl+c`-means-interrupt/abort muscle-memory inversion (decision
  2026-07-21, plan-review; maintainer accepted the recommendation). The footer LABEL stays
  `⚙ Config`; only the accelerator changed to `^g`.
- Maintainer's target layout line (the look to match, with the `^g` rebind applied):
  `[space] Select  ^q Quit  ^b ☐Sidebar  ^u ↻Update  ^s🔎Search  ^d🩺Doctor  ^r ▶Running  ^g ⚙Config`
  (plus `^m Main`, added per the maintainer's follow-up question).
- The maintainer explicitly asked "if there's a better layout, please propose"; the overlay
  design below is that proposal, accepted by the maintainer (overlay ModalScreens for
  Doctor/Running/Config).
- Doctor/Running/Config open as **overlay ModalScreens** (maintainer choice) instead of tabs;
  `^m` (and `Esc`) returns to the main tabbed workspace. The Storage/Running/Config TAB PANES
  are removed since the footer + overlays supersede them.

## Design decisions (settled with maintainer)

- **Footer is a custom widget, not the stock Footer** (maintainer chose "custom footer bar of
  styled buttons"): needed for per-button backgrounds, unicode glyphs, and the live
  checked/unchecked Sidebar box.
- **Sidebar-visibility glyph is live:** `^b 🗹 Sidebar` when visible, `^b ☐ Sidebar` when
  hidden. Per the maintainer's request, the `b` WITHIN the word "Side[b]bar[/b]" is bold to
  advertise the `^b` accelerator (the `^b` prefix is also bold). Updated on every toggle.
- **Per-command glyphs (exact):** Sidebar 🗹/☐, Update ↻, Search 🔎, Doctor 🩺, Running ▶,
  Config ⚙. These are the maintainer's specified unicode; keep them verbatim.
- **Doctor == the Storage view.** There is no separate "doctor" pane; the read-only doctor
  checkup already lives in `StorageWidget`. `^d`/Doctor opens the Storage view as an overlay.
- **Overlays instantiate FRESH widgets** (`StorageWidget()`, `RunningWidget()`), which self-load
  on `on_mount` (Storage runs its guarded checkup worker; Running refreshes). This avoids
  re-parenting the existing tab-pane widgets and preserves the hardened storage-worker lifecycle.
- **Config overlay** hosts the `#cfg-*` inputs/checkboxes + Save/Reset. `load_tui_config` /
  `save_tui_config` use app-level `self.query_one("#cfg-...")` (verified `app.py:2271-2279`,
  `2289-2311`), which searches the whole DOM (including a mounted modal), so config load/save
  keeps working from the overlay. Config load is triggered after the modal mounts;
  auto-save-on-change (the `cfg-*` `Input.Submitted`/`Checkbox.Changed` handlers at
  `app.py:2364-2372`) is preserved because those handlers are app-level and still fire.
- **CRITICAL: the auto-save-on-tab-SWITCH path is LOST and must be replaced.** Today config is
  auto-saved by `on_tabbed_content_tab_activated` (`app.py`) when the user leaves the config TAB;
  the existing test `test_tui_config_tab` (`tests/test_tui.py:611-618`) asserts exactly this
  ("auto-save via tab activation"). Once Config is a modal (not a tab) that trigger NO LONGER
  fires. The Config overlay MUST therefore call `save_tui_config(notify=False)` on dismiss
  (`^m`/`Esc`/close), and the test must be migrated to assert save-on-dismiss. Not doing this
  silently drops config persistence.
- **Binding conflicts resolved:** old `^s`=Toggle Sidebar and `^r`=Refresh collided with the new
  `^s`=Search / `^r`=Running. Rebind Sidebar->`^b`, Refresh->`^u` (Update), Config->`^g`.
  Config was originally proposed on `^c` but rebound to `^g` in plan-review (see Goal) to keep
  `ctrl+c` out of a surprising "open a screen" role; `^q` quits. NOTE: the CURRENT in-tree
  edit still binds `ctrl+c`=show_config (app.py:1034) - the executor MUST change that binding to
  `ctrl+g` and update the `foot-config` label accelerator when doing TF-07..TF-14. TF-12 MUST
  test that `^g` opens Config and `^q` still quits.
- **Transition ordering (MUST):** the footer actions currently call `_activate_tab("tab-...")`.
  TF-07 (push overlays) and TF-09 (remove the tabs) MUST land in the SAME edit: rewire
  `action_show_doctor/running/config` from `_activate_tab(...)` to `push_screen(<Modal>())`
  BEFORE or WITH removing the panes. Removing a pane while an action still queries it would make
  `^d/^r/^g` and the footer buttons crash or no-op.
- **Esc is not automatic:** existing modals in this file (`app.py:78+`) `dismiss()` on a Cancel
  BUTTON; none binds Escape. The new overlays MUST add `BINDINGS = [Binding("escape","dismiss"),
  Binding("ctrl+m","dismiss")]` (or equivalent) for TF-08 to hold.
- **No `ocman/cli.py` change**; TUI-only. No DB, no dependency, no serialized-format change.

## Findings / requirements

| ID | Requirement | Status |
|----|-------------|--------|
| TF-01 | `#sidebar-pane` fixed width (40) so `#workspace` (1fr) takes the rest | DONE |
| TF-02 | Custom `#footer-bar`: key hints + clickable, distinctly-styled command buttons | DONE |
| TF-03 | Bindings: space/^q/^b/^u/^s/^d/^r/^g (note: in-tree still ^c; rebind to ^g in TF-07..14) wired to actions | DONE |
| TF-04 | Live sidebar glyph (🗹/☐) + bold `b`, updated on every toggle | DONE |
| TF-05 | `^s`/Search focuses the search field (un-hiding the sidebar if hidden) | DONE |
| TF-06 | Footer buttons clickable and equivalent to their key bindings | DONE (tab-switch form) |
| TF-07 | Doctor/Running/Config open as overlay ModalScreens (not tabs) | DONE |
| TF-08 | `^m` Main button + `Esc` dismiss overlay; overlays add `Binding("escape"/"ctrl+m","dismiss")` (not automatic) | DONE |
| TF-09 | Remove the Storage/Running/Config TAB PANES (superseded) | DONE |
| TF-10 | Config overlay: load-on-mount + auto-save-on-change + Save/Reset AND save_tui_config on dismiss (replaces the lost tab-switch save) | DONE |
| TF-11 | Storage/Running overlays self-load via fresh widget on_mount (verified: storage.py:113/129 worker, running.py:36/46 refresh) | DONE |
| TF-12 | New tests: footer buttons present, glyph toggles, each overlay opens/closes via key+button, focus-search, config round-trips from overlay incl. save-on-dismiss, `^g` opens Config and `^q` quits | DONE |
| TF-13 | Transition ordering: rewire show_doctor/running/config to push_screen IN THE SAME edit that removes the tabs (never query a removed pane) | DONE |
| TF-14 | Migrate existing tab-based tests: test_tui_config_tab (test_tui.py:585-624) + storage/running tests (test_tui.py:695-908) set TabbedContent.active to the removed tabs; rewrite to the overlay flow so they do not break | DONE |
| TF-15 | BUG in TF-01/TF-04: toggle_sidebar hides only `#sidebar` (the tree), leaving the search Input + `#search-results` visible. Toggle the whole `#sidebar-pane` instead so search + tree + results all hide/show together. Update `action_focus_search` and the footer glyph to read pane visibility. Add a regression test. | DONE |

## Non-goals

- No change to `ocman/cli.py` or any CLI behavior.
- No change to the Details/Actions/Admin/Spend/Models/Activity tabs.
- No new dependency; no DB or serialized-format change.
- Not reworking the doctor/running/config CONTENT, only how it is reached.

## Validation plan

- `PYTHONPATH=. pytest -q tests/test_tui.py` green, INCLUDING the MIGRATED tab-based tests
  (TF-14: test_tui_config_tab and the storage/running tests rewritten to the overlay flow) and
  the new TF-12 tests. A green run here must show the migrated tests pass, not just that new
  ones were added.
- Full suite `PYTHONPATH=. pytest -q` still 473+ pass (net of the migrated tests), 2 skipped.
  Paste the ACTUAL runner output (hard-MUST honesty rule); do not claim a count not run.
- Headless pilot smoke: footer buttons present; ^b toggles glyph; ^s focuses search; ^d/^r/^g
  open the correct overlay; ^m/Esc returns; config loads AND saves-on-dismiss from the overlay;
  ^g opens Config and ^q quits.
- No em/en dash in authored prose (`grep -nP $'[\u2013\u2014]'`).

### Acceptance gate (maintainer sign-off, MUST)

The maintainer said "I'll test some more then this is done." This work is NOT considered done on
green automated tests alone: the maintainer's own hand-testing of the running TUI is the final
acceptance gate. Do not mark the IPD executed / close the item until the maintainer confirms the
hand-tested result. Automated tests + pilot smoke are necessary but not sufficient.

## Commit grouping

- The already-in-tree in-progress edits (TF-01..TF-06: bindings + footer compose + actions +
  button wiring + CSS width/footer) are UNCOMMITTED to git at IPD authoring time. They commit as
  one "TUI footer bar + sidebar-width fix" unit once the plan is approved.
- Remaining (TF-07..TF-14): overlay ModalScreens + `^m`/Esc dismiss + tab removal + config
  save-on-dismiss + transition rewire + NEW tests + MIGRATED tests, as one coherent commit
  referencing TF IDs, after plan-review + maintainer approval. Both commits path-scoped to
  `ocman_tui/` + `tests/test_tui.py`; never `git add -A`; never push.

## Gate / execution contract (MUST, per AGENTS.md)

Before writing any code for the remaining work, the executor MUST first create a step-granular
TodoWrite checklist (one item per TF-07..TF-14 sub-step). Then:

- **Open questions:** all resolved in this plan (see plan-review Workflow history). None block execution.
- **Scope fence:** touch ONLY `ocman_tui/app.py`, `ocman_tui/css/style.css`, `tests/test_tui.py`.
  No `ocman/cli.py`, no DB, no dependency, no other tab's content.
- **Honesty rule (hard-MUST):** paste the ACTUAL `pytest` runner output for the validation run;
  never claim a pass/count that was not run.
- **Commits:** path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`/bare, never push.
- **Lifecycle:** on completion AND maintainer hand-test sign-off (the Acceptance gate above),
  `git mv` this plan `pending/ -> executed/` and re-`git add` the executed path so content stages.
  Do NOT mark executed on green automated tests alone.
- **Release interaction:** the paused 1.3.0 promotion (release-review run 20260721-180742) must get
  a delta re-review covering this TUI change before rung C resumes.

## Deferred / open

- Whether the Spend / Models / Admin / Activity views should ALSO move to overlays for
  consistency: deferred; this cut only moves the three the maintainer named (Doctor/Running/
  Config). Revisit if the maintainer wants a fully footer-driven navigation model.
