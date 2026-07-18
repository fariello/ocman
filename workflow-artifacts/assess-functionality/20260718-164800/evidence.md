# Evidence - assess functionality (TUI parity)

## Inspected

### TUI package (`ocman_tui/`)
- `ocman_tui/__init__.py` - exports `OrsessionApp`.
- `ocman_tui/app.py` (1746 lines) - `OrsessionApp(App)` at :762; `compose()` 6-tab layout
  :795-900; global BINDINGS :767-771; `on_button_pressed` dispatch :1196-1227; sidebar
  select :1027; delete workers :1396 (session), :1500 (project) calling
  `db_delete_session_recursive`/`db_delete_project_recursive` with force=True/confirm=False
  (:1453-1459, :1567-1573); MoveProjectModal :396 / move worker :1521; ExportSessionModal
  :567; ImportSessionModal :627; history-clear stub -> FutureTodoModal :875,:1220.
- `ocman_tui/widgets/database.py` (456 lines) - `DatabaseAdminWidget` + `OrphanInspectorModal`;
  prune via `db_run_cleanup` :250,:351 (integer retention days input :236,:358);
  backup create/restore :406/:428; import :342.
- `ocman_tui/widgets/sidebar.py` - single-select `SidebarWidget(Tree)`.
- `ocman_tui/widgets/models.py` - model pricing table; "search" filters that table only :76.
- `ocman_tui/core.py` - re-export shim; unused re-exports `db_move_session_metadata` :50,
  `db_rebase_paths` :51, `db_get_session_subtree` :52.

### CLI reference (`ocman/cli.py`)
- `build_parser()` command tree (session/project/db/backup/history/config + top-level
  verbs spend/running/doctor/reclaim/filter/move/export/models/ui/help).
- Feature functions confirmed present: db_export_session_data, extract_sessions_before_delete,
  resolve_extract_choice, run_delete_extracts; cli_doctor/run_doctor_checks; cli_reclaim;
  cli_spend; cli_list_running; bundle_session_data/bundle_project_data;
  extract_and_import_session/extract_and_import_project; db_run_cleanup; chunk_turns;
  db_move_session_metadata/db_rebase_paths; cli_backup/cli_restore; db_search_sessions.

## Commands run

- Repo structure + git state (`git log`, `git status`), version (`pyproject.toml`),
  tags (`git tag`).
- Targeted reads of the TUI files above and the CLI parser/feature functions.
- A prior explore-agent pass produced the initial gap table; every cited line was
  re-derived from the files listed here.

## Sampling / truncation notes

- `ocman/cli.py` is ~16k lines; only the parser, dispatch, and the named feature functions
  were read in full. TUI files were read in full for the layout/dispatch/delete/move
  sections.
- No DB contents were needed for the gap analysis (structural, code-level assessment).
