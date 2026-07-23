# IPD: TUI polish batch 2 (search-as-filter, metadata fix, layout, button theme, log prune)

- Date: 2026-07-21
- Concern: UI/UX + accessibility + one correctness bug (metadata not updating on search-select)
- Scope: `ocman_tui/app.py`, `ocman_tui/css/style.css`, `ocman_tui/widgets/{sidebar,database}.py`,
  possibly `ocman_tui/core.py` (read-only helpers), `tests/test_tui.py`. Item 12 (log prune by
  age) may need a small `ocman/cli.py` helper (`prune_history_older_than`) IF one does not exist;
  prefer reusing existing history helpers. No DB schema change. No new dependency.
- Status: executed (maintainer authorized move to executed/ 2026-07-22; hand-tested across subsequent batches)
- Target version: rides the in-flight 1.3.0 line (final promotion still paused; a delta
  release-review must cover all the TUI work before rung C).
- Approval: maintainer approved 2026-07-21 ("Approved. Go.")
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history
- 2026-07-21 (its_direct/pt3-claude-opus-4.8): second round of maintainer hand-test feedback
  (15 items + a global button-theme change) after the polish batch (20260721-2138-01).
- 2026-07-21 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED;
  PR-201..PR-206. Verified evidence: parse_duration_to_days exists with exactly h/d/w/mo/y units
  (cli.py:4910) and db clean uses --older-than (6185); transcript is a Markdown widget (1218);
  copy_to_clipboard present; est-cost generic-catch confirmed (1803). Decided NOT to split (one
  coherent subsystem pass, tightly coupled). Revisions: pinned the duration parser (B2-10a/12),
  scoped click-to-copy to metadata/model + honest transcript report (B2-11), split the est-cost
  error handling (B2-15), defined transcript-line matching (B2-07c), added visual/CSS regression
  guards (validation). Status -> reviewed; GO - PENDING HUMAN APPROVAL.

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
| B2-04 | SESSION METADATA: no blank line before data; specific field layout + labels | Rewrite update_metadata_view to the field list (FU-2 applied): `Project:` = project root (project_dir/worktree); `Session ID:`; `Model:`; `Created:`; `Updated:` + duration `(Nd HH:MM:SS)`; `Cost:`; then `Directory:` = session dir LAST and ONLY if it differs from Project. Remove the leading gap (panel-card-title margin -> 0). | app.py:1679 update_metadata_view |
| B2-05 | BUG: selecting a search-matched session updates TRANSCRIPT but NOT SESSION METADATA | on_data_table_row_selected (search path, app.py:1387) sets selected_* + start_session_export but never calls update_metadata_view. Fetch the full session row and call update_metadata_view like the tree path (app.py:1614). | app.py:1387-1413 vs 1605-1615 |
| B2-06 | TRANSCRIPT LOG: remove all inner padding (outer/inner box, scrollbar, top/bottom/left) | CSS: `.transcript-area`/`#transcript-md`/`#transcript-container` padding 0; scrollbar-gutter tight. | style.css:271 .transcript-area |
| B2-07 | Search box filters the TREE (projects+sessions) and TRANSCRIPT lines; no separate results box | REDESIGN: on search SUBMIT (Enter only, FU-1), filter the sidebar Tree to projects-with-matches and matching sessions; filter transcript to matching lines (same query); REMOVE the `#search-results` DataTable. Empty query => full tree/transcript. See "Item 7 design" below. | app.py:1203 search-results; sidebar.py load_data |
| B2-08 | Remove the now-useless `^s Search` (search box always visible) | RESOLVED: remove the foot-search footer button, the `ctrl+s` binding, AND action_focus_search entirely. | footer foot-search; binding ctrl+s; action_focus_search |
| B2-09 | Database SYSTEM METRICS: add much more info | Add rows (WAL size, page count/size, freelist, event-log row count, sessions/projects/parts counts, largest tables, last-vacuum). Reuse doctor/storage queries; read-only. | database.py:216-227 metrics-fields |
| B2-10a | DATABASE OPERATIONS: Retention -> "Clean Older Than: [5-char box] (example: 2h or 3mo)" | Relabel + accept a duration string; parse via the EXISTING `parse_duration_to_days(text)` (cli.py:4910), which supports exactly `h/d/w/mo/y` and raises `DurationError` on bad input (surface that as an inline error, do not crash). Do NOT write a new parser. | cli.py:4910 parse_duration_to_days; db clean already uses --older-than AGE cli.py:6185 |
| B2-10b | Add a units help line: h/d/w/mo/y | Static help label under the field. | database.py |
| B2-10c | Label the non-descript operation text boxes | Add labels/hints for each operation input. | database.py operations card |
| B2-11 | Allow selecting/copying text (Model, Transcript, SESSION METADATA) | RESOLVED "do what you can": click-to-copy scoped to the DISCRETE metadata values + model (Static widgets we control -> on_click -> `App.copy_to_clipboard(value)` + confirming toast). The TRANSCRIPT is a `Markdown#transcript-md` widget (app.py:1218) where per-value click-to-copy is not feasible; do NOT promise transcript click-to-copy - instead note that terminal-native selection may or may not work and REPORT honestly. Textual `copy_to_clipboard` exists (verified); still OSC-52-dependent. | app.py:1218 Markdown transcript; copy_to_clipboard verified present |
| B2-12 | Log tab: replace "Clear Historical Activity Log" with a "Clean Older Than:" duration prune + [DELETE] with confirm | UPDATED (item 12a): use the EXACT SAME time approach as B2-10a/b in Database Operations - a `Clean Older Than: [5-char box] (example: 2h or 3mo)` field + the same `h = hours, d = days, w = weeks, mo = months, y = years` legend line + the SAME shared duration parser. A [DELETE] button opens a confirm modal, then prunes `runs[]` older than the parsed cutoff ONLY. RESOLVED: `cumulative` historical spend/metadata is KEPT in perpetuity (NOT recomputed), so `spend --historical` is unchanged; only old action-log entries stop displaying. Needs a runs-only prune helper that takes the same cutoff. | app.py clear-history-log button; cli.py _load/_save_history; shared duration parser (B2-10a) |
| B2-13 | Rename "Actions & Recovery" -> "Actions" | TabPane title. | app.py:1231 |
| B2-14 | Rename "Activity Log" -> "Log" | TabPane title. | app.py "Activity Log" |
| B2-15 | Actions -> LLM COMPACTION RUNNER: "Est Cost: Config load error" | `update_estimated_cost` wraps `load_opencode_config` + `extract_models_from_config` + `resolve_model` in ONE `except Exception` -> the generic "Config load error" (app.py:1803-1807). Split the handling: distinguish config-load failure from model-not-resolvable, and show the SPECIFIC reason (e.g. "no compatible model configured" / "model <spec> not found") instead of the misleading generic string. Fix the underlying cause if it is a real resolve bug. | app.py:1795-1815 |
| B2-GEN | All buttons one color: 215 (yellow) fallback orange, black text. Dangerous buttons keep the neutral color but label `⚠Scary Thing` with `⚠` bold red. | Collapse Button.-primary/-success/-error INTO ONE style (bg ~ `#ffd75f` = xterm 215 / orange fallback, black text). FU-3: this includes the footer command bar (fold `.footer-btn` into the shared style, keeping footer height/density). Danger conveyed by the `[b red]⚠[/]` label prefix, not button color. Update all destructive button labels. | style.css Button variants + .footer-btn; all destructive buttons |

## Item 7 design (search-as-filter; the biggest change)
- Today: typing in the search box runs `db_search_sessions` and fills a separate `#search-results`
  DataTable below the tree (app.py:1203/1360). The tree is unaffected.
- New model:
  1. The sidebar Tree shows only projects that contain >=1 matching session, and only the matching
     sessions under them (7a/7b). Empty query => full tree.
  2. Selecting a filtered session updates BOTH metadata and transcript (ties into B2-05).
  3. The transcript view filters to matching lines when a query is active (7c), using the SAME
     query (FU-1/B2-07c). "Matching line" = case-insensitive substring match on the rendered
     transcript line; non-matching lines are dropped (no surrounding context lines in this cut).
     Applied in render_current_transcript AFTER the existing truncation, so an active query
     narrows what is shown. Empty query => no line filtering.
  4. Remove the `#search-results` DataTable entirely (7d) unless a benefit is articulated (none is).
- This needs: a sidebar `load_data(filter=...)` that prunes non-matching nodes; wiring the search
  input's `Submitted` (Enter ONLY, FU-1; not Changed) to re-filter the tree; and a transcript-line
  filter in render_current_transcript keyed off the same active query.

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
  recomputed/reduced by a log prune, so `spend --historical` is unchanged). The prune ONLY
  drops old entries from the `runs[]` ACTION LOG so they no longer display in the Log tab.
  Cumulative totals are untouched. UPDATED (item 12a): the cutoff is entered with the SAME
  "Clean Older Than:" duration field + legend + shared parser as Database Operations (B2-10a/b),
  NOT a plain "N days" box.

## Follow-up questions (RESOLVED with maintainer 2026-07-21)
- FU-1 (search timing): RESOLVED = filter ONLY on Enter (`Input.Submitted`), never per-keystroke
  ("it's slow enough already"). The tree + transcript re-filter on submit.
- FU-2 (metadata dirs): RESOLVED = show TWO distinct lines: `Project:` = the project root
  (`project_dir`/`worktree`), and `Directory:` = the session's own dir, placed UNDER `Cost`,
  and shown ONLY IF it differs from the project dir. If they are equal, omit the `Directory:`
  line. (Revises the B2-04 field list: Project replaces the old "Project (Dir)"; Directory is
  conditional and last.)
- FU-3 (button theme reach): RESOLVED = apply the one-color button theme to ALL buttons,
  INCLUDING the footer command bar ("consistency is king/queen"). Collapse footer-btn into the
  shared button style (keeping only the density/height the footer needs). B2-GEN now covers the
  footer buttons too.
- FU-4 (clipboard): ACKNOWLEDGED = proceed with click-to-copy; terminal OSC-52 dependency noted,
  report if it no-ops. No change.

## Split assessment (maintainer asked "split if it should be")
DECISION: keep as ONE IPD (do NOT split). The 19 items are a single coherent polish pass over
one subsystem (`ocman_tui/`), share the same files, one test file, and one hand-test acceptance
gate, and are tightly coupled: B2-05 ties into B2-07; B2-07 removes the search-results box that
B2-08's `^s` targeted; B2-10a's `parse_duration_to_days` is reused by B2-12; B2-GEN restyles
every button including the footer buttons that B2-01/B2-02 add/relabel. Splitting would fracture
these couplings and multiply the regression surface for no benefit. Execution still uses a
step-granular TodoWrite checklist per item.

- 2026-07-21 (its_direct/pt3-claude-opus-4.8): EXECUTED B2-01..B2-15 + B2-GEN (commits 6f4aa18
  part 1; 874a9ac part 2). Full suite 489 passed, 2 skipped. Notes: B2-11 click-to-copy uses
  Textual `copy_to_clipboard` (OSC-52) on the metadata block - works in most terminals, may
  no-op over some SSH; verify in hand-test. B2-09 metrics use fast PRAGMAs + COUNTs on the mount
  path (no event-log scan). B2-12 added `prune_history_runs_older_than` (cli.py) keeping
  cumulative in perpetuity. Search redesign (B2-07) removed `#search-results`; 4 old tests were
  migrated + `test_tui_clear_history` rewritten for age-prune. Real user config NOT touched
  (isolated). CAVEATS for hand-test: B2-11 clipboard (terminal-dependent), and the visual items
  (B2-03a layout, B2-04 metadata, B2-06 transcript padding, B2-08 no ^s, B2-09 metrics,
  B2-10/12 fields, B2-GEN button color). Plan stays in pending/ until maintainer hand-test
  sign-off, then git mv -> executed/.
- 2026-07-21 (its_direct/pt3-claude-opus-4.8): B2-GEN COMPLETION (commit 3b3507b). The initial
  B2-GEN commit unified button COLOR but only labeled 1 of the destructive buttons with the
  bold-red warn glyph; on maintainer challenge ("do you believe you're done?") this was verified
  as an under-delivery and fixed: all 18 destructive buttons (10 app.py, 3 database.py, 5
  storage.py incl. PROCEED + reclaim/VACUUM) now carry `[b red]⚠[/]`, with a regression-guard
  test (test_tui_destructive_buttons_carry_warn_glyph). Suite 490 passed, 2 skipped.

## Plan-review findings (2026-07-21)
| ID | Sev | Scope | Area | Evidence | Finding | Decision |
|----|-----|-------|------|----------|---------|----------|
| PR-201 | MEDIUM | IN-SCOPE | C/arch | whole IPD | Split-or-not decision (maintainer asked) | FIXED (keep one IPD; rationale above) |
| PR-202 | LOW | UNDER-SCOPE | A/correctness | cli.py:4910 | B2-10a/B2-12 said "reuse any parser" vaguely | FIXED (pinned parse_duration_to_days; units match h/d/w/mo/y) |
| PR-203 | MEDIUM | UNDER-SCOPE | F/UX | app.py:1218 | B2-11 implied transcript click-to-copy; transcript is a Markdown widget where that is not feasible | FIXED (scope copy to metadata/model Statics; transcript honest-report) |
| PR-204 | MEDIUM | UNDER-SCOPE | A/correctness | app.py:1803 | B2-15 generic catch hides model-resolve vs config-load | FIXED (split handling, show specific reason) |
| PR-205 | LOW | UNDER-SCOPE | E/testing | style.css | visual items (03a/04/06/09/GEN) had no regression guard | FIXED (CSS/label-presence asserts added to validation) |
| PR-206 | MEDIUM | UNDER-SCOPE | A/correctness | app.py:1770 | B2-07c "matching lines" was undefined | FIXED (case-insensitive substring, drop non-matching, after truncation) |

## Non-goals
- No DB schema change; no new dependency; no change to CLI behavior except a possibly-new,
  small, well-tested history-prune helper reused by the TUI.
- Not redesigning the data shown, except B2-09 (more metrics) and B2-04 (metadata field layout).

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green; paste ACTUAL output. Every TUI test isolates
  `OCMAN_CONFIG_PATH` (never write the real user config).
- New/updated tests: B2-05 (search-select updates metadata), B2-07 (tree filters to matches;
  no #search-results widget), B2-12 (duration-string prune keeps newer runs, drops older,
  confirm modal, cumulative untouched; parses 2h/3mo via the shared B2-10a parser),
  B2-13/14 (tab titles), B2-15 (est-cost path surfaces a real reason, not a generic error),
  B2-GEN (all buttons share one style class; destructive labels carry the warn glyph),
  B2-01/02 (footer quit/select clickable; glyph-label spacing), B2-11 (copy action fires a toast).
- Headless pilot smoke of the new search-filter + renamed tabs.
- PR-205 regression guards: assert (in tests) the presence of the one-color button style, the
  transcript zero-padding CSS, the FORMAT-CONTROLS width cap, the metadata no-leading-gap, and
  the expanded metrics rows, so a later edit cannot silently revert these visual/CSS fixes.
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
