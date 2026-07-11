# Repository Inventory

- **Run ID**: 20260617-193252
- **Project Type and Scope**: Python command-line utility and Textual TUI application for managing OpenCode sessions, database pruning, and recovery file compilation.
- **Languages**: Python (>=3.10)
- **Key Project Files**:
  - [ocman.py](file:///home/gfariello/VC/ocman/ocman.py) (CLI entry point, database interaction layer, and recovery compiling helper functions)
  - [ocman_tui/app.py](file:///home/gfariello/VC/ocman/ocman_tui/app.py) (Main Textual TUI App controller class)
  - [ocman_tui/core.py](file:///home/gfariello/VC/ocman/ocman_tui/core.py) (TUI-specific core wrapper functions importing from ocman.py)
  - [ocman_tui/css/style.css](file:///home/gfariello/VC/ocman/ocman_tui/css/style.css) (CSS stylesheet for Catppuccin Macchiato style dark mode layout)
  - [ocman_tui/widgets/sidebar.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/sidebar.py) (Project and session tree sidebar panel)
  - [ocman_tui/widgets/database.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/database.py) (DB Admin panel and Orphaned File Inspector modal dialog)
  - [ocman_tui/widgets/models.py](file:///home/gfariello/VC/ocman/ocman_tui/widgets/models.py) (Pricing models library datatable and search bar)
  - [pyproject.toml](file:///home/gfariello/VC/ocman/pyproject.toml) (Hatchling build-system configuration, dependency constraints, and package scripts definition)

- **Public Contract Summary**:
  - Positional CLI commands: `info`, `help`, `ui`, `gui`
  - Option flags: `--session`, `--project`, `--list-projects`, `--list-sessions`, `--all-sessions`, `--details`, `--head`, `--tail`, `--compact`, `--delete`, `--clean`, `--days`, `--clean-orphans`, `--db`, `--dry-run`, `--force`, `--show-models`, `--show-compaction-prompt`, `--verbose`, `--info`, `--clear-history`

- **Test and Validation Inventory**:
  - Automated tests are in [tests/](file:///home/gfariello/VC/ocman/tests) directory.
  - [tests/test_core.py](file:///home/gfariello/VC/ocman/tests/test_core.py) (verifies configuration loaders, turn consolidation, and truncation logic)
  - [tests/test_ocman.py](file:///home/gfariello/VC/ocman/tests/test_ocman.py) (verifies SQLite database listings, deletions, and history sidecar ledger recording)
  - [tests/test_tui.py](file:///home/gfariello/VC/ocman/tests/test_tui.py) (verifies Textual App widgets compose, datatable rendering, and modal screens)
  - Execution command: `PYTHONPATH=. pytest -v` (using Python 3.14.4 virtualenv)

- **Documentation Inventory**:
  - [README.md](file:///home/gfariello/VC/ocman/README.md)
  - [CHANGELOG.md](file:///home/gfariello/VC/ocman/CHANGELOG.md)
  - [SPEC-orsession.md](file:///home/gfariello/VC/ocman/SPEC-orsession.md) (legacy orsession TUI specification)
  - [agents/plans/ocman_gui_spec.md](file:///home/gfariello/VC/ocman/agents/plans/ocman_gui_spec.md) (specification for the new TUI)
  - [agents/plans/ocman_gui_ipd.md](file:///home/gfariello/VC/ocman/agents/plans/ocman_gui_ipd.md) (TUI design implementation plan)

- **Build/Packaging/CI Inventory**:
  - Hatchling backend defined in `pyproject.toml`.
  - Python dependencies: `textual>=3.0.0`, `rich>=13.0.0`, `pysqlite3-binary>=0.5.0`
  - Development dependencies: `pytest>=7.0`
  - GitHub Actions CI workflows: None found.
