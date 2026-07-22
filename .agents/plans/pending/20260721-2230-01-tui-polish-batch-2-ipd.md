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
| B2-08 | Remove the now-useless `^s Search` (search box always visible) | RESOLVED: remove the foot-search footer button, the `ctrl+s` binding, AND action_focus_search entirely. | footer foot-search; binding ctrl+s; action_focus_search |
| B2-09 | Database SYSTEM METRICS: add much more info | Add rows (WAL size, page count/size, freelist, event-log row count, sessions/projects/parts counts, largest tables, last-vacuum). Reuse doctor/storage queries; read-only. | database.py:216-227 metrics-fields |
| B2-10a | DATABASE OPERATIONS: Retention -> "Clean Older Than: [5-char box] (example: 2h or 3mo)" | Relabel + accept a duration string (2h/3d/1w/3mo/1y); parse to a cutoff. Reuse any existing duration parser in cli.py. | database.py operations card |
| B2-10b | Add a units help line: h/d/w/mo/y | Static help label under the field. | database.py |
| B2-10c | Label the non-descript operation text boxes | Add labels/hints for each operation input. | database.py operations card |
| B2-11 | Allow selecting/copying text (Model, Transcript, SESSION METADATA) | RESOLVED "do what you can": attempt click-to-copy on metadata values + model via Textual `App.copy_to_clipboard` + a confirming toast. If the installed Textual has no working clipboard path (or SSH/no OSC-52), do NOT fake it: leave plain text and REPORT that copy is unavailable + why. Verify capability in execution. | Textual copy_to_clipboard availability |
| B2-12 | Activity Log: replace "Clear Historical Activity Log" with "Delete entries older than [box] days" + [DELETE] with confirm | New input + Delete button -> confirm modal -> prune `runs[]` older than N days ONLY. RESOLVED: `cumulative` historical spend/metadata is KEPT in perpetuity (NOT recomputed), so `spend --historical` is unchanged; only old action-log entries stop displaying. Needs a runs-only prune helper. | app.py clear-history-log button; cli.py _load/_save_history |
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

## Design decisions (RESOLVED with maintainer 2026-07-21)
- B2-08: RESOLVED = REMOVE `^s Search` entirely (the `ctrl+s` binding AND the foot-search button
  AND action_focus_search), since the search box is always visible in the sidebar. Also remove
  the B2-05/earlier "focus search / un-hide pane" behavior tied to it.
- B2-11: RESOLVED = "do what you can; if nothing, say so." PLAN: attempt click-to-copy on the
  metadata values + model via Textual `App.copy_to_clipboard` (fires a confirming toast). If the
  installed Textual lacks a working clipboard path (or it is a no-op over SSH/no OSC-52), do NOT
  fake it: leave the values as plain text and REPORT to the maintainer that copy is unavailable
  and why. Verify capability during execution; record the outcome.
- B2-07c: RESOLVED = the transcript-line filter uses the SAME query as the tree/search box
  (one query drives tree filtering + transcript-line filtering).
- B2-09: RESOLVED = add the broad-but-bounded metric set (WAL/SHM size, page count/size, freelist,
  row counts for session/project/parts/message, largest tables, last-vacuum, DB+WAL totals). MUST
  reuse doctor/storage's already-bounded queries and MUST NOT put a full event-log scan on the
  synchronous mount path (run heavy bits in the existing worker pattern if needed).
- B2-12: RESOLVED = the historical `cumulative` spend/metadata is kept IN PERPETUITY (never
  recomputed/reduced by a log prune, so `spend --historical` is unchanged). The age-prune ONLY
  drops old entries from the `runs[]` ACTION LOG so they no longer display in the Log tab.
  Cumulative totals are untouched.

## Follow-up questions (raised 2026-07-21; awaiting maintainer before plan-review)
- FU-1 (search timing): should the tree + transcript re-filter LIVE as the user types (on
  `Input.Changed`), or only on Enter (`Input.Submitted`)? Live is nicer but re-queries per
  keystroke. RECOMMEND: filter on Enter (submit); it matches the current "Enter to run" hint and
  avoids per-keystroke DB work on a large DB.
- FU-2 (metadata "Project (Dir)"): item 4a says "Project (Dir): /home/.../Fariel.com". The
  session dict has BOTH `directory` (the session's own dir) and `project_dir`/`worktree` (the
  owning project's root). Which do you want shown on that line - the project root, or the
  session directory? (They are often equal but not always.)
- FU-3 (button theme reach): B2-GEN one-color buttons - apply to ALL buttons including the
  compact footer command buttons (which currently have their own footer-btn style), or leave the
  footer bar as-is and only unify the in-pane action/dialog buttons? RECOMMEND: unify in-pane +
  dialog buttons; keep the footer bar its own (denser) style so the command bar stays distinct.
- FU-4 (clipboard confirmed available): Textual `App.copy_to_clipboard` EXISTS in the installed
  version, so B2-11 click-to-copy will be attempted; note it still depends on the terminal
  supporting OSC-52 (works in most modern terminals; may be a no-op over some SSH setups). No
  decision needed unless you want a different approach.

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
- Open questions: the 5 prior design decisions are RESOLVED (see Design decisions). Remaining
  follow-ups to settle in plan-review: FU-1 (search filter timing), FU-2 (metadata field data
  sources), FU-3 (button-theme scope) - see "Follow-up questions" below.
- Scope fence: `ocman_tui/**`, `tests/test_tui.py`, and (only if required for B2-12) one small
  tested helper in `ocman/cli.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output; never claim an unrun result.
- Config safety: every TUI test sets an isolated OCMAN_CONFIG_PATH; never touch the real config.
- Commits: path-scoped, never `git add -A`, never push.
- Lifecycle: on completion AND maintainer hand-test sign-off, git mv pending/ -> executed/.
- Release: 1.3.0 rung-C needs a delta release-review covering this batch.

## Deferred / open
- The 5 OPEN decisions above are resolved in plan-review before execution.
