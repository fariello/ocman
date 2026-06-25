# Implementation Plan - Portable Session Export & Import in ocman

This document details the functional specification, technical architecture, and step-by-step implementation design for exporting an opencode session (with its complete subagent descendant tree and all associated database and disk assets) from one environment and importing it into another.

---

## 1. Functional Specification

The goal of this feature is to allow users to capture a session's entire history and state, transfer it to another machine (e.g., via a single `.ocbox` file), and import it into another database without affecting existing data.

### 1.1 Export Bundle Format (`.ocbox`)
An `.ocbox` file is a ZIP archive containing the following files:

#### A. `meta.json`
Contains metadata about the export format, system of origin, and structural outline of the exported session subtree.
```json
{
  "export_version": "1.0",
  "exported_at": "2026-06-25T16:35:00Z",
  "source_system": {
    "os": "linux",
    "python_version": "3.14.4",
    "ocman_version": "1.0.0"
  },
  "main_session_id": "ses_13d4a9047ffeGnMzvZx3bzBWeA",
  "all_session_ids": [
    "ses_13d4a9047ffeGnMzvZx3bzBWeA",
    "ses_subagent_child_1",
    "ses_subagent_child_2"
  ],
  "source_project": {
    "id": "proj_abc123",
    "name": "ocman",
    "worktree": "/home/gfariello/VC/ocman"
  }
}
```

#### B. `db_data.json`
Contains all SQL table rows related to the sessions in `all_session_ids`. To prevent column ordering or schema version differences from breaking the import, data is serialized as a mapping of table names to lists of dictionaries (column-name to value).
```json
{
  "session": [
    {
      "id": "ses_13d4a9047ffeGnMzvZx3bzBWeA",
      "project_id": "proj_abc123",
      "title": "Initial workspace analysis",
      "time_created": 1782390123000,
      "time_updated": 1782390456000,
      "directory": "/home/gfariello/VC/ocman/opencode-recovery",
      "cost": 0.0452,
      "tokens_input": 12050,
      "tokens_output": 4050,
      "tokens_cache_read": 6020,
      "summary_additions": 12,
      "summary_deletions": 2,
      "summary_files": 3,
      "slug": "workspace-analysis",
      "model": "gemini-1.5-pro",
      "agent": "Antigravity",
      "parent_id": null
    }
  ],
  "message": [
    {
      "id": "msg_01",
      "session_id": "ses_13d4a9047ffeGnMzvZx3bzBWeA",
      "role": "user",
      "content": "Analyze the codebase."
    }
  ]
}
```

#### C. `session_diffs/`
A folder containing the raw session state JSON files zipped directly from `~/.local/share/opencode/storage/session_diff/`.
- `session_diffs/ses_13d4a9047ffeGnMzvZx3bzBWeA.json`
- `session_diffs/ses_subagent_child_1.json`
- `session_diffs/ses_subagent_child_2.json`

---

### 1.2 Collision Resolution Strategy
To enforce isolation and prevent overwriting or polluting target database records:
1. **Detection**: Upon reading the bundle, query the target database `session` table for any matching session ID in `all_session_ids`.
2. **Conflict Mode**: If any session ID already exists on the target system:
   - Generate a brand-new UUID4 string for *every* session in the bundle to keep the imported subtree's structure self-consistent and separate.
   - Maintain a translation map: `id_map: dict[str, str]` (e.g. `{"ses_old_1": "ses_new_1"}`).
   - Update foreign keys and primary keys in `db_data.json` before SQL insertion:
     - `session.id` -> `id_map[session.id]`
     - `session.parent_id` -> `id_map[session.parent_id]`
     - Relational tables' `session_id` or `aggregate_id` -> `id_map[original_id]`
3. **Session Diff File Renaming & Rewriting**:
   - Write the imported JSON files to the target storage directory using the new UUID name (e.g., `<new_uuid>.json`).
   - Parse each session diff JSON structure and replace any internal string references to old session IDs with the new UUIDs to ensure internal consistency.

---

### 1.3 Project Remapping Strategy
Sessions must belong to a valid project row in the database.
- **Scenario A: Project exists on target (matching ID and path)**:
  - Link the imported sessions to it automatically.
- **Scenario B: Project ID exists but directory path is different**:
  - Update the session `directory` column by replacing the old project's `worktree` path prefix with the target project's `worktree` path prefix.
- **Scenario C: Project does not exist on target**:
  - The CLI/TUI will prompt the user to:
    1. **Remap**: Select an existing project on the target system to adopt these sessions.
    2. **Create**: Create a new project row in the database, supplying a local `worktree` path.

---

### 1.4 CLI Functional Specification
- **Export Command**:
  ```bash
  ocman --export-session <session_id> --to <file_path.ocbox>
  ```
  - If `<session_id>` is a session index number, resolves it.
  - If output file path does not end in `.ocbox` or `.zip`, append `.ocbox`.
- **Import Command**:
  ```bash
  ocman --import-session <bundle_path.ocbox> [--to-project <project_id>] [--new-project-path <path>]
  ```
  - If not in an interactive terminal, fails immediately if project mapping is required but flags are missing.
  - In interactive terminals, prompts with list of local projects or choice to initialize a new project workspace.

---

### 1.5 TUI Functional Specification
- **Export Integration**:
  - Next to "Delete Session" in Tab 2, a new button `Export Session` is added.
  - Clicking it displays an overlay dialog with a file selector. Clicking submit runs the export in a worker thread.
- **Import Integration**:
  - A button `Import Session Bundle` is added to Tab 3 (Database Admin).
  - Displays `ImportSessionModal` containing:
    - Zip bundle file path input.
    - Radio buttons: `[ ] Map to existing project` / `[ ] Create new project workspace`.
    - Dropdown dropdown menu listing target projects (enabled if Map selected).
    - Text inputs for New Project Name and Worktree Path (enabled if Create selected).
    - Submit and Cancel buttons.

---

## 2. Technical Architecture & Database Mapping

### 2.1 Schema Mapping
We must read and write data to the following SQLite tables using parameterized queries inside a transaction:

| Table | Column mapping to Session ID | Action on Export | Action on Import |
|---|---|---|---|
| `session` | `id` (Primary Key), `parent_id` | Extract row | Insert row (UUID remapped if conflict) |
| `message` | `session_id` | Extract rows | Insert rows (session_id remapped) |
| `session_message` | `session_id` | Extract rows | Insert rows (session_id remapped) |
| `session_input` | `session_id` | Extract rows | Insert rows (session_id remapped) |
| `session_share` | `session_id` | Extract rows | Insert rows (session_id remapped) |
| `session_context_epoch` | `session_id` | Extract rows | Insert rows (session_id remapped) |
| `todo` | `session_id` | Extract rows | Insert rows (session_id remapped) |
| `part` | `session_id` | Extract rows | Insert rows (session_id remapped) |
| `event` | `aggregate_id` | Extract rows | Insert rows (aggregate_id remapped) |
| `event_sequence` | `aggregate_id` | Extract rows | Insert rows (aggregate_id remapped) |

---

## 3. Implementation Plan & Code Prototypes

### 3.1 Backend Functions in `ocman.py`

#### Prototype A: Gathering the Subtree
```python
def db_get_session_subtree(session_id: str) -> list[str]:
    """Retrieve the given session ID and all its recursive subagent child session IDs."""
    sqlite3 = _get_sqlite()
    conn = sqlite3.connect(str(OPENCODE_DB_PATH))
    cursor = conn.cursor()
    
    # Recursive CTE to find all descendant sessions
    cursor.execute("""
        WITH RECURSIVE session_tree(id) AS (
            SELECT id FROM session WHERE id = ?
            UNION
            SELECT s.id FROM session s JOIN session_tree st ON s.parent_id = st.id
        )
        SELECT id FROM session_tree;
    """, (session_id,))
    
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids
```

#### Prototype B: Bundling Session Data
```python
def bundle_session_data(session_id: str, bundle_path: Path) -> None:
    """Export a session and its subagents into an .ocbox ZIP bundle."""
    import zipfile
    import json
    
    sqlite3 = _get_sqlite()
    session_ids = db_get_session_subtree(session_id)
    if not session_ids:
        raise RecoveryError(f"Session {session_id} not found.")

    conn = sqlite3.connect(str(OPENCODE_DB_PATH))
    # Configure cursor to return row dictionaries
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get parent project details
    cursor.execute("""
        SELECT p.id, p.name, p.worktree FROM project p
        JOIN session s ON s.project_id = p.id
        WHERE s.id = ?
    """, (session_id,))
    proj_row = cursor.fetchone()
    proj_meta = dict(proj_row) if proj_row else {}

    # Extract database rows
    db_export = {}
    placeholders = ",".join("?" for _ in session_ids)
    
    for table, col in SESSION_RELATIONAL_TABLES:
        cursor.execute(f"SELECT * FROM {table} WHERE {col} IN ({placeholders})", session_ids)
        db_export[table] = [dict(row) for row in cursor.fetchall()]

    conn.close()

    # Create Zip Bundle
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Write metadata
        meta = {
            "export_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "main_session_id": session_id,
            "all_session_ids": session_ids,
            "source_project": proj_meta
        }
        zipf.writestr("meta.json", json.dumps(meta, indent=2))
        zipf.writestr("db_data.json", json.dumps(db_export, indent=2))

        # Write storage diff files
        for sid in session_ids:
            diff_file = OPENCODE_STORAGE_DIR / f"{sid}.json"
            if diff_file.exists():
                zipf.write(diff_file, f"session_diffs/{sid}.json")
```

#### Prototype C: Extraction & Database Injection
```python
def extract_and_import_session(
    bundle_path: Path, 
    target_project_id: Optional[str] = None, 
    new_project_path: Optional[str] = None
) -> str:
    """
    Import session database rows and diff files from an .ocbox bundle.
    Handles UUID rewriting upon collision and project association.
    """
    import zipfile
    import json
    import uuid

    if not bundle_path.exists():
        raise RecoveryError(f"Bundle file not found: {bundle_path}")

    # Read zip bundle
    with zipfile.ZipFile(bundle_path, "r") as zipf:
        meta = json.loads(zipf.read("meta.json").decode("utf-8"))
        db_data = json.loads(zipf.read("db_data.json").decode("utf-8"))

    all_ids = meta["all_session_ids"]
    sqlite3 = _get_sqlite()
    conn = sqlite3.connect(str(OPENCODE_DB_PATH))
    cursor = conn.cursor()

    # 1. Collision Check
    collision = False
    placeholders = ",".join("?" for _ in all_ids)
    cursor.execute(f"SELECT id FROM session WHERE id IN ({placeholders})", all_ids)
    if cursor.fetchall():
        collision = True

    # Generate translation map if collisions occur
    id_map = {}
    for sid in all_ids:
        id_map[sid] = f"ses_{uuid.uuid4().hex}" if collision else sid

    # 2. Project Remapping Resolution
    proj_id = target_project_id
    if not proj_id:
        # Check if original project ID exists on target
        orig_proj = meta["source_project"]
        cursor.execute("SELECT id FROM project WHERE id = ?", (orig_proj.get("id"),))
        if cursor.fetchone():
            proj_id = orig_proj["id"]
        elif new_project_path:
            # Create a new project row
            proj_id = f"proj_{uuid.uuid4().hex[:8]}"
            cursor.execute(
                "INSERT INTO project (id, worktree, name) VALUES (?, ?, ?)",
                (proj_id, str(Path(new_project_path).resolve()), orig_proj.get("name", "Imported Project"))
            )
        else:
            raise RecoveryError("Project mapping required. Specify --to-project or --new-project-path.")

    # 3. Apply translations & Rewrite paths
    orig_worktree = meta["source_project"].get("worktree", "")
    target_worktree = ""
    if orig_worktree:
        cursor.execute("SELECT worktree FROM project WHERE id = ?", (proj_id,))
        p_row = cursor.fetchone()
        if p_row:
            target_worktree = p_row[0]

    # Pre-flight backup
    backup_file = db_create_rollback_backup()
    copied_diffs = []
    
    try:
        conn.execute("BEGIN TRANSACTION")
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Update and Insert Rows
        for table, rows in db_data.items():
            if not rows:
                continue
            
            for row in rows:
                # Rewrite session IDs
                for col_name, val in list(row.items()):
                    if col_name in ("id", "parent_id", "session_id", "aggregate_id") and val in id_map:
                        row[col_name] = id_map[val]
                
                # Rewrite project ID and directory paths for sessions
                if table == "session":
                    row["project_id"] = proj_id
                    if row.get("directory") and orig_worktree and target_worktree:
                        # Rebase path
                        old_dir = row["directory"]
                        if old_dir.startswith(orig_worktree):
                            row["directory"] = old_dir.replace(orig_worktree, target_worktree, 1)

                # Format dynamically into parameterized SQL
                cols = ", ".join(row.keys())
                vals_placeholders = ", ".join("?" for _ in row.values())
                sql = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({vals_placeholders})"
                cursor.execute(sql, list(row.values()))

        # 4. Copy Session Diffs to local disk
        storage_dir = OPENCODE_STORAGE_DIR
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(bundle_path, "r") as zipf:
            for old_id, new_id in id_map.items():
                zip_member = f"session_diffs/{old_id}.json"
                try:
                    diff_data = json.loads(zipf.read(zip_member).decode("utf-8"))
                    # Rewrite session ID references inside JSON structure if colliding
                    if collision:
                        # Perform recursive string substitution in JSON structure
                        diff_data_str = json.dumps(diff_data)
                        for o_id, n_id in id_map.items():
                            diff_data_str = diff_data_str.replace(o_id, n_id)
                        diff_data = json.loads(diff_data_str)

                    target_file = storage_dir / f"{new_id}.json"
                    target_file.write_text(json.dumps(diff_data, indent=2), encoding="utf-8")
                    copied_diffs.append(target_file)
                except KeyError:
                    pass # File not found in zip, skip

        conn.commit()
        if backup_file.exists():
            backup_file.unlink()
            
    except Exception as e:
        conn.rollback()
        db_restore_rollback_backup(backup_file)
        if backup_file.exists():
            backup_file.unlink()
        # Clean up any written disk files
        for f in copied_diffs:
            if f.exists():
                f.unlink()
        raise RecoveryError(f"Import failed: {e}")
    finally:
        conn.close()

    return id_map[meta["main_session_id"]]
```

---

## 4. Verification Plan

### 4.1 Automated Tests
- Implement `tests/test_export_import.py`:
  - `test_export_creates_valid_zip`: Runs `bundle_session_data` and asserts `meta.json` and `db_data.json` files are readable and schemas conform to expectations.
  - `test_import_creates_rows`: Runs `extract_and_import_session` and checks SQLite database that rows are correctly populated in child and parent tables.
  - `test_import_with_collision`: Inserts identical session ID prior to import, runs import, asserts target database contains both the original session rows AND the imported session rows under new UUID values.
  - `test_import_remap_project`: Tests mapping the bundle to a different existing project.

### 4.2 Manual Verification
- CLI: Run `ocman --export-session 1 --to ~/backup.ocbox`. Move `.ocbox` to another directory, change DB path config, and run `ocman --import-session ~/backup.ocbox --new-project-path ~/VC/new_project` to confirm new project creation and session import works properly.
- TUI: Select a project/session, trigger the modals, and verify UI components work seamlessly.
