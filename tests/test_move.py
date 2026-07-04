import os
import shutil
import sqlite3
import pytest
from pathlib import Path
import ocman
from ocman import (
    db_create_rollback_backup,
    db_restore_rollback_backup,
    move_directory_structure,
    db_find_project,
    db_find_session,
    db_move_project_metadata,
    db_move_session_metadata,
    db_rebase_paths,
    RecoveryError,
)

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "opencode.db"
    orig_path = ocman.OPENCODE_DB_PATH
    orig_history_path = ocman.OPENCODE_HISTORY_PATH
    
    ocman.OPENCODE_DB_PATH = db_path
    ocman.OPENCODE_HISTORY_PATH = tmp_path / "test_ocman_history.json"
    
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
    conn.commit()
    conn.close()
    
    yield db_path
    
    ocman.OPENCODE_DB_PATH = orig_path
    ocman.OPENCODE_HISTORY_PATH = orig_history_path


def test_db_find_project_and_session(temp_db):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/path/to/project1', 'Project 1')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'Session 1', '/path/to/project1/session1')")
    conn.commit()
    conn.close()

    proj = db_find_project("proj-1")
    assert proj is not None
    assert proj[0] == "proj-1"
    assert proj[1] == "/path/to/project1"

    # Find project by path
    proj_by_path = db_find_project("/path/to/project1")
    assert proj_by_path is not None
    assert proj_by_path[0] == "proj-1"

    sess = db_find_session("sess-1")
    assert sess is not None
    assert sess[0] == "sess-1"
    assert sess[1] == "/path/to/project1/session1"
    assert sess[2] == "proj-1"


def test_db_move_project_metadata(temp_db):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/path/to/project1', 'Project 1')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'Session 1', '/path/to/project1/session1')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-2', 'proj-1', 'Session 2', '/path/to/project1')")
    # A session outside the project path that should not be touched
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-3', 'proj-1', 'Session 3', '/other/path')")
    conn.commit()
    conn.close()

    db_move_project_metadata("proj-1", "/path/to/project1", "/new/path/project1")

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    
    cursor.execute("SELECT worktree FROM project WHERE id = 'proj-1'")
    assert cursor.fetchone()[0] == str(Path("/new/path/project1").resolve())

    cursor.execute("SELECT id, directory FROM session ORDER BY id")
    rows = cursor.fetchall()
    assert rows[0] == ("sess-1", str(Path("/new/path/project1/session1").resolve()))
    assert rows[1] == ("sess-2", str(Path("/new/path/project1").resolve()))
    assert rows[2] == ("sess-3", "/other/path")
    conn.close()


def test_db_move_session_metadata(temp_db):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'Session 1', '/path/to/sess1')")
    # Nested session
    cursor.execute("INSERT INTO session (id, project_id, title, directory, parent_id) VALUES ('sess-2', 'proj-1', 'Session 2', '/path/to/sess1/nested', 'sess-1')")
    conn.commit()
    conn.close()

    db_move_session_metadata("sess-1", "/path/to/sess1", "/new/path/sess1")

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id, directory FROM session ORDER BY id")
    rows = cursor.fetchall()
    assert rows[0] == ("sess-1", str(Path("/new/path/sess1").resolve()))
    assert rows[1] == ("sess-2", str(Path("/new/path/sess1/nested").resolve()))
    conn.close()


def test_db_rebase_paths(temp_db):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/old/prefix/project1', 'Project 1')")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-2', '/other/prefix/project2', 'Project 2')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'Session 1', '/old/prefix/project1/session1')")
    conn.commit()
    conn.close()

    stats = db_rebase_paths("/old/prefix", "/new/prefix")
    assert stats["projects_updated"] == 1
    assert stats["sessions_updated"] == 1

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id, worktree FROM project ORDER BY id")
    proj_rows = cursor.fetchall()
    assert proj_rows[0] == ("proj-1", str(Path("/new/prefix/project1").resolve()))
    assert proj_rows[1] == ("proj-2", "/other/prefix/project2")

    cursor.execute("SELECT id, directory FROM session ORDER BY id")
    sess_rows = cursor.fetchall()
    assert sess_rows[0] == ("sess-1", str(Path("/new/prefix/project1/session1").resolve()))
    conn.close()


def test_db_move_project_metadata_non_canonical_path(temp_db):
    """Characterization (PERF-3): a stored directory with non-canonical components
    (`..`) still matches/rebases because comparison resolves the path. Guards the
    shared-helper refactor against silently switching to raw-string matching."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/path/to/project1', 'Project 1')")
    # Non-canonical stored dir that resolves to /path/to/project1/session1
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'S1', '/path/to/project1/sub/../session1')")
    conn.commit()
    conn.close()

    db_move_project_metadata("proj-1", "/path/to/project1", "/new/path/project1")

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT directory FROM session WHERE id = 'sess-1'")
    # Resolves to .../session1 and is rebased under the new prefix.
    assert cursor.fetchone()[0] == str(Path("/new/path/project1/session1").resolve())
    conn.close()


def test_move_directory_structure(tmp_path):
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    (old_dir / "file.txt").write_text("hello")
    new_dir = tmp_path / "new"

    move_directory_structure(old_dir, new_dir)
    assert not old_dir.exists()
    assert new_dir.exists()
    assert (new_dir / "file.txt").read_text() == "hello"

    # Collision test
    old_dir.mkdir()
    with pytest.raises(RecoveryError):
        move_directory_structure(old_dir, new_dir)


def test_db_rollback_backup(temp_db):
    # Setup some test data
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', 'w1', 'n1')")
    conn.commit()
    conn.close()

    # Create backup
    backup_file = db_create_rollback_backup()
    assert backup_file.exists()

    # Modify DB
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("UPDATE project SET name = 'n2' WHERE id = 'p1'")
    conn.commit()
    conn.close()

    # Restore backup
    db_restore_rollback_backup(backup_file)

    # Verify original name is restored
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM project WHERE id = 'p1'")
    assert cursor.fetchone()[0] == 'n1'
    conn.close()

    # Clean up backup
    if backup_file.exists():
        backup_file.unlink()


def test_cli_move_project_metadata_only(temp_db, monkeypatch):
    # Setup some test data
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/nonexistent/old', 'n1')")
    conn.commit()
    conn.close()

    # Call main with --move-project and --metadata-only
    monkeypatch.setattr("sys.argv", ["ocman", "--move-project", "p1", "--to", "/nonexistent/new", "--metadata-only"])
    
    # Run main, should not raise SystemExit with failure code
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0 or e.code is None

    # Verify metadata was updated
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT worktree FROM project WHERE id = 'p1'")
    assert cursor.fetchone()[0] == str(Path("/nonexistent/new").resolve())
    conn.close()


def test_cli_move_project_missing_directory_prompt(temp_db, monkeypatch):
    # Setup some test data
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/nonexistent/old', 'n1')")
    conn.commit()
    conn.close()

    # Call main without --metadata-only, mock isatty and input
    monkeypatch.setattr("sys.argv", ["ocman", "--move-project", "p1", "--to", "/nonexistent/new"])
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "yes")

    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0 or e.code is None

    # Verify metadata was updated because we said yes to prompt
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT worktree FROM project WHERE id = 'p1'")
    assert cursor.fetchone()[0] == str(Path("/nonexistent/new").resolve())
    conn.close()
