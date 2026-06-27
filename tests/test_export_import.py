import os
import shutil
import sqlite3
import zipfile
import json
import pytest
from pathlib import Path
import ocman
from ocman import (
    db_get_session_subtree,
    bundle_session_data,
    extract_and_import_session,
    RecoveryError,
)

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "opencode.db"
    orig_path = ocman.OPENCODE_DB_PATH
    orig_history_path = ocman.OPENCODE_HISTORY_PATH
    orig_storage_dir = ocman.OPENCODE_STORAGE_DIR
    
    ocman.OPENCODE_DB_PATH = db_path
    ocman.OPENCODE_HISTORY_PATH = tmp_path / "test_ocman_history.json"
    ocman.OPENCODE_STORAGE_DIR = tmp_path / "storage"
    ocman.OPENCODE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE project (
            id TEXT PRIMARY KEY,
            worktree TEXT,
            name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE session (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            title TEXT,
            time_created INTEGER,
            time_updated INTEGER,
            directory TEXT,
            cost REAL,
            tokens_input INTEGER,
            tokens_output INTEGER,
            tokens_cache_read INTEGER,
            summary_additions INTEGER,
            summary_deletions INTEGER,
            summary_files INTEGER,
            slug TEXT,
            model TEXT,
            agent TEXT,
            parent_id TEXT
        )
    """)
    for table, col in ocman.SESSION_RELATIONAL_TABLES:
        if table == "session":
            continue
        cursor.execute(f"CREATE TABLE {table} (id TEXT, {col} TEXT)")
        
    conn.commit()
    conn.close()
    
    yield db_path
    
    ocman.OPENCODE_DB_PATH = orig_path
    ocman.OPENCODE_HISTORY_PATH = orig_history_path
    ocman.OPENCODE_STORAGE_DIR = orig_storage_dir


def test_db_get_session_subtree(temp_db):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    # Root session
    cursor.execute("INSERT INTO session (id, title, parent_id) VALUES ('s1', 'root', NULL)")
    # Child 1
    cursor.execute("INSERT INTO session (id, title, parent_id) VALUES ('s2', 'child1', 's1')")
    # Child 2
    cursor.execute("INSERT INTO session (id, title, parent_id) VALUES ('s3', 'child2', 's2')")
    # Unrelated
    cursor.execute("INSERT INTO session (id, title, parent_id) VALUES ('s4', 'unrelated', NULL)")
    conn.commit()
    conn.close()

    subtree = db_get_session_subtree("s1")
    assert set(subtree) == {"s1", "s2", "s3"}


def test_bundle_session_data(temp_db, tmp_path):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/old/path', 'My Project')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('s1', 'proj-1', 'Root', '/old/path/s1')")
    cursor.execute("INSERT INTO message (id, session_id) VALUES ('m1', 's1')")
    conn.commit()
    conn.close()

    # Create dummy storage JSON file
    diff_file = ocman.OPENCODE_STORAGE_DIR / "s1.json"
    diff_file.write_text(json.dumps({"session_id": "s1", "data": "dummy"}), encoding="utf-8")

    bundle_file = tmp_path / "bundle.ocbox"
    bundle_session_data("s1", bundle_file)

    assert bundle_file.exists()

    # Read zip
    with zipfile.ZipFile(bundle_file, "r") as zipf:
        meta = json.loads(zipf.read("meta.json").decode("utf-8"))
        session_rows = [json.loads(line.decode("utf-8")) for line in zipf.read("db_data/session.jsonl").splitlines() if line]
        message_rows = [json.loads(line.decode("utf-8")) for line in zipf.read("db_data/message.jsonl").splitlines() if line]
        diff_content = json.loads(zipf.read("session_diffs/s1.json").decode("utf-8"))

    assert meta["main_session_id"] == "s1"
    assert meta["source_project"]["id"] == "proj-1"
    assert len(session_rows) == 1
    assert session_rows[0]["id"] == "s1"
    assert len(message_rows) == 1
    assert message_rows[0]["id"] == "m1"
    assert diff_content["session_id"] == "s1"


def test_import_session_standard(temp_db, tmp_path):
    # 1. Create a bundle
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/old/path', 'My Project')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('s1', 'proj-1', 'Root', '/old/path/s1')")
    cursor.execute("INSERT INTO message (id, session_id) VALUES ('m1', 's1')")
    conn.commit()
    conn.close()

    bundle_file = tmp_path / "bundle.ocbox"
    bundle_session_data("s1", bundle_file)

    # 2. Clear original sessions from database and disk storage
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM message")
    conn.commit()
    conn.close()

    # 3. Import
    imported_id = extract_and_import_session(bundle_file, target_project_id="proj-1")
    assert imported_id == "s1"

    # 4. Verify DB
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_id, title, directory FROM session")
    s_row = cursor.fetchone()
    assert s_row == ("s1", "proj-1", "Root", "/old/path/s1")

    cursor.execute("SELECT id, session_id FROM message")
    m_row = cursor.fetchone()
    assert m_row == ("m1", "s1")
    conn.close()


def test_import_session_with_collision(temp_db, tmp_path):
    # 1. Create a bundle
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/old/path', 'My Project')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('s1', 'proj-1', 'Root', '/old/path/s1')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory, parent_id) VALUES ('s2', 'proj-1', 'Child', '/old/path/s1/s2', 's1')")
    cursor.execute("INSERT INTO message (id, session_id) VALUES ('m1', 's1')")
    conn.commit()
    conn.close()

    diff_file = ocman.OPENCODE_STORAGE_DIR / "s1.json"
    diff_file.write_text(json.dumps({"session_id": "s1", "parent": None}), encoding="utf-8")

    diff_file2 = ocman.OPENCODE_STORAGE_DIR / "s2.json"
    diff_file2.write_text(json.dumps({"session_id": "s2", "parent": "s1"}), encoding="utf-8")

    bundle_file = tmp_path / "bundle.ocbox"
    bundle_session_data("s1", bundle_file)

    # Do not delete DB entries: calling import now triggers a collision!
    imported_id = extract_and_import_session(bundle_file, target_project_id="proj-1")
    
    assert imported_id != "s1"
    assert imported_id.startswith("ses_")

    # Verify that BOTH the original and imported session exist
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id, parent_id FROM session ORDER BY id")
    rows = cursor.fetchall()
    
    # We should have 4 sessions (s1, s2, new_s1, new_s2)
    assert len(rows) == 4
    
    # Verify the tree relationships of the imported session are correct
    imported_root = imported_id
    cursor.execute("SELECT id, parent_id FROM session WHERE parent_id = ?", (imported_root,))
    imported_child = cursor.fetchone()
    assert imported_child is not None
    assert imported_child[0] != "s2"
    
    # Verify that the new diff JSON was written to storage
    assert (ocman.OPENCODE_STORAGE_DIR / f"{imported_root}.json").exists()
    assert (ocman.OPENCODE_STORAGE_DIR / f"{imported_child[0]}.json").exists()
    
    conn.close()


def test_import_session_remap_project(temp_db, tmp_path):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    old_path = str(Path("/old/path").resolve())
    new_path = str(Path("/new/local/path").resolve())
    old_s1 = str(Path("/old/path/s1").resolve())
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', ?, 'My Project')", (old_path,))
    # Add a target project to remap to
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-2', ?, 'Target Project')", (new_path,))
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('s1', 'proj-1', 'Root', ?)", (old_s1,))
    conn.commit()
    conn.close()

    bundle_file = tmp_path / "bundle.ocbox"
    bundle_session_data("s1", bundle_file)

    # Delete session
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    conn.commit()
    conn.close()

    # Import and map to proj-2
    imported_id = extract_and_import_session(bundle_file, target_project_id="proj-2")
    assert imported_id == "s1"

    # Verify project ID was remapped and directory path rebased
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT project_id, directory FROM session WHERE id = 's1'")
    row = cursor.fetchone()
    assert row[0] == "proj-2"
    assert row[1] == str(Path("/new/local/path/s1").resolve())
    conn.close()


def test_import_session_sql_injection_rejection(temp_db, tmp_path):
    import zipfile
    import json

    bundle_file = tmp_path / "malicious_sql.ocbox"
    meta = {
        "export_version": "1.0",
        "exported_at": "2026-06-25T12:00:00",
        "main_session_id": "s1",
        "all_session_ids": ["s1"],
        "source_project": {"id": "p1", "name": "Test", "worktree": "/path"}
    }
    # Inject malicious table name
    db_data = {
        "session; DROP TABLE project; --": [{"id": "s1", "project_id": "p1"}]
    }

    with zipfile.ZipFile(bundle_file, "w") as zipf:
        zipf.writestr("meta.json", json.dumps(meta))
        zipf.writestr("db_data.json", json.dumps(db_data))

    with pytest.raises(RecoveryError, match="Invalid or unauthorized database table name"):
        extract_and_import_session(bundle_file, target_project_id="p1")


def test_import_session_path_traversal_rejection(temp_db, tmp_path):
    import zipfile
    import json

    bundle_file = tmp_path / "malicious_traversal.ocbox"
    meta = {
        "export_version": "1.0",
        "exported_at": "2026-06-25T12:00:00",
        "main_session_id": "../evil",
        "all_session_ids": ["../evil"],
        "source_project": {"id": "p1", "name": "Test", "worktree": "/path"}
    }
    db_data = {
        "session": [{"id": "../evil", "project_id": "p1"}]
    }

    with zipfile.ZipFile(bundle_file, "w") as zipf:
        zipf.writestr("meta.json", json.dumps(meta))
        zipf.writestr("db_data.json", json.dumps(db_data))

    with pytest.raises(RecoveryError, match="Invalid session ID format"):
        extract_and_import_session(bundle_file, target_project_id="p1")

