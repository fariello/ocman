# Functional Specification & Wireframes - Unified `ocman` TUI

This document details the functional specification, screen workflows, and layout wireframes for the new unified Textual TUI (`ocman ui`).

---

## 1. Screen Wireframes & Layouts

### 1.1 Main Dashboard Layout (Split Pane)
This is the default screen. It splits the terminal window into a left-hand navigation sidebar and a right-hand tabbed workspace.

```text
+--------------------------------------------------------------------------------------+
| [Header] Ocman TUI Controller v0.2.0                    Active CWD: /path/to/project |
+----------------------------+---------------------------------------------------------+
| PROJECTS & SESSIONS        |  [TabDetails]  [TabActions]  [TabAdmin]  [TabModels]    |
| > My Project 1 (CWD)       +---------------------------------------------------------+
|   ses_1391320 (Root)       |                                                         |
|   ses_12e8be (Root)        |                                                         |
|     ⤷ ses_13714 (Child)    |                 < ACTIVE TAB WORKSPACE >                |
| > Project 2                |                                                         |
|   ses_1651cc (Root)        |                                                         |
|                            |                                                         |
|                            |                                                         |
|                            |                                                         |
|                            |                                                         |
|                            |                                                         |
|                            |                                                         |
|                            |                                                         |
|                            |                                                         |
+----------------------------+---------------------------------------------------------+
| [Footer] Ctrl+Q: Quit | Ctrl+S: Toggle Sidebar | Ctrl+R: Refresh DB                 |
+--------------------------------------------------------------------------------------+
```

---

### 1.2 "Details & Transcript" Tab Layout
Displays the selected session's details and active conversation turns. Users can adjust settings in the sidebar to dynamically format the transcript.

```text
+--------------------------------------------------------------------------------------+
| SESSIONS                   |  [*Details]  [Actions]  [Admin]  [Models]               |
| > My Project 1 (CWD)       +---------------------------------------------------------+
|   ses_1391320 (Root)       | METADATA:                                               |
|   ses_12e8be (Root)        |   Title: Finalize topic pipeline  | ID: ses_12e8be653ff |
|     ⤷ ses_13714 (Child)    |   Cost:  $1.2431                  | Model: cl-opus-4.8  |
|                            |   Created: 2026-06-15 10:20       | Updated: 2026-06-16 |
|                            | ----------------------------------+---------------------+
|                            | TRANSCRIPT VIEW                   | FORMAT CONTROLS     |
|                            |                                   |                     |
|                            |   [User]:                         | [x] Include Tools   |
|                            |   How should we structure the DB  | [ ] All Roles       |
|                            |   migration schema?               |                     |
|                            |                                   | Max Interactions:   |
|                            |   [Assistant - Tool Call]:        | [ 50              ] |
|                            |   call_mcp_tool(inspect_dbs)      |                     |
|                            |                                   | Max Lines:          |
|                            |   [Assistant]:                    | [ [No Limit]      ] |
|                            |   Based on the schema, we...      |                     |
|                            |                                   | [ Refresh View ]    |
+----------------------------+-----------------------------------+---------------------+
```

---

### 1.3 "Actions & Recovery" Tab Layout
Contains tools to generate recovery files, run LLM compactions, and perform recursive session deletions.

```text
+--------------------------------------------------------------------------------------+
| SESSIONS                   |  [Details]  [*Actions]  [Admin]  [Models]               |
| > My Project 1 (CWD)       +---------------------------------------------------------+
|   ses_1391320 (Root)       | RECOVERY FILE GENERATOR                                 |
|   ses_12e8be (Root)        |   [ Write Transcript (.transcript.md) ]                 |
|     ⤷ ses_13714 (Child)    |   [ Write Restart Wrapper (.restart.md)  ]                 |
|                            |   [ Write Compaction Prompt (.compact-prompt.md) ]      |
|                            | -------------------------------------------------------- |
|                            | LLM COMPACTION RUNNER                                    |
|                            |   Select Model: [ uri/its_direct/pt3-claude-opus-4.8   v ] |
|                            |   Est Cost: $0.12 (Input: 20k, Output: 4k tokens)        |
|                            |   [ Run Compaction API ]                                |
|                            | -------------------------------------------------------- |
|                            | DANGER ZONE                                              |
|                            |   [ Recursively Delete Session & Descendants ]          |
+----------------------------+---------------------------------------------------------+
```

---

### 1.4 "Database Admin" Tab Layout
Provides a dashboard to execute database prunes, orphan sweeps, and display active + historical ledger metrics.

```text
+--------------------------------------------------------------------------------------+
| SESSIONS                   |  [Details]  [Actions]  [*Admin]  [Models]               |
| > My Project 1 (CWD)       +---------------------------------------------------------+
|   ses_1391320 (Root)       | SYSTEM METRICS                    | DATABASE OPERATIONS |
|   ses_12e8be (Root)        |   Size on disk:  2.31 GB          |                     |
|     ⤷ ses_13714 (Child)    |   SQLite Version: 3.51.1          | Retention Clean:    |
|                            |   Total Projects: 9 active        |   Days: [ 5       ] |
|                            |   Total Sessions: 51 active       |   [x] Dry Run       |
|                            |   Total Messages: 11,903 active   |   [ ] Force Bypass  |
|                            |   -----------------------------   |   [ Run Prune ]     |
|                            |   Historical Cost: $5.90          |                     |
|                            |   Historical Msg:  51 deleted     | Orphan Sweep:       |
|                            |                                   |   [x] Dry Run       |
|                            |                                   |   [ Sweep Orphans ] |
|                            | ----------------------------------+---------------------|
|                            | LIVE OPERATIONS LOG OUTPUT:                             |
|                            |   [-] Deleted 206 rows from event (age-based)           |
|                            |   [-] Deleted 51 rows from message (age-based)          |
+----------------------------+---------------------------------------------------------+
```

---

### 1.5 Deletion Safety Modal Overlay (Pop-up)
A modal screen that blocks the dashboard during recursive deletes to prevent accidental data loss.

```text
+--------------------------------------------------------------------------------------+
|                                                                                      |
|                     +------------------------------------------+                     |
|                     | CONFIRM RECURSIVE SESSION DELETION       |                     |
|                     |                                          |                     |
|                     | You are about to recursively delete:     |                     |
|                     |   - ses_12e8be (Parent)                  |                     |
|                     |   - ses_13714 (Child)                    |                     |
|                     |                                          |                     |
|                     | Rows that will be deleted:               |                     |
|                     |   - event: 206  - message: 51            |                     |
|                     |                                          |                     |
|                     | This action is irreversible.             |                     |
|                     | Please type 'yes' below to confirm:      |                     |
|                     | [ yes                                  ] |                     |
|                     |                                          |                     |
|                     |        [ Cancel ]    [ CONFIRM DELETE ]  |                     |
|                     +------------------------------------------+                     |
|                                                                                      |
+--------------------------------------------------------------------------------------+
```

### 1.6 Orphaned File Inspector Modal
This modal lets users inspect and selectively delete orphaned session diff JSON files on disk.

```text
+------------------------------------------------------------+
| ORPHANED FILE INSPECTOR                                    |
+------------------------------------------------------------+
| The following diff JSON files on disk are orphaned         |
| (they have no corresponding session in the database):      |
|                                                            |
| [x] ses_orphan1.json (Size: 12.4 KB, Created: 2026-06-01)  |
| [ ] ses_orphan2.json (Size: 45.1 KB, Created: 2026-06-03)  |
| [x] ses_orphan3.json (Size: 104.2 KB, Created: 2026-06-05) |
|                                                            |
| Selected: 2 files | Total Size: 116.6 KB                   |
|                                                            |
|      [ Refresh List ]    [ Cancel ]    [ DELETE SELECTED ] |
+------------------------------------------------------------+
```

### 1.7 Post-Execution Summary Overlay
Displays a detailed breakdown of resources removed and disk space reclaimed after cleanups, prunes, or deletions have finished.

```text
+------------------------------------------------------------+
| OPERATION COMPLETE SUMMARY                                 |
+------------------------------------------------------------+
| Deletion/Prune operation completed successfully.           |
|                                                            |
| DATABASE CHANGES:                                          |
|   - Sessions Deleted:  12 (4 root, 8 subagent)             |
|   - Database Rows:     event: -1,234, part: -412           |
|                                                            |
| DISK STORAGE CHANGES:                                      |
|   - Diff Files Deleted: 10 JSON files                      |
|                                                            |
| SPACE RECLAIMED:                                           |
|   - DB File Shrunk:    42.12 MB (after VACUUM)             |
|   - JSON Files Freed:  1.24 MB                             |
|   - Total Saved:       43.36 MB                            |
|                                                            |
|                                                   [ OK ]   |
+------------------------------------------------------------+
```

---

## 2. Functional Workflows

### 2.1 Project & Session Navigation
1.  On startup, the TUI queries SQLite for all projects and sessions in `opencode.db`.
2.  The `Sidebar` tree widget is populated. Projects are parent nodes; sessions are leaf nodes. Child subagent sessions are nested under their respective parents.
3.  Clicking a session dynamically updates the selected session context across all tabs.

### 2.2 Transcript Rendering & Controls
1.  When a session is selected, the TUI loads its export JSON. If the file is not exported yet, the TUI prompts the user to export it.
2.  The transcript settings (Include Tools, All Roles, Max Lines) are loaded from the controls widget.
3.  The core formatting library consolidates and renders turns as scrollable Markdown.
4.  Checking or unchecking any format controls triggers an immediate re-rendering of the transcript log.

### 2.3 Compaction Execution
1.  The TUI queries `load_opencode_config()` to fetch the list of compatible LLMs.
2.  The user selects a model from the dropdown.
3.  The TUI estimates input/output tokens and cost and displays them.
4.  Clicking "Run Compaction API" spawns a background thread running `call_compaction_api`.
5.  A live progress bar is updated. On completion, the generated compacted markdown is shown in a preview window.

### 2.4 Database Administrative Tasks & Orphan Sweeps
1.  The `Database Admin` tab pulls data from `db_show_info` and the sidecar `ocman_history.json`.
2.  Triggering a clean runs the prune function. If `dry_run` is selected, it output logs the potential deletes without modifying the database.
3.  If a real delete occurs, the database stats refresh dynamically to show the new sizes and incremented historical deleted ledger metrics.
4.  Opening the **Orphaned File Inspector** scans `storage/session_diff` on disk and compares files with active session IDs in the DB.
5.  Users select orphan files to sweep. The selected files are unlinked, and space reclaimed is calculated.

### 2.5 Post-Execution Reporting
1.  Upon completing any deletion, age-based prune, or orphan file sweep:
    - Compare `opencode.db` size before the run with the post-`VACUUM` size to get the SQLite reclaimed space.
    - Measure sizes of deleted JSON diff files.
    - Count rows deleted per table.
2.  Populate and display the **Post-Execution Summary Overlay** to present these metrics clearly to the user.
3.  Load the cumulative totals from `ocman_history.json` and refresh the statistics values in the Database Admin layout.
