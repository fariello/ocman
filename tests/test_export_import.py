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
    bundle_project_data,
    extract_and_import_session,
    extract_and_import_project,
    RecoveryError,
)
from conftest import abs_path

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
    
    # Full-column project table (matches the real schema) so whole-project
    # export/import fidelity tests are meaningful. Existing tests that insert
    # only (id, worktree, name) still work: the rest default to NULL.
    cursor.execute("""
        CREATE TABLE project (
            id TEXT PRIMARY KEY,
            worktree TEXT,
            vcs TEXT,
            name TEXT,
            icon_url TEXT,
            icon_color TEXT,
            time_created INTEGER,
            time_updated INTEGER,
            time_initialized INTEGER,
            sandboxes TEXT,
            commands TEXT,
            icon_url_override TEXT
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
    # Project-scoped tables used by whole-project bundles.
    cursor.execute("""
        CREATE TABLE project_directory (
            project_id TEXT NOT NULL,
            directory TEXT NOT NULL,
            type TEXT,
            strategy TEXT,
            time_created INTEGER,
            PRIMARY KEY(project_id, directory)
        )
    """)
    cursor.execute("""
        CREATE TABLE workspace (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL DEFAULT 'local',
            name TEXT NOT NULL DEFAULT '',
            branch TEXT,
            directory TEXT,
            extra TEXT,
            project_id TEXT NOT NULL,
            time_used INTEGER NOT NULL DEFAULT 0
        )
    """)
    for table, col in ocman.SESSION_RELATIONAL_TABLES:
        if table == "session":
            continue
        # `part` needs a data column for content-bearing tests; others are minimal.
        if table == "part":
            cursor.execute(f"CREATE TABLE {table} (id TEXT, {col} TEXT, data TEXT)")
        else:
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


def test_bundle_session_data_no_leftover_temp(temp_db, tmp_path, monkeypatch):
    """PERF-5: export stages table JSONL in a per-run temp dir that is removed afterward;
    no ocman-export-* directories should be left behind."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/old/path', 'My Project')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('s1', 'proj-1', 'Root', '/old/path/s1')")
    cursor.execute("INSERT INTO message (id, session_id) VALUES ('m1', 's1')")
    conn.commit()
    conn.close()

    # Redirect the system temp dir to an isolated location we can inspect.
    fake_tmp = tmp_path / "systmp"
    fake_tmp.mkdir()
    monkeypatch.setattr(ocman.tempfile, "gettempdir", lambda: str(fake_tmp))

    bundle_file = tmp_path / "bundle.ocbox"
    bundle_session_data("s1", bundle_file)
    assert bundle_file.exists()

    # No per-run export staging directories should remain.
    leftovers = list(fake_tmp.glob("ocman-export-*"))
    assert leftovers == [], f"leftover export temp dirs: {leftovers}"


def test_import_session_dry_run_writes_nothing(temp_db, tmp_path, capsys):
    """F7: --dry-run reports the plan and writes nothing to the DB."""
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/old/path', 'My Project')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('s1', 'proj-1', 'Root', '/old/path/s1')")
    conn.commit()
    conn.close()
    bundle_file = tmp_path / "bundle.ocbox"
    bundle_session_data("s1", bundle_file)

    # Clear the DB so a real import would re-create the session.
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("DELETE FROM session")
    conn.commit(); conn.close()

    extract_and_import_session(bundle_file, target_project_id="proj-1", dry_run=True)
    out = capsys.readouterr().out
    assert "Import dry run" in out and "Dry run complete" in out

    # Nothing written.
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM session")
    assert cur.fetchone()[0] == 0
    conn.close()


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
    assert s_row == ("s1", "proj-1", "Root", str(Path("/old/path/s1")))

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


def test_import_session_collision_remaps_ids_in_diffs_no_substring_corruption(temp_db, tmp_path):
    """Characterization + correctness (PERF-1): on collision, every session id inside a
    stored diff file must be remapped to its new id by EXACT match, and an id that is a
    substring of an unrelated token must NOT be corrupted.

    Guards the structural-remap refactor: the old code did json.dumps + substring
    str.replace per id, which could corrupt substrings. The remap must be exact-id only.
    """
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/old/path', 'My Project')")
    # Two sessions; 's1' is a *substring* of the value 's1x' used elsewhere in the diff.
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('s1', 'proj-1', 'Root', '/old/path/s1')")
    cursor.execute("INSERT INTO session (id, project_id, title, directory, parent_id) VALUES ('s1x', 'proj-1', 'Child', '/old/path/s1/child', 's1')")
    conn.commit()
    conn.close()

    # Diff payloads: the string 's1' appears as an exact id value AND as a substring of 's1x'
    # and inside an unrelated token 'prefix-s1-suffix' that must be left untouched.
    diff1 = ocman.OPENCODE_STORAGE_DIR / "s1.json"
    diff1.write_text(json.dumps({"session_id": "s1", "note": "prefix-s1-suffix"}), encoding="utf-8")
    diff2 = ocman.OPENCODE_STORAGE_DIR / "s1x.json"
    diff2.write_text(json.dumps({"session_id": "s1x", "parent": "s1"}), encoding="utf-8")

    bundle_file = tmp_path / "bundle.ocbox"
    bundle_session_data("s1", bundle_file)

    # Import WITHOUT deleting originals -> collision -> ids remapped.
    imported_id = extract_and_import_session(bundle_file, target_project_id="proj-1")
    assert imported_id != "s1"
    assert imported_id.startswith("ses_")

    # Find the imported child (parent == imported root).
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM session WHERE parent_id = ?", (imported_id,))
    child_row = cursor.fetchone()
    conn.close()
    assert child_row is not None
    imported_child = child_row[0]
    assert imported_child not in ("s1", "s1x")

    # The imported root's diff: session_id remapped exactly; the unrelated 'prefix-s1-suffix'
    # token must NOT have its embedded 's1' rewritten (that was the substring-corruption bug).
    root_diff = json.loads((ocman.OPENCODE_STORAGE_DIR / f"{imported_id}.json").read_text(encoding="utf-8"))
    assert root_diff["session_id"] == imported_id
    assert root_diff["note"] == "prefix-s1-suffix", "unrelated substring must not be corrupted"

    # The imported child's diff: its own id and its parent id remapped exactly.
    child_diff = json.loads((ocman.OPENCODE_STORAGE_DIR / f"{imported_child}.json").read_text(encoding="utf-8"))
    assert child_diff["session_id"] == imported_child
    assert child_diff["parent"] == imported_id


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


def test_import_session_legacy_db_data_json_roundtrip(temp_db, tmp_path):
    """TEST-8: positive round-trip for the legacy single-blob db_data.json import format
    (previously only exercised by the SQLi/traversal rejection tests)."""
    bundle_file = tmp_path / "legacy.ocbox"
    meta = {
        "export_version": "1.0",
        "exported_at": "2026-06-25T12:00:00",
        "main_session_id": "legacy1",
        "all_session_ids": ["legacy1"],
        "source_project": {"id": "proj-1", "name": "Legacy", "worktree": "/old/path"},
    }
    db_data = {
        "session": [
            {"id": "legacy1", "project_id": "proj-1", "title": "Legacy Root", "directory": "/old/path/legacy1"}
        ],
        "message": [
            {"id": "lm1", "session_id": "legacy1"}
        ],
    }
    with zipfile.ZipFile(bundle_file, "w") as zipf:
        zipf.writestr("meta.json", json.dumps(meta))
        zipf.writestr("db_data.json", json.dumps(db_data))

    # Target project must exist for remap.
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', '/old/path', 'Legacy')")
    conn.commit()
    conn.close()

    imported_id = extract_and_import_session(bundle_file, target_project_id="proj-1")
    assert imported_id == "legacy1"

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_id, title FROM session WHERE id = 'legacy1'")
    assert cursor.fetchone() == ("legacy1", "proj-1", "Legacy Root")
    cursor.execute("SELECT id, session_id FROM message WHERE id = 'lm1'")
    assert cursor.fetchone() == ("lm1", "legacy1")
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



# ---------------------------------------------------------------------------
# Whole-project export/import (.ocbox) - IPD 20260708-project-export
# ---------------------------------------------------------------------------


def _seed_project(db_path, *, proj_id="p1", worktree=None,
                  sessions=(("sroot", None), ("ssub", "sroot")),
                  with_scoped=True, full_project=True):
    """Insert a project with sessions (+ a part row + a diff file) into temp_db."""
    # Default worktree must be OS-appropriate absolute (Windows: drive-anchored),
    # since ocman refuses a non-absolute bundle worktree on import.
    if worktree is None:
        worktree = abs_path("/home/me/proj")
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    if full_project:
        c.execute(
            "INSERT INTO project (id, worktree, vcs, name, commands) "
            "VALUES (?,?,?,?,?)",
            (proj_id, worktree, "git", "My Proj", "cmd"),
        )
    else:
        c.execute("INSERT INTO project (id, worktree, name) VALUES (?,?,?)",
                  (proj_id, worktree, "My Proj"))
    for sid, parent in sessions:
        c.execute(
            "INSERT INTO session (id, project_id, parent_id, title, directory) "
            "VALUES (?,?,?,?,?)",
            (sid, proj_id, parent, f"title {sid}", worktree),
        )
    c.execute("INSERT INTO part (id, session_id, data) VALUES ('pt1', ?, ?)",
              (sessions[0][0], json.dumps({"type": "text", "text": "hi"})))
    if with_scoped:
        c.execute("INSERT INTO project_directory (project_id, directory, type, time_created) "
                  "VALUES (?,?,?,?)", (proj_id, worktree, "main", 1))
        c.execute("INSERT INTO workspace (id, type, name, project_id, time_used) "
                  "VALUES ('w1','local','ws',?,5)", (proj_id,))
    conn.commit()
    conn.close()
    # a session-diff file for the root session
    (ocman.OPENCODE_STORAGE_DIR / f"{sessions[0][0]}.json").write_text(
        json.dumps({"x": 1}), encoding="utf-8"
    )


def _wipe_all(db_path):
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    for t in ("session", "project_directory", "workspace", "part", "project"):
        c.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()
    for f in list(ocman.OPENCODE_STORAGE_DIR.glob("*.json")):
        f.unlink()


def test_bundle_project_data_contents(temp_db, tmp_path):
    _seed_project(temp_db)
    box = tmp_path / "p.ocbox"
    bundle_project_data("p1", box)
    with zipfile.ZipFile(box) as zf:
        names = set(zf.namelist())
        meta = json.loads(zf.read("meta.json").decode())
    assert meta["kind"] == "project"
    assert meta["main_session_id"] is None
    assert set(meta["all_session_ids"]) == {"sroot", "ssub"}
    for t in ("project", "project_directory", "workspace", "session", "part"):
        assert f"db_data/{t}.jsonl" in names, t
    assert "session_diffs/sroot.json" in names


def test_bundle_project_empty_errors(temp_db, tmp_path):
    conn = sqlite3.connect(str(temp_db))
    conn.execute("INSERT INTO project (id, worktree, name) VALUES ('empty', '/x', 'E')")
    conn.commit()
    conn.close()
    with pytest.raises(RecoveryError, match="no sessions"):
        bundle_project_data("empty", tmp_path / "e.ocbox")


def test_project_roundtrip_full_fidelity(temp_db, tmp_path):
    _seed_project(temp_db)
    box = tmp_path / "p.ocbox"
    bundle_project_data("p1", box)
    _wipe_all(temp_db)

    dest = extract_and_import_project(box, interactive=False)
    assert dest == "p1"

    conn = sqlite3.connect(str(temp_db))
    c = conn.cursor()
    # full project row restored (not just id/name/worktree)
    row = c.execute("SELECT id, vcs, name, commands FROM project").fetchone()
    assert row == ("p1", "git", "My Proj", "cmd")
    assert {r[0] for r in c.execute("SELECT id FROM session")} == {"sroot", "ssub"}
    assert c.execute("SELECT project_id FROM project_directory").fetchone()[0] == "p1"
    assert c.execute("SELECT project_id FROM workspace").fetchone()[0] == "p1"
    assert c.execute("SELECT session_id FROM part").fetchone()[0] == "sroot"
    conn.close()
    assert (ocman.OPENCODE_STORAGE_DIR / "sroot.json").exists()


def test_project_import_refuses_collision_non_interactive(temp_db, tmp_path):
    _seed_project(temp_db)
    box = tmp_path / "p.ocbox"
    bundle_project_data("p1", box)
    # project still present -> collision -> non-interactive must refuse
    with pytest.raises(RecoveryError, match="already exists"):
        extract_and_import_project(box, interactive=False)


def test_project_import_new_project_path_rebases(temp_db, tmp_path):
    seeded_worktree = abs_path("/home/me/proj")
    _seed_project(temp_db, worktree=seeded_worktree)
    box = tmp_path / "p.ocbox"
    bundle_project_data("p1", box)
    # original project stays; import as a new project at a new worktree.
    # Use a real path under tmp_path (portable) rather than a hardcoded /home/me path.
    # Compare via realpath on BOTH sides so a symlinked temp dir (macOS resolves
    # /var -> /private/var) does not cause a spurious prefix mismatch.
    new_root = tmp_path / "copy"
    expected = os.path.realpath(str(new_root))
    old_root = os.path.realpath(str(Path(seeded_worktree).expanduser()))
    dest = extract_and_import_project(box, new_project_path=str(new_root), interactive=False)
    assert dest != "p1"
    conn = sqlite3.connect(str(temp_db))
    c = conn.cursor()
    # sessions collided -> rewritten under the new project, directory rebased
    rows = c.execute("SELECT project_id, directory FROM session WHERE project_id = ?", (dest,)).fetchall()
    assert rows, "new-project sessions missing"
    for _, d in rows:
        real_d = os.path.realpath(d)
        # Every rebased session dir must live at or under the NEW project root.
        # os.path.commonpath compares whole components, so it will not be fooled
        # by a sibling like ".../copy2". This proves the rebase happened, and it
        # is portable (macOS resolves /var -> /private/var identically on both
        # sides via realpath).
        assert os.path.commonpath([real_d, expected]) == expected, (real_d, expected)
        # And none may still sit under the OLD worktree (not left un-rebased).
        assert not real_d.startswith(old_root + os.sep) and real_d != old_root, real_d
    conn.close()


def test_project_import_merge_does_not_clobber_metadata(temp_db, tmp_path):
    _seed_project(temp_db)
    box = tmp_path / "p.ocbox"
    bundle_project_data("p1", box)
    # A distinct target project to merge INTO.
    conn = sqlite3.connect(str(temp_db))
    conn.execute("INSERT INTO project (id, worktree, vcs, name, commands) "
                 "VALUES ('target', '/t', 'hg', 'Target Name', 'tcmd')")
    conn.commit()
    conn.close()

    dest = extract_and_import_project(box, target_project_id="target", interactive=False)
    assert dest == "target"
    conn = sqlite3.connect(str(temp_db))
    c = conn.cursor()
    # target's own metadata is untouched (not overwritten by the bundle's project row)
    assert c.execute("SELECT name, vcs, commands FROM project WHERE id='target'").fetchone() \
        == ("Target Name", "hg", "tcmd")
    # imported sessions are attached to the target
    assert {r[0] for r in c.execute("SELECT project_id FROM session")} <= {"p1", "target"}
    assert any(pid == "target" for (pid,) in c.execute("SELECT project_id FROM session"))
    conn.close()


def test_project_import_back_compat_session_bundle(temp_db, tmp_path):
    """A legacy session bundle (no meta.kind) still imports as a session."""
    _seed_project(temp_db, sessions=(("s1", None),))
    box = tmp_path / "s.ocbox"
    bundle_session_data("s1", box)  # session bundle: no kind
    with zipfile.ZipFile(box) as zf:
        assert "kind" not in json.loads(zf.read("meta.json").decode())
    _wipe_all(temp_db)
    # session importer path: reuse existing project id via source_project
    conn = sqlite3.connect(str(temp_db))
    conn.execute("INSERT INTO project (id, worktree, name) VALUES ('p1',?,'P')",
                 (abs_path("/home/me/proj"),))
    conn.commit()
    conn.close()
    imported = extract_and_import_session(box, target_project_id="p1")
    assert imported == "s1"


def test_project_import_rejects_bad_worktree(temp_db, tmp_path):
    _seed_project(temp_db)
    box = tmp_path / "p.ocbox"
    bundle_project_data("p1", box)
    # Corrupt the bundle's project worktree to a traversal path.
    import io
    src = zipfile.ZipFile(box)
    meta = json.loads(src.read("meta.json").decode())
    meta["source_project"]["worktree"] = "../../etc"
    members = {n: src.read(n) for n in src.namelist()}
    src.close()
    members["meta.json"] = json.dumps(meta).encode()
    with zipfile.ZipFile(box, "w") as zf:
        for n, data in members.items():
            zf.writestr(n, data)
    with pytest.raises(RecoveryError, match="(traversal|absolute)"):
        extract_and_import_project(box, interactive=False)


def test_project_import_rollback_no_orphan(temp_db, tmp_path, monkeypatch):
    """A Phase-3 failure must leave NO partial state, including no orphan project row."""
    _seed_project(temp_db)
    box = tmp_path / "p.ocbox"
    bundle_project_data("p1", box)
    _wipe_all(temp_db)

    # Force a failure during the diff-restore step (inside the import transaction).
    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(ocman, "_remap_ids_in_json", boom)

    # No collision (project wiped), but make session ids collide to trigger the
    # remap path we just sabotaged: re-seed a colliding session id.
    conn = sqlite3.connect(str(temp_db))
    z_wt = abs_path("/z")
    conn.execute("INSERT INTO project (id, worktree, name) VALUES ('z',?,'Z')", (z_wt,))
    conn.execute("INSERT INTO session (id, project_id, parent_id, title, directory) "
                 "VALUES ('sroot','z',NULL,'x',?)", (z_wt,))
    conn.commit()
    conn.close()

    # bundle's project id 'p1' does not exist now, so Axis A = create-from-bundle;
    # session 'sroot' collides -> remap path -> boom.
    with pytest.raises(RecoveryError, match="Project import failed"):
        extract_and_import_project(box, interactive=False)

    conn = sqlite3.connect(str(temp_db))
    c = conn.cursor()
    # The bundle's project 'p1' must NOT have been left behind (no orphan row).
    assert c.execute("SELECT COUNT(*) FROM project WHERE id='p1'").fetchone()[0] == 0
    # Pre-existing unrelated project/session survive untouched.
    assert c.execute("SELECT COUNT(*) FROM project WHERE id='z'").fetchone()[0] == 1
    conn.close()


def test_project_import_rebases_when_worktree_canonicalizes(temp_db, tmp_path, monkeypatch):
    """Rebase must survive a worktree that the OS canonicalizes to a different path.

    On macOS, /home, /var, /tmp are firmlinks, so Path("/home/me/proj").resolve()
    yields "/System/Volumes/Data/home/me/proj". _validate_worktree_path resolves the
    bundle worktree, so if the rebase then compared that RESOLVED prefix against the
    RAW stored session.directory ("/home/me/proj"), the prefix would not match and the
    session directory would be left un-rebased under the old worktree. This is the
    macOS-only CI failure of test_project_import_new_project_path_rebases; it is
    reproduced here on any OS by simulating the firmlink, and guards the fix (rebase
    now resolves the stored directory before matching, via _rebased_dir).
    """
    import pathlib

    real_resolve = pathlib.Path.resolve

    def fake_resolve(self, *a, **k):
        s = str(self)
        if s == "/home/me/proj" or s.startswith("/home/me/proj/"):
            return pathlib.PurePosixPath("/System/Volumes/Data" + s)
        return real_resolve(self, *a, **k)

    monkeypatch.setattr(pathlib.Path, "resolve", fake_resolve)

    real_realpath = os.path.realpath

    def fake_realpath(p, *a, **k):
        p = os.fspath(p)
        if p == "/home/me/proj" or p.startswith("/home/me/proj/"):
            return "/System/Volumes/Data" + p
        return real_realpath(p, *a, **k)

    monkeypatch.setattr(os.path, "realpath", fake_realpath)

    _seed_project(temp_db, worktree="/home/me/proj")
    box = tmp_path / "p.ocbox"
    bundle_project_data("p1", box)
    new_root = tmp_path / "copy"
    expected = real_realpath(str(new_root))
    dest = extract_and_import_project(box, new_project_path=str(new_root), interactive=False)
    conn = sqlite3.connect(str(temp_db))
    rows = conn.execute("SELECT directory FROM session WHERE project_id=?", (dest,)).fetchall()
    conn.close()
    assert rows, "new-project sessions missing"
    for (d,) in rows:
        # The rebased dir must live under the NEW root, never still under the old worktree.
        assert not d.startswith("/home/me/proj"), ("session left un-rebased", d)
        assert os.path.commonpath([real_realpath(d), expected]) == expected, (d, expected)
