# Roadmap: bring the TUI to feature parity with the CLI (umbrella)

- Date: 2026-07-18
- Concern: functionality (feature completeness / CLI<->TUI parity), with a ui-ux lens
- Scope: the Textual TUI package `ocman_tui/` (app + widgets + modals), measured
  against the current CLI feature set in `ocman/cli.py`. The CLI itself is NOT in scope
  (it is the reference implementation).
- Status: executed (umbrella; all 5 per-phase IPDs are executed)
- Author: its_direct/pt3-claude-opus-4.8

## What this document is

This is the UMBRELLA / roadmap for the TUI-parity effort, not a single executable plan.
The assessment found that "bring the TUI to parity" is really an epic: each phase is its
own design problem (its own tabs/modals, tests, and risk profile). So the executable work
is split into one focused IPD per phase; this file is the shared reference (findings
inventory, architecture notes, cross-cutting decisions, and the phase index). Each
per-phase IPD is written, hardened via `plan-review`, human-approved, then executed and
moved to `executed/` on its own.

Full 5-phase parity is the release gate (maintainer decision, OQ-5). New TUI views use new
top-level tabs (maintainer decision, OQ-6).

## Phase index (one IPD per phase)

| Phase | Scope | IPD | Status |
|-------|-------|-----|--------|
| 1 | Delete-safety: extract-on-delete in TUI + working clear-history | `executed/20260718-1648-02-tui-p1-delete-safety-ipd.md` | EXECUTED (commit 45eb8c4) |
| 2 | Storage checkup (read-only doctor view) + guarded reclaim | `executed/20260718-1648-03-tui-p2-doctor-reclaim-ipd.md` | EXECUTED |
| 3 | Reporting: spend + running views (read-only) | `executed/20260718-1648-04-tui-p3-spend-running-ipd.md` | EXECUTED |
| 4 | Bulk + large sessions: multi-select batch, db clean duration/scope, chunk | `executed/20260718-1648-05-tui-p4-bulk-and-chunk-ipd.md` | EXECUTED |
| 5 | Breadth: project bundles, local move, backup clean, content search, filter | `executed/20260718-1648-06-tui-p5-breadth-ipd.md` | EXECUTED |

The one hard exclusion across all phases: the reclaim snapshot-force mode stays CLI-only
(OQ-2); the TUI shows a note pointing to `ocman reclaim --force-snapshots` / `ocman doctor`.

## Follow-ups discovered during execution (not in scope of the parity phases)

- FU-01 (found in P4): `save_tui_config` (`ocman_tui/app.py`) writes only the keys the config
  form manages, and `save_ocman_config` merges the passed subset over `DEFAULT_CONFIG` (not
  over the EXISTING config). So a TUI config save silently RESETS unmanaged keys
  (`chunk_max_interactions`, `chunk_max_lines`, `reclaim_*`, `filter_*`,
  `copy_restart_to_project_prompts`, `history_max_runs`) to their defaults, discarding a
  user's customization. Pre-existing (not introduced by the parity work) and out of the P4
  scope fence. Recommend a small corrective IPD: either have `save_tui_config` load-merge
  the current config before saving, or have `save_ocman_config` merge over the existing file
  rather than over `DEFAULT_CONFIG`. Data-loss-of-config severity: Medium.
- FU-02 (found in P5, FIXED in P5's commit): the transcript `export_worker` error path called
  `self.query_one("#transcript-md")` directly in the worker thread; with a modal active (or
  during teardown) the widget is absent and it raised an unhandled thread exception. Fixed by
  marshalling the error render onto the UI thread and guarding the lookup. Noted here for the
  record; no further action needed.

## Status: ALL PHASES EXECUTED

Phases 1-5 are all executed (commits 45eb8c4, 79f5818, 2fde996, 6e6286a, and the P5 commit).
The TUI now has parity with the CLI for the in-scope features; the only deliberate CLI-only
exclusions are the reclaim snapshot-force mode (OQ-2) and remote/git-aware move + `db rebase`
(OQ-3 / T-15). Remaining non-phase follow-ups: FU-01 (config-save key reset) and the
consolidated README/ARCHITECTURE TUI-docs update.

## Workflow history

- 2026-07-18 /assess functionality tui-parity (its_direct/pt3-claude-opus-4.8): assessed
  the TUI against the CLI; proposed a phased parity plan.
- 2026-07-18 restructured into this umbrella + per-phase IPDs (maintainer direction: the
  parity work should generate several distinct, reviewable IPDs, not one). Phase 1 was
  already executed (45eb8c4) and is retro-documented as its own executed IPD.

## Goal

The CLI has grown a large feature set (doctor/reclaim, spend, list-running,
extract-on-delete, chunking, batch delete, db clean --older-than, git-aware move,
project export/import, backup clean, search, filter). The Textual TUI (`ocman_tui/`)
is a separate package that has fallen well behind: most of these features are not
reachable from the TUI at all, and a few are only partially wired. Before release we
want the TUI to expose the same core capabilities as the CLI, so a user who prefers the
interactive UI is not silently missing functionality (and is not exposed to a MORE
dangerous default in the UI than the CLI, e.g. deleting without recovery extracts).

This IPD proposes the parity work as ordered, reviewable phases. It does not execute.

## Project conventions discovered (Step 0)

- Intent/audience: ocman administers, maintains, and repairs an OpenCode agentic
  environment (sessions, DB, config), for a technically-comfortable single maintainer and
  power users. The TUI is the interactive front door; the CLI is the scriptable one.
- Guiding principles: AGENTS.md + the universal fallback (intuitive/self-documenting,
  general-case/configurable, KISS, honest UX). Prose rule: NO em/en dashes in authored
  text (the em-dash "not available" table glyph is the only sanctioned exception).
- Plan lifecycle: `.agents/plans/pending/` -> `.agents/plans/executed/`; filename
  `YYYYMMDD-HHMM-NN-<slug>.md`; front-matter Status draft -> to-review -> reviewed ->
  approved -> executed.
- Contributor contract: AGENTS.md (path-scoped commits, never push, paste REAL pytest
  output). This IPD touches TUI code when executed, so each executed phase MUST run the
  suite (`PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`) and paste the result.
- Stack: `ocman/cli.py` (CLI + all core logic; the TUI imports from it via
  `ocman_tui/core.py`) and `ocman_tui/` (Textual App: 6-tab `TabbedContent`, a
  single-select sidebar `Tree`, worker-thread pattern for long ops, `ModalScreen`
  confirmations).

## TUI architecture (as-is), for the executing agent

- Entry: `ocman ui` / `ocman gui` -> `ocman/cli.py` launches `ocman_tui.app.OrsessionApp`.
- `OrsessionApp(App)` (`ocman_tui/app.py:762`): 6 tabs - Details & Transcript,
  Actions & Recovery, Database Admin (`DatabaseAdminWidget`), Models Library,
  Activity Log, Configuration Settings. Global keybindings ctrl+q/ctrl+s/ctrl+r.
- Sidebar `SidebarWidget(Tree)` (`ocman_tui/widgets/sidebar.py`): SINGLE-select
  (`on_tree_node_selected`, `app.py:1027`); selecting a node sets
  `selected_session_id` / `selected_project_id` and enables the action buttons.
- `DatabaseAdminWidget` + `OrphanInspectorModal` (`ocman_tui/widgets/database.py`).
- `ocman_tui/core.py` is a thin re-export shim over `ocman`; it already re-exports some
  unused symbols (`db_move_session_metadata`, `db_rebase_paths`, `db_get_session_subtree`).
- Long operations run in worker threads and marshal UI updates back to the app; new
  long-running features (doctor/reclaim/extraction) MUST follow this pattern and honor
  the `_shutting_down` guard.

## Findings

Severity = user impact if left as-is. Remediation Risk = the Fix-Bar gate (complexity of
wiring it into the TUI). Persona: PU = power user, NOV = novice, STK = stakeholder,
QA = quality/QA. Class: Required (blocks the TUI's purpose as a management UI), Expected
(a UI user will assume it exists because the CLI has it), Nice-to-have.

| ID | Sev | Rem.Risk | Persona | Class | Feature missing/partial in TUI | Evidence |
|----|-----|----------|---------|-------|-------------------------------|----------|
| T-01 | High | Medium | PU/QA | Required | **extract-on-delete not in TUI.** TUI delete calls `db_delete_session_recursive` / `db_delete_project_recursive` with `force=True, confirm=False` and never writes recovery extracts. The UI is thus MORE destructive than the CLI (CLI now offers/writes extracts by default). | `ocman_tui/app.py:1453-1459`, `1567-1573`; CLI `run_delete_extracts`/`resolve_extract_choice` in `cli.py` |
| T-02 | High | Medium | STK/PU | Expected | **doctor (storage checkup) absent.** No import, button, or view. The headline "diagnose and repair" capability is CLI-only. | no ref in `ocman_tui/`; CLI `cli_doctor`/`run_doctor_checks` |
| T-03 | High | Med-High | STK/PU | Expected | **reclaim (disk reclamation) absent.** Guarded, multi-mode, destructive; needs careful UI (preview + confirms + the snapshot warning). | no ref in `ocman_tui/`; CLI `cli_reclaim` |
| T-04 | Medium | Medium | PU | Expected | **spend / spend --historical absent.** TUI shows only per-session cost and lifetime "saved" totals; no per-project spend table or historical view. | `app.py:1081,1007`, `database.py:322`; CLI `cli_spend` |
| T-05 | Medium | Medium | PU/STK | Expected | **list running (running + insecure OpenCode instances) absent.** No security surfacing of unauthenticated/non-loopback control servers. | no ref; CLI `cli_list_running` |
| T-06 | Medium | Medium | PU | Expected | **batch / multi-session actions absent.** Sidebar is single-select; no multi-select delete/export. CLI does consolidated batch delete. | `app.py:1027` single-select; CLI `session delete SPECS...` |
| T-07 | Medium | Low | PU | Expected | **db clean is integer-days only.** No `--older-than` duration (2h/6w/6mo/1y), no per-project scope, no `-y`, no extract option. | `database.py:236,358`; CLI `_add_clean_opts` |
| T-08 | Medium | Low | PU | Expected | **--chunk not offered in TUI recover/compact.** TUI only truncates a large session; no split-into-parts option. | `app.py:1157`; CLI `chunk_turns` |
| T-09 | Medium | Medium | PU | Expected | **project export & project import absent.** TUI export button is disabled for projects; import modal is session-only. Only session .ocbox is supported. | `app.py:1075` (export disabled for project), import modal session-scoped; CLI `bundle_project_data`/`extract_and_import_project` |
| T-10 | Low | Low | PU | Expected | **session move absent; project move is local-only.** `MoveProjectModal` does a local physical move; no remote `host:/path` runbook, git-awareness, dry-run, or `--confirm-remote-delete`; no session-move at all. `db_move_session_metadata`/`db_rebase_paths` are imported but unused. | `app.py:396,1521`; `core.py:50-51`; CLI `session move`/`project move`/`db rebase` |
| T-11 | Low | Low | PU | Expected | **backup clean absent** (prune old backup archives). CLI has `backup clean --older-than`. | no ref; CLI `backup clean` |
| T-12 | Low | Med | PU | Expected | **content search absent.** No session content/title search in the TUI (the Models tab "search" only filters the model table). | `models.py:76`; CLI `session search`/`search` |
| T-13 | Low | Med | PU | Nice | **filter (LLM re-scope a document) absent.** | no ref; CLI top-level `filter` |
| T-14 | Low | Low | NOV | Required (honesty) | **history clear is a stub** ("Planned" button -> `FutureTodoModal`); it should either work (CLI `history clear`) or be removed so the UI does not advertise a dead control. | `app.py:875,1220`; CLI `history clear` |
| T-15 | Low | Low | PU | Nice | **db rebase absent** (bulk path rewrite). Advanced/rare; `db_rebase_paths` already imported but unwired. | `core.py:51`; CLI `db rebase` |

## Phase breakdown (source spec for the per-phase IPDs)

Each phase below is expanded into its own executable IPD (see the Phase index). This
section is the shared source spec; the per-phase IPD is the authority for execution. Order
is safety-first, then high-value, then breadth.

### Phase 1 - Close the safety gap (T-01, T-14). Rem.Risk: Medium.
1. Wire extract-on-delete into both TUI delete paths so the UI is not more destructive
   than the CLI. Reuse `extract_sessions_before_delete` (DB-direct; do NOT launch
   OpenCode) against the session ids being deleted, before the delete runs. Add a
   checkbox/toggle in the delete confirmation modals (`DeletionSafetyModal` `app.py:136`,
   `ProjectDeletionSafetyModal` `app.py:257`): "Write recovery extracts first" default
   ON, output to the configured out-dir. Run the extraction in the existing worker-thread
   pattern.
2. history clear (T-14): either implement the button against `history clear` (clear the
   ledger's detail runs, preserving cumulative totals, with a typed-yes confirm) OR remove
   the stub button and its `FutureTodoModal` path. Recommend implementing it (small, and
   it removes a dishonest "Planned" control). Decide in review (OQ-1).
- Validation: deleting via the TUI writes the three recovery files to the out-dir unless
  the toggle is off; deletes still succeed; suite green.

### Phase 2 - Storage checkup & reclaim (T-02, T-03). Rem.Risk: Medium / Med-High.
3. Add a "Storage" (or "Doctor") view (new tab, or a card in Database Admin) that runs
   `run_doctor_checks` in a worker thread and renders the findings table read-only
   (status tag, size/count, the suggested fix). This is safe (read-only) and high value.
4. Add reclaim as guarded actions from that view: a bare "Checkpoint + VACUUM" button, and
   opt-in toggles/buttons for `--reclaim-temp` / `--reclaim-parts` / a backups-dir prune,
   each with a preview + confirm modal, mirroring the CLI's guards (refuse-while-open
   unless override, backup-first). Per OQ-2, do NOT expose the snapshot-force path in the
   TUI; instead show a short note directing the user to the CLI
   (`ocman reclaim --force-snapshots ...` and/or `ocman doctor`) for that highest-risk mode.
- Validation: doctor view matches `ocman doctor` output for the same DB; reclaim actions
  match the CLI's effects and refuse under the same conditions; suite green.

### Phase 3 - Reporting: spend + running (T-04, T-05). Rem.Risk: Medium.
5. Add a spend view (per-project table; a `--historical` toggle) rendering `cli_spend`'s
   data. Read-only.
6. Add a running view (list running instances; flag insecure control servers in red),
   rendering `cli_list_running`'s data, with a manual refresh. Read-only, observe-only.
- Validation: both views match the CLI reports; suite green.

### Phase 4 - Bulk + large-session handling (T-06, T-07, T-08). Rem.Risk: Medium/Low.
7. Multi-select in the sidebar (or a checkbox list) enabling batch delete/export that
   routes through the CLI's consolidated batch path (`db_delete_sessions_batch`,
   honoring extract-on-delete from Phase 1).
8. db clean: accept a duration (`--older-than` forms) and optional project scope in the
   Database Admin prune UI, and offer the extract option; keep the integer-days input as a
   shortcut.
9. Offer `--chunk` (split into parts) alongside truncation in the recovery controls.
- Validation: batch delete/export match CLI results; duration parsing matches
  `_add_clean_opts`; chunk produces `.part-NNofMM` files; suite green.

### Phase 5 - Breadth: project bundles, move, backup clean, search (T-09..T-12). Rem.Risk: Low/Med.
10. Project export/import (`bundle_project_data`/`extract_and_import_project`): enable the
    export button for project selections; extend the import modal to auto-detect kind.
11. Session move + git-aware/remote project move + `db rebase`: expose the metadata-only
    local move first (reusing the now-unused imports); the remote runbook / git-aware
    flow may stay CLI-only for now (OQ-3).
12. backup clean (prune old archives) as a button in Database Admin / backup card.
13. Content search: a search box that runs `db_search_sessions` and lists hits, selecting
    into the sidebar.
- Validation: each maps to and matches its CLI counterpart; suite green.

### Scope after the full-parity decision (OQ-5 = all phases gate release)
- T-13 `filter`, and the advanced/remote parts of T-10 (move) and T-15 (db rebase) are
  IN SCOPE for the release under full parity, pending the OQ-3/OQ-4 confirmations at
  Phase 5 about how much of the remote/git-aware move counts as "parity".

## Deferred / out of scope (with named axis)

- T-03 snapshot-force reclaim path: EXCLUDED from the TUI by explicit maintainer decision
  (OQ-2). Remediation Risk Med-High on the Safety axis (it can break OpenCode undo/revert).
  The TUI exposes the safe reclaim modes and shows a note directing the user to the CLI
  (`ocman reclaim --force-snapshots` / `ocman doctor`) for the snapshot-force mode. This is
  the one hard exclusion; everything else is in-scope for full parity.

## Required tests / validation

- Per phase: run `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and paste the
  real output. Add TUI-level tests where feasible (Textual `run_test()` harness) for the
  new modals/actions, and unit tests for any new non-UI helper.
- Behavior parity check: for each wired feature, confirm the TUI produces the same result
  as the equivalent CLI command on the same DB (spot-check doctor/spend/reclaim/delete).
- No em/en dashes introduced in authored text.

## Spec / documentation sync

When executed, update README's TUI section (currently `README.md` "The TUI Dashboard")
and ARCHITECTURE's TUI description to list the new tabs/capabilities, and add CHANGELOG
entries per phase. The docs currently describe only the 6 existing tabs.

## Open questions

RESOLVED by the maintainer 2026-07-18:

- OQ-1 (T-14): RESOLVED - implement `history clear` in the TUI (wire the button to the
  real `history clear`: clear the ledger's detail runs, preserve cumulative totals, typed-
  yes confirm). No dishonest stub remains.
- OQ-2 (T-03): RESOLVED - keep the reclaim snapshot-force path CLI-only. The TUI reclaim
  view MUST NOT offer snapshot-force; instead it MUST show a short note telling the user to
  use the command line (`ocman reclaim --force-snapshots ...`) and/or run `ocman doctor` on
  the CLI for that highest-risk mode. The safe reclaim modes (checkpoint+VACUUM,
  --reclaim-temp, --reclaim-parts, backups-dir prune) are still exposed in the TUI.
- OQ-5 (scope/release): RESOLVED - ALL FIVE PHASES gate the release (full CLI<->TUI
  parity). Nothing ships until the TUI matches the CLI across the proposed features.

Still open (non-blocking for starting; decide before the relevant phase):

- OQ-3 (T-10, Phase 5): does the TUI need remote / git-aware move, or is local metadata
  move enough (remote stays a CLI runbook)? Note: OQ-5 says full parity, so if remote move
  is considered in-parity it must be included; confirm at Phase 5 whether "parity" includes
  the remote runbook or only the local move.
- OQ-4 (T-13, Phase 5): is `filter` wanted in the TUI? Under full-parity (OQ-5) this
  likely moves from "deferred" to "included"; confirm at Phase 5.
- OQ-6 (structure): RESOLVED - use new top-level tabs per area (Storage/Doctor, Spend,
  Running), not cards folded into Database Admin (maintainer decision 2026-07-18).

## Impact of full-parity decision (OQ-5) on the "Not proposed" list

Because the maintainer chose FULL parity, the two items previously deferred as
gold-plating (T-13 `filter`, and the advanced/remote parts of T-10 move and T-15 rebase)
are RECLASSIFIED as in-scope for the release, pending the OQ-3/OQ-4 confirmations at
Phase 5. The only hard exclusion that stands is the reclaim snapshot-force mode (OQ-2),
which stays CLI-only by explicit decision, with an in-TUI pointer to the CLI.

## Execution model (per-phase, not one plan)

This umbrella is NOT executed directly. For each phase:

1. Its per-phase IPD is written (Status: to-review) using the source spec above.
2. `plan-review` hardens it (Status: reviewed).
3. The maintainer approves it (Status: approved).
4. It is executed: FIRST create a TodoWrite checklist that tracks the phase at step
   granularity (one item per numbered Step, plus core.py re-exports, the full-suite run with
   pasted output, the CHANGELOG entry, the path-scoped commit, and the Status-executed +
   `git mv` lifecycle move), keeping exactly one item in_progress at a time; THEN implement,
   run the suite (paste real output), update docs/CHANGELOG, commit path-scoped (never push
   without direction). Every per-phase IPD's gate MUST carry this "create a TodoWrite
   checklist first" instruction.
5. On completion, its Status becomes `executed` and the per-phase IPD is moved to
   `.agents/plans/executed/`.

This umbrella stays in `pending/` as the live index until all phases are executed, then it
too moves to `executed/`. Phase 1's IPD is already in `executed/` (commit 45eb8c4).
