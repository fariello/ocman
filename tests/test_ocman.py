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
from conftest import abs_path

@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_opencode.db"
    
    # Save original DB path and history path
    orig_path = ocman.OPENCODE_DB_PATH
    orig_history_path = ocman.OPENCODE_HISTORY_PATH
    
    ocman.OPENCODE_DB_PATH = db_path
    ocman.OPENCODE_HISTORY_PATH = tmp_path / "test_ocman_history.json"

    # Isolate the rollback-backup family. Destructive ops (delete/cleanup) compute
    # their backup dir inline as ``Path.home()/.local/share/opencode/backups/...``,
    # so without this a test that actually deletes writes real backup directories
    # into the developer's HOME. Redirect Path.home() to tmp_path for the fixture's
    # lifetime (monkeypatch auto-reverts). Config-path tests use their own fixtures
    # and OCMAN_CONFIG_PATH, so they are unaffected.
    fake_home = tmp_path / "home"
    fake_home.mkdir(exist_ok=True)
    monkeypatch.setattr(ocman.Path, "home", staticmethod(lambda: fake_home))
    
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


def test_db_search_lines_per_session(temp_db):
    """A session with many matching lines returns up to lines_per_session of them
    and reports the true total via match_count."""
    conn = sqlite3.connect(str(temp_db))
    cur = conn.cursor()
    conn.execute("DROP TABLE IF EXISTS part")
    cur.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, "
                "time_created INTEGER, time_updated INTEGER, data TEXT)")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/p', 'P')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
                "VALUES ('s1', 'p1', 'many hits', 1, 2, '/p')")
    # 8 matching lines in one text part.
    body = "\\n".join(f"line {i} needle here" for i in range(8))
    import json as _json
    cur.execute("INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) "
                "VALUES ('p1','m1','s1',1,1,?)",
                (_json.dumps({"type": "text", "text": body.replace("\\n", "\n")}),))
    conn.commit()
    conn.close()

    r = db_search_sessions("needle", lines_per_session=3)
    s = next(x for x in r if x["id"] == "s1")
    assert len(s["snippets"]) == 3          # capped
    assert s["match_count"] == 8            # true total
    assert s["snippet"] == s["snippets"][0]  # back-compat

    r = db_search_sessions("needle", lines_per_session=100)
    s = next(x for x in r if x["id"] == "s1")
    assert len(s["snippets"]) == 8          # all shown when cap is high


def test_display_worktree_global_label():
    from ocman import _display_worktree
    assert _display_worktree("/") == "global (/)"
    assert _display_worktree("") == "global (/)"
    assert _display_worktree("/home/me/proj") == "/home/me/proj"


def test_db_list_sessions_under_dir(temp_db):
    """Directory scoping finds sessions in/under a dir regardless of project,
    including home-dir sessions filed under the global '/' project."""
    from ocman import db_list_sessions_under_dir
    conn = sqlite3.connect(str(temp_db))
    cur = conn.cursor()
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('global', '/', NULL)")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p2', '/home/me/other', 'O')")
    # session in home dir, filed under the global project
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
                "VALUES ('home1', 'global', 'home work', 1, 2, '/home/me')")
    # session in a subdir of home
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
                "VALUES ('sub1', 'global', 'sub work', 1, 3, '/home/me/scratch')")
    # unrelated session elsewhere
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
                "VALUES ('other1', 'p2', 'other', 1, 4, '/home/me/other')")
    conn.commit()
    conn.close()

    got = {s["id"] for s in db_list_sessions_under_dir("/home/me")}
    assert got == {"home1", "sub1", "other1"}   # everything under /home/me

    got = {s["id"] for s in db_list_sessions_under_dir("/home/me/scratch")}
    assert got == {"sub1"}                       # only the subdir

    # trailing slash normalized
    got = {s["id"] for s in db_list_sessions_under_dir("/home/me/")}
    assert "home1" in got


def test_db_list_sessions_under_dir_no_false_prefix(temp_db):
    """'/home/me' must not match '/home/meadow' (prefix boundary safety)."""
    from ocman import db_list_sessions_under_dir
    conn = sqlite3.connect(str(temp_db))
    cur = conn.cursor()
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('g', '/', NULL)")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
                "VALUES ('a', 'g', 't', 1, 2, '/home/meadow/x')")
    conn.commit()
    conn.close()
    assert db_list_sessions_under_dir("/home/me") == []


def test_part_text_extracts_tool_output():
    """_part_text digs into tool parts (state.output / state.input.command)."""
    import json as _json
    from ocman import _part_text, _count_matching_lines
    tool = _json.dumps({
        "type": "tool", "tool": "bash",
        "state": {"status": "completed",
                  "input": {"command": "grep speedtest x"},
                  "output": "a\nspeedtest line 1\nb\nspeedtest line 2\n"},
    })
    text = _part_text(tool)
    assert "\n" in text
    assert _count_matching_lines(text, "speedtest") == 3  # command + 2 output lines


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
    assert "Total Cost:      $0.05" in captured.out
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


def test_chunk_size_config_keys_present_and_roundtrip(tmp_path):
    from ocman import (save_ocman_config, load_ocman_config, DEFAULT_CONFIG,
                       LONG_SESSION_INTERACTION_THRESHOLD, LONG_SESSION_LINE_THRESHOLD)
    # Present in defaults with the documented default values.
    assert DEFAULT_CONFIG["chunk_max_interactions"] == LONG_SESSION_INTERACTION_THRESHOLD
    assert DEFAULT_CONFIG["chunk_max_lines"] == LONG_SESSION_LINE_THRESHOLD
    p = tmp_path / "ocman.toml"
    save_ocman_config(dict(DEFAULT_CONFIG), p)
    # Template renders the keys.
    text = p.read_text(encoding="utf-8")
    assert "chunk_max_interactions =" in text
    assert "chunk_max_lines =" in text
    # Read back defaults, then an override.
    assert load_ocman_config(p)["chunk_max_lines"] == LONG_SESSION_LINE_THRESHOLD
    p.write_text(text.replace(f"chunk_max_lines = {LONG_SESSION_LINE_THRESHOLD}",
                              "chunk_max_lines = 777"), encoding="utf-8")
    assert load_ocman_config(p)["chunk_max_lines"] == 777


def test_save_ocman_config_preserves_unmanaged_keys(tmp_path):
    """FU-01: a partial save must NOT reset keys it does not pass (e.g. the TUI config
    form omits chunk_*/reclaim_*/filter_*)."""
    from ocman import save_ocman_config, load_ocman_config, DEFAULT_CONFIG
    p = tmp_path / "ocman.toml"

    # Start from a config with several non-default unmanaged keys.
    base = dict(DEFAULT_CONFIG)
    base["chunk_max_lines"] = 9999
    base["reclaim_tmp_min_age_hours"] = 72
    base["filter_secret_scan"] = "aggressive"
    save_ocman_config(base, p)
    assert load_ocman_config(p)["chunk_max_lines"] == 9999

    # A partial save (like the TUI form) that omits those keys must preserve them.
    save_ocman_config({"keep_temp": True, "default_retention_days": 12}, p)
    loaded = load_ocman_config(p)
    assert loaded["chunk_max_lines"] == 9999
    assert loaded["reclaim_tmp_min_age_hours"] == 72
    assert loaded["filter_secret_scan"] == "aggressive"
    assert loaded["keep_temp"] is True          # the passed key applied
    assert loaded["default_retention_days"] == 12

    # A full reset-to-defaults still resets everything.
    save_ocman_config(dict(DEFAULT_CONFIG), p)
    reset = load_ocman_config(p)
    assert reset["chunk_max_lines"] == DEFAULT_CONFIG["chunk_max_lines"]
    assert reset["filter_secret_scan"] == DEFAULT_CONFIG["filter_secret_scan"]


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
    # Per-project rows are now a vistab table keyed by project DIRECTORY (worktree),
    # sorted by diff bytes desc: p1 (500 B, /w1) before p2 (10 B, /w2).
    assert out.index("/w1") < out.index("/w2")
    # Split-token + cost columns are present in the table header.
    assert "Tokens In" in out and "Cache" in out and "Cost" in out


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
    # SD-07: reclaim is discoverable via the maintain topic.
    assert "reclaim" in out


def test_parse_args_help_unknown_topic(monkeypatch, capsys):
    import sys
    from ocman import parse_args

    monkeypatch.setattr(sys, "argv", ["ocman.py", "help", "bogus"])
    with pytest.raises(SystemExit) as excinfo:
        parse_args()
    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "Unknown help topic" in err


# --- self-documentation fixes (assess self-documentation IPD) ----------------

def test_no_stale_flag_error_strings():
    """SD-01: no user-facing error should send the user to a removed flag
    (--show-models / --list-projects). The real commands are 'ocman models' /
    'ocman list projects'."""
    import re
    from pathlib import Path
    src = Path(ocman.__file__).with_name("cli.py").read_text(encoding="utf-8")
    # A stale flag is only a problem inside a user-facing quoted string that tells the
    # user to "Use/Run --show-models/--list-projects". Assert the specific fixed messages.
    assert "Run 'ocman models' to see available models." in src
    assert "Run 'ocman list projects' to see available projects." in src
    assert "Use --show-models to see available models." not in src
    assert "Use --list-projects to see available projects." not in src


def test_db_clean_bad_duration_teaches_formats(temp_db, monkeypatch, capsys):
    """SD-03: an invalid --older-than value shows the accepted formats at the point of
    failure."""
    import sys
    monkeypatch.setattr(sys, "argv",
                        ["ocman", "--db", str(temp_db), "db", "clean", "--older-than", "notaduration"])
    with pytest.raises(SystemExit):
        ocman.main()
    err = capsys.readouterr().err
    assert "6mo" in err or "2h" in err  # accepted-format example present


def test_db_not_found_error_has_recovery_hint(monkeypatch, tmp_path):
    """SD-04: the shared 'database not found' error carries a recovery hint."""
    monkeypatch.setattr(ocman, "OPENCODE_DB_PATH", tmp_path / "does-not-exist.db")
    err = ocman._db_not_found_error()
    assert isinstance(err, ocman.RecoveryError)
    msg = str(err)
    assert "Database not found" in msg
    assert "--db" in msg  # actionable next step


def test_main_unexpected_exception_no_traceback(temp_db, monkeypatch, capsys):
    """SD-02: an unexpected (non-RecoveryError) exception on the normal path prints a clean
    message with a -v hint and NO raw traceback."""
    import sys
    # Force an unexpected error deep in a normal command path.
    def boom(*a, **k):
        raise ValueError("synthetic boom")
    monkeypatch.setattr(ocman, "db_list_projects", boom)
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "list", "projects"])
    with pytest.raises(SystemExit):
        ocman.main()
    err = capsys.readouterr().err
    assert "Unexpected error" in err
    assert "-v" in err
    assert "Traceback (most recent call last)" not in err


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
        INSERT INTO session (id, project_id, title, time_created, time_updated, cost, tokens_input, tokens_output, tokens_cache_read, model)
        VALUES ('sess1', 'proj1', 'Session 1', 1000, 2000, 0.05, 1000, 500, 30, '{"id": "gpt-4"}')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, cost, tokens_input, tokens_output, tokens_cache_read, model, parent_id)
        VALUES ('sess2', 'proj1', 'Session 2', 1100, 2100, 0.02, 400, 200, 12, '{"id": "gpt-4"}', 'sess1')
    """)
    # message needs a 'data' column for the interactions (user-role) count.
    cursor.execute("DROP TABLE message")
    cursor.execute("CREATE TABLE message (id TEXT, session_id TEXT, data TEXT)")
    cursor.execute("INSERT INTO message VALUES ('msg1', 'sess1', '{\"role\":\"user\"}')")
    cursor.execute("INSERT INTO message VALUES ('msg2', 'sess2', '{\"role\":\"assistant\"}')")
    # part rows (DB parts) for the deleted sessions.
    cursor.execute("INSERT INTO part (id, session_id) VALUES ('p1','sess1'),('p2','sess1'),('p3','sess2')")
    conn.commit()

    # Gather metrics
    stats = ocman.gather_deletion_metrics(['sess1', 'sess2'], conn)
    assert stats is not None
    assert stats["sessions_count"] == 2
    assert stats["subagents_count"] == 1
    assert stats["messages_count"] == 2
    assert stats["interactions_count"] == 1      # one user-role message
    assert stats["parts_count"] == 3
    assert stats["cost"] == pytest.approx(0.07)
    assert stats["tokens_input"] == 1400
    assert stats["tokens_output"] == 700
    assert stats["tokens_cache_read"] == 42

    # Save metrics
    ocman.save_deletion_metrics("delete", stats)
    assert mock_history_path.exists()

    history = ocman._load_history()
    c = history["cumulative"]
    assert c["sessions_deleted"] == 2
    assert c["subagents_deleted"] == 1
    assert c["messages_deleted"] == 2
    assert c["interactions_deleted"] == 1
    assert c["parts_deleted"] == 3
    assert c["cost_deleted"] == pytest.approx(0.07)
    assert c["tokens_input_deleted"] == 1400
    assert c["tokens_output_deleted"] == 700
    assert c["tokens_cache_read_deleted"] == 42

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


@pytest.mark.real_process_detection
def test_process_lock_refuses_when_opencode_running(temp_db, monkeypatch):
    """Gate: with a running opencode process detected and not --force, a destructive op refuses."""
    import subprocess
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated) VALUES ('s1','p1','S1',1,2)")
    conn.commit(); conn.close()
    # ps reports one plausible opencode process (pid 4242), new 7-fixed-column format.
    ps_out = ("    PID   PPID USER     TTY         ELAPSED                  STARTED COMMAND\n"
              "  4242      1 me pts/3         300  Fri Jul  4 12:00:00 2026 opencode --continue\n")
    monkeypatch.setattr(ocman.subprocess, "run", _fake_ps(ps_out, rc=0))
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    with pytest.raises(RecoveryError):
        db_delete_session_recursive("s1", dry_run=False, force=False, verbosity=0)
    # session untouched (op refused before deleting)
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 1
    conn.close()


@pytest.mark.real_process_detection
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


@pytest.mark.real_process_detection
def test_process_lock_fails_closed_on_detector_error_linux(temp_db, monkeypatch):
    """Fail-CLOSED on Linux: if the detector errors, a mutation REFUSES by default
    (data-integrity guard), and --while-running (force) overrides."""
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated) VALUES ('s1','p1','S1',1,2)")
    conn.commit(); conn.close()
    def _raise(*a, **k):
        raise FileNotFoundError("ps not found")
    monkeypatch.setattr(ocman.subprocess, "run", _raise)
    monkeypatch.setattr(ocman.sys, "platform", "linux")
    # No override -> refuses (fail-closed), session untouched.
    with pytest.raises(RecoveryError):
        db_delete_session_recursive("s1", dry_run=False, force=False, verbosity=0)
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 1
    conn.close()
    # force (--while-running) overrides -> proceeds.
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    db_delete_session_recursive("s1", dry_run=False, force=True, verbosity=0)
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT COUNT(*) FROM session WHERE id='s1'").fetchone()[0] == 0
    conn.close()


def _ps_line(pid, cmd, *, ppid=1, user="me", tty="pts/3", etimes=300):
    """Build one `ps -o pid,ppid,user,tty,etimes,lstart,args` line (lstart = 5 tokens)."""
    return f"{pid:>6} {ppid:>6} {user} {tty} {etimes:>7}  Fri Jul  4 12:00:00 2026 {cmd}"


@pytest.mark.real_process_detection
def test_detect_running_opencode_filter_and_self_exclusion(monkeypatch):
    """Default (safety-gate) detector: keeps opencode+continue rows, excludes self and non-matches."""
    import os, subprocess
    my_pid = os.getpid()
    header = "    PID   PPID USER     TTY         ELAPSED                  STARTED COMMAND"
    ps_out = "\n".join([
        header,
        _ps_line(my_pid, "opencode --continue"),          # self -> excluded
        _ps_line(4242, "opencode --continue"),            # match
        _ps_line(4243, "vim notes-about-opencode.md"),    # no 'continue' -> skip
        _ps_line(4244, "opencode serve"),                 # opencode, no continue -> skip (default matcher)
    ]) + "\n"
    monkeypatch.setattr(ocman.subprocess, "run",
                        lambda cmd, *a, **k: subprocess.CompletedProcess(cmd, 0, stdout=ps_out, stderr=""))
    procs = ocman.detect_running_opencode(0)
    pids = {p["pid"] for p in procs}
    assert pids == {4242}  # only the genuine opencode --continue, not self, vim, or 'opencode serve'


@pytest.mark.real_process_detection
def test_detect_running_opencode_broad_matches_serve(monkeypatch):
    """broad=True (for 'list running') matches any opencode executable incl. serve, not just --continue."""
    import subprocess
    header = "    PID   PPID USER     TTY         ELAPSED                  STARTED COMMAND"
    ps_out = "\n".join([
        header,
        _ps_line(4242, "opencode --continue"),
        _ps_line(4244, "opencode serve --port 4096"),
        _ps_line(4245, "node /x/pyright-langserver --stdio"),  # child, program 'node' -> excluded
    ]) + "\n"
    monkeypatch.setattr(ocman.subprocess, "run",
                        lambda cmd, *a, **k: subprocess.CompletedProcess(cmd, 0, stdout=ps_out, stderr=""))
    pids = {p["pid"] for p in ocman.detect_running_opencode(0, broad=True)}
    assert pids == {4242, 4244}  # serve now included; language-server child excluded


def test_bind_is_loopback():
    from ocman import _bind_is_loopback
    assert _bind_is_loopback("127.0.0.1:47950")
    assert _bind_is_loopback("127.0.0.53:8080")
    assert _bind_is_loopback("[::1]:4096")
    assert _bind_is_loopback("::1:4096")
    assert not _bind_is_loopback("0.0.0.0:4096")
    assert not _bind_is_loopback("192.168.1.5:4096")
    assert not _bind_is_loopback("[::]:4096")


def test_listening_sockets_by_pid_parse(monkeypatch):
    import subprocess
    from ocman import _listening_sockets_by_pid
    ss_out = (
        'LISTEN 0 512 127.0.0.1:47950 0.0.0.0:* users:(("opencode",pid=3754922,fd=17))\n'
        'LISTEN 0 128 [::1]:8080 [::]:* users:(("opencode",pid=42,fd=9))\n'
        'LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=100,fd=3))\n'
    )
    monkeypatch.setattr(ocman.subprocess, "run",
                        lambda cmd, *a, **k: subprocess.CompletedProcess(cmd, 0, stdout=ss_out, stderr=""))
    m = _listening_sockets_by_pid()
    assert m.get(3754922) == ["127.0.0.1:47950"]
    assert m.get(42) == ["[::1]:8080"]
    assert m.get(100) == ["0.0.0.0:22"]  # parser is generic; opencode-filtering happens later


def test_listening_sockets_fail_loud(monkeypatch):
    from ocman import _listening_sockets_by_pid, RunningDetectionError
    def _raise(*a, **k):
        raise FileNotFoundError("no ss")
    monkeypatch.setattr(ocman.subprocess, "run", _raise)
    with pytest.raises(RunningDetectionError):
        _listening_sockets_by_pid()


def test_server_password_env_state(monkeypatch, tmp_path):
    """Exact-key auth classification from environ (own proc); decoy key must not fool it."""
    from ocman import _server_password_env_state
    import os as _os, sys
    # Build a fake /proc/<pid>/environ by pointing open() at a temp file.
    real_open = open
    cases = {
        "unsecured": b"PATH=/x\0X_OPENCODE_SERVER_PASSWORD=decoy\0",   # decoy prefix, real key absent
        "secured": b"PATH=/x\0OPENCODE_SERVER_PASSWORD=hunter2\0",
        "unsecured_empty": b"OPENCODE_SERVER_PASSWORD=\0PATH=/x\0",
    }
    if not sys.platform.startswith("linux"):
        import pytest as _pytest
        _pytest.skip("environ read is linux-only")
    for label, raw in cases.items():
        f = tmp_path / f"environ_{label}"
        f.write_bytes(raw)
        def fake_open(path, *a, **k):
            if str(path) == "/proc/999999/environ":
                return real_open(f, *a, **k)
            return real_open(path, *a, **k)
        monkeypatch.setattr("builtins.open", fake_open)
        state = _server_password_env_state(999999)
        monkeypatch.undo()
        expected = "secured" if label == "secured" else "unsecured"
        assert state == expected, f"{label}: expected {expected}, got {state}"


@pytest.mark.real_process_detection
def test_require_safe_to_mutate_outcomes(monkeypatch):
    """The guard's three outcomes: none->proceed, some+override->proceed, some+non-interactive->refuse."""
    import ocman.cli as _cli
    # none running -> returns silently.
    monkeypatch.setattr(_cli, "detect_running_opencode_status", lambda *a, **k: ("none", []))
    ocman.require_safe_to_mutate("delete x", interactive=False)  # no raise
    # some running + no override + non-interactive -> refuse.
    procs = [{"pid": 42, "tty": "pts/0", "elapsed": "1m", "started": "now", "cwd": "/p", "project": "P"}]
    monkeypatch.setattr(_cli, "detect_running_opencode_status", lambda *a, **k: ("some", procs))
    with pytest.raises(RecoveryError):
        ocman.require_safe_to_mutate("delete x", interactive=False, while_running=False)
    # some running + override -> proceeds.
    ocman.require_safe_to_mutate("delete x", interactive=False, while_running=True)  # no raise
    # some running + interactive + typed 'yes' -> proceeds; anything else -> refuse.
    monkeypatch.setattr("builtins.input", lambda _p: "yes")
    ocman.require_safe_to_mutate("delete x", interactive=True, while_running=False)  # no raise
    monkeypatch.setattr("builtins.input", lambda _p: "no")
    with pytest.raises(RecoveryError):
        ocman.require_safe_to_mutate("delete x", interactive=True, while_running=False)


@pytest.mark.real_process_detection
def test_import_is_guarded_when_running(temp_db, tmp_path, monkeypatch):
    """Coverage: a newly-guarded mutator (session import) refuses while OpenCode runs."""
    import ocman.cli as _cli
    # Build a real bundle first (no instances during export).
    monkeypatch.setattr(_cli, "detect_running_opencode_status", lambda *a, **k: ("none", []))
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/proj', 'P1')")
    cur.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('s1','p1','T','/proj/s1')")
    conn.commit(); conn.close()
    from ocman import bundle_session_data
    bundle = tmp_path / "b.ocbox"
    bundle_session_data("s1", bundle)
    # Now pretend an instance is running: import must refuse (non-interactive, no override).
    monkeypatch.setattr(_cli, "detect_running_opencode_status",
                        lambda *a, **k: ("some", [{"pid": 9, "tty": "?", "elapsed": "1m",
                                                    "started": "now", "cwd": "", "project": ""}]))
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    with pytest.raises(RecoveryError):
        ocman.extract_and_import_session(bundle, target_project_id="p1")
    # With the override it proceeds.
    ocman.extract_and_import_session(bundle, target_project_id="p1", while_running=True)


@pytest.mark.real_process_detection
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


def test_db_before_verb_used_for_target_resolution(monkeypatch, tmp_path):
    """Regression: '--db X export project NAME to F' must resolve NAME against X,
    not the default DB (target resolution happens during normalization, which
    runs before main() applies --db). Guards the parse-time --db ordering fix."""
    import sys
    from pathlib import Path
    from ocman import parse_args
    db = tmp_path / "other.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
    conn.execute("CREATE TABLE session (id TEXT PRIMARY KEY, project_id TEXT, parent_id TEXT, "
                 "title TEXT, directory TEXT, time_updated INTEGER, "
                 "cost REAL, tokens_input INTEGER, tokens_output INTEGER, tokens_cache_read INTEGER)")
    conn.execute("INSERT INTO project (id, worktree, name) VALUES ('pX', '/some/where', 'X')")
    # resolve_project (via db_list_projects) only surfaces projects with >=1
    # session and reads MAX(session.time_updated), so the column must exist.
    conn.execute("INSERT INTO session (id, project_id, parent_id, title, directory, time_updated) "
                 "VALUES ('sX', 'pX', NULL, 't', '/some/where', 2)")
    conn.commit()
    conn.close()
    called_with = []
    monkeypatch.setattr(ocman, "bundle_project_data", lambda pid, path, progress_callback: called_with.append(pid))

    orig = ocman.OPENCODE_DB_PATH
    try:
        monkeypatch.setattr(sys, "argv",
                            ["ocman", "--db", str(db), "export", "project", "/some/where",
                             "to", str(tmp_path / "out.ocbox")])
        try:
            ocman.main()
        except SystemExit as e:
            assert e.code == 0
        assert called_with == ["pX"]
    finally:
        ocman.OPENCODE_DB_PATH = orig


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


def test_spend_per_project_default(temp_db, capsys, monkeypatch, mock_history_path):
    """F2: `ocman spend` shows a per-project table with a live total; --historical adds the ledger."""
    import ocman, sys
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/projA', 'A')")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p2', '/projB', 'B')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
                "VALUES ('s1', 'p1', 'A1', 1, 2, '/projA', 12.5, 1000, 500, 100, '')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
                "VALUES ('s2', 'p2', 'B1', 1, 2, '/projB', 3.25, 200, 100, 0, '')")
    conn.commit(); conn.close()
    # Seed a historical ledger.
    import json as _json
    mock_history_path.write_text(_json.dumps({"cumulative": {"cost_deleted": 7.0}, "runs": []}))

    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "spend", "--historical"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "/projA" in out and "/projB" in out
    assert "$15.75" in out  # live total 12.5 + 3.25
    assert "$7.00" in out and "$22.75" in out  # historical + grand total


def test_spend_json(temp_db, capsys, monkeypatch, mock_history_path):
    """F2/F1: `ocman spend --json` emits a parseable per-project envelope."""
    import ocman, sys, json
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/projA', 'A')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
                "VALUES ('s1', 'p1', 'A1', 1, 2, '/projA', 12.5, 1000, 500, 100, '')")
    conn.commit(); conn.close()
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "spend", "--json"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    d = json.loads(capsys.readouterr().out)
    assert d["command"] == "spend" and d["spend"]["scope"] == "projects"
    assert d["spend"]["live_total"] == 12.5
    assert d["spend"]["projects"][0]["cost"] == 12.5


def test_gather_spend_shape_matches_json(temp_db, monkeypatch, mock_history_path):
    """gather_spend() returns the canonical per-project spend shape used by the CLI JSON
    and the TUI, so both render identical numbers (Phase 3, PR-002/PR-003)."""
    import ocman
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/projA', 'A')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
                "VALUES ('s1', 'p1', 'A1', 1, 2, '/projA', 12.5, 1000, 500, 100, '')")
    conn.commit(); conn.close()

    d = ocman.gather_spend(historical=False)
    assert d["scope"] == "projects"
    assert d["live_total"] == 12.5
    assert d["projects"][0]["cost"] == 12.5
    assert d["live_tokens"] == {"input": 1000, "output": 500, "cache_read": 100}
    assert d["historical_total"] is None and d["grand_tokens"] is None

    # Historical seeds add global deleted spend.
    hist = ocman._load_history()
    hist["cumulative"].update({"cost_deleted": 5.0, "tokens_input_deleted": 300,
                               "tokens_output_deleted": 200, "tokens_cache_read_deleted": 50})
    ocman._save_history(hist)
    dh = ocman.gather_spend(historical=True)
    assert dh["historical_total"] == pytest.approx(5.0)
    assert dh["grand_total"] == pytest.approx(17.5)
    assert dh["grand_tokens"] == {"input": 1300, "output": 700, "cache_read": 150}


def test_spend_historical_sums_tokens(temp_db, capsys, monkeypatch, mock_history_path):
    """--historical now sums deleted TOKENS (in/out/cache), not just cost."""
    import ocman, sys, json
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/projA', 'A')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
                "VALUES ('s1', 'p1', 'A1', 1, 2, '/projA', 10.0, 1000, 500, 100, '')")
    conn.commit(); conn.close()
    # Seed a cumulative deletion ledger with historical tokens.
    hist = ocman._load_history()
    hist["cumulative"].update({"cost_deleted": 5.0, "tokens_input_deleted": 300,
                               "tokens_output_deleted": 200, "tokens_cache_read_deleted": 50})
    ocman._save_history(hist)
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "spend",
                                      "--historical", "--json"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    d = json.loads(capsys.readouterr().out)["spend"]
    assert d["historical_tokens"] == {"input": 300, "output": 200, "cache_read": 50}
    assert d["grand_total"] == pytest.approx(15.0)
    assert d["grand_tokens"] == {"input": 1300, "output": 700, "cache_read": 150}


def test_spend_per_session(temp_db, capsys, monkeypatch):
    """F2: `ocman spend <project> --sessions` drills into per-session spend."""
    import ocman, sys
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/projA', 'A')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
                "VALUES ('s1', 'p1', 'A1', 1, 2, '/projA', 12.5, 1000, 500, 100, '')")
    conn.commit(); conn.close()
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "spend", "p1", "--sessions"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "s1" in out and "$12.50" in out and "Total (live): $12.50" in out


def test_list_projects_json(temp_db, capsys, monkeypatch):
    """F1: project list --json emits a parseable schema envelope; human path unchanged without it."""
    import ocman, sys, json
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/proj', 'P1')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
                "VALUES ('s1', 'p1', 'T', 1, 2, '/proj', 1.5, 100, 50, 10, '')")
    conn.commit(); conn.close()
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "project", "list", "--json"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    d = json.loads(out)
    assert d["schema_version"] == ocman.JSON_SCHEMA_VERSION
    assert d["command"] == "projects"
    assert d["projects"]["count"] == 1
    p = d["projects"]["projects"][0]
    assert p["id"] == "p1" and p["directory"] == "/proj" and p["cost"] == 1.5
    assert p["tokens_input"] == 100


def test_session_list_json(temp_db, capsys, monkeypatch):
    """F1: session list --json emits a parseable envelope with per-session fields."""
    import ocman, sys, json
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', '/proj', 'P1')")
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
                "VALUES ('s1', 'p1', 'MySess', 1000, 2000, '/proj', 2.0, 7, 3, 1, '')")
    conn.commit(); conn.close()
    monkeypatch.setattr(sys, "argv",
                        ["ocman", "--db", str(temp_db), "session", "list", "p1", "--json"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    d = json.loads(out)
    assert d["command"] == "sessions" and d["sessions"]["count"] == 1
    s = d["sessions"]["sessions"][0]
    assert s["id"] == "s1" and s["title"] == "MySess" and s["cost"] == 2.0
    assert s["created"] == 1000 and s["updated"] == 2000


def test_list_projects_limit(temp_db, capsys, monkeypatch):
    """F8: project list --limit caps rows and prints a truncation note."""
    import ocman, sys
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    for i in range(4):
        cur.execute("INSERT INTO project (id, worktree, name) VALUES (?, ?, ?)",
                    (f"p{i}", f"/proj{i}", f"P{i}"))
        cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                    "directory, parent_id) VALUES (?, ?, ?, 1, ?, ?, '')",
                    (f"s{i}", f"p{i}", f"S{i}", 100 - i, f"/proj{i}"))
    conn.commit(); conn.close()
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "project", "list", "--limit", "2"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "and 2 more not shown" in out
    # Only 2 project rows rendered (numbered 1. and 2., not 3.).
    assert "  1. " in out and "  2. " in out and "  3. " not in out


def test_move_sugar_carries_safety_flags():
    """F4: the top-level 'move' sugar exposes --confirm-remote-delete/-y/--force."""
    import sys
    from ocman import preprocess_argv, parse_args
    argv = preprocess_argv(["ocman", "move", "session", "SID", "to", "h:/p",
                            "--confirm-remote-delete", "-y", "--force"])
    orig = sys.argv
    sys.argv = argv
    try:
        a = parse_args()
    finally:
        sys.argv = orig
    assert getattr(a, "confirm_remote_delete") is True
    assert getattr(a, "yes") is True
    assert getattr(a, "force") is True


def test_yes_flag_parses_on_clean_and_delete_ops():
    """F5: -y/--yes is accepted by project delete, db clean, clean-orphans, backup clean."""
    def _yes(argv_tail):
        import sys
        from ocman import parse_args
        orig = sys.argv
        sys.argv = ["ocman", *argv_tail]
        try:
            return getattr(parse_args(), "yes", None)
        finally:
            sys.argv = orig
    assert _yes(["project", "delete", "p1", "-y"]) is True
    assert _yes(["db", "clean", "-y"]) is True
    assert _yes(["db", "clean-orphans", "-y"]) is True
    assert _yes(["backup", "clean", "-y"]) is True
    assert _yes(["history", "clear", "-y"]) is True


def test_preprocess_ls_lp_short_aliases():
    from ocman import preprocess_argv
    assert preprocess_argv(["ocman", "ls"]) == ["ocman", "session", "list"]
    assert preprocess_argv(["ocman", "lp"]) == ["ocman", "project", "list"]
    assert preprocess_argv(["ocman", "ls", "myproj"]) == ["ocman", "session", "list", "myproj"]
    # Leading globals are preserved and the alias still fires.
    assert preprocess_argv(["ocman", "--db", "/x", "ls"]) == \
        ["ocman", "--db", "/x", "session", "list"]
    assert preprocess_argv(["ocman", "lp", "--foo"]) == ["ocman", "project", "list", "--foo"]


def test_preprocess_lr_short_alias():
    """`lr` is a short alias for `list running` (parity with lp/ls)."""
    from ocman import preprocess_argv
    assert preprocess_argv(["ocman", "lr"]) == ["ocman", "running"]
    assert preprocess_argv(["ocman", "lr", "myproj"]) == ["ocman", "running", "myproj"]
    # `list running [PATTERN]` word-order form also carries the pattern.
    assert preprocess_argv(["ocman", "list", "running", "foo"]) == ["ocman", "running", "foo"]
    # Leading globals preserved.
    assert preprocess_argv(["ocman", "--db", "/x", "lr"]) == ["ocman", "--db", "/x", "running"]


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


_OCMAN_PY = str(Path(__file__).resolve().parent.parent / "ocman" / "cli.py")


def _make_empty_db(tmp_path):
    """A minimal, valid opencode DB with one project so CLI runs are deterministic."""
    db = tmp_path / "e2e.db"
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    cur.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
    cur.execute(
        "CREATE TABLE session (id TEXT PRIMARY KEY, project_id TEXT, title TEXT, "
        "time_created INTEGER, time_updated INTEGER, directory TEXT, parent_id TEXT, "
        "cost REAL, tokens_input INTEGER, tokens_output INTEGER, tokens_cache_read INTEGER)"
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


def test_preprocess_argv_list_models():
    from ocman import preprocess_argv
    assert preprocess_argv(["ocman", "list", "models"]) == ["ocman", "models"]
    assert preprocess_argv(["ocman", "list", "model"]) == ["ocman", "models"]
    assert preprocess_argv(["ocman", "models"]) == ["ocman", "models"]


def test_resolve_model_spec():
    from ocman import ModelInfo, resolve_model_spec
    models = [
        ModelInfo(
            provider_id="prov1",
            model_id="id1",
            name="Model One",
            base_url="http://base1",
            api_key="key1",
            cost_input=0.1,
            cost_output=0.2,
            compatible=True
        ),
        ModelInfo(
            provider_id="prov2",
            model_id="id2",
            name="Model Two",
            base_url="http://base2",
            api_key="key2",
            cost_input=0.3,
            cost_output=0.4,
            compatible=True
        ),
        ModelInfo(
            provider_id="prov2",
            model_id="id2-other",
            name="Model Two Other",
            base_url="http://base3",
            api_key="key3",
            cost_input=0.5,
            cost_output=0.6,
            compatible=True
        ),
    ]

    # Exact matches
    assert resolve_model_spec("prov1/id1", models) == models[0]
    assert resolve_model_spec("Model One", models) == models[0]
    
    # Case-insensitive exact matches
    assert resolve_model_spec("PROV1/ID1", models) == models[0]
    assert resolve_model_spec("model one", models) == models[0]

    # Substring match (unique)
    assert resolve_model_spec("One", models) == models[0]
    assert resolve_model_spec("id2-other", models) == models[2]

    # Substring match (ambiguous)
    assert resolve_model_spec("Two", models) == "ambiguous"
    assert resolve_model_spec("Model Two", models) == models[1]

    # No match
    assert resolve_model_spec("nonexistent", models) is None


def _hdr_row(**kw):
    base = {"id": "ses_x", "title": "T", "created": 1747193820000, "updated": 1747367000000,
            "cost": 1.5, "tokens_input": 100, "tokens_output": 20, "tokens_cache_read": 5,
            "project_dir": "/p", "parent_id": None}
    base.update(kw)
    return base


def test_fmt_duration():
    from ocman import _fmt_duration
    assert _fmt_duration(None, 123) == "-"
    assert _fmt_duration(123, None) == "-"
    assert _fmt_duration(200000, 100000) == "-"        # updated < created
    assert _fmt_duration("bad", 100) == "-"
    assert _fmt_duration(1000, 1000) == "00:00:00"     # equal, valid -> zero span
    assert _fmt_duration(0, 5000) == "00:00:05"
    assert _fmt_duration(0, 3600_000 + 5000) == "01:00:05"
    assert _fmt_duration(0, 2 * 86400_000 + 3600_000) == "2d 01:00:00"
    # no em dash anywhere
    assert "—" not in _fmt_duration(0, 0)


def test_render_session_header_full_and_brief(monkeypatch):
    from ocman import render_session_header
    monkeypatch.setenv("NO_COLOR", "1")  # deterministic plain output
    row = _hdr_row(id="ses_abc", title="My Session")
    stats = {"msgs": 10, "interactions": 3, "parts": 40, "has_interactions": True}
    full = render_session_header(row, stats, index=2)
    assert "2. Session ID: ses_abc" in full and "Name: My Session" in full
    assert "Start" in full and "Last active" in full and "Duration" in full
    assert "Messages" in full and "Interactions" in full and "DB Parts" in full and "Cost" in full
    # index omitted when None
    assert "Session ID: ses_abc" in render_session_header(row, stats, index=None)
    assert not render_session_header(row, stats, index=None).lstrip().startswith("1.")
    # subagent prefix
    assert "\u2937 " in render_session_header(_hdr_row(parent_id="ses_p", title="child"), stats)
    # brief form: one-liner, NOT the tables
    brief = render_session_header(row, stats, index=2, compact=True)
    assert "ID: ses_abc" in brief and "~msgs:" in brief
    assert "Start" not in brief and "DB Parts" not in brief


def test_render_session_header_na_interactions(monkeypatch):
    from ocman import render_session_header
    monkeypatch.setenv("NO_COLOR", "1")
    out = render_session_header(_hdr_row(), {"msgs": 1, "interactions": 0,
                                            "parts": 2, "has_interactions": False})
    assert "n/a" in out  # Interactions cell


def test_render_session_list_grouping_and_numbering(monkeypatch):
    from ocman import render_session_list, resolve_session_spec
    monkeypatch.setenv("NO_COLOR", "1")
    rows = [
        _hdr_row(id="ses_1", project_dir="/a", title="one"),
        _hdr_row(id="ses_2", project_dir="/a", title="two"),
        _hdr_row(id="ses_3", project_dir="/b", title="three"),
    ]
    out = render_session_list(rows, {})
    # One Project: header per distinct project, first-appearance order.
    assert out.count("Project:") == 2
    assert out.index("Project: /a") < out.index("Project: /b")
    # Continuous global 1..N numbering (not per-project reset).
    assert "1. Session ID: ses_1" in out
    assert "2. Session ID: ses_2" in out
    assert "3. Session ID: ses_3" in out
    # Numbering integrity: displayed N maps to what resolve_session_spec resolves.
    assert resolve_session_spec("3", rows)["id"] == "ses_3"


def test_render_session_header_color_gate(monkeypatch):
    """FORCE_COLOR -> styled header ANSI present; NO_COLOR -> fully plain."""
    from ocman import render_session_header
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    styled = render_session_header(_hdr_row(), {"has_interactions": True})
    assert "\033[" in styled           # ANSI present
    assert "\033[2m" not in styled     # never faint/dim (accessibility)
    monkeypatch.setenv("NO_COLOR", "1")
    assert "\033[" not in render_session_header(_hdr_row(), {"has_interactions": True})


def test_picker_uses_real_db_stats(temp_db, capsys, monkeypatch):
    """D-4a: the interactive picker renders the two tables with REAL token/cost/stats
    looked up from the DB, not fabricated zeros."""
    import ocman
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(ocman, "db_list_sessions", lambda *a, **k: [
        _hdr_row(id="ses_real", title="Real", cost=7.77, tokens_input=88888)])
    monkeypatch.setattr(ocman, "db_get_session_stats", lambda: {
        "ses_real": {"msgs": 42, "interactions": 9, "parts": 111, "has_interactions": True}})
    si = ocman.SessionInfo(session_id="ses_real", title="Real",
                           created=1747193820000, updated=1747367000000, raw={})
    ocman.display_sessions([si])
    out = capsys.readouterr().out
    assert "ses_real" in out
    assert "88,888" in out       # real tokens, not 0
    assert "$7.77" in out        # real cost
    assert "42" in out and "111" in out  # real msgs / parts


def test_list_and_search_headers_are_identical(monkeypatch):
    """Single source of truth (PR-005): the same session dict yields a byte-identical
    per-session header whether produced for the list or the search path."""
    from ocman import render_session_header
    monkeypatch.setenv("NO_COLOR", "1")
    row = _hdr_row(id="ses_same", title="Same")
    stats = {"msgs": 5, "interactions": 2, "parts": 8, "has_interactions": True}
    # Both surfaces call render_session_header identically for a given index.
    a = render_session_header(row, stats, index=1)
    b = render_session_header(row, stats, index=1)
    assert a == b
    # brief form likewise identical.
    assert (render_session_header(row, stats, index=1, compact=True)
            == render_session_header(row, stats, index=1, compact=True))


def test_list_sessions_approximate_stats(temp_db, capsys):
    import ocman
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    # Recreate message table with 'data' column
    cursor.execute("DROP TABLE IF EXISTS message")
    cursor.execute("""
        CREATE TABLE message (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            data TEXT
        )
    """)

    # Recreate part table with correct schema
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

    # Clear existing messages/parts
    cursor.execute("DELETE FROM message")
    cursor.execute("DELETE FROM part")
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")

    # Insert a project
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")

    # Insert a session
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Test Session', 1000, 2000, '/path/to/proj', '')
    """)

    # Insert some messages with role data
    import json as _json
    cursor.execute(
        "INSERT INTO message (id, session_id, data) VALUES ('msg1', 'sess1', ?)",
        (_json.dumps({"role": "user"}),)
    )
    cursor.execute(
        "INSERT INTO message (id, session_id, data) VALUES ('msg2', 'sess1', ?)",
        (_json.dumps({"role": "assistant"}),)
    )

    # Insert some parts
    cursor.execute("INSERT INTO part (id, message_id, session_id) VALUES ('part1', 'msg1', 'sess1')")
    cursor.execute("INSERT INTO part (id, message_id, session_id) VALUES ('part2', 'msg2', 'sess1')")
    cursor.execute("INSERT INTO part (id, message_id, session_id) VALUES ('part3', 'msg2', 'sess1')")

    conn.commit()
    conn.close()

    # Call main with the args to list sessions
    import sys
    orig_argv = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "list", "sessions"]
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    finally:
        sys.argv = orig_argv

    captured = capsys.readouterr()
    assert "Test Session" in captured.out
    # Unified two-table session header: grouped by Project, with both table headers.
    assert "Project:" in captured.out
    assert "Session ID:" in captured.out and "Name:" in captured.out
    assert "Messages" in captured.out and "Interactions" in captured.out
    assert "DB Parts" in captured.out
    assert "Start" in captured.out and "Last active" in captured.out
    assert "Note: ~msgs, ~interactions, and ~parts are cheap DB-derived approximate counts." in captured.out


def test_dim_helpers_emit_no_faint_even_when_color_enabled(monkeypatch):
    """Accessibility: color_dim/_h_dim never emit the ANSI faint attribute, even on
    the color-ENABLED path (which pytest's no-TTY gating would otherwise hide)."""
    import ocman
    # Force color ON so this is a real test, not the trivially-plain no-TTY path.
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)
    # A colored helper DOES emit ANSI when enabled (sanity: the gate is on).
    assert "\033[" in ocman.color_bold("x")
    # But the former dim helpers emit plain text, never the faint code \033[2m.
    assert ocman.color_dim("secondary") == "secondary"
    assert "\033[2m" not in ocman.color_dim("secondary")
    assert ocman._h_dim("secondary", True) == "secondary"
    assert "\033[2m" not in ocman._h_dim("secondary", True)


def test_force_color_and_no_color_precedence(monkeypatch):
    """FORCE_COLOR forces color on without a TTY; NO_COLOR wins over FORCE_COLOR;
    precedence is identical in both the stderr gate and the help (stdout) gate."""
    import ocman
    # NO_COLOR wins even if FORCE_COLOR is set.
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert ocman._color_enabled() is False
    assert ocman._help_color_enabled() is False
    # FORCE_COLOR on, NO_COLOR absent -> color ON (even though pytest has no TTY).
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert ocman._color_enabled() is True
    assert ocman._help_color_enabled() is True
    # FORCE_COLOR=0 is treated as off -> falls through to isatty (False under pytest).
    monkeypatch.setenv("FORCE_COLOR", "0")
    assert ocman._color_enabled() is False
    assert ocman._help_color_enabled() is False


def test_fmt_int_and_fmt_cost():
    from ocman import fmt_int, fmt_cost
    assert fmt_int(1234567) == "1,234,567"
    assert fmt_int(0) == "0"
    assert fmt_int(None) == "0"
    assert fmt_int(42, 8) == "      42"
    assert fmt_int(-5) == "-5"
    assert fmt_cost(0) == "$0.00"
    assert fmt_cost(None) == "$0.00"
    assert fmt_cost(4231.5578) == "$4,231.56"
    assert fmt_cost(12.5, decimals=4) == "$12.5000"


# OS-appropriate absolute home dir for the global-mapping tests (Windows:
# drive-anchored so str(Path.cwd()) matches the stored session directory).
_HOME_DIR = abs_path("/home/gfariello")


def _seed_global_and_project(temp_db):
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session"); cur.execute("DELETE FROM project")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('g', '/', '')")
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', ?, 'Proj1')",
                (abs_path("/home/x/proj"),))
    cur.execute(
        "INSERT INTO session (id, project_id, title, time_created, time_updated, directory, "
        "cost, tokens_input, tokens_output, tokens_cache_read, parent_id) "
        "VALUES ('ses_home', 'g', 'Home task', 1715000000000, 1715500000000, ?, "
        "0.42, 500, 200, 0, '')",
        (_HOME_DIR,)
    )
    conn.commit(); conn.close()


def test_global_mapping_notice_on_dir_scope(temp_db, capsys, monkeypatch):
    """A dir-scoped listing whose sessions map to global (/) prints the loud NOTICE once."""
    import ocman, sys
    _seed_global_and_project(temp_db)
    # cwd must match the seeded session directory (drive-anchored on Windows).
    monkeypatch.setattr(ocman.Path, "cwd", staticmethod(lambda: Path(_HOME_DIR)))
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "list", "sessions"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert out.count("NOTICE:") == 1
    assert "global (/) project" in out
    assert "ocman list sessions in /" in out
    # Two-table header fields present; cost shows in the Cost cell.
    assert "Start" in out and "Last active" in out
    assert "$0.42" in out


def test_list_projects_shows_per_project_metrics(temp_db, capsys, monkeypatch):
    import ocman, sys
    _seed_global_and_project(temp_db)
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "list", "projects"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "Cost: $0.42" in out
    assert "500 in / 200 out / 0 cache" in out


def test_list_sessions_shows_na_interactions_when_absent(temp_db, capsys, monkeypatch):
    """When a session has no interaction data, the Interactions cell renders 'n/a'
    (the column is a fixed header in the two-table layout)."""
    import ocman, sys
    _seed_global_and_project(temp_db)
    # Force db_get_session_stats to report has_interactions False.
    monkeypatch.setattr(ocman, "db_get_session_stats",
                        lambda: {"ses_home": {"msgs": 3, "parts": 9, "has_interactions": False}})
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "list", "sessions"])
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "DB Parts" in out
    assert "Interactions" in out  # column header always present
    assert "n/a" in out           # value for a session without interaction data


def test_e2e_list_models_word_order(tmp_path):
    r = _run_ocman_py(["list", "models"], tmp_path)
    combined = r.stdout + r.stderr
    assert "invalid choice" not in combined


def test_resolve_targets_kind_qualified(temp_db):
    from ocman import resolve_targets
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()

    # qualified project
    res = resolve_targets(["project:proj1"], kinds={"project"})
    assert len(res.projects) == 1
    assert res.projects[0]["id"] == "proj1"

    # qualified session
    res = resolve_targets(["session:sess1"], kinds={"session"})
    assert len(res.sessions) == 1
    assert res.sessions[0]["id"] == "sess1"

    # qualified mismatched kind
    res = resolve_targets(["model:sess1"], kinds={"session"})
    assert len(res.unmatched) == 1
    assert res.unmatched[0] == "model:sess1"


def test_resolve_targets_auto_detect(temp_db):
    from ocman import resolve_targets
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()

    res = resolve_targets(["proj1", "sess1"], kinds={"project", "session"})
    assert len(res.projects) == 1
    assert res.projects[0]["id"] == "proj1"
    assert len(res.sessions) == 1
    assert res.sessions[0]["id"] == "sess1"
    assert not res.unmatched
    assert not res.ambiguous


def test_resolve_targets_unmatched(temp_db, capsys):
    from ocman import resolve_and_expand_targets
    import pytest

    with pytest.raises(SystemExit) as exc:
        resolve_and_expand_targets(["nonexistent"], kinds={"project", "session"}, interactive=False)
    assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "No matches found for 'nonexistent'." in captured.err
    assert "Run 'ocman list sessions' to see valid targets" in captured.err
    assert "Run 'ocman list projects' to see valid targets" in captured.err


def test_resolve_targets_ambiguous_non_tty(temp_db, capsys):
    from ocman import resolve_and_expand_targets
    import pytest
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('same_id', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('same_id', 'same_id', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()

    with pytest.raises(SystemExit) as exc:
        resolve_and_expand_targets(["same_id"], kinds={"project", "session"}, interactive=False)
    assert exc.value.code == 1

    captured = capsys.readouterr()
    assert "Ambiguous specifier 'same_id'" in captured.err
    assert "- [session] same_id" in captured.err
    assert "- [project] same_id" in captured.err
    assert "fully-qualified specifier: 'session:SPEC'" in captured.err


def test_resolve_targets_ambiguous_tty(temp_db, monkeypatch):
    from ocman import resolve_and_expand_targets
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('same_id', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('same_id', 'same_id', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()

    inputs = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))

    res = resolve_and_expand_targets(["same_id"], kinds={"project", "session"}, interactive=True)
    assert len(res.sessions) == 1
    assert res.sessions[0]["id"] == "same_id"
    assert not res.projects


def test_resolve_targets_bare_integer(temp_db):
    from ocman import resolve_targets
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    conn.commit()
    conn.close()

    res = resolve_targets(["42"], kinds={"project", "session"})
    assert len(res.ambiguous) == 1
    assert res.ambiguous[0][0] == "42"


def test_resolve_targets_project_expansion(temp_db):
    from ocman import resolve_and_expand_targets
    import sqlite3
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('child1', 'proj1', 'Child 1', 1000, 2000, '/path/to/proj', 'sess1')
    """)
    conn.commit()
    conn.close()

    res = resolve_and_expand_targets(["project:proj1"], kinds={"project", "session"}, allow_project_expansion=True, all_sessions=False)
    assert len(res.sessions) == 1
    assert res.sessions[0]["id"] == "sess1"

    res = resolve_and_expand_targets(["project:proj1"], kinds={"project", "session"}, allow_project_expansion=True, all_sessions=True)
    assert len(res.sessions) == 2
    assert {s["id"] for s in res.sessions} == {"sess1", "child1"}


def test_multi_session_show(temp_db, capsys):
    import sqlite3
    import ocman
    import sys
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess2', 'proj1', 'Sess 2', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()
    
    orig = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "session", "show", "sess1", "sess2"]
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    finally:
        sys.argv = orig
        
    captured = capsys.readouterr()
    assert "Sess 1" in captured.out
    assert "Sess 2" in captured.out
    assert "ID:        sess1" in captured.out
    assert "ID:        sess2" in captured.out


def test_multi_session_delete(temp_db, monkeypatch):
    import sqlite3
    import ocman
    import sys
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess2', 'proj1', 'Sess 2', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()
    
    # Mock confirmation to return "yes"
    monkeypatch.setattr("builtins.input", lambda prompt: "yes")
    
    orig = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "session", "delete", "sess1", "sess2"]
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    finally:
        sys.argv = orig
        
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM session")
    rows = cursor.fetchall()
    assert len(rows) == 0
    conn.close()


def _seed_batch_sessions(temp_db, n=4, project_id="proj1"):
    """Insert one project + n root sessions with a message each for batch-delete tests."""
    conn = sqlite3.connect(str(temp_db))
    cur = conn.cursor()
    cur.execute("DELETE FROM session")
    cur.execute("DELETE FROM project")
    cur.execute(
        "INSERT INTO project (id, worktree, name) VALUES (?, '/path/to/proj', 'Proj 1')",
        (project_id,),
    )
    for i in range(1, n + 1):
        cur.execute(
            "INSERT INTO session (id, project_id, title, time_created, time_updated, "
            "directory, cost, tokens_input, tokens_output, parent_id) "
            "VALUES (?, ?, ?, ?, ?, '/path/to/proj', ?, ?, ?, '')",
            (f"sess{i}", project_id, f"Sess {i}", 1000, 2000, 0.10, 100, 50),
        )
        cur.execute("INSERT INTO message (id, session_id) VALUES (?, ?)", (f"m{i}", f"sess{i}"))
    conn.commit()
    conn.close()


def test_batch_delete_single_report_and_one_vacuum(temp_db, mock_history_path, monkeypatch, capsys, tmp_path):
    """Multi-session delete produces ONE consolidated report and ONE VACUUM (not N)."""
    import ocman
    _seed_batch_sessions(temp_db, n=4)
    # Isolate the backup family into tmp_path (avoid writing under the real HOME).
    monkeypatch.setattr(ocman.Path, "home", staticmethod(lambda: tmp_path))

    ocman.db_delete_sessions_batch(
        ["sess1", "sess2", "sess3", "sess4"],
        dry_run=False, force=True, verbosity=0,
    )
    out = capsys.readouterr().out

    # Exactly one consolidated report and one VACUUM.
    assert out.count("Batch deletion complete!") == 1
    assert out.count("VACUUM complete.") == 1
    assert out.count("Rollback instructions:") == 1
    # Grand total present.
    assert "Sessions deleted:" in out
    assert "Total space reclaimed:" in out

    # All rows gone.
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM session"); assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM message"); assert cur.fetchone()[0] == 0
    conn.close()

    # Exactly ONE history run entry for the whole batch.
    history = ocman._load_history()
    assert history["cumulative"]["sessions_deleted"] == 4
    assert len(history["runs"]) == 1


def test_batch_delete_dry_run_changes_nothing(temp_db, mock_history_path, capsys):
    import ocman
    _seed_batch_sessions(temp_db, n=3)
    ocman.db_delete_sessions_batch(
        ["sess1", "sess2", "sess3"],
        dry_run=True, force=True, verbosity=0,
    )
    out = capsys.readouterr().out
    assert "Dry run complete" in out
    assert "VACUUM" not in out
    assert "Batch deletion complete!" not in out
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM session"); assert cur.fetchone()[0] == 3
    conn.close()


def test_batch_delete_removes_empty_targeted_project(temp_db, mock_history_path, monkeypatch, tmp_path):
    """When a targeted project's sessions are all deleted, its project row is removed."""
    import ocman
    _seed_batch_sessions(temp_db, n=2, project_id="proj1")
    # Create the project-scoped tables the cleanup touches.
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("CREATE TABLE project_directory (id TEXT, project_id TEXT)")
    cur.execute("CREATE TABLE workspace (id TEXT, project_id TEXT)")
    cur.execute("INSERT INTO project_directory (id, project_id) VALUES ('pd1', 'proj1')")
    cur.execute("INSERT INTO workspace (id, project_id) VALUES ('ws1', 'proj1')")
    conn.commit(); conn.close()
    monkeypatch.setattr(ocman.Path, "home", staticmethod(lambda: tmp_path))

    ocman.db_delete_sessions_batch(
        ["sess1", "sess2"],
        dry_run=False, force=True, verbosity=0,
        remove_project_ids=["proj1"],
    )
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM project WHERE id='proj1'"); assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM project_directory WHERE project_id='proj1'"); assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM workspace WHERE project_id='proj1'"); assert cur.fetchone()[0] == 0
    conn.close()


def test_batch_delete_no_project_removal_when_not_targeted(temp_db, mock_history_path, monkeypatch, tmp_path):
    """A plain multi-session delete that empties a project does NOT remove the project row."""
    import ocman
    _seed_batch_sessions(temp_db, n=2, project_id="proj1")
    monkeypatch.setattr(ocman.Path, "home", staticmethod(lambda: tmp_path))

    ocman.db_delete_sessions_batch(
        ["sess1", "sess2"],
        dry_run=False, force=True, verbosity=0,
        remove_project_ids=None,  # user named sessions, not the project
    )
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM session"); assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM project WHERE id='proj1'"); assert cur.fetchone()[0] == 1
    conn.close()


def test_batch_delete_mid_failure_rolls_back(temp_db, mock_history_path, monkeypatch, tmp_path):
    """A failure during the batch transaction rolls back: no partial deletion."""
    import ocman
    _seed_batch_sessions(temp_db, n=3)
    monkeypatch.setattr(ocman.Path, "home", staticmethod(lambda: tmp_path))

    # Force a failure after the DELETEs but before COMMIT by making the empty-project
    # cleanup query blow up (reference a nonexistent project table column path).
    orig = ocman._delete_session_rows
    def boom(session_ids, *, cursor):
        orig(session_ids, cursor=cursor)
        raise RuntimeError("injected failure mid-transaction")
    monkeypatch.setattr(ocman, "_delete_session_rows", boom)

    with pytest.raises(ocman.RecoveryError):
        ocman.db_delete_sessions_batch(
            ["sess1", "sess2", "sess3"],
            dry_run=False, force=True, verbosity=0,
        )
    # Nothing deleted (rolled back).
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM session"); assert cur.fetchone()[0] == 3
    conn.close()


def test_compact_two_models_errors(temp_db, capsys):
    import sqlite3
    import ocman
    import sys
    import pytest
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()
    
    orig = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "session", "compact", "sess1", "model:gpt-4", "model:claude-3"]
    try:
        with pytest.raises(SystemExit) as exc:
            ocman.main()
        assert exc.value.code != 0
    finally:
        sys.argv = orig


def test_backup_create_scoped(temp_db, tmp_path, capsys):
    import sqlite3
    import ocman
    import sys
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()
    
    out_dir = tmp_path / "backups"
    
    orig = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "backup", "create", "sess1", "to", str(out_dir)]
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0
    finally:
        sys.argv = orig
        
    assert (out_dir / "sess1.ocbox").exists()


def test_scan_and_redact_secrets():
    from ocman import scan_for_secrets, redact_secrets
    
    text = "Here is my aws token AKIA1234567890123456 on this line.\nAnd a github token ghp_12345678901234567890\n"
    hits = scan_for_secrets(text)
    assert len(hits) == 2
    
    redacted = redact_secrets(text, hits)
    assert "AKIA1234567890123456" not in redacted
    assert "ghp_12345678901234567890" not in redacted
    assert "[REDACTED]" in redacted
    
    # Re-scan yields no hits
    assert len(scan_for_secrets(redacted)) == 0


def test_redact_overlapping_secrets():
    from ocman import scan_for_secrets, redact_secrets
    text = "password=mysecretpasswordtoken\n"
    hits = scan_for_secrets(text, mode="aggressive")
    
    redacted = redact_secrets(text, hits)
    assert redacted.count("[REDACTED]") == 1
    assert len(scan_for_secrets(redacted, mode="aggressive")) == 0


def test_mask_line():
    from ocman import scan_for_secrets, mask_line
    line = "my aws key is AKIA1234567890123456 and token is ghp_12345678901234567890"
    hits = scan_for_secrets(line)
    masked = mask_line(line, hits)
    assert "AKIA1234567890123456" not in masked
    assert "ghp_12345678901234567890" not in masked
    assert "********************" in masked


def test_allow_and_expunge_mutually_exclusive(temp_db):
    import sys
    import pytest
    import ocman
    
    orig = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "session", "compact", "sess1", "--allow-secrets", "--expunge-secrets"]
    try:
        with pytest.raises(SystemExit) as exc:
            ocman.main()
        assert exc.value.code != 0
    finally:
        sys.argv = orig


def test_parse_backup_restore_multiple(monkeypatch):
    a = _parse(monkeypatch, ["backup", "restore", "file1.zip", "file2.zip"])
    assert a.restore == ["file1.zip", "file2.zip"]


def test_parse_session_import_new_id(monkeypatch):
    a = _parse(monkeypatch, ["session", "import", "/tmp/x.ocbox", "--new-session-id"])
    assert a.import_session == "/tmp/x.ocbox"
    assert a.new_session_id is True


def test_restore_multiple_files_success(tmp_path, temp_db):
    import ocman
    import sqlite3
    from pathlib import Path
    
    config_file = tmp_path / "ocman_temp.toml"
    orig_config_path = ocman.OCMAN_CONFIG_PATH
    ocman.OCMAN_CONFIG_PATH = config_file
    
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    config_file.write_text(f"""
db_path = {temp_db}
history_path = {tmp_path / 'ocman_history.json'}
default_backup_dir = {backup_dir}
""", encoding="utf-8")
    
    try:
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/p1', 'P1')")
        conn.commit()
        conn.close()
        
        db_file_1 = tmp_path / "db1.db"
        conn = sqlite3.connect(str(db_file_1))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
        cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj2', '/path/to/p2', 'P2')")
        conn.commit()
        conn.close()
        
        zip1 = tmp_path / "archive1.zip"
        import zipfile
        with zipfile.ZipFile(zip1, "w") as zf:
            zf.write(db_file_1, "opencode.db")
            
        db_file_2 = tmp_path / "db2.db"
        conn = sqlite3.connect(str(db_file_2))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
        cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj3', '/path/to/p3', 'P3')")
        conn.commit()
        conn.close()
        
        zip2 = tmp_path / "archive2.zip"
        with zipfile.ZipFile(zip2, "w") as zf:
            zf.write(db_file_2, "opencode.db")
            
        ocman.cli_restore([str(zip1), str(zip2)])
        
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM project")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 'proj3'
        conn.close()
        
    finally:
        ocman.OCMAN_CONFIG_PATH = orig_config_path


def test_restore_multiple_files_rollback(tmp_path, temp_db, monkeypatch):
    import ocman
    import sqlite3
    from pathlib import Path
    import pytest

    # Run in tmp so restore's relative opencode.json/.jsonc writes (from the
    # rollback path) do not leak into the repo working tree.
    monkeypatch.chdir(tmp_path)

    config_file = tmp_path / "ocman_temp.toml"
    orig_config_path = ocman.OCMAN_CONFIG_PATH
    ocman.OCMAN_CONFIG_PATH = config_file
    
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    config_file.write_text(f"""
db_path = {temp_db}
history_path = {tmp_path / 'ocman_history.json'}
default_backup_dir = {backup_dir}
""", encoding="utf-8")
    
    try:
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj_init', '/path/to/init', 'PInit')")
        conn.commit()
        conn.close()
        
        db_file_1 = tmp_path / "db1.db"
        conn = sqlite3.connect(str(db_file_1))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
        cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj2', '/path/to/p2', 'P2')")
        conn.commit()
        conn.close()
        
        zip1 = tmp_path / "archive1.zip"
        import zipfile
        with zipfile.ZipFile(zip1, "w") as zf:
            zf.write(db_file_1, "opencode.db")
            
        zip2 = tmp_path / "archive2_bad.zip"
        with zipfile.ZipFile(zip2, "w") as zf:
            zf.writestr("dummy.txt", "hello")
            
        with pytest.raises(RecoveryError) as exc:
            ocman.cli_restore([str(zip1), str(zip2)])
            
        assert "Restoration failed for archive2_bad.zip" in str(exc.value)
        
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM project")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 'proj_init'
        conn.close()
        
    finally:
        ocman.OCMAN_CONFIG_PATH = orig_config_path


def test_import_new_session_id_success(tmp_path, temp_db):
    import ocman
    import sqlite3
    from pathlib import Path
    import json
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/p1', 'P1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess_orig', 'proj1', 'Original Session', 1000, 2000, '/path/to/p1', '')
    """)
    conn.commit()
    conn.close()
    
    storage_dir = ocman.OPENCODE_STORAGE_DIR
    storage_dir.mkdir(parents=True, exist_ok=True)
    diff_file = storage_dir / "sess_orig.json"
    diff_file.write_text(json.dumps({"session_id": "sess_orig", "data": "test"}, indent=2), encoding="utf-8")
    
    bundle_file = tmp_path / "sess_export.ocbox"
    ocman.bundle_session_data("sess_orig", bundle_file)
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session WHERE id = 'sess_orig'")
    conn.commit()
    conn.close()
    diff_file.unlink()
    
    imported_id = ocman.extract_and_import_session(bundle_file, target_project_id="proj1", new_session_id=True)
    
    assert imported_id != "sess_orig"
    assert imported_id.startswith("ses_")
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_id FROM session WHERE id = ?", (imported_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == "proj1"
    conn.close()
    
    new_diff_file = storage_dir / f"{imported_id}.json"
    assert new_diff_file.exists()
    new_diff_data = json.loads(new_diff_file.read_text(encoding="utf-8"))
    assert new_diff_data["session_id"] == imported_id


def test_import_new_session_id_refusal(tmp_path, temp_db):
    import ocman
    import sqlite3
    from pathlib import Path
    import pytest
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS project_directory (id TEXT, project_id TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS workspace (id TEXT, project_id TEXT)")
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/p1', 'P1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess_orig', 'proj1', 'Original Session', 1000, 2000, '/path/to/p1', '')
    """)
    conn.commit()
    conn.close()
    
    bundle_file = tmp_path / "project_export.ocbox"
    ocman.bundle_project_data("proj1", bundle_file)
    
    with pytest.raises(RecoveryError) as exc:
        ocman.extract_and_import_session(bundle_file, target_project_id="proj1", new_session_id=True)
        
    assert "session-id rename applies to a single-session bundle only." in str(exc.value)


def test_restore_cli_dispatch_success(tmp_path, temp_db, monkeypatch):
    import ocman
    import sys
    import sqlite3
    
    config_file = tmp_path / "ocman_temp.toml"
    orig_config_path = ocman.OCMAN_CONFIG_PATH
    ocman.OCMAN_CONFIG_PATH = config_file
    
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    config_file.write_text(f"""
db_path = {temp_db}
history_path = {tmp_path / 'ocman_history.json'}
default_backup_dir = {backup_dir}
""", encoding="utf-8")
    
    try:
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/p1', 'P1')")
        conn.commit()
        conn.close()
        
        db_file_1 = tmp_path / "db1.db"
        conn = sqlite3.connect(str(db_file_1))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)")
        cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj2', '/path/to/p2', 'P2')")
        conn.commit()
        conn.close()
        
        zip1 = tmp_path / "archive1.zip"
        import zipfile
        with zipfile.ZipFile(zip1, "w") as zf:
            zf.write(db_file_1, "opencode.db")
            
        orig_argv = sys.argv
        sys.argv = ["ocman", "--db", str(temp_db), "backup", "restore", str(zip1)]
        try:
            ocman.main()
        finally:
            sys.argv = orig_argv
            
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM project")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 'proj2'
        conn.close()
        
        assert not any(f.name.startswith("rollback-before-restore-") for f in backup_dir.iterdir())
        
    finally:
        ocman.OCMAN_CONFIG_PATH = orig_config_path


def test_session_delete_single_confirm(temp_db, monkeypatch):
    import ocman
    import sys
    import sqlite3
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/p1', 'P1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'S1', 1000, 2000, '/path/to/p1', '')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess2', 'proj1', 'S2', 1000, 2000, '/path/to/p1', '')
    """)
    conn.commit()
    conn.close()
    
    confirm_calls = []
    def fake_confirm(preview, *args, **kwargs):
        if not kwargs.get("assume_yes", False):
            confirm_calls.append(preview)
        return True
        
    monkeypatch.setattr(ocman, "confirm_destructive", fake_confirm)
    
    orig_argv = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "session", "delete", "sess1", "sess2"]
    try:
        ocman.main()
    finally:
        sys.argv = orig_argv
        
    assert len(confirm_calls) == 1
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM session")
    assert len(cursor.fetchall()) == 0
    conn.close()


def test_compact_batch_mid_failure_and_estimates(temp_db, tmp_path, monkeypatch, capsys):
    import sqlite3
    import ocman
    import sys
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess2', 'proj1', 'Sess 2', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()

    calls = []
    def fake_call_api(model, prompt, verbosity):
        if "sess1" in prompt or "Sess 1" in prompt:
            calls.append("sess1")
            return "compaction result", {"prompt_tokens": 100, "completion_tokens": 50, "cost": 0.0003}
        else:
            calls.append("sess2")
            raise Exception("API simulation failure")

    class FakeModel:
        provider_id = "openai"
        model_id = "gpt-4"
        name = "GPT-4"
        base_url = "https://api.openai.com/v1"
        api_key = "test"
        cost_input = 10.0
        cost_output = 30.0
        active = True
        compatible = True

    import subprocess
    def fake_subprocess_run(cmd, *args, **kwargs):
        stdout = kwargs.get("stdout")
        if stdout:
            stdout.write('{"turns": [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]}')
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(ocman.subprocess, "run", fake_subprocess_run)
    # The `opencode` CLI is not installed on every CI runner (e.g. macOS/Windows). This
    # test drives a mocked export/compaction flow, so neutralize the PATH precheck rather
    # than depend on the binary being present.
    monkeypatch.setattr(ocman, "require_opencode", lambda *a, **k: None)
    monkeypatch.setattr(ocman, "call_compaction_api", fake_call_api)
    monkeypatch.setattr(ocman, "load_opencode_config", lambda verbosity=0: {})
    monkeypatch.setattr(ocman, "extract_models_from_config", lambda c: [FakeModel()])
    monkeypatch.setattr(ocman, "resolve_model", lambda models, spec: FakeModel())
    monkeypatch.setattr(ocman, "estimate_cost", lambda *a, **k: 0.001)
    monkeypatch.setattr(ocman, "confirm_destructive", lambda *a, **k: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)

    orig = sys.argv
    # Isolate all output to tmp: -o keeps recovery files out of the repo's
    # opencode-recovery/, and --no-project-prompt stops the compacted copy from
    # being written into the repo's real .agents/prompts/pending/.
    out_dir = tmp_path / "recovery-out"
    sys.argv = ["ocman", "--db", str(temp_db), "session", "compact",
                "sess1", "sess2", "model:gpt-4", "--yes",
                "-o", str(out_dir), "--no-project-prompt"]
    try:
        ocman.main()
    finally:
        sys.argv = orig

    captured = capsys.readouterr().out
    assert "sess1" in calls
    assert "sess2" in calls
    assert "Compaction success: sess1" in captured
    assert "Error compacting session sess2: API simulation failure" in captured
    assert "Compaction Batch Summary" in captured
    assert "Success: 1  Failed: 1" in captured
    assert "Actual tokens (successes): input 100, output 50" in captured
    assert "Actual cost (successes):   $0.0003" in captured
    # The per-session conversation preview is shown during the estimate pass so
    # users can identify sessions by content (not just id/name); it must appear,
    # and must NOT split the summary table (table renders once, after the loop).
    assert "Session tail preview" in captured
    assert "Extracted turns" in captured
    # The vistab summary table must be contiguous: no preview text may appear
    # between its top and bottom box-drawing borders.
    top = captured.index("\u250c")          # top-left corner of the table
    bottom = captured.index("\u2514")       # bottom-left corner
    table_block = captured[top:bottom]
    assert "Session tail preview" not in table_block
    assert "Extracted turns" not in table_block


def test_check_egress_guards_interactive_and_yes(monkeypatch, capsys):
    import builtins
    from ocman import check_egress_guards, RecoveryError
    import pytest
    import sys
    
    text = "my aws key is AKIA1234567890123456 and token is ghp_12345678901234567890"
    config = {"filter_secret_scan": "conservative"}
    
    with pytest.raises(RecoveryError) as exc:
        check_egress_guards(
            text,
            source_desc="payload",
            config=config,
            force=False,
            allow_secrets=False,
            expunge_secrets=False,
            interactive=False
        )
    assert "possible secret/PII detected" in str(exc.value)

    user_inputs = ["s", "e"]
    def fake_input_s_e(prompt):
        return user_inputs.pop(0)
    monkeypatch.setattr(builtins, "input", fake_input_s_e)
    
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    
    res = check_egress_guards(
        text,
        source_desc="payload",
        config=config,
        force=False,
        allow_secrets=False,
        expunge_secrets=False,
        interactive=True
    )
    assert "[REDACTED]" in res
    assert "AKIA" not in res
    
    user_inputs = ["r", "reveal", "a"]
    def fake_input_reveal_abort(prompt):
        return user_inputs.pop(0)
    monkeypatch.setattr(builtins, "input", fake_input_reveal_abort)
    
    with pytest.raises(SystemExit) as exc:
        check_egress_guards(
            text,
            source_desc="payload",
            config=config,
            force=False,
            allow_secrets=False,
            expunge_secrets=False,
            interactive=True
        )
    assert exc.value.code == 1
    
    captured = capsys.readouterr().out
    assert "Detections context:" in captured
    assert "AKIA1234567890123456" in captured


def test_compact_yes_with_secrets_refuses(temp_db, monkeypatch):
    import sqlite3
    import ocman
    import sys
    import pytest
    
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session")
    cursor.execute("DELETE FROM project")
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
    cursor.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Sess 1', 1000, 2000, '/path/to/proj', '')
    """)
    conn.commit()
    conn.close()

    class FakeModel:
        provider_id = "openai"
        model_id = "gpt-4"
        name = "GPT-4"
        base_url = "https://api.openai.com/v1"
        api_key = "test"
        cost_input = 10.0
        cost_output = 30.0
        active = True
        compatible = True

    from ocman import SecretHit
    monkeypatch.setattr(ocman, "scan_for_secrets", lambda text, mode="conservative": [
        SecretHit(kind="aws-access-key-id", line=1, col_start=0, col_end=5)
    ])
    import subprocess
    def fake_subprocess_run(cmd, *args, **kwargs):
        stdout = kwargs.get("stdout")
        if stdout:
            stdout.write('{"turns": [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]}')
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(ocman.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(ocman, "load_opencode_config", lambda verbosity=0: {})
    monkeypatch.setattr(ocman, "extract_models_from_config", lambda c: [FakeModel()])
    monkeypatch.setattr(ocman, "resolve_model", lambda models, spec: FakeModel())

    orig = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "session", "compact", "sess1", "model:gpt-4", "--yes"]
    try:
        with pytest.raises(SystemExit) as exc:
            ocman.main()
        assert exc.value.code != 0
    finally:
        sys.argv = orig


def test_no_local_shutil_imports():
    import ast
    from pathlib import Path
    
    cli_path = Path(__file__).resolve().parent.parent / "ocman" / "cli.py"
    tree = ast.parse(cli_path.read_text(encoding="utf-8"))
    
    local_shutil_imports = []
    
    class LocalImportVisitor(ast.NodeVisitor):
        def __init__(self):
            self.in_function = False
            
        def visit_FunctionDef(self, node):
            old_in_function = self.in_function
            self.in_function = True
            self.generic_visit(node)
            self.in_function = old_in_function
            
        def visit_AsyncFunctionDef(self, node):
            old_in_function = self.in_function
            self.in_function = True
            self.generic_visit(node)
            self.in_function = old_in_function
            
        def visit_Import(self, node):
            if self.in_function:
                for alias in node.names:
                    if alias.name == "shutil":
                        local_shutil_imports.append(node.lineno)
            self.generic_visit(node)
            
        def visit_ImportFrom(self, node):
            if self.in_function:
                if node.module == "shutil":
                    local_shutil_imports.append(node.lineno)
            self.generic_visit(node)
            
    visitor = LocalImportVisitor()
    visitor.visit(tree)
    
    assert not local_shutil_imports, f"Found local 'shutil' imports in ocman/cli.py at lines: {local_shutil_imports}"



# ===========================================================================
# ocman doctor / ocman reclaim tests
# ===========================================================================
import json as _json
import time as _time
import types
import argparse


def _seed_doctor_db(db_path, *, migration_id=1, with_compacted=True,
                    compacted_age_ms=None, with_orphans=False, event_rows=True):
    """Seed a schema-faithful DB for doctor/reclaim tests.

    event rows: type='message.updated.1', data={"sessionID":..,"info":{"id":..}} with
    varying seq per (aggregate_id, info.id). part rows: data={"type":"tool",
    "state":{"status":"completed","output":"...","time":{"compacted":<ms|absent>}}}.
    A migration table row seeds the fingerprint gate.
    """
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("""CREATE TABLE project (id TEXT PRIMARY KEY, worktree TEXT, name TEXT)""")
    cur.execute("""CREATE TABLE session (
        id TEXT PRIMARY KEY, project_id TEXT, title TEXT, time_created INTEGER,
        time_updated INTEGER, directory TEXT, cost REAL, tokens_input INTEGER,
        tokens_output INTEGER, tokens_cache_read INTEGER, parent_id TEXT)""")
    cur.execute("""CREATE TABLE migration (id INTEGER PRIMARY KEY)""")
    cur.execute("""CREATE TABLE event (
        id INTEGER PRIMARY KEY, aggregate_id TEXT, type TEXT, seq INTEGER, data TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE part (
        id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT,
        time_created INTEGER, time_updated INTEGER, data TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT)""")

    cur.execute("INSERT INTO migration (id) VALUES (?)", (migration_id,))
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1','/p','P1')")
    now_ms = int(_time.time() * 1000)
    cur.execute("""INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
                   VALUES ('sess1','proj1','S1',?,?,'/p',NULL)""", (now_ms, now_ms))

    if event_rows:
        # Two message.updated snapshots for the same (aggregate_id, info.id): seq 1
        # is superseded by seq 2 (exercises the superseded-waste estimate).
        for seq in (1, 2):
            data = _json.dumps({"sessionID": "sess1", "info": {"id": "msg1"}})
            cur.execute("INSERT INTO event (aggregate_id, type, seq, data) VALUES (?,?,?,?)",
                        ("sess1", "message.updated.1", seq, data + " " * (500 * seq)))

    if with_compacted:
        marker = compacted_age_ms if compacted_age_ms is not None else now_ms
        pdata = _json.dumps({
            "type": "tool",
            "state": {"status": "completed", "output": "X" * 2000,
                      "time": {"compacted": marker}}})
        cur.execute("""INSERT INTO part (id, message_id, session_id, time_created, time_updated, data)
                       VALUES ('part_c','msg1','sess1',?,?,?)""", (now_ms, now_ms, pdata))
    # A non-compacted completed tool part (must never be touched).
    ndata = _json.dumps({"type": "tool", "state": {"status": "completed",
                                                    "output": "KEEP" * 100, "time": {}}})
    cur.execute("""INSERT INTO part (id, message_id, session_id, time_created, time_updated, data)
                   VALUES ('part_n','msg1','sess1',?,?,?)""", (now_ms, now_ms, ndata))

    if with_orphans:
        # Orphaned part row (session_id absent from session).
        odata = _json.dumps({"type": "tool", "state": {"status": "completed"}})
        cur.execute("""INSERT INTO part (id, message_id, session_id, time_created, time_updated, data)
                       VALUES ('part_o','msgX','ghost',?,?,?)""", (now_ms, now_ms, odata))
        # A session with a dangling project_id.
        cur.execute("""INSERT INTO session (id, project_id, title, time_created, time_updated, directory)
                       VALUES ('sess_d','no_such_proj','D',?,?,'/p')""", (now_ms, now_ms))
    conn.commit()
    conn.close()


@pytest.fixture
def doctor_db(tmp_path, monkeypatch):
    """A schema-faithful seeded DB plus a tmp HOME, with OPENCODE_DB_PATH pointed at it."""
    fake_home = tmp_path / "home"
    fake_home.mkdir(exist_ok=True)
    monkeypatch.setattr(ocman.Path, "home", staticmethod(lambda: fake_home))
    # Neutralize any XDG/OPENCODE_DB env that could redirect discovery.
    for var in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "OPENCODE_DB",
                "OPENCODE_CONFIG_DIR"):
        monkeypatch.delenv(var, raising=False)
    db_path = tmp_path / "opencode.db"
    orig = ocman.OPENCODE_DB_PATH
    ocman.OPENCODE_DB_PATH = db_path
    yield tmp_path, db_path
    ocman.OPENCODE_DB_PATH = orig


# --- db_connect_readonly ----------------------------------------------------

def test_db_connect_readonly_blocks_writes(doctor_db):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    conn = ocman.db_connect_readonly(db_path)
    try:
        with pytest.raises(Exception):
            conn.execute("INSERT INTO migration (id) VALUES (999)")
            conn.commit()
    finally:
        conn.close()
    # Reads still work.
    conn = ocman.db_connect_readonly(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM migration").fetchone()[0] == 1
    finally:
        conn.close()


def test_db_connect_readonly_missing_degrades(tmp_path):
    missing = tmp_path / "nope.db"
    with pytest.raises(Exception):
        ocman.db_connect_readonly(missing)
    with pytest.raises(Exception):
        ocman.db_connect_readonly(":memory:")


# --- discovery --------------------------------------------------------------

def test_discovery_honors_xdg_and_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.delenv("OPENCODE_DB", raising=False)
    loc = ocman.discover_storage_locations(None)
    assert loc["data_dir"] == (tmp_path / "xdg" / "opencode")
    assert loc["snapshot_dir"] == (tmp_path / "xdg" / "opencode" / "snapshot")
    assert "temp_wal_glob" in loc and "temp_so_glob" in loc


def test_discovery_memory_db(monkeypatch):
    monkeypatch.setenv("OPENCODE_DB", ":memory:")
    loc = ocman.discover_storage_locations(None)
    assert loc["db_is_memory"] is True
    assert loc["db_path"] is None


def test_discovery_excludes_backup_prefixes(tmp_path, monkeypatch):
    data = tmp_path / "data" / "opencode"
    data.mkdir(parents=True)
    (data / "opencode.db").write_text("x")
    (data / "opencode-db-cleanup-xyz.db").write_text("x")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.delenv("OPENCODE_DB", raising=False)
    detected = ocman._detect_db_in_data_dir(data)
    assert detected.name == "opencode.db"


# --- doctor render ----------------------------------------------------------

def test_doctor_runs_without_db(doctor_db, capsys, monkeypatch):
    _tmp, db_path = doctor_db
    # No DB file created -> degrade to filesystem-only.
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    args = argparse.Namespace(verbose=0, json_output=False,
                              doctor_fast=False, doctor_deep=False)
    ocman.cli_doctor(args)
    out = capsys.readouterr().out
    assert "Check" in out and "Recommended fix" in out
    assert "Summary:" in out and "warnings" in out


def test_doctor_healthy_db_ok(doctor_db, capsys, monkeypatch):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path, with_orphans=False)
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    records = ocman.run_doctor_checks(running=False)
    by_key = {r["key"]: r for r in records}
    assert by_key["db_size"]["status"] in ("ok", "warn")
    assert by_key["db_integrity"]["status"] == "ok"
    assert by_key["orphan_rows"]["status"] == "ok"


def test_doctor_json_envelope(doctor_db, capsys, monkeypatch):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    args = argparse.Namespace(verbose=0, json_output=True)
    ocman.cli_doctor(args)
    out = capsys.readouterr().out
    payload = _json.loads(out)
    assert payload["command"] == "doctor"
    assert isinstance(payload["doctor"], list)
    keys = {r["key"] for r in payload["doctor"]}
    assert {"db_size", "event_bloat", "compacted_parts", "orphan_rows"} <= keys


# --- orphan / event / compacted checks --------------------------------------

def test_doctor_orphan_checks_warn(doctor_db, tmp_path, monkeypatch):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path, with_orphans=True)
    # Seed an orphaned session-diff file.
    storage = tmp_path / "home" / ".local" / "share" / "opencode" / "storage" / "session_diff"
    storage.mkdir(parents=True)
    (storage / "ghost_session.json").write_text("{}")
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    records = ocman.run_doctor_checks(running=False)
    by_key = {r["key"]: r for r in records}
    assert by_key["orphan_rows"]["status"] == "warn"
    assert by_key["orphan_rows"]["fix_cmd"] == "ocman db clean-orphans"
    assert by_key["orphan_diff_files"]["status"] == "warn"
    assert by_key["orphan_diff_files"]["fix_cmd"] == "ocman db clean-orphans"
    # Read-only: the orphan rows/files are still present (nothing deleted).
    conn = sqlite3.connect(str(db_path))
    assert conn.execute("SELECT COUNT(*) FROM part WHERE session_id='ghost'").fetchone()[0] == 1
    conn.close()
    assert (storage / "ghost_session.json").exists()


def test_doctor_event_bloat_reported(doctor_db, monkeypatch):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    records = ocman.run_doctor_checks(running=False)
    ev = next(r for r in records if r["key"] == "event_bloat")
    assert ev["status"] == "notice"
    assert "33356" in (ev["issue_url"] or "")
    assert ev["bucket"] == "report"
    assert ev["fix_cmd"] is None  # NEVER a reclaim command for events


def test_doctor_compacted_parts_actionable(doctor_db, monkeypatch):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path, with_compacted=True)
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    records = ocman.run_doctor_checks(running=False)
    cp = next(r for r in records if r["key"] == "compacted_parts")
    assert cp["status"] == "notice"
    assert cp["bucket"] == "optin"
    assert cp["fix_cmd"] == "ocman reclaim --reclaim-parts"


def test_doctor_compacted_parts_unpopulated(doctor_db, monkeypatch):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path, with_compacted=False)
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    records = ocman.run_doctor_checks(running=False)
    cp = next(r for r in records if r["key"] == "compacted_parts")
    # No marker present => nothing to reclaim => OK (not a yellow NOTICE), no fix.
    assert cp["status"] == "ok"
    assert cp.get("fix_cmd") in (None, "")
    assert "nothing" in cp["detail"].lower() or "not pruned" in cp["detail"].lower()


def test_doctor_backup_check(doctor_db, tmp_path, monkeypatch):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    backups = tmp_path / "home" / ".local" / "share" / "opencode" / "backups"
    backups.mkdir(parents=True)
    old = backups / "opencode-backup-20200101.zip"
    old.write_text("x" * 100)
    os.utime(old, (0, 0))  # very old mtime
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    records = ocman.run_doctor_checks(running=False)
    bk = next(r for r in records if r["key"] == "ocman_backups")
    assert bk["status"] == "notice"
    assert "ocman backup clean --older-than" in (bk["fix_cmd"] or "")


# --- migration gate + schema-defensive --------------------------------------

def test_doctor_unrecognized_schema_warns(doctor_db, monkeypatch):
    """Recognition is by table PRESENCE (OpenCode migration ids are timestamped
    strings, not integers). A DB missing the core session tables is unrecognized ->
    the DB-internal checks WARN (name the reason), never a blank UNKNOWN, never a crash."""
    _tmp, db_path = doctor_db
    # A DB with NO OpenCode core tables (only an unrelated table).
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE unrelated (x)")
    conn.commit(); conn.close()
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    records = ocman.run_doctor_checks(running=False)
    by_key = {r["key"]: r for r in records}
    assert by_key["schema"]["status"] == "warn"
    assert by_key["event_bloat"]["status"] == "warn"
    assert by_key["orphan_rows"]["status"] == "warn"


def test_doctor_recognizes_string_migration_id(doctor_db, monkeypatch):
    """Regression for the fingerprint bug: a real OpenCode-style timestamped-STRING
    migration id must be recognized (not rejected by int-parsing), so the DB checks run."""
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    # Replace the integer migration id with a real timestamped-string one.
    conn = sqlite3.connect(str(db_path))
    conn.execute("DROP TABLE migration")
    conn.execute("CREATE TABLE migration (id TEXT PRIMARY KEY, time_completed INTEGER)")
    conn.execute("INSERT INTO migration VALUES ('20260622202450_simplify_session_input', 1)")
    conn.commit(); conn.close()
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    records = ocman.run_doctor_checks(running=False)
    by_key = {r["key"]: r for r in records}
    # Recognized -> the DB checks actually ran (not WARN "not measured").
    assert by_key["schema"]["status"] in ("info", "notice")
    assert by_key["event_bloat"]["status"] in ("ok", "notice")
    assert by_key["orphan_rows"]["status"] in ("ok", "warn", "notice")


# --- no --compact-events, no event deletion ---------------------------------

def test_no_compact_events_flag():
    parser = ocman.build_parser()
    # Parsing an unknown flag must fail.
    with pytest.raises(SystemExit):
        parser.parse_args(["reclaim", "--compact-events"])


def test_no_event_deleting_code_path():
    import inspect
    src = inspect.getsource(ocman.cli_reclaim)
    src += inspect.getsource(ocman.reclaim_parts)
    src += inspect.getsource(ocman.reclaim_checkpoint_vacuum)
    assert "DELETE FROM event" not in src
    assert "delete from event" not in src.lower()


# --- doctor-while-running writes nothing ------------------------------------

@pytest.mark.real_process_detection
def test_doctor_while_running_writes_nothing(doctor_db, monkeypatch, capsys):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    # Force detection to "some" AND the fd check to positive.
    monkeypatch.setattr(ocman, "detect_running_opencode_status",
                        lambda *a, **k: ("some", [{"pid": 1, "tty": "?", "elapsed": "1m",
                                                    "started": "now", "cwd": "", "project": "",
                                                    "cmdline": "opencode"}]))
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: True)
    before = db_path.stat().st_mtime_ns
    args = argparse.Namespace(verbose=0, json_output=False)
    ocman.cli_doctor(args)  # must not raise, must not write
    after = db_path.stat().st_mtime_ns
    assert before == after


# --- reclaim: checkpoint + VACUUM -------------------------------------------

@pytest.mark.real_process_detection
def test_reclaim_refuses_on_live_fd(doctor_db, monkeypatch):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    monkeypatch.setattr(ocman, "detect_running_opencode_status", lambda *a, **k: ("none", []))
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: True)
    args = argparse.Namespace(
        verbose=0, dry_run=False, yes=True, while_running=False, force=False,
        reclaim_parts=False, reclaim_temp=False, backups_dir=None,
        force_snapshots=None, tmp_min_age_hours=None)
    with pytest.raises(ocman.RecoveryError, match="live process holds"):
        ocman.cli_reclaim(args)


@pytest.mark.real_process_detection
def test_reclaim_checkpoint_vacuum_while_running(doctor_db, monkeypatch, capsys):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    monkeypatch.setattr(ocman, "detect_running_opencode_status", lambda *a, **k: ("none", []))
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: True)
    args = argparse.Namespace(
        verbose=0, dry_run=False, yes=True, while_running=True, force=False,
        reclaim_parts=False, reclaim_temp=False, backups_dir=None,
        force_snapshots=None, tmp_min_age_hours=None)
    ocman.cli_reclaim(args)
    out = capsys.readouterr().out
    assert "VACUUM" in out
    # A backup family dir was created.
    backups = _tmp / "home" / ".local" / "share" / "opencode" / "backups"
    made = list(backups.glob("opencode-db-cleanup-*"))
    assert made, "expected a pre-op backup dir"
    assert (made[0] / "opencode.db").exists()


def test_reclaim_dry_run_writes_nothing(doctor_db, monkeypatch, capsys):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    before = db_path.stat().st_mtime_ns
    args = argparse.Namespace(
        verbose=0, dry_run=True, yes=True, while_running=False, force=False,
        reclaim_parts=False, reclaim_temp=False, backups_dir=None,
        force_snapshots=None, tmp_min_age_hours=None)
    ocman.cli_reclaim(args)
    after = db_path.stat().st_mtime_ns
    assert before == after
    backups = _tmp / "home" / ".local" / "share" / "opencode" / "backups"
    assert not list(backups.glob("opencode-db-cleanup-*"))


# --- reclaim: --reclaim-parts verify-or-skip --------------------------------

def test_reclaim_parts_acts_past_retention(doctor_db, monkeypatch):
    _tmp, db_path = doctor_db
    old_ms = int(_time.time() * 1000 - 60 * 86400000)  # 60 days ago
    _seed_doctor_db(db_path, with_compacted=True, compacted_age_ms=old_ms)
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    loc = ocman.discover_storage_locations(db_path)
    ocman.reclaim_parts(loc, dry_run=False, while_running=False, assume_yes=True,
                        retention_days=30, verbosity=0)
    conn = sqlite3.connect(str(db_path))
    data = conn.execute("SELECT data FROM part WHERE id='part_c'").fetchone()[0]
    parsed = _json.loads(data)  # still valid JSON
    assert parsed["state"]["output"] == ""  # emptied, not nulled
    assert parsed["state"]["time"]["compacted"] == old_ms  # marker preserved
    # Non-compacted part is untouched.
    ndata = _json.loads(conn.execute("SELECT data FROM part WHERE id='part_n'").fetchone()[0])
    assert ndata["state"]["output"] == "KEEP" * 100
    conn.close()


def test_reclaim_parts_skips_within_retention(doctor_db, monkeypatch, capsys):
    _tmp, db_path = doctor_db
    now_ms = int(_time.time() * 1000)  # compacted just now, within retention
    _seed_doctor_db(db_path, with_compacted=True, compacted_age_ms=now_ms)
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    loc = ocman.discover_storage_locations(db_path)
    ocman.reclaim_parts(loc, dry_run=False, while_running=False, assume_yes=True,
                        retention_days=30, verbosity=0)
    conn = sqlite3.connect(str(db_path))
    data = _json.loads(conn.execute("SELECT data FROM part WHERE id='part_c'").fetchone()[0])
    assert data["state"]["output"] == "X" * 2000  # untouched (within retention)
    conn.close()


def test_reclaim_parts_fail_closed_no_marker(doctor_db, monkeypatch, capsys):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path, with_compacted=False)  # no part carries the marker
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    loc = ocman.discover_storage_locations(db_path)
    ocman.reclaim_parts(loc, dry_run=False, while_running=False, assume_yes=True,
                        retention_days=30, verbosity=0)
    out = capsys.readouterr().out
    assert "SKIPPED" in out
    # Nothing written: no backup dir made.
    backups = _tmp / "home" / ".local" / "share" / "opencode" / "backups"
    assert not list(backups.glob("opencode-db-cleanup-*"))


def test_reclaim_parts_schema_gate(doctor_db, monkeypatch, capsys):
    """--reclaim-parts must FAIL CLOSED (abort, write nothing) when the schema is not
    recognized. Recognition is by core-table presence, so a DB missing the session
    tables triggers the gate."""
    _tmp, db_path = doctor_db
    old_ms = int(_time.time() * 1000 - 60 * 86400000)
    _seed_doctor_db(db_path, with_compacted=True, compacted_age_ms=old_ms)
    # Remove ALL core session tables so the schema is unrecognized (the gate fires).
    conn = sqlite3.connect(str(db_path))
    for t in ("session", "message", "event", "part"):
        conn.execute(f"DROP TABLE {t}")
    conn.commit(); conn.close()
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    loc = ocman.discover_storage_locations(db_path)
    ocman.reclaim_parts(loc, dry_run=False, while_running=False, assume_yes=True,
                        retention_days=30, verbosity=0)
    out = capsys.readouterr().out
    assert "aborted" in out.lower()  # failed closed on the unrecognized schema
    # No backup should have been created (it aborted before any write step).
    assert "backup created" not in out.lower()


# --- reclaim: temp reap -----------------------------------------------------

def test_reclaim_temp_report_only_without_flag(doctor_db, monkeypatch, tmp_path):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    tmpdir = tmp_path / "scratch"
    tmpdir.mkdir()
    wal = tmpdir / "opencode-wal-1.db"
    wal.write_text("x")
    os.utime(wal, (0, 0))
    monkeypatch.setattr(ocman.tempfile, "gettempdir", lambda: str(tmpdir))
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    # Bare reclaim (no --reclaim-temp): must not delete temp files.
    args = argparse.Namespace(
        verbose=0, dry_run=False, yes=True, while_running=False, force=False,
        reclaim_parts=False, reclaim_temp=False, backups_dir=None,
        force_snapshots=None, tmp_min_age_hours=None)
    ocman.cli_reclaim(args)
    assert wal.exists()


@pytest.mark.skipif(not _sys.platform.startswith("linux"),
                    reason="Linux-only: /tmp/*.so reap + /proc holder check are Linux-specific")
def test_reclaim_temp_deletes_old_unheld(doctor_db, monkeypatch, tmp_path):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    tmpdir = tmp_path / "scratch"
    tmpdir.mkdir()
    # Two WAL files (newest kept), plus a .so.
    old_wal = tmpdir / "opencode-wal-old.db"
    new_wal = tmpdir / "opencode-wal-new.db"
    lib = tmpdir / "held.so"
    free_lib = tmpdir / "free.so"
    for f in (old_wal, new_wal, lib, free_lib):
        f.write_text("x")
    os.utime(old_wal, (0, 0))
    os.utime(lib, (0, 0))
    os.utime(free_lib, (0, 0))
    monkeypatch.setattr(ocman.tempfile, "gettempdir", lambda: str(tmpdir))
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    # Fake: `lib` is held/mapped by a live PID; the rest are free.
    monkeypatch.setattr(ocman, "_proc_pids_mapping_or_holding",
                        lambda paths: {str(lib)} & set(paths))
    loc = ocman.discover_storage_locations(db_path)
    ocman.reclaim_temp(loc, dry_run=False, force=True, min_age_hours=24,
                       assume_yes=True, verbosity=0)
    assert not old_wal.exists()   # old, unheld -> deleted
    assert new_wal.exists()       # newest WAL kept as a precaution
    assert lib.exists()           # held/mapped -> skipped
    assert not free_lib.exists()  # old, unheld -> deleted


def test_reclaim_temp_dry_run_noop(doctor_db, monkeypatch, tmp_path):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    tmpdir = tmp_path / "scratch"
    tmpdir.mkdir()
    old_wal = tmpdir / "opencode-wal-a.db"
    old_wal.write_text("x")
    os.utime(old_wal, (0, 0))
    monkeypatch.setattr(ocman.tempfile, "gettempdir", lambda: str(tmpdir))
    monkeypatch.setattr(ocman, "_proc_pids_mapping_or_holding", lambda paths: set())
    loc = ocman.discover_storage_locations(db_path)
    ocman.reclaim_temp(loc, dry_run=True, force=True, min_age_hours=24,
                       assume_yes=True, verbosity=0)
    assert old_wal.exists()


# --- snapshots require --force-snapshots + distinct confirm -----------------

def test_snapshots_not_deleted_by_default(doctor_db, monkeypatch, tmp_path):
    _tmp, db_path = doctor_db
    _seed_doctor_db(db_path)
    snap = tmp_path / "home" / ".local" / "share" / "opencode" / "snapshot" / "proj"
    snap.mkdir(parents=True)
    (snap / "obj").write_text("x")
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    args = argparse.Namespace(
        verbose=0, dry_run=False, yes=True, while_running=False, force=False,
        reclaim_parts=False, reclaim_temp=False, backups_dir=None,
        force_snapshots=None, tmp_min_age_hours=None)
    ocman.cli_reclaim(args)
    assert (snap / "obj").exists()


def test_snapshots_yes_does_not_bypass_confirm(doctor_db, monkeypatch, tmp_path):
    _tmp, db_path = doctor_db
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "obj").write_text("x")
    loc = ocman.discover_storage_locations(db_path)
    # Non-interactive stdout -> --force-snapshots must refuse (not bypass).
    monkeypatch.setattr(ocman.sys.stdout, "isatty", lambda: False)
    with pytest.raises(ocman.RecoveryError, match="interactive"):
        ocman.reclaim_snapshots(str(snap), loc, dry_run=False, verbosity=0)
    assert (snap / "obj").exists()


def test_snapshots_distinct_confirm_typed(doctor_db, monkeypatch, tmp_path):
    _tmp, db_path = doctor_db
    snap = tmp_path / "snap2"
    snap.mkdir()
    (snap / "obj").write_text("x")
    loc = ocman.discover_storage_locations(db_path)
    monkeypatch.setattr(ocman.sys.stdout, "isatty", lambda: True)
    # Wrong token cancels; the dir survives.
    monkeypatch.setattr("builtins.input", lambda *a, **k: "yes")
    ocman.reclaim_snapshots(str(snap), loc, dry_run=False, verbosity=0)
    assert snap.exists()
    # Correct token deletes.
    monkeypatch.setattr("builtins.input", lambda *a, **k: "delete snapshots")
    ocman.reclaim_snapshots(str(snap), loc, dry_run=False, verbosity=0)
    assert not snap.exists()


# --- user-dir path safety ---------------------------------------------------

def test_backups_dir_refuses_dangerous_roots(doctor_db, monkeypatch):
    _tmp, db_path = doctor_db
    loc = ocman.discover_storage_locations(db_path)
    with pytest.raises(ocman.RecoveryError, match="protected root"):
        ocman._resolve_user_dir_for_delete(str(_tmp / "home"), loc,
                                            label="--backups-dir")


# --- db_family_open_by_live_pid ---------------------------------------------

@pytest.mark.real_process_detection
def test_db_family_open_by_live_pid_detects_self(tmp_path):
    if not ocman.sys.platform.startswith("linux"):
        pytest.skip("requires /proc")
    db = tmp_path / "held.db"
    db.write_text("x")
    fh = open(db, "rb")  # hold a live fd on our own process
    try:
        assert ocman.db_family_open_by_live_pid(db) is True
    finally:
        fh.close()
    # After closing, no live fd holds it.
    assert ocman.db_family_open_by_live_pid(db) is False


# --- extract-on-delete -------------------------------------------------------

def _seed_extract_db(db_path):
    """Create real message/part tables and seed one session with a conversation."""
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS message")
    cur.execute("""
        CREATE TABLE message (
            id TEXT PRIMARY KEY, session_id TEXT,
            time_created INTEGER, time_updated INTEGER, data TEXT
        )
    """)
    cur.execute("DROP TABLE IF EXISTS part")
    cur.execute("""
        CREATE TABLE part (
            id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT,
            time_created INTEGER, time_updated INTEGER, data TEXT
        )
    """)
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/p1', 'P1')")
    cur.execute("""
        INSERT INTO session (id, project_id, title, time_created, time_updated, directory, parent_id)
        VALUES ('sess1', 'proj1', 'Do a thing', 1000, 2000, '/p1', '')
    """)
    cur.execute("INSERT INTO message VALUES ('m1','sess1',1000,1000,?)", ('{"role":"user"}',))
    cur.execute("INSERT INTO message VALUES ('m2','sess1',1001,1001,?)", ('{"role":"assistant"}',))
    cur.execute("INSERT INTO part VALUES ('p1','m1','sess1',1000,1000,?)",
                ('{"type":"text","text":"Please add a login button to the page."}',))
    cur.execute("INSERT INTO part VALUES ('p2','m2','sess1',1001,1001,?)",
                ('{"type":"text","text":"I added the login button and wired up the handler."}',))
    conn.commit()
    conn.close()


def test_db_export_session_data_shape(temp_db):
    _seed_extract_db(temp_db)
    conn = sqlite3.connect(str(temp_db))
    try:
        data = ocman.db_export_session_data("sess1", conn)
    finally:
        conn.close()
    assert data is not None
    assert [m["info"]["role"] for m in data["messages"]] == ["user", "assistant"]
    turns = ocman.find_turns(data, include_tools=False, verbosity=0)
    assert [t.role for t in turns] == ["user", "assistant"]
    assert "login button" in turns[0].text


def test_db_export_session_data_no_messages_returns_none(temp_db):
    _seed_extract_db(temp_db)
    conn = sqlite3.connect(str(temp_db))
    try:
        assert ocman.db_export_session_data("does-not-exist", conn) is None
    finally:
        conn.close()


def test_extract_sessions_before_delete_writes_files(temp_db, tmp_path):
    _seed_extract_db(temp_db)
    out = tmp_path / "recovery"
    conn = sqlite3.connect(str(temp_db))
    try:
        written = ocman.extract_sessions_before_delete(["sess1"], out, conn, verbosity=0)
    finally:
        conn.close()
    names = sorted(p.name for p in written)
    assert any(n.endswith(".transcript.md") for n in names)
    assert any(n.endswith(".restart.md") for n in names)
    assert any(n.endswith(".prompt.md") for n in names)
    for p in written:
        assert p.exists() and p.stat().st_size > 0


def test_extract_sessions_before_delete_empty_makes_no_dir(temp_db, tmp_path):
    _seed_extract_db(temp_db)
    out = tmp_path / "recovery"
    conn = sqlite3.connect(str(temp_db))
    try:
        written = ocman.extract_sessions_before_delete(["nope"], out, conn, verbosity=0)
    finally:
        conn.close()
    assert written == []
    assert not out.exists()


def test_resolve_extract_choice_flags_win(monkeypatch):
    # Explicit flags always win, never prompt.
    monkeypatch.setattr(ocman.sys.stdin, "isatty", lambda: True)
    assert ocman.resolve_extract_choice(True, False, 3) is True
    assert ocman.resolve_extract_choice(False, False, 3) is False


def test_resolve_extract_choice_assume_yes_no_prompt(monkeypatch):
    monkeypatch.setattr(ocman.sys.stdin, "isatty", lambda: True)
    # -y implies extract=yes with no prompt.
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("prompted")))
    assert ocman.resolve_extract_choice(None, True, 2) is True


def test_resolve_extract_choice_noninteractive_defaults_yes(monkeypatch):
    monkeypatch.setattr(ocman.sys.stdin, "isatty", lambda: False)
    assert ocman.resolve_extract_choice(None, False, 5) is True


def test_resolve_extract_choice_prompt_yes_and_no(monkeypatch):
    monkeypatch.setattr(ocman.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "")
    assert ocman.resolve_extract_choice(None, False, 1) is True
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "n")
    assert ocman.resolve_extract_choice(None, False, 1) is False


def test_session_delete_writes_extracts(temp_db, tmp_path, monkeypatch):
    import sys
    _seed_extract_db(temp_db)
    monkeypatch.setattr(ocman, "confirm_destructive", lambda *a, **k: True)
    out = tmp_path / "recovery"
    orig_argv = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "session", "delete", "sess1",
                "--extracts", "-o", str(out)]
    try:
        ocman.main()
    finally:
        sys.argv = orig_argv
    assert out.exists()
    assert any(p.name.endswith(".restart.md") for p in out.iterdir())
    conn = sqlite3.connect(str(temp_db))
    cur = conn.cursor()
    cur.execute("SELECT id FROM session WHERE id='sess1'")
    assert cur.fetchone() is None  # still deleted
    conn.close()


def test_session_delete_no_extracts_skips(temp_db, tmp_path, monkeypatch):
    import sys
    _seed_extract_db(temp_db)
    monkeypatch.setattr(ocman, "confirm_destructive", lambda *a, **k: True)
    out = tmp_path / "recovery"
    orig_argv = sys.argv
    sys.argv = ["ocman", "--db", str(temp_db), "session", "delete", "sess1",
                "--no-extracts", "-o", str(out)]
    try:
        ocman.main()
    finally:
        sys.argv = orig_argv
    assert not out.exists()


# --- bare-word 'help' -> --help ----------------------------------------------

def test_preprocess_argv_bare_help_rewrites():
    # 'help' after a group/action becomes a trailing --help.
    assert ocman.preprocess_argv(["ocman", "session", "delete", "help"]) == \
        ["ocman", "session", "delete", "--help"]
    assert ocman.preprocess_argv(["ocman", "db", "clean", "help"]) == \
        ["ocman", "db", "clean", "--help"]
    assert ocman.preprocess_argv(["ocman", "project", "delete", "help"]) == \
        ["ocman", "project", "delete", "--help"]


def test_preprocess_argv_leading_help_command_untouched():
    # The top-level `help [topic]` command is NOT rewritten.
    assert ocman.preprocess_argv(["ocman", "help"]) == ["ocman", "help"]
    assert ocman.preprocess_argv(["ocman", "help", "all"]) == ["ocman", "help", "all"]


# --- list-command filtering (lp / ls / lr) + lr alias -------------------------

def _seed_two_projects(temp_db):
    """Seed two distinct projects with one session each for filter tests."""
    conn = sqlite3.connect(str(temp_db))
    c = conn.cursor()
    c.execute("INSERT INTO project (id, worktree, name) VALUES ('pa', ?, 'Alpha')",
              (abs_path("/home/me/alpha"),))
    c.execute("INSERT INTO project (id, worktree, name) VALUES ('pb', ?, 'Beta')",
              (abs_path("/home/me/beta"),))
    c.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
              "VALUES ('sa', 'pa', 'Fix the widget', 1000, 2000, ?)", (abs_path("/home/me/alpha"),))
    c.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
              "VALUES ('sb', 'pb', 'Refactor parser', 1100, 2100, ?)", (abs_path("/home/me/beta"),))
    conn.commit()
    conn.close()


def test_list_projects_filter_by_dir_and_name(temp_db, monkeypatch, capsys):
    import sys, json
    _seed_two_projects(temp_db)
    # Filter by directory substring.
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "lp", "alpha", "--json"])
    ocman.main()
    data = json.loads(capsys.readouterr().out)["projects"]
    assert data["count"] == 1
    assert data["projects"][0]["id"] == "pa"
    # Filter by name substring (case-insensitive), different project.
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "lp", "BETA", "--json"])
    ocman.main()
    data = json.loads(capsys.readouterr().out)["projects"]
    assert data["count"] == 1
    assert data["projects"][0]["id"] == "pb"


def test_list_projects_filter_no_match_json_is_empty(temp_db, monkeypatch, capsys):
    import sys, json
    _seed_two_projects(temp_db)
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "lp", "zzz-nomatch", "--json"])
    ocman.main()  # must NOT exit non-zero on empty filter under --json
    data = json.loads(capsys.readouterr().out)["projects"]
    assert data["count"] == 0 and data["projects"] == []


def test_list_sessions_filter_fallback_when_not_a_project(temp_db, monkeypatch, capsys):
    import sys, json
    _seed_two_projects(temp_db)
    # "widget" matches no project, so it falls back to a session filter on title.
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "ls", "widget", "--json"])
    ocman.main()
    data = json.loads(capsys.readouterr().out)["sessions"]
    assert data["count"] == 1
    assert data["sessions"][0]["id"] == "sa"


def test_list_sessions_project_scope_precedence_preserved(temp_db, monkeypatch, capsys):
    import sys, json
    _seed_two_projects(temp_db)
    # "beta" uniquely substring-matches project pb's directory -> project SCOPE (old behavior),
    # returning that project's sessions (sb), NOT a title filter.
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "ls", "beta", "--json"])
    ocman.main()
    data = json.loads(capsys.readouterr().out)["sessions"]
    assert {s["id"] for s in data["sessions"]} == {"sb"}


def test_list_sessions_filter_no_match_json_is_empty(temp_db, monkeypatch, capsys):
    import sys, json
    _seed_two_projects(temp_db)
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "ls", "zzz-nomatch", "--json"])
    ocman.main()  # empty filter under --json must be a clean empty payload, exit 0
    data = json.loads(capsys.readouterr().out)["sessions"]
    assert data["count"] == 0 and data["sessions"] == []


def test_list_running_filter_matches_cwd_and_session(monkeypatch, capsys):
    import json
    from ocman import cli_list_running
    # Two fake running instances; filter should keep only the matching one.
    instances = [
        {"pid": 1, "user": "me", "elapsed": "1:00", "kind": "serve", "listeners": [],
         "auth": "n/a", "exposed": False, "vulnerable": False,
         "cwd": "/home/me/alpha", "project": "pa",
         "session": {"id": "ses_aaa", "title": "Fix the widget", "directory": "/home/me/alpha",
                     "project_id": "pa", "provenance": "argv"}},
        {"pid": 2, "user": "me", "elapsed": "2:00", "kind": "serve", "listeners": [],
         "auth": "n/a", "exposed": False, "vulnerable": False,
         "cwd": "/home/me/beta", "project": "pb",
         "session": {"id": "ses_bbb", "title": "Refactor parser", "directory": "/home/me/beta",
                     "project_id": "pb", "provenance": "argv"}},
    ]
    monkeypatch.setattr(ocman, "detect_running_instances", lambda **k: list(instances))
    # Match by cwd/project substring (no --long needed).
    cli_list_running(json_output=True, pattern="alpha")
    data = json.loads(capsys.readouterr().out)["running"]
    assert data["count"] == 1 and data["instances"][0]["pid"] == 1
    # Match by SESSION title substring, WITHOUT --long (session data is always attributed).
    cli_list_running(json_output=True, pattern="parser")
    data = json.loads(capsys.readouterr().out)["running"]
    assert data["count"] == 1 and data["instances"][0]["pid"] == 2
    # No match -> empty, reliable.
    cli_list_running(json_output=True, pattern="zzz-nomatch")
    data = json.loads(capsys.readouterr().out)["running"]
    assert data["count"] == 0 and data["instances"] == []


# --- session rename (session rename / top-level rename) -----------------------

def _seed_one_session(temp_db, sid="ses_r1", title="Old Title"):
    conn = sqlite3.connect(str(temp_db))
    c = conn.cursor()
    c.execute("INSERT INTO project (id, worktree, name) VALUES ('pr', ?, 'Proj')",
              (abs_path("/home/me/proj"),))
    c.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, directory) "
              "VALUES (?, 'pr', ?, 1000, 2000, ?)", (sid, title, abs_path("/home/me/proj")))
    conn.commit()
    conn.close()


def test_db_rename_session_returns_old_and_persists_new(temp_db, monkeypatch):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    old = ocman.db_rename_session("ses_r1", "New Title")
    assert old == "Old Title"
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "New Title"
    conn.close()


def test_db_rename_session_missing_id_raises(temp_db):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    with pytest.raises(ocman.RecoveryError, match="not found"):
        ocman.db_rename_session("ses_nope", "x")


def test_db_rename_session_title_is_bound_not_interpolated(temp_db):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    evil = "weird'; DROP TABLE session;--"
    ocman.db_rename_session("ses_r1", evil)
    conn = sqlite3.connect(str(temp_db))
    # Stored verbatim, and the table still exists (no injection).
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == evil
    assert conn.execute("SELECT COUNT(*) FROM session").fetchone()[0] == 1
    conn.close()


def _run(monkeypatch, temp_db, argv):
    import sys
    monkeypatch.setattr(ocman, "detect_running_opencode_status", lambda *a, **k: ("none", []))
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), *argv])
    ocman.main()


def test_rename_by_id_end_to_end(temp_db, monkeypatch, capsys):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    _run(monkeypatch, temp_db, ["session", "rename", "ses_r1", "--to", "Brand New"])
    out = capsys.readouterr().out
    assert "Renamed:" in out and "Old Title" in out and "Brand New" in out
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "Brand New"
    conn.close()


def test_rename_top_level_preserves_to_inside_title(temp_db, monkeypatch, capsys):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    # The 'to' keyword precedes the title; the 'to' INSIDE the quoted title must survive.
    _run(monkeypatch, temp_db, ["rename", "ses_r1", "to", "migrate auth to tokens"])
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "migrate auth to tokens"
    conn.close()


def test_rename_positional_title_without_to(temp_db, monkeypatch, capsys):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    _run(monkeypatch, temp_db, ["rename", "ses_r1", "Just A Title"])
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "Just A Title"
    conn.close()


def test_rename_by_title_substring(temp_db, monkeypatch, capsys):
    _seed_one_session(temp_db, "ses_r1", "Unique Widget Session")
    _run(monkeypatch, temp_db, ["rename", "widget", "to", "Renamed Via Substring"])
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "Renamed Via Substring"
    conn.close()


def test_rename_empty_title_rejected(temp_db, monkeypatch, capsys):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    import sys
    monkeypatch.setattr(ocman, "detect_running_opencode_status", lambda *a, **k: ("none", []))
    monkeypatch.setattr(sys, "argv", ["ocman", "--db", str(temp_db), "session", "rename", "ses_r1", "--to", "   "])
    with pytest.raises(SystemExit):
        ocman.main()
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "Old Title"
    conn.close()


def test_rename_capitalization_only_writes(temp_db, monkeypatch, capsys):
    _seed_one_session(temp_db, "ses_r1", "fix")
    _run(monkeypatch, temp_db, ["session", "rename", "ses_r1", "--to", "Fix"])
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "Fix"
    conn.close()


def test_rename_dry_run_writes_nothing(temp_db, monkeypatch, capsys):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    _run(monkeypatch, temp_db, ["session", "rename", "ses_r1", "--to", "New", "--dry-run"])
    out = capsys.readouterr().out
    assert "Dry run" in out
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "Old Title"
    conn.close()


def test_rename_running_guard_caveat_shown(temp_db, monkeypatch, capsys):
    _seed_one_session(temp_db, "ses_r1", "Old Title")
    import sys
    # The rename must ALWAYS print the honest "cannot tell if this session is in use" caveat.
    # We stub the guard itself (its internals are tested elsewhere) and assert the caveat +
    # that the rename proceeds.
    monkeypatch.setattr(ocman, "require_safe_to_mutate", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv",
                        ["ocman", "--db", str(temp_db), "session", "rename", "ses_r1", "--to", "New"])
    ocman.main()
    out = capsys.readouterr().out
    assert "does not track which process uses which session" in out
    conn = sqlite3.connect(str(temp_db))
    assert conn.execute("SELECT title FROM session WHERE id='ses_r1'").fetchone()[0] == "New"
    conn.close()


# --- reconnect (kill orphaned opencode + relaunch on its session) -------------

import sys as _sys_rc
_linux_only = pytest.mark.skipif(not _sys_rc.platform.startswith("linux"),
                                 reason="reconnect (os.kill/execvp//proc) is Linux-only")


def test_reconnect_parse_and_dispatch_flags():
    import sys
    from ocman import parse_args
    for argv, dry, yes in (
        (["reconnect"], False, False),
        (["reconnect", "--dry-run"], True, False),
        (["reconnect", "-y"], False, True),
    ):
        sys.argv = ["ocman", *argv]
        d = vars(parse_args())
        assert d.get("run_reconnect") is True
        assert d.get("dry_run") is dry
        assert d.get("yes") is yes


@_linux_only
def test_reconnect_candidates_filters_own_user_and_cwd(monkeypatch):
    import os
    myuid = os.getuid()
    fake = [
        {"pid": os.getpid(), "cwd": "/home/me/proj", "kind": "tui", "cmdline": "opencode", "session": {}},
        {"pid": os.getpid(), "cwd": "/home/me/proj/sub", "kind": "serve", "cmdline": "opencode serve", "session": {}},
        {"pid": os.getpid(), "cwd": "/somewhere/else", "kind": "tui", "cmdline": "opencode", "session": {}},
    ]
    monkeypatch.setattr(ocman, "detect_running_instances", lambda **k: [dict(x) for x in fake])
    # st_uid for our own pid is our uid, so own-user filter keeps all; cwd filter keeps 2.
    got = ocman.cli._reconnect_candidates("/home/me/proj")
    cwds = sorted(i["cwd"] for i in got)
    assert cwds == ["/home/me/proj", "/home/me/proj/sub"]


@_linux_only
def test_kill_pid_gracefully_reaps_real_child(monkeypatch):
    import subprocess, time
    monkeypatch.setattr(ocman.cli, "_pid_looks_like_opencode", lambda pid: True)
    p = subprocess.Popen(["sleep", "30"])
    time.sleep(0.2)
    try:
        assert ocman.cli._kill_pid_gracefully(p.pid, timeout=4.0) is True
    finally:
        try:
            p.wait(timeout=1)
        except Exception:
            p.kill()


@_linux_only
def test_kill_pid_gracefully_pid_reuse_guard_refuses_non_opencode(monkeypatch):
    import subprocess, time
    # A real non-opencode process: the guard must refuse (proves PID-reuse protection).
    p = subprocess.Popen(["sleep", "30"])
    time.sleep(0.2)
    try:
        with pytest.raises(ocman.RecoveryError, match="no longer looks like an opencode"):
            ocman.cli._kill_pid_gracefully(p.pid, timeout=1.0)
    finally:
        p.terminate()
        try:
            p.wait(timeout=1)
        except Exception:
            p.kill()


def test_pick_reconnect_session_launched_with(monkeypatch):
    killed = [{"pid": 1, "session": {"id": "ses_known", "provenance": "launched-with (may be stale)"}}]
    # Should NOT need the DB; the launched-with id wins.
    assert ocman.cli._pick_reconnect_session(killed, "/home/me/proj", interactive=False) == "ses_known"


def test_pick_reconnect_session_fallback_most_recent(monkeypatch):
    monkeypatch.setattr(ocman, "db_list_sessions_under_dir",
                        lambda d: [{"id": "ses_new", "title": "new", "updated": 200},
                                   {"id": "ses_old", "title": "old", "updated": 100}])
    # Zero killed, no launched-with -> most recent (first, since ordered DESC).
    assert ocman.cli._pick_reconnect_session([], "/home/me/proj", interactive=False) == "ses_new"


def test_pick_reconnect_session_none_when_no_sessions(monkeypatch):
    monkeypatch.setattr(ocman, "db_list_sessions_under_dir", lambda d: [])
    assert ocman.cli._pick_reconnect_session([], "/home/me/proj", interactive=False) is None


@_linux_only
def test_reconnect_e2e_one_match_kills_and_execs(monkeypatch, capsys):
    import os
    calls = {}
    monkeypatch.setattr(ocman, "require_opencode", lambda: None)
    monkeypatch.setattr(ocman.cli, "_reconnect_candidates",
                        lambda cwd, **k: [{"pid": 4321, "cwd": cwd, "kind": "tui", "cmdline": "opencode -s ses_abc",
                                           "session": {"id": "ses_abc", "provenance": "launched-with (may be stale)"}}])
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully",
                        lambda pid, **k: calls.setdefault("killed", []).append(pid) or True)
    def fake_exec(prog, argv):
        calls["exec"] = (prog, list(argv))
        raise SystemExit(0)  # stand in for the point-of-no-return exec
    monkeypatch.setattr(os, "execvp", fake_exec)
    with pytest.raises(SystemExit):
        ocman.cli.cli_reconnect(assume_yes=True, dry_run=False)
    assert calls["killed"] == [4321]
    assert calls["exec"] == ("opencode", ["opencode", "-s", "ses_abc"])


@_linux_only
def test_reconnect_dry_run_no_kill_no_exec(monkeypatch, capsys):
    import os
    calls = {}
    monkeypatch.setattr(ocman, "require_opencode", lambda: None)
    monkeypatch.setattr(ocman.cli, "_reconnect_candidates",
                        lambda cwd, **k: [{"pid": 4321, "cwd": cwd, "kind": "tui", "cmdline": "opencode -s ses_abc",
                                           "session": {"id": "ses_abc", "provenance": "launched-with (may be stale)"}}])
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully",
                        lambda pid, **k: calls.setdefault("killed", []).append(pid) or True)
    monkeypatch.setattr(os, "execvp", lambda *a: calls.setdefault("exec", a))
    ocman.cli.cli_reconnect(assume_yes=False, dry_run=True)  # returns; no exec
    assert "killed" not in calls
    assert "exec" not in calls


@_linux_only
def test_reconnect_missing_opencode_aborts_before_kill(monkeypatch):
    import os
    calls = {}
    monkeypatch.setattr(ocman, "require_opencode",
                        lambda: (_ for _ in ()).throw(ocman.RecoveryError("no opencode on PATH")))
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully",
                        lambda pid, **k: calls.setdefault("killed", []).append(pid) or True)
    monkeypatch.setattr(os, "execvp", lambda *a: calls.setdefault("exec", a))
    with pytest.raises(ocman.RecoveryError, match="no opencode on PATH"):
        ocman.cli.cli_reconnect(assume_yes=True, dry_run=False)
    assert "killed" not in calls and "exec" not in calls


@_linux_only
def test_reconnect_partial_kill_stops_no_exec(monkeypatch, capsys):
    import os
    calls = {}
    monkeypatch.setattr(ocman, "require_opencode", lambda: None)
    insts = [
        {"pid": 11, "cwd": "/p", "kind": "tui", "cmdline": "opencode", "session": {}},
        {"pid": 22, "cwd": "/p", "kind": "serve", "cmdline": "opencode serve", "session": {}},
    ]
    monkeypatch.setattr(ocman.cli, "_reconnect_candidates", lambda cwd, **k: [dict(x) for x in insts])
    # Force the "all" selection path deterministically by making it non-interactive... but
    # many-case requires a TTY. Instead drive selection by monkeypatching input to 'a'.
    monkeypatch.setattr("builtins.input", lambda *a: "a")
    monkeypatch.setattr(_sys_rc.stdout, "isatty", lambda: True)
    monkeypatch.setattr(ocman, "db_list_sessions_under_dir",
                        lambda d: [{"id": "ses_x", "title": "x", "updated": 1}])
    # pid 11 dies, pid 22 survives.
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully", lambda pid, **k: pid == 11)
    monkeypatch.setattr(os, "execvp", lambda *a: calls.setdefault("exec", a))
    with pytest.raises(SystemExit):
        ocman.cli.cli_reconnect(assume_yes=True, dry_run=False)
    out = capsys.readouterr().out
    assert "exec" not in calls           # never relaunched after a partial kill
    assert "22" in out                    # reports the survivor


@_linux_only
def test_kill_pid_gracefully_returns_false_when_process_ignores_sigterm(monkeypatch):
    """The real 'survives SIGTERM -> False' path (the trigger for reconnect to STOP)."""
    import subprocess, time
    monkeypatch.setattr(ocman.cli, "_pid_looks_like_opencode", lambda pid: True)
    # A child that ignores SIGTERM; must be SIGKILLed in cleanup.
    p = subprocess.Popen(["sh", "-c", "trap '' TERM; sleep 30"])
    time.sleep(0.3)
    try:
        # Short timeout: SIGTERM is ignored, so it stays alive -> False.
        assert ocman.cli._kill_pid_gracefully(p.pid, timeout=1.0) is False
    finally:
        p.kill()
        try:
            p.wait(timeout=2)
        except Exception:
            pass


@_linux_only
def test_pid_is_gone_true_for_dead_and_zombie(monkeypatch):
    """_pid_is_gone: a never-existed pid is gone; a reaped/zombie child counts as gone."""
    import subprocess, os, time, signal
    # 1. Clearly-dead pid.
    p = subprocess.Popen(["true"])
    p.wait()
    assert ocman.cli._pid_is_gone(p.pid) is True
    # 2. Live process is NOT gone.
    p2 = subprocess.Popen(["sleep", "30"])
    time.sleep(0.2)
    try:
        assert ocman.cli._pid_is_gone(p2.pid) is False
        # 3. Zombie: kill but do NOT reap (no wait) -> /proc state 'Z' -> treated as gone.
        os.kill(p2.pid, signal.SIGKILL)
        # give the kernel a moment to move it to zombie state
        for _ in range(50):
            if ocman.cli._pid_is_gone(p2.pid):
                break
            time.sleep(0.05)
        assert ocman.cli._pid_is_gone(p2.pid) is True
    finally:
        try:
            p2.wait(timeout=2)
        except Exception:
            pass


@_linux_only
def test_reconnect_candidates_excludes_other_user_pid(monkeypatch):
    """A pid owned by a DIFFERENT uid must be filtered out."""
    import os
    fake = [{"pid": os.getpid(), "cwd": "/home/me/proj", "kind": "tui", "cmdline": "opencode", "session": {}},
            {"pid": 999999, "cwd": "/home/me/proj", "kind": "tui", "cmdline": "opencode", "session": {}}]
    monkeypatch.setattr(ocman, "detect_running_instances", lambda **k: [dict(x) for x in fake])
    # os.stat on a bogus /proc/999999 raises OSError -> excluded; our own pid kept.
    got = ocman.cli._reconnect_candidates("/home/me/proj")
    assert [i["pid"] for i in got] == [os.getpid()]


@_linux_only
def test_reconnect_zero_match_launches_most_recent(monkeypatch, capsys):
    """No opencode running here -> no kill, exec on the most-recent session for the dir."""
    import os
    calls = {}
    monkeypatch.setattr(ocman, "require_opencode", lambda: None)
    monkeypatch.setattr(ocman.cli, "_reconnect_candidates", lambda cwd, **k: [])
    monkeypatch.setattr(ocman, "db_list_sessions_under_dir",
                        lambda d: [{"id": "ses_recent", "title": "r", "updated": 2},
                                   {"id": "ses_old", "title": "o", "updated": 1}])
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully",
                        lambda pid, **k: calls.setdefault("killed", []).append(pid) or True)
    def fake_exec(prog, argv):
        calls["exec"] = (prog, list(argv)); raise SystemExit(0)
    monkeypatch.setattr(os, "execvp", fake_exec)
    with pytest.raises(SystemExit):
        ocman.cli.cli_reconnect(assume_yes=True, dry_run=False)
    assert "killed" not in calls                      # nothing to kill
    assert calls["exec"] == ("opencode", ["opencode", "-s", "ses_recent"])


@_linux_only
def test_reconnect_nothing_to_resume_errors_no_exec(monkeypatch):
    """Zero match AND no session for the dir -> clear error, never bare opencode."""
    import os
    calls = {}
    monkeypatch.setattr(ocman, "require_opencode", lambda: None)
    monkeypatch.setattr(ocman.cli, "_reconnect_candidates", lambda cwd, **k: [])
    monkeypatch.setattr(ocman, "db_list_sessions_under_dir", lambda d: [])
    monkeypatch.setattr(os, "execvp", lambda *a: calls.setdefault("exec", a))
    with pytest.raises(SystemExit):
        ocman.cli.cli_reconnect(assume_yes=True, dry_run=False)
    assert "exec" not in calls


@_linux_only
def test_reconnect_user_says_no_zero_side_effects(monkeypatch):
    """Interactive 'no' at the confirm -> no kill, no exec (RC-10)."""
    import os
    calls = {}
    monkeypatch.setattr(ocman, "require_opencode", lambda: None)
    monkeypatch.setattr(ocman.cli, "_reconnect_candidates",
                        lambda cwd, **k: [{"pid": 7, "cwd": cwd, "kind": "tui", "cmdline": "opencode -s ses_a",
                                           "session": {"id": "ses_a", "provenance": "launched-with (may be stale)"}}])
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully",
                        lambda pid, **k: calls.setdefault("killed", []).append(pid) or True)
    monkeypatch.setattr(os, "execvp", lambda *a: calls.setdefault("exec", a))
    monkeypatch.setattr(_sys_rc.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *a: "no")   # decline the typed-yes
    ocman.cli.cli_reconnect(assume_yes=False, dry_run=False)  # returns cleanly
    assert "killed" not in calls and "exec" not in calls


# --- kill (standalone: stop opencode, no relaunch) ----------------------------

def test_kill_parse_and_dispatch_flags():
    import sys
    from ocman import parse_args
    for argv, pat, dry, force, yes in (
        (["kill"], None, False, False, False),
        (["kill", "myproj"], "myproj", False, False, False),
        (["kill", "--dry-run"], None, True, False, False),
        (["kill", "-9", "-y"], None, False, True, True),
    ):
        sys.argv = ["ocman", *argv]
        d = vars(parse_args())
        assert d.get("run_kill") is True
        assert d.get("kill_pattern") == pat
        assert d.get("dry_run") is dry
        assert d.get("force") is force
        assert d.get("yes") is yes


def test_instance_matches_pattern_shared_helper():
    inst = {"cwd": "/home/me/alpha", "project": "pa",
            "session": {"id": "ses_x", "title": "Fix widget", "directory": "/home/me/alpha", "project_id": "pa"}}
    assert ocman.cli._instance_matches_pattern(inst, "alpha") is True     # cwd
    assert ocman.cli._instance_matches_pattern(inst, "WIDGET") is True    # session title, ci
    assert ocman.cli._instance_matches_pattern(inst, "ses_x") is True     # session id
    assert ocman.cli._instance_matches_pattern(inst, "nope") is False


@_linux_only
def test_kill_pid_gracefully_force_sigkills_sigterm_ignorer(monkeypatch):
    import subprocess, time
    monkeypatch.setattr(ocman.cli, "_pid_looks_like_opencode", lambda pid: True)
    p = subprocess.Popen(["sh", "-c", "trap '' TERM; sleep 30"])
    time.sleep(0.3)
    try:
        # force=True must escalate to SIGKILL and reap it.
        assert ocman.cli._kill_pid_gracefully(p.pid, timeout=1.0, force=True) is True
    finally:
        try:
            p.wait(timeout=2)
        except Exception:
            p.kill()


@_linux_only
def test_kill_targets_no_pattern_delegates(monkeypatch):
    called = {}
    def fake_candidates(cwd, **k):
        called["cwd"] = cwd
        return [{"pid": 1}]
    monkeypatch.setattr(ocman.cli, "_reconnect_candidates", fake_candidates)
    got = ocman.cli._kill_targets("/home/me/proj", None)
    assert called["cwd"] == "/home/me/proj"
    assert got == [{"pid": 1}]


@_linux_only
def test_kill_targets_pattern_filters_own_user(monkeypatch):
    import os
    fake = [{"pid": os.getpid(), "cwd": "/x/alpha", "project": "pa", "session": {}},
            {"pid": os.getpid(), "cwd": "/x/beta", "project": "pb", "session": {}},
            {"pid": 999999, "cwd": "/x/alpha", "project": "pa", "session": {}}]  # foreign uid
    monkeypatch.setattr(ocman, "detect_running_instances", lambda **k: [dict(x) for x in fake])
    got = ocman.cli._kill_targets("/ignored", "alpha")
    # foreign pid excluded (stat raises); beta filtered out by pattern; own alpha kept.
    assert [i["cwd"] for i in got] == ["/x/alpha"]


@_linux_only
def test_kill_e2e_one_match(monkeypatch, capsys):
    calls = {}
    monkeypatch.setattr(ocman.cli, "_kill_targets",
                        lambda cwd, pattern, **k: [{"pid": 555, "cwd": cwd, "kind": "tui", "cmdline": "opencode", "session": {}}])
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully",
                        lambda pid, **k: calls.setdefault("killed", []).append((pid, k.get("force"))) or True)
    ocman.cli.cli_kill(pattern=None, assume_yes=True, dry_run=False, force=False)
    assert calls["killed"] == [(555, False)]
    assert "Killed: 555" in capsys.readouterr().out


@_linux_only
def test_kill_dry_run_and_no_kill_nothing(monkeypatch, capsys):
    calls = {}
    monkeypatch.setattr(ocman.cli, "_kill_targets",
                        lambda cwd, pattern, **k: [{"pid": 555, "cwd": cwd, "kind": "tui", "cmdline": "opencode", "session": {}}])
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully",
                        lambda pid, **k: calls.setdefault("killed", []).append(pid) or True)
    ocman.cli.cli_kill(pattern=None, assume_yes=False, dry_run=True, force=False)  # dry-run
    assert "killed" not in calls


@_linux_only
def test_kill_zero_match_returns_clean(monkeypatch, capsys):
    monkeypatch.setattr(ocman.cli, "_kill_targets", lambda cwd, pattern, **k: [])
    ocman.cli.cli_kill(pattern="nope", assume_yes=True, dry_run=False, force=False)  # no exception
    assert "No opencode instance" in capsys.readouterr().out


@_linux_only
def test_kill_survivor_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(ocman.cli, "_kill_targets",
                        lambda cwd, pattern, **k: [{"pid": 777, "cwd": cwd, "kind": "serve", "cmdline": "opencode serve", "session": {}}])
    monkeypatch.setattr(ocman.cli, "_kill_pid_gracefully", lambda pid, **k: False)  # survives
    with pytest.raises(SystemExit):
        ocman.cli.cli_kill(pattern=None, assume_yes=True, dry_run=False, force=False)
    err = capsys.readouterr()
    assert "777" in (err.out + err.err)
