# IPD: TUI polish batch 2 (search-as-filter, metadata fix, layout, button theme, log prune)

- Date: 2026-07-21
- Concern: UI/UX + accessibility + one correctness bug (metadata not updating on search-select)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{sidebar,database}.py`,
  possibly `ocman_tui/core.py` (read-only helpers), `tests/test_tui.py`. Item 12 (log prune by
  age) may need a small `ocman/cli.py` helper (`prune_history_older_than`) IF one does not exist;
  prefer reusing existing history helpers. No DB schema change. No new dependency.
- Status: PROPOSED (not yet executed)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused; a delta
  release-review must cover all the TUI work before rung C).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-21 (its_direct/pt3-claude-opus-4.8): second round of maintainer hand-test feedback
  (15 items + a global button-theme change) after the polish batch (20260721-2138-01).

## Answered up front (maintainer question)
Activity/history log storage: JSON sidecar at `~/.local/share/opencode/ocman_history.json`
(config key `history_path`). Shape: `{"cumulative": {..deleted totals..}, "runs": [ {..per-run
record with a "timestamp"..} ]}` (not line-oriented). Confirmed run records carry `timestamp`
(cli.py ~1441), so age-based pruning of `runs[]` + recompute of `cumulative` is feasible (item 12).

## Itemized requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| B2-01 | `^q` Quit and Space Select should be clickable | Convert the two `footer-key` Statics into clickable footer Buttons (foot-quit, foot-select) wired to action_quit / action_toggle_select. | footer-bar Statics in compose |
| B2-02 | Remove the space between the unicode glyph and the label in the footer | Footer button labels: drop the space (e.g. `🔎Search`, `🩺Doctor`) per the maintainer mockup. | footer buttons |
| B2-03a | FORMAT CONTROLS pane too wide; cap 25-30 cols, place right of SESSION METADATA | Layout: put SESSION METADATA + FORMAT CONTROLS in a Horizontal; `#controls-panel { width: 30; }`; metadata takes 1fr. | app.py:1211/1221 controls-panel |
| B2-03b | Label the unnamed text boxes under FORMAT CONTROLS | They are "Max Interactions" and "Max Lines" (labels exist but may be unclear); add a one-line hint of what they do (limit transcript size). | app.py:1224-1227 |
| B2-04 | SESSION METADATA: no blank line before data; specific field layout + labels | Rewrite update_metadata_view to the maintainer's exact field list/labels (Project (Dir), Session ID, Model, Created, Updated + duration, Cost); remove leading gap (panel-card-title margin). | app.py:1679 update_metadata_view |
| B2-05 | BUG: selecting a search-matched session updates TRANSCRIPT but NOT SESSION METADATA | on_data_table_row_selected (search path, app.py:1387) sets selected_* + start_session_export but never calls update_metadata_view. Fetch the full session row and call update_metadata_view like the tree path (app.py:1614). | app.py:1387-1413 vs 1605-1615 |
| B2-06 | TRANSCRIPT LOG: remove all inner padding (outer/inner box, scrollbar, top/bottom/left) | CSS: `.transcript-area`/`#transcript-md`/`#transcript-container` padding 0; scrollbar-gutter tight. | style.css:271 .transcript-area |
| B2-07 | Search box filters the TREE (projects+sessions) and TRANSCRIPT lines; no separate results box | REDESIGN: on search input, filter the sidebar Tree to projects-with-matches and matching sessions; filter transcript to matching lines; REMOVE the `#search-results` DataTable. See "Item 7 design" below. | app.py:1203 search-results; sidebar.py load_data |
| B2-08 | If the search box stays always-visible, remove the now-useless `^s Search` menu item | Remove foot-search button + ctrl+s binding + action_focus_search (or keep action, drop the footer button + binding). DECIDE in review: keep ^s as a focus-jump or remove entirely. | footer foot-search; binding ctrl+s |
| B2-09 | Database SYSTEM METRICS: add much more info | Add rows (WAL size, page count/size, freelist, event-log row count, sessions/projects/parts counts, largest tables, last-vacuum). Reuse doctor/storage queries; read-only. | database.py:216-227 metrics-fields |
| B2-10a | DATABASE OPERATIONS: Retention -> "Clean Older Than: [5-char box] (example: 2h or 3mo)" | Relabel + accept a duration string (2h/3d/1w/3mo/1y); parse to a cutoff. Reuse any existing duration parser in cli.py. | database.py operations card |
| B2-10b | Add a units help line: h/d/w/mo/y | Static help label under the field. | database.py |
| B2-10c | Label the non-descript operation text boxes | Add labels/hints for each operation input. | database.py operations card |
| B2-11 | Allow selecting/copying text (Model, Transcript, SESSION METADATA) OR click-to-copy | Prefer click-to-copy (Textual selection in a TUI is limited): make metadata values + model click-to-copy via `app.copy_to_clipboard` with a toast; transcript already selectable in a Markdown/scroll? Verify. DECIDE approach in review. | Textual copy_to_clipboard availability |
| B2-12 | Activity Log: replace "Clear Historical Activity Log" with "Delete entries older than [box] days" + [DELETE] with confirm | New input + Delete button -> ClearHistoryModal-style confirm -> prune runs[] older than N days and recompute cumulative. Needs a prune helper (see scope). | app.py clear-history-log button; cli.py _load/_save_history |
| B2-13 | Rename "Actions & Recovery" -> "Actions" | TabPane title. | app.py:1231 |
| B2-14 | Rename "Activity Log" -> "Log" | TabPane title. | app.py "Activity Log" |
| B2-15 | Actions -> LLM COMPACTION RUNNER: "Est Cost: Config load error" | update_estimated_cost catches all exceptions -> "Config load error" (app.py:1803-1807). Diagnose the real load_opencode_config failure (surface the actual error, and fix the cause; likely no compatible model / no api_key/base_url). | app.py:1795-1807 |
| B2-GEN | All buttons one color: 215 (yellow) fallback orange, black text. Dangerous buttons keep the neutral color but label `⚠Scary Thing` with `⚠` bold red. | Collapse Button.-primary/-success/-error to ONE style (bg ~ #ffd75f-ish / orange fallback, black text). Danger conveyed by the `[b red]⚠[/]` label prefix, not button color. Update all destructive button labels. | style.css Button variants; all destructive buttons |

## Item 7 design (search-as-filter; the biggest change)
- Today: typing in the search box runs `db_search_sessions` and fills a separate `#search-results`
  DataTable below the tree (app.py:1203/1360). The tree is unaffected.
- New model:
  1. The sidebar Tree shows only projects that contain >=1 matching session, and only the matching
     sessions under them (7a/7b). Empty query => full tree.
  2. Selecting a filtered session updates BOTH metadata and transcript (ties into B2-05).
  3. The transcript view filters to matching lines when a query is active (7c). DECIDE: is the
     transcript-line filter the SAME query as the tree filter, or a separate control? RECOMMEND
     same query, applied in render_current_transcript, with a note.
  4. Remove the `#search-results` DataTable entirely (7d) unless a benefit is articulated (none is).
- This needs: a sidebar `load_data(filter=...)` that prunes non-matching nodes; wiring the search
  input's Changed/Submitted to re-filter the tree (debounce not required at this scale); and a
  transcript-line filter in render_current_transcript.

## Design decisions to settle in plan-review (OPEN)
- B2-08: remove `^s Search` entirely, or keep `^s` as a "jump focus to the always-visible search
  box" accelerator (footer button removed either way)? RECOMMEND keep the binding, drop the footer button.
- B2-11: click-to-copy vs enabling text selection. RECOMMEND click-to-copy on metadata values +
  model (Textual `App.copy_to_clipboard`), because terminal text selection is unreliable in a
  full-screen app; verify the Textual version supports it, else fall back to a note.
- B2-07c: transcript-line filter uses the same query as the tree filter (RECOMMEND) vs a separate box.
- B2-09: exact metric set (bounded, read-only, must not be slow on a large DB - reuse doctor's
  already-bounded queries; do NOT add a full event-log scan to a synchronous mount path).
- B2-12: N-days prune semantics - prune `runs[]` older than N days AND recompute `cumulative`
  from the survivors, or keep cumulative as an all-time total and only prune runs[]? DECIDE (the
  cumulative is used by `spend --historical`, so recomputing changes that number).

## Non-goals
- No DB schema change; no new dependency; no change to CLI behavior except a possibly-new,
  small, well-tested history-prune helper reused by the TUI.
- Not redesigning the data shown, except B2-09 (more metrics) and B2-04 (metadata field layout).

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. Every TUI test isolates
  `OCMAN_CONFIG_PATH` (never write the real user config).
- New/updated tests: B2-05 (search-select updates metadata), B2-07 (tree filters to matches;
  no #search-results widget), B2-12 (age-prune keeps newer runs, drops older, confirm modal),
  B2-13/14 (tab titles), B2-15 (est-cost path surfaces a real reason, not a generic error),
  B2-GEN (all buttons share one style class; destructive labels carry the warn glyph),
  B2-01/02 (footer quit/select clickable; glyph-label spacing), B2-11 (copy action fires a toast).
- Headless pilot smoke of the new search-filter + renamed tabs.
- No em/en dash in authored prose.
- Manual hand-test acceptance gate (below) for the visual items (03a, 04, 06, 09, 10, GEN).

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one item per B2-* sub-step) BEFORE coding.
- Open questions: B2-08, B2-11, B2-07c, B2-09 scope, B2-12 semantics (resolve in plan-review).
- Scope fence: `ocman_tui/**`, `tests/test_tui.py`, and (only if required for B2-12) one small
  tested helper in `ocman/cli.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output; never claim an unrun result.
- Config safety: every TUI test sets an isolated OCMAN_CONFIG_PATH; never touch the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off, git mv pending/ -> executed/.
- Release: 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- The 5 OPEN decisions above are resolved in plan-review before execution.
