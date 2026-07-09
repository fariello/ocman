import os
import sqlite3
import pytest
from pathlib import Path
import ocman
from ocman import (
    db_list_projects,
    db_list_sessions,
    db_search_sessions,
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


def _seed_search_db(db_path):
    """Populate a temp_db with projects, sessions and part content for search tests."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # The temp_db fixture creates a stub `part` table without a `data` column.
    # Recreate it to match the real opencode schema used by db_search_sessions.
    cursor.execute("DROP TABLE IF EXISTS part")
    cursor.execute("""
        CREATE TABLE part (
            id TEXT PRIMARY KEY,
            message_id TEXT,
            session_id TEXT,
            time_created INTEGER,
            time_updated INTEGER,
            data TEXT
        )
    """)

    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj2', '/other/proj', 'Proj 2')")

    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory)
        VALUES ('sess1', 'proj1', 'Fix the widget crash', 1000, 2000, '/path/to/proj')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sub1', 'proj1', 'explore subagent', 1050, 2050, '/path/to/proj', 'sess1')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory)
        VALUES ('sess2', 'proj2', 'Unrelated work', 1100, 2100, '/other/proj')
    """)

    # part.data holds JSON message text (as opencode stores it).
    cursor.execute(
        "INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES (?,?,?,?,?,?)",
        ("p1", "m1", "sess1", 1000, 1000, '{"type":"text","text":"Traceback: AttributeError on the widget"}'),
    )
    cursor.execute(
        "INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES (?,?,?,?,?,?)",
        ("p2", "m2", "sub1", 1050, 1050, '{"type":"text","text":"child ran an AttributeError repro"}'),
    )
    cursor.execute(
        "INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) VALUES (?,?,?,?,?,?)",
        ("p3", "m3", "sess2", 1100, 1100, '{"type":"text","text":"totally different content"}'),
    )
    conn.commit()
    conn.close()


def test_db_search_sessions_content_match(temp_db):
    _seed_search_db(temp_db)
    # Content match, excluding subagents by default via the caller; the function
    # itself returns all matches and lets callers filter.
    results = db_search_sessions("AttributeError")
    ids = {r["id"] for r in results}
    assert "sess1" in ids  # matched on content
    assert "sub1" in ids    # subagent also matched on content
    assert "sess2" not in ids
    sess1 = next(r for r in results if r["id"] == "sess1")
    assert sess1["match_where"] == "content"
    assert "AttributeError" in sess1["snippet"]


def test_db_search_sessions_title_match(temp_db):
    _seed_search_db(temp_db)
    results = db_search_sessions("widget crash")
    ids = {r["id"] for r in results}
    assert "sess1" in ids
    sess1 = next(r for r in results if r["id"] == "sess1")
    assert sess1["match_where"] == "title"


def test_db_search_sessions_project_scope(temp_db):
    _seed_search_db(temp_db)
    # Scoped to proj2 should not return proj1 sessions.
    results = db_search_sessions("AttributeError", project_id="proj2")
    assert results == []
    results = db_search_sessions("content", project_id="proj2")
    assert {r["id"] for r in results} == {"sess2"}


def test_db_search_sessions_case_insensitive(temp_db):
    _seed_search_db(temp_db)
    lower = {r["id"] for r in db_search_sessions("attributeerror")}
    upper = {r["id"] for r in db_search_sessions("ATTRIBUTEERROR")}
    assert lower == upper
    assert "sess1" in lower


def test_db_search_sessions_empty_query(temp_db):
    _seed_search_db(temp_db)
    assert db_search_sessions("") == []
    assert db_search_sessions("   ") == []


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


def test_db_run_cleanup_fractional_days(temp_db, monkeypatch, mock_history_path):
    """--days accepts fractions: 0.25 day = 6 hours. A session 12h old is pruned; 3h old kept."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    import time
    now_ms = int(time.time() * 1000)
    three_hours_ago = now_ms - int(3 * 3600 * 1000)
    twelve_hours_ago = now_ms - int(12 * 3600 * 1000)
    cursor.execute(
        "INSERT INTO session (id, project_id, title, time_created, time_updated) "
        "VALUES ('recent_sess', 'proj1', 'Recent', ?, ?)", (three_hours_ago, three_hours_ago))
    cursor.execute(
        "INSERT INTO session (id, project_id, title, time_created, time_updated) "
        "VALUES ('halfday_sess', 'proj1', 'Half day', ?, ?)", (twelve_hours_ago, twelve_hours_ago))
    conn.commit()
    conn.close()

    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    # 0.25 days == 6 hours retention.
    db_run_cleanup(days=0.25, project_id=None, project_dir=None, dry_run=False, force=True, clean_orphans=False, verbosity=0)

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    remaining = [row[0] for row in cursor.execute("SELECT id FROM session").fetchall()]
    assert "recent_sess" in remaining       # 3h < 6h retention -> kept
    assert "halfday_sess" not in remaining  # 12h > 6h retention -> pruned
    conn.close()


def test_parse_args_days_accepts_float(monkeypatch):
    """'db clean --days' parses as float (0.25) and normalizes to args.days."""
    import sys
    from ocman import parse_args
    monkeypatch.setattr(sys, "argv", ["ocman", "db", "clean", "--days", "0.25"])
    args = parse_args()
    assert args.days == 0.25
    assert args.clean is True


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


def test_dir_usage(tmp_path):
    from ocman import dir_usage
    # Empty dir
    assert dir_usage(tmp_path) == (0, 0)
    # A top-level file
    (tmp_path / "a.zip").write_bytes(b"x" * 100)
    # A top-level backup directory with nested files
    d = tmp_path / "opencode-db-cleanup-20260101-000000"
    d.mkdir()
    (d / "opencode.db").write_bytes(b"y" * 250)
    (d / "opencode.db-wal").write_bytes(b"z" * 50)
    total, count = dir_usage(tmp_path)
    assert total == 400  # 100 + 250 + 50
    assert count == 2     # one file + one dir at top level
    # Nonexistent path is tolerated
    assert dir_usage(tmp_path / "nope") == (0, 0)


def test_db_show_info_backups_section(temp_db, capsys, monkeypatch, tmp_path):
    import ocman
    from ocman import db_show_info, save_ocman_config, DEFAULT_CONFIG, OCMAN_CONFIG_PATH

    # Point config at a temp backup dir with a known-size backup.
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    d = backup_dir / "opencode-db-cleanup-20260101-000000"
    d.mkdir()
    (d / "opencode.db").write_bytes(b"x" * 1024)
    cfg_path = tmp_path / "ocman_test.toml"
    monkeypatch.setattr(ocman, "OCMAN_CONFIG_PATH", cfg_path)
    cfg = dict(DEFAULT_CONFIG)
    cfg["default_backup_dir"] = str(backup_dir)
    save_ocman_config(cfg, cfg_path)

    class Args:
        verbose = 0
        by_project = False
    db_show_info(Args())
    out = capsys.readouterr().out
    assert "Backups (Disk Storage):" in out
    assert "Backups:         1" in out
    assert "1.00 KB" in out


def test_db_show_info_by_project(temp_db, capsys, monkeypatch, tmp_path):
    import ocman
    from ocman import db_show_info
    # Isolate storage dir so we do not touch the real one.
    storage = tmp_path / "session_diff"
    monkeypatch.setattr(ocman, "OPENCODE_STORAGE_DIR", storage)
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/w1', 'Proj One')")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('p2', '/w2', 'Proj Two')")
    cursor.execute("INSERT INTO session (id, project_id, title, tokens_input, tokens_output) VALUES ('s1', 'p1', 'S1', 100, 50)")
    cursor.execute("INSERT INTO session (id, project_id, title, tokens_input, tokens_output) VALUES ('s2', 'p2', 'S2', 10, 5)")
    cursor.execute("INSERT INTO message (id, session_id) VALUES ('m1', 's1')")
    conn.commit()
    conn.close()

    # Seed session-diff files so p1 has more on-disk bytes than p2.
    (ocman.OPENCODE_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    (ocman.OPENCODE_STORAGE_DIR / "s1.json").write_bytes(b"x" * 500)
    (ocman.OPENCODE_STORAGE_DIR / "s2.json").write_bytes(b"y" * 10)

    class Args:
        verbose = 0
        by_project = True
    db_show_info(Args())
    out = capsys.readouterr().out
    assert "Per-Project Disk Usage (session-diff files):" in out
    assert "single shared file" in out  # honest-docs note, no per-project DB bytes
    # p1 (500 B) must be listed before p2 (10 B) — sorted by diff bytes desc.
    assert out.index("Proj One") < out.index("Proj Two")
    assert "Sessions: 1" in out


def test_disk_alias_parses_to_info_by_project(monkeypatch):
    """'disk' is a subcommand that normalizes to info + by-project."""
    import sys
    from ocman import parse_args
    monkeypatch.setattr(sys, "argv", ["ocman", "disk"])
    args = parse_args()
    assert args.info is True
    assert args.by_project is True


def test_parse_args_help(monkeypatch, capsys):
    import sys
    from ocman import parse_args
    
    # Mock sys.argv to pass help
    monkeypatch.setattr(sys, "argv", ["ocman.py", "help"])
    
    with pytest.raises(SystemExit) as excinfo:
        parse_args()
        
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    # 'ocman help' now renders ocman's custom, verb-first help screen.
    output = captured.out + captured.err
    assert "ocman - OpenCode Manager" in output
    assert "Usage" in output
    # Subcommand syntax must be discoverable from help.
    assert "session list" in output


def test_build_help_overview_is_verb_first():
    from ocman import build_help
    text = build_help(None)
    # No ANSI in non-tty test environment.
    assert "\033[" not in text
    # Subcommand syntax is the primary interface shown.
    assert "ocman list sessions" in text
    assert "ocman search" in text
    assert "ocman db info" in text
    # It advertises focused topics and the full reference.
    assert "help TOPIC" in text
    assert "help all" in text
    # It must be reasonably compact (not the old 190-line wall).
    assert len(text.splitlines()) < 70


def test_build_help_topics_render():
    from ocman import build_help, HELP_TOPICS
    for topic in HELP_TOPICS:
        text = build_help(topic)
        assert text.strip()
        assert "ocman" in text


def test_build_help_all_is_full_reference():
    from ocman import build_help
    text = build_help("all")
    # Every command group and key action should appear in the full reference.
    for token in ("session <action>", "project <action>", "db <action>",
                  "backup <action>", "clean-orphans", "rebase", "compact",
                  "config create", "recovery options"):
        assert token in text, token


def test_build_help_unknown_topic_falls_back_to_overview():
    from ocman import build_help
    assert build_help("does-not-exist") == build_help(None)


def test_parse_args_help_topic(monkeypatch, capsys):
    import sys
    from ocman import parse_args

    monkeypatch.setattr(sys, "argv", ["ocman.py", "help", "maintain"])
    with pytest.raises(SystemExit) as excinfo:
        parse_args()
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "db clean" in out


def test_parse_args_help_unknown_topic(monkeypatch, capsys):
    import sys
    from ocman import parse_args

    monkeypatch.setattr(sys, "argv", ["ocman.py", "help", "bogus"])
    with pytest.raises(SystemExit) as excinfo:
        parse_args()
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "Unknown help topic" in err


def test_parse_args_dash_h(monkeypatch, capsys):
    import sys
    from ocman import parse_args

    monkeypatch.setattr(sys, "argv", ["ocman.py", "-h"])
    with pytest.raises(SystemExit) as excinfo:
        parse_args()
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "ocman - OpenCode Manager" in out


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
    assert f"ocman.py {ocman.__version__}" in output or f"ocman {ocman.__version__}" in output


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


def _fake_ps(stdout="", rc=0):
    """Build a fake subprocess.run replacement returning a canned CompletedProcess."""
    import subprocess
    def _run(cmd, *a, **k):
        return subprocess.CompletedProcess(cmd, rc, stdout=stdout, stderr="")
    return _run


def test_process_lock_refuses_when_opencode_running(temp_db, monkeypatch):
    """Gate: with a running opencode process detected and not --force, a destructive op refuses."""
    import subprocess
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated) VALUES ('s1','p1','S1',1,2)")
    conn.commit(); conn.close()
    # ps reports one plausible opencode process (pid 4242).
    ps_out = ("  PID TTY      ELAPSED                     STARTED COMMAND\n"
              " 4242 pts/3        300  Fri Jul  4 12:00:00 2026 opencode --continue\n")
    monkeypatch.setattr(ocman.subprocess, "run", _fake_ps(ps_out, rc=0))
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    with pytest.raises(RecoveryError):
        db_delete_session_recursive("s1", dry_run=False, force=False, verbosity=0)
    # session untouched (op refused before deleting)
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 1
    conn.close()


def test_process_lock_force_bypasses(temp_db, monkeypatch):
    """--force skips the process-lock check entirely (never even runs ps)."""
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated) VALUES ('s1','p1','S1',1,2)")
    conn.commit(); conn.close()
    def _boom(*a, **k):
        raise AssertionError("ps must not run when --force is given")
    monkeypatch.setattr(ocman.subprocess, "run", _boom)
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    db_delete_session_recursive("s1", dry_run=False, force=True, verbosity=0)  # no raise
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 0  # deleted
    conn.close()


def test_process_lock_fails_open_on_detector_error(temp_db, monkeypatch):
    """If the detector errors (e.g. ps missing), the op proceeds (fail-open), matching prior behavior."""
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated) VALUES ('s1','p1','S1',1,2)")
    conn.commit(); conn.close()
    def _raise(*a, **k):
        raise FileNotFoundError("ps not found")
    monkeypatch.setattr(ocman.subprocess, "run", _raise)
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    db_delete_session_recursive("s1", dry_run=False, force=False, verbosity=0)  # no raise (fail-open)
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 0  # proceeded
    conn.close()


def test_detect_running_opencode_filter_and_self_exclusion(monkeypatch):
    """Detector: keeps plausible opencode+continue rows, excludes self and non-matching rows."""
    import os, subprocess
    my_pid = os.getpid()
    ps_out = (
        "  PID TTY      ELAPSED                     STARTED COMMAND\n"
        f"{my_pid:>5} pts/1        100  Fri Jul  4 12:00:00 2026 opencode --continue\n"   # self -> excluded
        " 4242 pts/3        300  Fri Jul  4 12:00:00 2026 opencode --continue\n"          # match
        " 4243 pts/4         10  Fri Jul  4 12:05:00 2026 vim notes-about-opencode.md\n"  # no 'continue' -> skip
        " 4244 ?             20  Fri Jul  4 12:06:00 2026 opencode serve\n"               # opencode, no continue -> skip
    )
    monkeypatch.setattr(ocman.subprocess, "run",
                        lambda cmd, *a, **k: subprocess.CompletedProcess(cmd, 0, stdout=ps_out, stderr=""))
    procs = ocman.detect_running_opencode(0)
    pids = {p["pid"] for p in procs}
    assert pids == {4242}  # only the genuine opencode --continue, not self, vim, or 'opencode serve'


def test_detect_running_opencode_fails_open(monkeypatch):
    """Detector returns [] (fail-open) when ps is unavailable."""
    def _raise(*a, **k):
        raise FileNotFoundError("no ps")
    monkeypatch.setattr(ocman.subprocess, "run", _raise)
    assert ocman.detect_running_opencode(0) == []


def test_render_running_opencode_lists_each_process():
    procs = [
        {"pid": 4242, "tty": "pts/3", "elapsed": "5m00s", "started": "Fri Jul 4 12:00:00 2026",
         "cwd": "/home/u/proj", "project": "My Project", "cmdline": "opencode --continue"},
        {"pid": 99, "tty": "?", "elapsed": "1h02m", "started": "Fri Jul 4 11:00:00 2026",
         "cwd": "", "project": "", "cmdline": "opencode --continue"},
    ]
    out = ocman._render_running_opencode(procs)
    assert "2 opencode process(es) are running" in out
    assert "PID 4242" in out and "PID 99" in out
    assert "cwd /home/u/proj" in out and "→ project My Project" in out
    assert "no tty" in out  # '?' tty normalized
    assert "--force" in out  # actionable footer


def test_delete_session_cancel_on_non_yes(temp_db, monkeypatch):
    """Characterization: delete-session cancels (no deletion) on a non-'yes' confirmation."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO session (id, project_id, title, time_created, time_updated) VALUES ('s1', 'p1', 'S1', 1000, 2000)")
    conn.commit(); conn.close()
    monkeypatch.setattr("builtins.input", lambda _: "no")
    db_delete_session_recursive("s1", dry_run=False, force=True, verbosity=0)
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 1  # not deleted
    conn.close()


def test_delete_session_force_still_prompts(temp_db, monkeypatch):
    """ARCH-9 characterization: --force does NOT skip the typed-'yes' prompt (it only bypasses
    the process-lock). With force=True and a non-'yes' answer, nothing is deleted."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO session (id, project_id, title, time_created, time_updated) VALUES ('s1', 'p1', 'S1', 1000, 2000)")
    conn.commit(); conn.close()
    prompted = {"n": 0}
    def _input(_):
        prompted["n"] += 1
        return "no"
    monkeypatch.setattr("builtins.input", _input)
    db_delete_session_recursive("s1", dry_run=False, force=True, verbosity=0)
    assert prompted["n"] == 1, "force=True must still prompt for typed 'yes'"
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 1
    conn.close()


def test_delete_session_confirm_false_skips_prompt(temp_db, monkeypatch):
    """Characterization: confirm=False (the TUI path) skips the prompt and deletes."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO session (id, project_id, title, time_created, time_updated) VALUES ('s1', 'p1', 'S1', 1000, 2000)")
    conn.commit(); conn.close()
    def _input(_):
        raise AssertionError("confirm=False must not prompt")
    monkeypatch.setattr("builtins.input", _input)
    db_delete_session_recursive("s1", dry_run=False, force=True, verbosity=0, confirm=False)
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 0  # deleted
    conn.close()


def test_clear_history_requires_confirmation(mock_history_path, monkeypatch):
    """--clear-history now prompts; a non-'yes' answer preserves the history."""
    import sys
    # Seed some history so we can detect whether it was cleared.
    ocman._save_history({"cumulative": {"sessions_deleted": 7}, "runs": [{"n": 1}, {"n": 2}]})
    monkeypatch.setattr("builtins.input", lambda _: "no")
    monkeypatch.setattr(sys, "argv", ["ocman", "--clear-history"])
    try:
        ocman.main()
    except SystemExit:
        pass
    hist = ocman._load_history()
    assert hist["cumulative"]["sessions_deleted"] == 7  # NOT cleared on 'no'
    assert len(hist["runs"]) == 2


def test_clear_history_force_bypasses_prompt(mock_history_path, monkeypatch):
    """--clear-history --force clears without prompting (scriptable)."""
    import sys
    ocman._save_history({"cumulative": {"sessions_deleted": 7}, "runs": [{"n": 1}]})
    def _no_input(_):
        raise AssertionError("--force must not prompt")
    monkeypatch.setattr("builtins.input", _no_input)
    monkeypatch.setattr(sys, "argv", ["ocman", "history", "clear", "--force"])
    try:
        ocman.main()
    except SystemExit:
        pass
    hist = ocman._load_history()
    assert hist["cumulative"]["sessions_deleted"] == 0  # cleared
    assert hist["runs"] == []


def test_preprocess_argv_passthrough():
    """Commands without 'in NAME' sugar are passed through unchanged."""
    from ocman import preprocess_argv

    for argv in (
        ["ocman", "project", "list"],
        ["ocman", "session", "list"],
        ["ocman", "session", "list", "my-proj"],
        ["ocman", "disk"],
        ["ocman", "logs"],
        ["ocman", "search", "AttributeError"],
        ["ocman", "search", "AttributeError", "-A"],
        ["ocman", "db", "clean"],
        ["ocman", "help", "maintain"],
    ):
        assert preprocess_argv(argv) == argv


def test_preprocess_argv_in_sugar():
    """'in [project] NAME' sugar for session list (positional) and search (flags)."""
    from ocman import preprocess_argv

    # session list in NAME -> NAME positional
    assert preprocess_argv(["ocman", "session", "list", "in", "my-proj"]) == \
        ["ocman", "session", "list", "my-proj"]

    # session list in NAME with trailing flag
    assert preprocess_argv(["ocman", "session", "list", "in", "my-proj", "-A"]) == \
        ["ocman", "session", "list", "my-proj", "-A"]

    # session search TEXT in project NAME -> scope flags
    assert preprocess_argv(["ocman", "session", "search", "bug", "in", "project", "my-proj"]) == \
        ["ocman", "session", "search", "bug", "--scope-kind", "project", "--scope-name", "my-proj"]

    # multi-word name (unquoted) is joined into --scope-name
    assert preprocess_argv(["ocman", "search", "bug", "in", "My", "Project", "Name"]) == \
        ["ocman", "search", "bug", "--scope-name", "My Project Name"]


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


def test_project_delete_parses(monkeypatch):
    """'project delete NAME' normalizes to delete_project + project."""
    import sys
    from ocman import parse_args
    monkeypatch.setattr(sys, "argv", ["ocman", "project", "delete", "my-proj", "--force"])
    args = parse_args()
    assert args.delete_project is True
    assert args.project == "my-proj"
    assert args.force is True


def _parse(monkeypatch, argv):
    import sys
    from ocman import parse_args
    monkeypatch.setattr(sys, "argv", ["ocman", *argv])
    return parse_args()


def test_subcommand_session_list(monkeypatch):
    a = _parse(monkeypatch, ["session", "list", "my-proj", "-A"])
    assert a.list_sessions is True
    assert a.project == "my-proj"
    assert a.all_sessions is True


def test_subcommand_session_search(monkeypatch):
    a = _parse(monkeypatch, ["session", "search", "needle", "-n", "10"])
    assert a.search == "needle"
    assert a.limit == 10


def test_subcommand_top_level_search_alias(monkeypatch):
    a = _parse(monkeypatch, ["search", "needle"])
    assert a.search == "needle"
    assert a.project is None


def test_subcommand_session_show_defaults_to_details(monkeypatch):
    a = _parse(monkeypatch, ["session", "show", "SID"])
    assert a.session == "SID"
    assert a.details is True


def test_subcommand_session_show_head_tail(monkeypatch):
    a = _parse(monkeypatch, ["session", "show", "SID", "-H", "3", "-T", "2"])
    assert a.session == "SID"
    assert a.head == 3
    assert a.tail == 2
    assert a.details is False


def test_subcommand_session_recover(monkeypatch):
    a = _parse(monkeypatch, ["session", "recover", "SID", "-mi", "50"])
    assert a.session == "SID"
    assert a.max_interactions == 50
    assert a.compact is None


def test_subcommand_session_compact_with_model(monkeypatch):
    a = _parse(monkeypatch, ["session", "compact", "SID", "some/model", "--allow-secrets"])
    assert a.session == "SID"
    assert a.compact == "some/model"
    assert a.allow_secrets is True


def test_subcommand_session_compact_interactive(monkeypatch):
    a = _parse(monkeypatch, ["session", "compact", "SID"])
    assert a.compact == ""  # empty -> interactive model pick


def test_subcommand_session_delete(monkeypatch):
    a = _parse(monkeypatch, ["session", "delete", "SID", "--dry-run"])
    assert a.delete is True
    assert a.session == "SID"
    assert a.dry_run is True


def test_subcommand_session_export(monkeypatch):
    a = _parse(monkeypatch, ["session", "export", "SID", "--to", "/tmp/x.ocbox"])
    assert a.export_session == "SID"
    assert a.to == "/tmp/x.ocbox"


def test_subcommand_session_import(monkeypatch):
    a = _parse(monkeypatch, ["session", "import", "/tmp/x.ocbox", "--to-project", "P1"])
    assert a.import_session == "/tmp/x.ocbox"
    assert a.to_project == "P1"


def test_subcommand_session_move(monkeypatch):
    a = _parse(monkeypatch, ["session", "move", "SID", "--to", "/new", "--metadata-only"])
    assert a.move_session == "SID"
    assert a.to == "/new"
    assert a.metadata_only is True


def test_subcommand_project_list(monkeypatch):
    a = _parse(monkeypatch, ["project", "list"])
    assert a.list_projects is True


def test_subcommand_project_move(monkeypatch):
    a = _parse(monkeypatch, ["project", "move", "p1", "--to", "/new"])
    assert a.move_project == "p1"
    assert a.to == "/new"


def test_subcommand_db_info(monkeypatch):
    a = _parse(monkeypatch, ["db", "info", "--by-project"])
    assert a.info is True
    assert a.by_project is True


def test_subcommand_db_clean_orphans(monkeypatch):
    a = _parse(monkeypatch, ["db", "clean-orphans", "--force"])
    assert a.clean_orphans is True
    assert a.force is True


def test_subcommand_db_rebase(monkeypatch):
    a = _parse(monkeypatch, ["db", "rebase", "--from", "/a", "--to", "/b"])
    assert a.rebase_paths is True
    assert a.from_prefix == "/a"
    assert a.to == "/b"


def test_subcommand_backup_create_restore_clean(monkeypatch):
    a = _parse(monkeypatch, ["backup", "create", "/tmp/dest"])
    assert a.backup_opencode == "/tmp/dest"
    a = _parse(monkeypatch, ["backup", "create"])
    assert a.backup_opencode == ""  # default destination
    a = _parse(monkeypatch, ["backup", "restore", "/tmp/x.zip"])
    assert a.restore == "/tmp/x.zip"
    a = _parse(monkeypatch, ["backup", "clean", "--days", "30"])
    assert a.clean_backups is True
    assert a.days == 30


def test_subcommand_history_and_config(monkeypatch):
    a = _parse(monkeypatch, ["history", "show"])
    assert a.show_logs is True
    a = _parse(monkeypatch, ["logs"])
    assert a.show_logs is True
    a = _parse(monkeypatch, ["history", "clear", "--force"])
    assert a.clear_history is True
    assert a.force is True
    a = _parse(monkeypatch, ["config", "create"])
    assert a.create_config is True


def test_subcommand_filter(monkeypatch):
    a = _parse(monkeypatch, ["filter", "doc.md", "--scope", "x only", "-P", "proj"])
    assert a.command == "filter"
    assert a.command_arg == "doc.md"
    assert a.scope == "x only"
    assert a.project == "proj"


def test_subcommand_models_and_prompt_and_ui(monkeypatch):
    assert _parse(monkeypatch, ["models"]).show_models is True
    assert _parse(monkeypatch, ["compaction-prompt"]).show_compaction_prompt is True
    assert _parse(monkeypatch, ["ui"]).command == "ui"
    assert _parse(monkeypatch, ["gui"]).command == "gui"


def test_subcommand_global_db_flag(monkeypatch):
    from pathlib import Path
    a = _parse(monkeypatch, ["--db", "/tmp/other.db", "project", "list"])
    assert a.db == Path("/tmp/other.db")
    assert a.list_projects is True


# ---- duration parsing (items 7 & 8) ---------------------------------------

def test_parse_duration_to_days():
    from ocman import parse_duration_to_days
    assert parse_duration_to_days("30") == 30.0            # bare number = days
    assert parse_duration_to_days("5d") == 5.0
    assert parse_duration_to_days("2h") == 2.0 / 24.0
    assert parse_duration_to_days("6w") == 42.0
    assert parse_duration_to_days("6mo") == 180.0
    assert parse_duration_to_days("1y") == 365.0
    assert parse_duration_to_days("30 days") == 30.0
    assert parse_duration_to_days("6 weeks") == 42.0


def test_parse_duration_rejects_garbage():
    from ocman import parse_duration_to_days, DurationError
    for bad in ("", "  ", "5x", "banana", "5 fortnights"):
        with pytest.raises(DurationError):
            parse_duration_to_days(bad)


def test_db_clean_older_than_and_positional(monkeypatch):
    # --older-than
    a = _parse(monkeypatch, ["db", "clean", "--older-than", "2w", "--dry-run"])
    assert a.clean is True and a.days == 14.0 and a.project is None
    # positional "30 days"
    a = _parse(monkeypatch, ["db", "clean", "30", "days"])
    assert a.days == 30.0 and a.project is None
    # compact positional
    a = _parse(monkeypatch, ["db", "clean", "6mo"])
    assert a.days == 180.0
    # deprecated --days alias still works
    a = _parse(monkeypatch, ["db", "clean", "--days", "7"])
    assert a.days == 7.0
    # NAME + duration
    a = _parse(monkeypatch, ["db", "clean", "myproj", "30", "days"])
    assert a.project == "myproj" and a.days == 30.0
    # NAME only keeps default (5)
    a = _parse(monkeypatch, ["db", "clean", "myproj"])
    assert a.project == "myproj" and a.days == 5


def test_backup_clean_duration(monkeypatch):
    a = _parse(monkeypatch, ["backup", "clean", "90", "days"])
    assert a.clean_backups is True and a.days == 90.0
    a = _parse(monkeypatch, ["backup", "clean", "--older-than", "1y"])
    assert a.days == 365.0


# ---- search: default 10, -n, scope kind (items 5 & 6) ---------------------

def test_search_default_limit_is_10(monkeypatch):
    a = _parse(monkeypatch, ["search", "needle"])
    assert a.search == "needle"
    assert a.limit == 10


def test_search_n_flag(monkeypatch):
    a = _parse(monkeypatch, ["search", "needle", "-n", "25"])
    assert a.limit == 25
    a = _parse(monkeypatch, ["search", "needle", "--limit", "3"])
    assert a.limit == 3


# ---- preprocess sugar (items 2, 3, 6) -------------------------------------

def test_preprocess_list_word_order():
    from ocman import preprocess_argv
    assert preprocess_argv(["ocman", "list", "projects"]) == ["ocman", "project", "list"]
    assert preprocess_argv(["ocman", "list", "sessions"]) == ["ocman", "session", "list"]
    assert preprocess_argv(["ocman", "list", "sessions", "myproj"]) == \
        ["ocman", "session", "list", "myproj"]


def test_preprocess_move_export_to_keyword():
    from ocman import preprocess_argv
    assert preprocess_argv(["ocman", "move", "X", "to", "Y"]) == ["ocman", "move", "X", "Y"]
    assert preprocess_argv(["ocman", "export", "S", "to", "F.ocbox"]) == \
        ["ocman", "export", "S", "F.ocbox"]


def test_preprocess_search_scope_kind():
    from ocman import preprocess_argv
    assert preprocess_argv(["ocman", "search", "bug", "in", "session", "My", "Sess"]) == \
        ["ocman", "search", "bug", "--scope-kind", "session", "--scope-name", "My Sess"]
    assert preprocess_argv(["ocman", "search", "bug", "in", "proj"]) == \
        ["ocman", "search", "bug", "--scope-name", "proj"]


# ---- resolve_target (items 3, 4, 6) ---------------------------------------

def _seed_target_db(db_path):
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/home/me/alpha', 'Alpha')")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p2', '/home/me/beta', 'Beta')")
    cur.execute("""INSERT INTO session (id, project_id, title, time_created, time_updated, directory)
                   VALUES ('sX', 'p1', 'the widget bug', 1000, 2000, '/home/me/alpha')""")
    conn.commit()
    conn.close()


def test_resolve_target_project(temp_db):
    from ocman import resolve_target
    _seed_target_db(temp_db)
    r = resolve_target("alpha")
    assert r.kind == "project"
    assert r.project["id"] == "p1"


def test_resolve_target_session(temp_db):
    from ocman import resolve_target
    _seed_target_db(temp_db)
    r = resolve_target("sX")
    assert r.kind == "session"
    assert r.session["id"] == "sX"


def test_resolve_target_bare_number_is_ambiguous(temp_db):
    from ocman import resolve_target
    _seed_target_db(temp_db)
    assert resolve_target("1").kind == "ambiguous"
    # with a prefer, a number is allowed (list index)
    assert resolve_target("1", prefer="project").kind == "project"


def test_resolve_target_none(temp_db):
    from ocman import resolve_target
    _seed_target_db(temp_db)
    assert resolve_target("does-not-exist-anywhere").kind == "none"


# ---- verbose backup/restore progress helpers (item 1) ---------------------

def test_copy_file_with_progress_roundtrip(tmp_path):
    from ocman import copy_file_with_progress
    src = tmp_path / "src.bin"
    src.write_bytes(b"hello world" * 1000)
    dst = tmp_path / "dst.bin"
    copy_file_with_progress(src, dst)
    assert dst.read_bytes() == src.read_bytes()


def test_zip_write_with_progress_roundtrip(tmp_path):
    import zipfile
    from ocman import zip_write_with_progress
    src = tmp_path / "src.bin"
    src.write_bytes(b"abc" * 5000)
    zp = tmp_path / "a.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        zip_write_with_progress(zf, src, "src.bin")
    with zipfile.ZipFile(zp) as zf:
        assert zf.read("src.bin") == src.read_bytes()


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


def test_resolve_project_and_session(temp_db):
    from ocman import resolve_project, resolve_session_spec
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    
    # Insert a single project with "2026" in the directory path
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/2026-meeting', 'Proj 1')")
    
    # Insert a session for that project
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory)
        VALUES ('sess1', 'proj1', 'Meeting 2', 1000, 2000, '/path/to/2026-meeting')
    """)
    conn.commit()
    conn.close()

    # 1. Test Project Resolution
    # Valid index -> proj1
    p = resolve_project("1")
    assert p is not None
    assert p["id"] == "proj1"

    # Out of bounds index "2" -> should NOT match the "2" in "2026-meeting" substring
    p = resolve_project("2")
    assert p is None

    # Numeric specifier "2026" -> should NOT substring match the directory "2026-meeting"
    p = resolve_project("2026")
    assert p is None

    # Non-numeric substring match -> should match the directory
    p = resolve_project("meeting")
    assert p is not None
    assert p["id"] == "proj1"

    # 2. Test Session Resolution
    sessions = db_list_sessions("proj1")
    assert len(sessions) == 1

    # Valid index "1" -> sess1
    s = resolve_session_spec("1", sessions)
    assert s is not None
    assert s["id"] == "sess1"

    # Out of bounds index "2" -> should NOT substring match "Meeting 2"
    s = resolve_session_spec("2", sessions)
    assert s is None

    # Non-numeric substring match -> should match the title
    s = resolve_session_spec("Meeting", sessions)
    assert s is not None
    assert s["id"] == "sess1"

    # 3. Test Session Resolution with Subagents and filter_subagents=True
    mixed_sessions = [
        {"id": "sess1", "title": "Meeting 1", "parent_id": None},
        {"id": "sub1", "title": "Subagent Session", "parent_id": "sess1"},
    ]

    # Index "2" with filter_subagents=True should be out of bounds (only 1 parent session)
    s = resolve_session_spec("2", mixed_sessions, filter_subagents=True)
    assert s is None

    # Index "2" with filter_subagents=False should match sub1
    s = resolve_session_spec("2", mixed_sessions, filter_subagents=False)
    assert s is not None
    assert s["id"] == "sub1"

    # Exact ID lookup should always work regardless of filter_subagents
    s = resolve_session_spec("sub1", mixed_sessions, filter_subagents=True)
    assert s is not None
    assert s["id"] == "sub1"

    # Substring lookup with filter_subagents=True should fail for subagent sessions
    s = resolve_session_spec("Subagent", mixed_sessions, filter_subagents=True)
    assert s is None

    # Substring lookup with filter_subagents=False should succeed for subagent sessions
    s = resolve_session_spec("Subagent", mixed_sessions, filter_subagents=False)
    assert s is not None
    assert s["id"] == "sub1"


def test_db_list_projects_exception_cleanup(temp_db, monkeypatch):
    close_called = False
    class MockConnection:
        def cursor(self):
            class MockCursor:
                def execute(self, *args, **kwargs):
                    raise Exception("Mock DB Error")
            return MockCursor()
        def close(self):
            nonlocal close_called
            close_called = True

    class MockSqlite:
        def connect(self, *args, **kwargs):
            return MockConnection()

    monkeypatch.setattr(ocman, "_get_sqlite", lambda: MockSqlite())
    
    projects = db_list_projects()
    assert len(projects) == 0
    assert close_called is True


def test_db_list_sessions_exception_cleanup(temp_db, monkeypatch):
    close_called = False
    class MockConnection:
        def cursor(self):
            class MockCursor:
                def execute(self, *args, **kwargs):
                    raise Exception("Mock DB Error")
            return MockCursor()
        def close(self):
            nonlocal close_called
            close_called = True

    class MockSqlite:
        def connect(self, *args, **kwargs):
            return MockConnection()

    monkeypatch.setattr(ocman, "_get_sqlite", lambda: MockSqlite())
    
    sessions = db_list_sessions("proj1")
    assert len(sessions) == 0
    assert close_called is True



def test_cli_help(monkeypatch, capsys):
    import sys
    monkeypatch.setattr(sys, "argv", ["ocman", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        ocman.main()
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "ocman" in captured.out or "opencode" in captured.out or "Manager" in captured.out


def test_cli_version(monkeypatch, capsys):
    import sys
    monkeypatch.setattr(sys, "argv", ["ocman", "--version"])
    with pytest.raises(SystemExit) as excinfo:
        ocman.main()
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert ocman.__version__ in captured.out


def test_per_project_disk_usage(temp_db, tmp_path):
    """_per_project_disk_usage attributes on-disk session-diff bytes/counts per project (S3-T1)."""
    conn = sqlite3.connect(str(temp_db))
    cur = conn.cursor()
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/w/p1', 'Proj One')")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p2', '/w/p2', 'Proj Two')")
    # p1: two sessions (tokens 10+20=30); p2: one session (tokens 5)
    cur.execute("INSERT INTO session (id, project_id, tokens_input, tokens_output) VALUES ('s1','p1',6,4)")
    cur.execute("INSERT INTO session (id, project_id, tokens_input, tokens_output) VALUES ('s2','p1',10,10)")
    cur.execute("INSERT INTO session (id, project_id, tokens_input, tokens_output) VALUES ('s3','p2',2,3)")
    # messages: 2 for s1, 1 for s3
    cur.execute("INSERT INTO message (id, session_id) VALUES ('m1','s1')")
    cur.execute("INSERT INTO message (id, session_id) VALUES ('m2','s1')")
    cur.execute("INSERT INTO message (id, session_id) VALUES ('m3','s3')")
    conn.commit()
    conn.close()

    # Fake session-diff storage: s1 -> 100 bytes, s2 -> 200 bytes (p1 total 300, 2 files);
    # p2's s3 has NO diff file on disk (0 bytes, 0 files).
    storage = tmp_path / "session_diff"
    storage.mkdir()
    (storage / "s1.json").write_bytes(b"x" * 100)
    (storage / "s2.json").write_bytes(b"y" * 200)

    rows = ocman._per_project_disk_usage(sqlite3, temp_db, storage)
    by_id = {r["id"]: r for r in rows}

    assert by_id["p1"]["name"] == "Proj One"
    assert by_id["p1"]["sessions"] == 2
    assert by_id["p1"]["messages"] == 2
    assert by_id["p1"]["tokens"] == 30
    assert by_id["p1"]["diff_files"] == 2
    assert by_id["p1"]["diff_bytes"] == 300

    assert by_id["p2"]["sessions"] == 1
    assert by_id["p2"]["messages"] == 1
    assert by_id["p2"]["tokens"] == 5
    assert by_id["p2"]["diff_files"] == 0
    assert by_id["p2"]["diff_bytes"] == 0

    # Sorted by diff_bytes descending → p1 first.
    assert rows[0]["id"] == "p1"


def test_startup_timestamps():
    import time
    ts_utc1 = ocman.get_startup_timestamp_utc()
    ts_local1 = ocman.get_startup_timestamp_local()
    
    # Wait a moment to ensure datetime.now() would normally change
    time.sleep(0.1)
    
    ts_utc2 = ocman.get_startup_timestamp_utc()
    ts_local2 = ocman.get_startup_timestamp_local()
    
    # Assert they are cached/set in stone
    assert ts_utc1 == ts_utc2
    assert ts_local1 == ts_local2
    
    # Assert format
    assert len(ts_utc1) == 15
    assert ts_utc1[8] == "-"
    assert len(ts_local1) == 15
    assert ts_local1[8] == "-"


# ---------------------------------------------------------------------------
# End-to-end CLI smoke tests
#
# The parse/normalize tests above import ocman in-process, so they validate the
# grammar logic but NOT the actual runnable entry point. These run ocman.py as a
# real subprocess (and the installed `ocman` console script when available) so
# that packaging/sys.path-shadowing regressions (e.g. a stale ocman.py in
# site-packages winning over the editable install) are caught by the suite.
# ---------------------------------------------------------------------------

import subprocess
import sys as _sys
import shutil as _shutil


_OCMAN_PY = str(Path(__file__).resolve().parent.parent / "ocman.py")


def _make_empty_db(tmp_path):
    """A minimal, valid opencode DB with one project so CLI runs are deterministic."""
    db = tmp_path / "e2e.db"
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    cur.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
    cur.execute(
        "CREATE TABLE session (id TEXT PRIMARY KEY, project_id TEXT, title TEXT, "
        "time_created INTEGER, time_updated INTEGER, directory TEXT, parent_id TEXT)"
    )
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/tmp/proj', 'Proj')")
    cur.execute(
        "INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
        "VALUES ('s1', 'p1', 'Sess', 1000, 2000, '/tmp/proj')"
    )
    conn.commit()
    conn.close()
    return db


def _run_ocman_py(args, tmp_path):
    """
    Run the repo ocman.py as a subprocess against a temp DB.

    Runs from tmp_path (not the repo dir) so the current directory cannot mask a
    site-packages shadow copy of ocman via sys.path[0].
    """
    db = _make_empty_db(tmp_path)
    return subprocess.run(
        [_sys.executable, _OCMAN_PY, "--db", str(db), *args],
        capture_output=True, text=True, cwd=str(tmp_path),
    )


def test_e2e_list_projects_word_order(tmp_path):
    """'ocman list projects' must be accepted by the real entry point."""
    r = _run_ocman_py(["list", "projects"], tmp_path)
    combined = r.stdout + r.stderr
    assert r.returncode == 0, combined
    assert "invalid choice" not in combined


def test_e2e_list_project_singular(tmp_path):
    r = _run_ocman_py(["list", "project"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_e2e_list_sessions_word_order(tmp_path):
    # We assert the grammar is accepted (no argparse rejection), not the exit
    # code: "no sessions" is a legitimate non-zero outcome for some DB states.
    r = _run_ocman_py(["list", "sessions"], tmp_path)
    assert "invalid choice" not in (r.stdout + r.stderr), r.stdout + r.stderr


def test_e2e_help_runs(tmp_path):
    r = _run_ocman_py(["help"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OpenCode Manager" in r.stdout


def test_e2e_db_info_runs(tmp_path):
    r = _run_ocman_py(["db", "info"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_e2e_unknown_command_errors(tmp_path):
    r = _run_ocman_py(["frobnicate"], tmp_path)
    assert r.returncode != 0
    assert "invalid choice" in (r.stdout + r.stderr)


def test_e2e_installed_console_script_matches(tmp_path):
    """
    If an `ocman` console script is installed, it must run the SAME grammar as
    the repo (guards against a stale shadow copy in site-packages winning over
    the editable install). Skipped when no console script is on PATH.
    """
    exe = _shutil.which("ocman")
    if not exe:
        pytest.skip("no 'ocman' console script on PATH")
    db = _make_empty_db(tmp_path)
    # Run from tmp_path so cwd cannot mask a site-packages shadow copy.
    r = subprocess.run([exe, "--db", str(db), "list", "projects"],
                       capture_output=True, text=True, cwd=str(tmp_path))
    combined = r.stdout + r.stderr
    assert r.returncode == 0, (
        "Installed 'ocman' rejected 'list projects'. Likely a stale ocman.py "
        "shadowing the editable install in site-packages.\n" + combined
    )
    assert "invalid choice" not in combined
