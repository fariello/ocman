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
from conftest import abs_path

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
    # OS-appropriate absolute paths (Windows: drive-anchored) so the stored
    # values are genuine absolute paths on every platform.
    proj_wt = abs_path("/path/to/project1")
    sess_dir = abs_path("/path/to/project1/session1")
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', ?, 'Project 1')", (proj_wt,))
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'Session 1', ?)", (sess_dir,))
    conn.commit()
    conn.close()

    proj = db_find_project("proj-1")
    assert proj is not None
    assert proj[0] == "proj-1"
    assert proj[1] == proj_wt

    # Find project by path
    proj_by_path = db_find_project(proj_wt)
    assert proj_by_path is not None
    assert proj_by_path[0] == "proj-1"

    sess = db_find_session("sess-1")
    assert sess is not None
    assert sess[0] == "sess-1"
    assert sess[1] == sess_dir
    assert sess[2] == "proj-1"


def test_db_move_project_metadata(temp_db):
    old_wt = abs_path("/path/to/project1")
    new_wt = abs_path("/new/path/project1")
    other = abs_path("/other/path")
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', ?, 'Project 1')", (old_wt,))
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'Session 1', ?)", (abs_path("/path/to/project1/session1"),))
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-2', 'proj-1', 'Session 2', ?)", (old_wt,))
    # A session outside the project path that should not be touched
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-3', 'proj-1', 'Session 3', ?)", (other,))
    conn.commit()
    conn.close()

    db_move_project_metadata("proj-1", old_wt, new_wt)

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    
    cursor.execute("SELECT worktree FROM project WHERE id = 'proj-1'")
    assert cursor.fetchone()[0] == str(Path(new_wt).resolve())

    cursor.execute("SELECT id, directory FROM session ORDER BY id")
    rows = cursor.fetchall()
    assert rows[0] == ("sess-1", str(Path(abs_path("/new/path/project1/session1")).resolve()))
    assert rows[1] == ("sess-2", str(Path(new_wt).resolve()))
    # Unrelated session directory is left untouched (stored verbatim).
    assert rows[2] == ("sess-3", other)
    conn.close()


def test_db_move_session_metadata(temp_db):
    old_dir = abs_path("/path/to/sess1")
    new_dir = abs_path("/new/path/sess1")
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'Session 1', ?)", (old_dir,))
    # Nested session
    cursor.execute("INSERT INTO session (id, project_id, title, directory, parent_id) VALUES ('sess-2', 'proj-1', 'Session 2', ?, 'sess-1')", (abs_path("/path/to/sess1/nested"),))
    conn.commit()
    conn.close()

    db_move_session_metadata("sess-1", old_dir, new_dir)

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id, directory FROM session ORDER BY id")
    rows = cursor.fetchall()
    assert rows[0] == ("sess-1", str(Path(new_dir).resolve()))
    assert rows[1] == ("sess-2", str(Path(abs_path("/new/path/sess1/nested")).resolve()))
    conn.close()


def test_db_rebase_paths(temp_db):
    other_wt = abs_path("/other/prefix/project2")
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', ?, 'Project 1')", (abs_path("/old/prefix/project1"),))
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-2', ?, 'Project 2')", (other_wt,))
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'Session 1', ?)", (abs_path("/old/prefix/project1/session1"),))
    conn.commit()
    conn.close()

    stats = db_rebase_paths(abs_path("/old/prefix"), abs_path("/new/prefix"))
    assert stats["projects_updated"] == 1
    assert stats["sessions_updated"] == 1

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT id, worktree FROM project ORDER BY id")
    proj_rows = cursor.fetchall()
    assert proj_rows[0] == ("proj-1", str(Path(abs_path("/new/prefix/project1")).resolve()))
    # Unrelated project worktree is left untouched (stored verbatim).
    assert proj_rows[1] == ("proj-2", other_wt)

    cursor.execute("SELECT id, directory FROM session ORDER BY id")
    sess_rows = cursor.fetchall()
    assert sess_rows[0] == ("sess-1", str(Path(abs_path("/new/prefix/project1/session1")).resolve()))
    conn.close()


def test_db_move_project_metadata_non_canonical_path(temp_db):
    """Characterization (PERF-3): a stored directory with non-canonical components
    (`..`) still matches/rebases because comparison resolves the path. Guards the
    shared-helper refactor against silently switching to raw-string matching."""
    old_wt = abs_path("/path/to/project1")
    new_wt = abs_path("/new/path/project1")
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj-1', ?, 'Project 1')", (old_wt,))
    # Non-canonical stored dir that resolves to .../project1/session1
    cursor.execute("INSERT INTO session (id, project_id, title, directory) VALUES ('sess-1', 'proj-1', 'S1', ?)", (abs_path("/path/to/project1/sub/../session1"),))
    conn.commit()
    conn.close()

    db_move_project_metadata("proj-1", old_wt, new_wt)

    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT directory FROM session WHERE id = 'sess-1'")
    # Resolves to .../session1 and is rebased under the new prefix.
    assert cursor.fetchone()[0] == str(Path(abs_path("/new/path/project1/session1")).resolve())
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
    old_wt = abs_path("/nonexistent/old")
    new_wt = abs_path("/nonexistent/new")
    # Setup some test data
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', ?, 'n1')", (old_wt,))
    conn.commit()
    conn.close()

    # Call main with 'project move ... --metadata-only'
    monkeypatch.setattr("sys.argv", ["ocman", "project", "move", "p1", "--to", new_wt, "--metadata-only"])
    
    # Run main, should not raise SystemExit with failure code
    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0 or e.code is None

    # Verify metadata was updated
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT worktree FROM project WHERE id = 'p1'")
    assert cursor.fetchone()[0] == str(Path(new_wt).resolve())
    conn.close()


def test_cli_move_project_missing_directory_prompt(temp_db, monkeypatch):
    old_wt = abs_path("/nonexistent/old")
    new_wt = abs_path("/nonexistent/new")
    # Setup some test data
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', ?, 'n1')", (old_wt,))
    conn.commit()
    conn.close()

    # Call main without --metadata-only, mock isatty and input.
    # New UX: a missing source shows a menu (1 = metadata-only), then a final
    # typed-'yes' confirm. Route each input by prompt text.
    monkeypatch.setattr("sys.argv", ["ocman", "project", "move", "p1", "--to", new_wt])
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    def fake_input(prompt):
        return "yes" if "yes" in prompt.lower() else "1"
    monkeypatch.setattr("builtins.input", fake_input)

    try:
        ocman.main()
    except SystemExit as e:
        assert e.code == 0 or e.code is None

    # Verify metadata was updated because we said yes to prompt
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()
    cursor.execute("SELECT worktree FROM project WHERE id = 'p1'")
    assert cursor.fetchone()[0] == str(Path(new_wt).resolve())
    conn.close()


# ---- Git-aware / remote-runbook move (IPD 20260711) ------------------------

def test_parse_move_dest():
    from ocman import _parse_move_dest
    assert _parse_move_dest("host:/path") == (True, "host", "/path")
    assert _parse_move_dest("user@host:/srv/proj") == (True, "user@host", "/srv/proj")
    assert _parse_move_dest("host:relative/dir") == (True, "host", "relative/dir")
    # Local paths (including Windows drives) are NOT remote.
    assert _parse_move_dest("/local/path")[0] is False
    assert _parse_move_dest("./rel")[0] is False
    assert _parse_move_dest("~/x")[0] is False
    assert _parse_move_dest("C:\\proj")[0] is False
    assert _parse_move_dest("C:/proj")[0] is False
    assert _parse_move_dest("")[0] is False


def _fake_git(monkeypatch, status_lines, is_worktree=True):
    """Patch run_git so git_state parses canned 'status --porcelain=v1 -b' output."""
    import subprocess

    def fake_run_git(repo, args, *, check=True):
        if args[:1] == ["rev-parse"]:
            out = "true\n" if is_worktree else "false\n"
            return subprocess.CompletedProcess(args, 0 if is_worktree else 1, stdout=out, stderr="")
        if args[:1] == ["status"]:
            return subprocess.CompletedProcess(args, 0, stdout="\n".join(status_lines) + "\n", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(ocman, "run_git", fake_run_git)


def test_git_state_clean_in_sync(monkeypatch, tmp_path):
    _fake_git(monkeypatch, ["## main...origin/main"])
    gs = ocman.git_state(tmp_path)
    assert gs["clean"] and gs["upstream"] and gs["ahead"] == 0 and gs["behind"] == 0


def test_git_state_ahead_behind(monkeypatch, tmp_path):
    _fake_git(monkeypatch, ["## main...origin/main [ahead 2, behind 1]"])
    gs = ocman.git_state(tmp_path)
    assert gs["ahead"] == 2 and gs["behind"] == 1 and gs["clean"]


def test_git_state_dirty(monkeypatch, tmp_path):
    _fake_git(monkeypatch, ["## main", " M file1.py", "?? new.txt", "A  staged.py"])
    gs = ocman.git_state(tmp_path)
    assert gs["dirty"] and gs["modified"] == 1 and gs["untracked"] == 1 and gs["staged"] == 1
    assert gs["upstream"] is False


def test_git_state_not_a_repo(monkeypatch, tmp_path):
    _fake_git(monkeypatch, [], is_worktree=False)
    assert ocman.git_state(tmp_path) is None


def test_remote_runbook_quotes_and_no_network(monkeypatch, tmp_path, capsys):
    """A remote move prints a runbook with shell-quoted values and runs NO network I/O."""
    import subprocess
    # Guard: local git inspection is allowed, but NO network transfer (ssh/scp/rsync,
    # or tar piped over ssh) may be spawned during a print-only remote move.
    real_run = subprocess.run
    def guarded_run(cmd, *a, **k):
        argv0 = (cmd[0] if isinstance(cmd, (list, tuple)) else str(cmd)).split("/")[-1]
        if argv0 in ("ssh", "scp", "rsync", "tar"):
            raise AssertionError(f"unexpected network subprocess: {cmd}")
        # Allow local git (source-repo inspection); everything else runs normally.
        return real_run(cmd, *a, **k)
    monkeypatch.setattr(subprocess, "run", guarded_run)
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)  # non-interactive -> no menus/confirm

    src = tmp_path / "my proj;rm -rf"  # space + shell metacharacters
    src.mkdir()
    ocman._execute_move(
        kind="session", spec="ses_x", id_for_metadata="ses_x", source_dir=str(src),
        project_id=None, dst="build@host:/srv/dest dir", metadata_only=False,
        confirm_remote_delete=False, assume_yes=True, force=False, verbosity=0,
    )
    out = capsys.readouterr().out
    assert "REMOTE MOVE RUNBOOK" in out
    assert "ocman session import" in out and "--new-project-path" in out
    # The dangerous source path must appear shell-quoted in the tar command
    # (shlex.quote wraps the whole path because it contains a space + ';').
    assert f"tar -C '{src}'" in out
    # The metacharacter must never appear as a bare, unquoted shell token.
    assert ";rm -rf -cz" not in out
    # Remote dest with a space is safely quoted inside the ssh payload.
    assert "'/srv/dest dir'" in out


def test_move_dry_run_changes_nothing(temp_db, monkeypatch, tmp_path, capsys):
    """F7: --dry-run reports the plan and moves nothing (local dest)."""
    import ocman
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    src = tmp_path / "srcproj"; src.mkdir()
    cur.execute("INSERT INTO project (id, worktree, name) VALUES ('p1', ?, 'P1')", (str(src),))
    conn.commit(); conn.close()
    dst = tmp_path / "dstproj"
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    ocman._execute_move(
        kind="project", spec="p1", id_for_metadata="p1", source_dir=str(src),
        project_id="p1", dst=str(dst), metadata_only=False,
        confirm_remote_delete=False, assume_yes=True, force=False, verbosity=0,
        dry_run=True,
    )
    out = capsys.readouterr().out
    assert "Dry run complete" in out
    assert src.exists() and not dst.exists()  # nothing moved
    # DB worktree unchanged.
    conn = sqlite3.connect(str(temp_db)); cur = conn.cursor()
    cur.execute("SELECT worktree FROM project WHERE id='p1'")
    assert cur.fetchone()[0] == str(src)
    conn.close()


def test_confirm_remote_delete_requires_remote(monkeypatch, tmp_path):
    """--confirm-remote-delete only applies to a remote destination."""
    with pytest.raises(SystemExit):
        ocman._execute_move(
            kind="session", spec="ses_x", id_for_metadata="ses_x",
            source_dir=str(tmp_path), project_id=None, dst="/local/only",
            metadata_only=False, confirm_remote_delete=True, assume_yes=True,
            force=False, verbosity=0,
        )


# --- TF-01 (follow-up IPD): pure _git_decisions_for_state branch tests --------

def _gs(**over):
    base = {"dirty": False, "staged": 0, "modified": 0, "untracked": 0, "other": 0,
            "clean": True, "upstream": True, "ahead": 0, "behind": 0}
    base.update(over)
    return base


def test_git_decisions_not_a_repo():
    cmds, labels, needs_bulk = ocman.cli._git_decisions_for_state(None)
    assert cmds == [] and needs_bulk is True
    assert any("not a git repo" in l for l in labels)


def test_git_decisions_clean_in_sync():
    cmds, labels, needs_bulk = ocman.cli._git_decisions_for_state(_gs())
    assert cmds == [] and needs_bulk is False
    assert any("in sync" in l for l in labels)


def test_git_decisions_clean_no_upstream():
    cmds, labels, needs_bulk = ocman.cli._git_decisions_for_state(_gs(upstream=False))
    assert cmds == [] and needs_bulk is False
    assert any("no upstream" in l for l in labels)


def test_git_decisions_ahead_push():
    cmds, labels, needs_bulk = ocman.cli._git_decisions_for_state(
        _gs(clean=False, ahead=2), divergence_choice=1)
    assert cmds == [["push"]] and needs_bulk is False
    # skip variant
    cmds2, _, _ = ocman.cli._git_decisions_for_state(_gs(clean=False, ahead=2), divergence_choice=2)
    assert cmds2 == []


def test_git_decisions_ahead_and_behind_pushpull():
    cmds, _, _ = ocman.cli._git_decisions_for_state(
        _gs(clean=False, ahead=1, behind=1), divergence_choice=1)
    assert cmds == [["push"], ["pull"]]
    cmds_p, _, _ = ocman.cli._git_decisions_for_state(_gs(clean=False, ahead=1, behind=1), divergence_choice=2)
    assert cmds_p == [["push"]]
    cmds_l, _, _ = ocman.cli._git_decisions_for_state(_gs(clean=False, ahead=1, behind=1), divergence_choice=3)
    assert cmds_l == [["pull"]]
    cmds_n, _, _ = ocman.cli._git_decisions_for_state(_gs(clean=False, ahead=1, behind=1), divergence_choice=4)
    assert cmds_n == []


def test_git_decisions_dirty_abort_raises():
    with pytest.raises(ocman.RecoveryError, match="aborted"):
        ocman.cli._git_decisions_for_state(_gs(dirty=True, clean=False, staged=1), dirty_choice=1)


def test_git_decisions_dirty_commit_staged_needs_bulk():
    cmds, labels, needs_bulk = ocman.cli._git_decisions_for_state(
        _gs(dirty=True, clean=False, staged=1, modified=2), dirty_choice=2)
    assert cmds == [["commit", "-m", "ocman move: commit staged changes"]]
    assert needs_bulk is True  # unstaged/untracked left behind -> only bulk carries them


def test_git_decisions_dirty_add_all():
    cmds, _, needs_bulk = ocman.cli._git_decisions_for_state(
        _gs(dirty=True, clean=False, modified=1), dirty_choice=3)
    assert cmds == [["add", "-A"], ["commit", "-m", "ocman move: commit all changes"]]
    assert needs_bulk is False


def test_git_decisions_dirty_no_commit_needs_bulk():
    cmds, _, needs_bulk = ocman.cli._git_decisions_for_state(
        _gs(dirty=True, clean=False, modified=1), dirty_choice=4)
    assert cmds == [] and needs_bulk is True
