# IPD: TUI footer command bar + sidebar-width fix + Doctor/Running/Config overlays

- Date: 2026-07-21
- Concern: UI/UX (TUI layout + discoverability of global views)
- Scope: `ocman_tui/app.py` (bindings, compose footer, actions, modal screens, tab removal),
  `ocman_tui/css/style.css` (sidebar-pane width, footer bar styling), `tests/test_tui.py`.
  No `ocman/cli.py` change. No DB schema change. No new dependency.
- Status: PROPOSED (partially executed; written retroactively - see Workflow history)
- Target version: rides the in-flight 1.3.0 line (final 1.3.0 promotion is paused pending this
  UI work; this rides along and re-triggers a release-review delta pass before promotion).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-21 (its_direct/pt3-claude-opus-4.8): the maintainer surfaced two TUI problems while
  hand-testing during the paused 1.3.0 release-review Section 9, and proposed a footer command
  bar. Implementation of the width fix + footer bar + rebindings BEGAN before an IPD existed
  (a process miss). This IPD is written RETROACTIVELY to capture the plan, mark the already-done
  parts, and gate the remaining overlay-screen refactor through the normal lifecycle. Per
  AGENTS.md the correct closure of a process gap is a new plan, not a silent continuation.

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
  `^r` ▶ Running, `^c` ⚙ Config, `^m` Main.
- Maintainer's target layout line (verbatim, the look to match):
  `[space] Select  ^q Quit  ^b ☐Sidebar  ^u ↻Update  ^s🔎Search  ^d🩺Doctor  ^r ▶Running  ^c ⚙Config`
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
  `save_tui_config` use app-level `self.query_one("#cfg-...")`, which searches the whole DOM
  (including a mounted modal), so config load/save keeps working from the overlay. Config load
  is triggered after the modal mounts; auto-save-on-change (the `cfg-*` handlers) is preserved.
- **Binding conflicts resolved:** old `^s`=Toggle Sidebar and `^r`=Refresh collided with the new
  `^s`=Search / `^r`=Running. Rebind Sidebar->`^b`, Refresh->`^u` (Update). `^c` overrides
  Textual's default quit-on-ctrl-c (intended: it is now Config; `^q` quits).
- **No `ocman/cli.py` change**; TUI-only. No DB, no dependency, no serialized-format change.

## Findings / requirements

| ID | Requirement | Status |
|----|-------------|--------|
| TF-01 | `#sidebar-pane` fixed width (40) so `#workspace` (1fr) takes the rest | DONE |
| TF-02 | Custom `#footer-bar`: key hints + clickable, distinctly-styled command buttons | DONE |
| TF-03 | Bindings: space/^q/^b/^u/^s/^d/^r/^c wired to actions | DONE |
| TF-04 | Live sidebar glyph (🗹/☐) + bold `b`, updated on every toggle | DONE |
| TF-05 | `^s`/Search focuses the search field (un-hiding the sidebar if hidden) | DONE |
| TF-06 | Footer buttons clickable and equivalent to their key bindings | DONE (tab-switch form) |
| TF-07 | Doctor/Running/Config open as overlay ModalScreens (not tabs) | PENDING |
| TF-08 | `^m` / Main button + `Esc` return to the main workspace (dismiss overlay) | PENDING |
| TF-09 | Remove the Storage/Running/Config TAB PANES (superseded) | PENDING |
| TF-10 | Config overlay preserves load-on-open + auto-save-on-change + Save/Reset | PENDING |
| TF-11 | Storage/Running overlays self-load via fresh widget on_mount | PENDING |
| TF-12 | Tests: footer buttons present, glyph toggles, each overlay opens/closes, focus-search, config round-trips from the overlay | PENDING |

## Non-goals

- No change to `ocman/cli.py` or any CLI behavior.
- No change to the Details/Actions/Admin/Spend/Models/Activity tabs.
- No new dependency; no DB or serialized-format change.
- Not reworking the doctor/running/config CONTENT, only how it is reached.

## Validation plan

- `PYTHONPATH=. pytest -q tests/test_tui.py` green, plus new TF-12 tests.
- Full suite `PYTHONPATH=. pytest -q` still 473+ pass, 2 skipped (paste real output).
- Headless pilot smoke: footer buttons present; ^b toggles glyph; ^s focuses search; ^d/^r/^c
  open the correct overlay; ^m/Esc returns; config loads and saves from the overlay.
- No em/en dash in authored prose.

### Acceptance gate (maintainer sign-off, MUST)

The maintainer said "I'll test some more then this is done." This work is NOT considered done on
green automated tests alone: the maintainer's own hand-testing of the running TUI is the final
acceptance gate. Do not mark the IPD executed / close the item until the maintainer confirms the
hand-tested result. Automated tests + pilot smoke are necessary but not sufficient.

## Commit grouping

- Already committed to the working tree as in-progress edits (NOT yet committed to git at IPD
  authoring time): bindings + footer compose + actions + button wiring + CSS width/footer.
- Remaining (TF-07..TF-12): overlay ModalScreens + tab removal + `^m` + tests, as one coherent
  commit referencing TF IDs, after plan-review + maintainer approval.

## Deferred / open

- Whether the Spend / Models / Admin / Activity views should ALSO move to overlays for
  consistency: deferred; this cut only moves the three the maintainer named (Doctor/Running/
  Config). Revisit if the maintainer wants a fully footer-driven navigation model.
