# Implementation Plan Document (IPD) - Unified Textual TUI (`ocman ui`)

This document outlines the detailed design, architecture, screen layout, testing plan, and migration steps for creating a brand new, unified Textual TUI interface for `ocman` (run via `ocman ui` or `ocman gui`) and retiring the legacy `orsession` application.

---

## 1. Goal & Requirements

### Primary Objectives:
- **100% Feature Parity**: Integrate all CLI functionality into the TUI, including database pruning (`--clean`), orphan sweeps (`--clean-orphans`), recursive session deletion (`--delete`), system info statistics (`info`), and model pricing libraries (`--show-models`).
- **Better Usability**: Replace the fragmented multi-screen workflow of `orsession` with a modern, unified Master-Detail split-pane interface using `TabbedContent`.
- **Clean Architecture**: Eliminate the separate `orsession` binary and compile all TUI logic under a clean package module `ocman_tui` loaded natively via `ocman ui` / `ocman gui`.

---

## 2. Architecture & Module Structure

The TUI code will live in a new module directory `ocman_tui/`. The old `orsession` directory will be deleted once the implementation is complete and verified.

### Directory Structure:
```text
ocman_tui/
├── __init__.py      # Module exports
├── app.py           # Main Textual App class (OrsessionApp successor)
├── core.py          # Unified core business logic (moved from orsession.core)
├── css/
│   └── style.css    # Externalized clean, premium stylesheet matching HSL palettes
└── widgets/         # Modular widget classes
    ├── sidebar.py   # Collapsible Projects & Sessions tree widget
    ├── database.py  # DB Admin / Pruning / Info dashboard widget
    └── models.py    # Model library & pricing grid widget
```

---

## 3. UI/UX & Layout Design

### Main Interface Layout (Split Pane)
```text
+-----------------------------------------------------------------------------+
|  [Header] Ocman Manager TUI  -  Active Project: /path/to/project            |
+----------------------------------+------------------------------------------+
|  [Sidebar Widget - Collapsible]  |  [Tabbed Content Pane - 4 Tabs]          |
|                                  |  > details  > actions  > admin  > models |
|  Projects list                   +------------------------------------------+
|    - Project #1 (3 sessions)     | [Details Tab]                            |
|    - Project #2 (1 session)      | Title: Compact transcript logs           |
|                                  | ID: ses_abc123   Cost: $0.12   Model:... |
|  Sessions tree                  | ---------------------------------------- |
|    - Session #1                  | [x] Include Tools  [ ] System  [ Max Lines: 50 ]
|      ⤷ Subagent #1.1             |                                          |
|    - Session #2                  | <Transcript scrollable log area...>      |
|                                  | User: How do I implement X?              |
|                                  | Agent: [Tool Call] git status...         |
|                                  |                                          |
+----------------------------------+------------------------------------------+
|  [Status Bar] Status: Idle  -  DB Size: 2.31 GB                             |
+-----------------------------------------------------------------------------+
```

### Tabs Breakdown:

#### Tab 1: Details & Transcript
- **Header**: Session metadata grid (ID, title, cost, tokens, time created/updated, parent/child relation).
- **Controls Panel (Sidebar inside tab)**: Checkboxes to toggle `Include Tools`, `All Roles`, and integer inputs/sliders for `Max Lines` and `Max Interactions`. Toggling these dynamically rebuilds and renders the transcript without leaving the page.
- **Transcript Viewer**: A rich, scrollable Markdown or Textarea logs area.

#### Tab 2: Actions & Recovery (Compaction & Deletes)
- **Recovery Panel**: Buttons to generate `.transcript.md`, `.restart.md`, and `.compact-prompt.md` in one click.
- **Compaction Panel**: Dropdown to select compaction model, preview of token/cost estimates, and a "Run Compaction" button showing progress bars.
- **Deletion Panel**: A recursive deletion triggers a modal overlay summarizing active/child database rows and files to be deleted. Requires typing `"yes"` or clicking confirm before proceeding safely.

#### Tab 3: Database Admin
- **Left Panel (Live Info)**: Runs `db_show_info` logic to show active + historical statistics (costs, tokens, files, DB disk sizes).
- **Right Panel (Cleanup Panel)**:
  - **Pruning**: Slider/Input for retention days, toggles for dry-run and force-bypass, and "Run Prune" button.
  - **Orphan Sweep**: Toggles for dry-run and force, and "Sweep Orphans" button.
  - Output log area showing deleted counts in real time.

#### Tab 4: Models Library
- A beautiful, sortable `DataTable` listing all known LLM models, providers, costs, and compatibility tables. Includes a search text input at the top to filter models in real-time.

---

## 4. Implementation Steps

### Phase 1: Core Setup & Module migration
1.  Create `ocman_tui/` directory structure.
2.  Copy and clean core functions from `orsession/core.py` to `ocman_tui/core.py`.
3.  Add `ocman_tui/css/style.css` stylesheet for widgets layout, colors, and border themes.

### Phase 2: CLI Integration
1.  Modify `parse_args()` in `ocman.py` to accept `ui` and `gui` as valid positional command choices.
2.  In `main()` of `ocman.py`, intercept `args.command in ("ui", "gui")` and run:
    ```python
    from ocman_tui.app import OrsessionApp
    # run application
    ```

### Phase 3: Screen & Widget Development
1.  Implement `OrsessionApp` class using `TabbedContent` framework.
2.  Develop `SidebarWidget` using Textual's `Tree` widget to display projects and sessions.
3.  Develop the `Details & Transcript` tab with dynamic query controls.
4.  Develop `DatabaseAdmin` panel linking directly to `db_run_cleanup()` and `db_show_info()` functions.
5.  Develop `ModelsTable` linking to `extract_models_from_config()`.

### Phase 4: Deprecation and Cleanup
1.  Modify `pyproject.toml` to:
    - Remove the `orsession = "orsession.app:main"` script entry point.
    - Update package targets to package `ocman_tui` instead of `orsession`.
2.  Delete the `orsession/` directory.

---

## 5. Testing Plan

### Automated Unit Tests
- Create `tests/test_tui.py`:
  - Mock SQLite data to verify `Sidebar` tree renders projects and sessions counts correctly.
  - Test TUI message handlers (e.g. toggling transcript settings triggers redraw).
  - Test database administration widget calling `db_run_cleanup` and `db_show_info` with mock parameters.

### Manual Verification
1.  Launch `ocman ui` from terminal window.
2.  Select a project/session and test that the details and transcript dynamically load and update when filters are toggled.
3.  Go to the `Database Admin` tab, trigger a dry-run database clean, and verify output matches database prunes.
4.  Verify that deleting a session correctly shows safety confirmation modal and logs deletion data to both database and `ocman_history.json`.
