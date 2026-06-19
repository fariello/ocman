import os
import sqlite3
import pytest
from pathlib import Path
import ocman
from ocman import (
    db_list_projects,
    db_list_sessions,
    db_delete_session_recursive,
    db_run_cleanup,
    db_show_info,
    RecoveryError,
)

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_opencode.db"
    
    # Save original DB path and history path
    orig_path = ocman.OPENCODE_DB_PATH
    orig_history_path = ocman.OPENCODE_HISTORY_PATH
    
    ocman.OPENCODE_DB_PATH = db_path
    ocman.OPENCODE_HISTORY_PATH = tmp_path / "test_ocman_history.json"
    
    # Initialize SQLite database with opencode schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create tables
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
    
    # Create session related tables
    for table, col in ocman.SESSION_RELATIONAL_TABLES:
        if table == "session":
            continue
        cursor.execute(f"CREATE TABLE {table} (id TEXT, {col} TEXT)")
        
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Restore original DB path and history path
    ocman.OPENCODE_DB_PATH = orig_path
    ocman.OPENCODE_HISTORY_PATH = orig_history_path


def test_db_list_projects_empty(temp_db):
    projects = db_list_projects()
    assert len(projects) == 0


def test_db_list_projects_and_sessions(temp_db):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    
    # Insert project
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    
    # Insert sessions
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory)
        VALUES ('sess1', 'proj1', 'Session 1', 1000, 2000, '/path/to/proj')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess2', 'proj1', 'Session 2', 1100, 2100, '/path/to/proj', 'sess1')
    """)
    conn.commit()
    conn.close()
    
    projects = db_list_projects()
    assert len(projects) == 1
    assert projects[0]["id"] == "proj1"
    assert projects[0]["session_count"] == 2
    
    sessions = db_list_sessions("proj1")
    assert len(sessions) == 2
    assert sessions[0]["id"] == "sess2"  # Sorted by time_updated DESC
    assert sessions[1]["id"] == "sess1"


def test_db_delete_session_recursive_dry_run(temp_db):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated)
        VALUES ('sess1', 'proj1', 'Session 1', 1000, 2000)
    """)
    # Insert message row linked to session
    cursor.execute("INSERT INTO message (id, session_id) VALUES ('msg1', 'sess1')")
    conn.commit()
    conn.close()
    
    # Dry run should not modify DB
    db_delete_session_recursive("sess1", dry_run=True, force=True, verbosity=0)
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM session")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM message")
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_db_delete_session_recursive_path_traversal(temp_db):
    # Pass a session ID containing path traversal characters
    with pytest.raises(RecoveryError) as excinfo:
        db_delete_session_recursive("../unsafe_id", dry_run=False, force=True, verbosity=0)
    assert "Unsafe session ID detected" in str(excinfo.value)


def test_db_run_cleanup_age_based(temp_db, monkeypatch, mock_history_path):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    
    # Insert old session (created 10 days ago) and new session (created today)
    import time
    now_ms = int(time.time() * 1000)
    ten_days_ago_ms = now_ms - (10 * 86400 * 1000)
    
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated)
        VALUES ('old_sess', 'proj1', 'Old Session', ?, ?)
    """, (ten_days_ago_ms, ten_days_ago_ms))
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated)
        VALUES ('new_sess', 'proj1', 'New Session', ?, ?)
    """, (now_ms, now_ms))
    
    conn.commit()
    conn.close()
    
    # Mock input() to automatically confirm deletion
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    
    # Run cleanup with 5 days retention
    db_run_cleanup(days=5, project_id=None, project_dir=None, dry_run=False, force=True, clean_orphans=False, verbosity=0)
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM session")
    remaining_ids = [row[0] for row in cursor.fetchall()]
    assert "new_sess" in remaining_ids
    assert "old_sess" not in remaining_ids
    conn.close()


def test_db_show_info(temp_db, capsys):
    # Setup some test data in mock db
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, cost, tokens_input, tokens_output, model)
        VALUES ('sess1', 'proj1', 'Session 1', 1000, 2000, 0.05, 1000, 500, '{"id": "gpt-4", "providerID": "openai"}')
    """)
    conn.commit()
    conn.close()

    # Create dummy args class
    class Args:
        verbose = 0
    
    # Run the info function
    db_show_info(Args())
    
    captured = capsys.readouterr()
    assert "OPENCODE SYSTEM INFORMATION" in captured.out
    assert "Projects:        1" in captured.out
    assert "Sessions:        1" in captured.out
    assert "Total Cost:      $0.0500" in captured.out
    assert "Tokens Input:    1,000" in captured.out
    assert "gpt-4 (openai)" in captured.out


def test_parse_args_help(monkeypatch, capsys):
    import sys
    from ocman import parse_args
    
    # Mock sys.argv to pass help
    monkeypatch.setattr(sys, "argv", ["ocman.py", "help"])
    
    with pytest.raises(SystemExit) as excinfo:
        parse_args()
        
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    # Argparse help output can be on stdout or stderr depending on python version/argparse implementation
    output = captured.out + captured.err
    assert "usage: ocman" in output


def test_parse_args_version(monkeypatch, capsys):
    import sys
    from ocman import parse_args
    
    # Mock sys.argv to pass --version
    monkeypatch.setattr(sys, "argv", ["ocman.py", "--version"])
    
    with pytest.raises(SystemExit) as excinfo:
        parse_args()
        
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "ocman.py 1.0.0" in output or "ocman 1.0.0" in output


@pytest.fixture
def mock_history_path(tmp_path, monkeypatch):
    hist_path = tmp_path / "test_ocman_history.json"
    monkeypatch.setattr(ocman, "OPENCODE_HISTORY_PATH", hist_path)
    return hist_path


def test_gather_and_save_deletion_metrics(temp_db, mock_history_path):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, cost, tokens_input, tokens_output, model)
        VALUES ('sess1', 'proj1', 'Session 1', 1000, 2000, 0.05, 1000, 500, '{"id": "gpt-4"}')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, cost, tokens_input, tokens_output, model, parent_id)
        VALUES ('sess2', 'proj1', 'Session 2', 1100, 2100, 0.02, 400, 200, '{"id": "gpt-4"}', 'sess1')
    """)
    cursor.execute("INSERT INTO message (id, session_id) VALUES ('msg1', 'sess1')")
    cursor.execute("INSERT INTO message (id, session_id) VALUES ('msg2', 'sess2')")
    conn.commit()

    # Gather metrics
    stats = ocman.gather_deletion_metrics(['sess1', 'sess2'], conn)
    assert stats is not None
    assert stats["sessions_count"] == 2
    assert stats["subagents_count"] == 1
    assert stats["messages_count"] == 2
    assert stats["cost"] == pytest.approx(0.07)
    assert stats["tokens_input"] == 1400
    assert stats["tokens_output"] == 700

    # Save metrics
    ocman.save_deletion_metrics("delete", stats)
    assert mock_history_path.exists()

    history = ocman._load_history()
    c = history["cumulative"]
    assert c["sessions_deleted"] == 2
    assert c["subagents_deleted"] == 1
    assert c["messages_deleted"] == 2
    assert c["cost_deleted"] == pytest.approx(0.07)
    assert c["tokens_input_deleted"] == 1400
    assert c["tokens_output_deleted"] == 700

    conn.close()


def test_db_delete_session_recursive_saves_history(temp_db, mock_history_path):
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, cost, tokens_input, tokens_output)
        VALUES ('sess1', 'proj1', 'Session 1', 1000, 2000, 0.10, 1000, 500)
    """)
    conn.commit()
    conn.close()

    # Run recursive delete (mock confirm input)
    import builtins
    orig_input = builtins.input
    builtins.input = lambda _: 'yes'
    try:
        db_delete_session_recursive("sess1", dry_run=False, force=True, verbosity=0)
    finally:
        builtins.input = orig_input

    # History should be updated
    history = ocman._load_history()
    c = history["cumulative"]
    assert c["sessions_deleted"] == 1
    assert c["cost_deleted"] == pytest.approx(0.10)


def test_preprocess_argv():
    """Test CLI subcommand translation/preprocessing logic."""
    from ocman import preprocess_argv

    # Test list projects and list porjects
    assert preprocess_argv(["ocman", "list", "projects"]) == ["ocman", "--list-projects"]
    assert preprocess_argv(["ocman", "list", "porjects"]) == ["ocman", "--list-projects"]

    # Test list sessions
    assert preprocess_argv(["ocman", "list", "sessions"]) == ["ocman", "--list-sessions"]

    # Test list sessions in project XXXX
    assert preprocess_argv(["ocman", "list", "sessions", "in", "project", "my-proj"]) == ["ocman", "--list-sessions", "--project", "my-proj"]
    
    # Test list sessions in XXXX
    assert preprocess_argv(["ocman", "list", "sessions", "in", "my-proj"]) == ["ocman", "--list-sessions", "--project", "my-proj"]

    # Test list sessions in project My Project Name (unquoted multi-word)
    assert preprocess_argv(["ocman", "list", "sessions", "in", "project", "My", "Project", "Name"]) == ["ocman", "--list-sessions", "--project", "My Project Name"]

    # Test list sessions in project My Project Name with flags
    assert preprocess_argv(["ocman", "list", "sessions", "in", "project", "My", "Project", "Name", "--all-sessions"]) == ["ocman", "--list-sessions", "--project", "My Project Name", "--all-sessions"]
    assert preprocess_argv(["ocman", "list", "sessions", "in", "project", "My", "Project", "Name", "-A"]) == ["ocman", "--list-sessions", "--project", "My Project Name", "-A"]


def test_preprocess_argv_show_logs():
    from ocman import preprocess_argv
    assert preprocess_argv(["ocman", "show", "logs"]) == ["ocman", "--show-logs"]
    assert preprocess_argv(["ocman", "SHOW", "loGs"]) == ["ocman", "--show-logs"]


def test_cli_show_logs(mock_history_path, capsys):
    import ocman
    # Setup some test history
    history = {
        "cumulative": {
            "projects_deleted": 1,
            "sessions_deleted": 2,
            "subagents_deleted": 3,
            "messages_deleted": 4,
            "cost_deleted": 0.5,
            "tokens_input_deleted": 100,
            "tokens_output_deleted": 200,
            "space_saved_deleted": 1024
        },
        "runs": [
            {
                "timestamp": "2026-06-18 12:00:00",
                "reason": "delete",
                "sessions_count": 1,
                "subagents_count": 0,
                "messages_count": 5,
                "cost": 0.01,
                "space_saved": 512,
                "sessions": [
                    {
                        "id": "test_sess_1",
                        "title": "Test Session 1",
                        "created": 1000000,
                        "updated": 2000000
                    }
                ]
            }
        ]
    }
    ocman._save_history(history)
    ocman.cli_show_logs()
    captured = capsys.readouterr()
    assert "GRAND TOTALS (ALL-TIME HISTORICAL RECOVERY)" in captured.out
    assert "Sessions Deleted:        2" in captured.out
    assert "Total Disk Space Saved:  1.00 KB" in captured.out
    assert "Test Session 1" in captured.out


def test_save_deletion_metrics_accumulates_space_saved(mock_history_path):
    import ocman
    stats = {
        "sessions_count": 1,
        "subagents_count": 0,
        "messages_count": 10,
        "cost": 0.05,
        "tokens_input": 500,
        "tokens_output": 250,
        "space_saved": 4096
    }
    ocman.save_deletion_metrics("delete", stats)
    history = ocman._load_history()
    assert history["cumulative"]["space_saved_deleted"] == 4096

    # Accumulate second time
    ocman.save_deletion_metrics("delete", stats)
    history = ocman._load_history()
    assert history["cumulative"]["space_saved_deleted"] == 8192


def test_preprocess_argv_delete_project():
    from ocman import preprocess_argv
    assert preprocess_argv(["ocman", "delete", "project", "my-proj"]) == ["ocman", "--delete-project", "--project", "my-proj"]
    assert preprocess_argv(["ocman", "delete", "project", "My", "Project", "Name", "--force"]) == ["ocman", "--delete-project", "--project", "My Project Name", "--force"]


def test_db_delete_project_recursive_saves_history(temp_db, mock_history_path):
    import ocman
    from ocman import db_delete_project_recursive
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, cost, tokens_input, tokens_output)
        VALUES ('sess1', 'proj1', 'Session 1', 1000, 2000, 0.10, 1000, 500)
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, parent_id, title, time_created, time_updated, cost, tokens_input, tokens_output)
        VALUES ('sub1', 'proj1', 'sess1', 'Sub 1', 1100, 2100, 0.05, 500, 250)
    """)
    conn.commit()
    conn.close()

    # Run recursive project delete (mock confirm input)
    import builtins
    orig_input = builtins.input
    builtins.input = lambda _: 'yes'
    try:
        db_delete_project_recursive("proj1", dry_run=False, force=True, verbosity=0)
    finally:
        builtins.input = orig_input

    # Check project is deleted
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM project WHERE id = 'proj1'")
    assert cursor.fetchone()[0] == 0
    cursor.execute("SELECT COUNT(*) FROM session")
    assert cursor.fetchone()[0] == 0
    conn.close()

    # History should be updated
    history = ocman._load_history()
    c = history["cumulative"]
    assert c["projects_deleted"] == 1
    assert c["sessions_deleted"] == 2
    assert c["cost_deleted"] == pytest.approx(0.15)






