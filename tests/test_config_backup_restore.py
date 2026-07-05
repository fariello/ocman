import os
import sqlite3
import pytest
import zipfile
import contextlib
from pathlib import Path
import ocman
from ocman import (
    load_ocman_config,
    save_ocman_config,
    cli_create_config,
    cli_backup,
    cli_restore,
    cli_clean_backups,
    DEFAULT_CONFIG,
    RecoveryError,
)

@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    # Mock config path
    cfg_path = tmp_path / "ocman_test.toml"
    monkeypatch.setattr(ocman, "OCMAN_CONFIG_PATH", cfg_path)
    
    # Save original DB, History, and Storage paths
    orig_db = ocman.OPENCODE_DB_PATH
    orig_hist = ocman.OPENCODE_HISTORY_PATH
    orig_storage = ocman.OPENCODE_STORAGE_DIR
    
    # Setup mock active DB and History
    db_path = tmp_path / "active_opencode.db"
    hist_path = tmp_path / "active_history.json"
    mock_storage = tmp_path / "mock_session_diff"
    mock_storage.mkdir(parents=True, exist_ok=True)
    
    # Create simple DB to backup
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE project (id TEXT PRIMARY KEY, name TEXT)")
    cursor.execute("INSERT INTO project VALUES ('p1', 'Test Project')")
    conn.commit()
    conn.close()
    
    # Create history file
    hist_path.write_text('{"runs": []}', encoding="utf-8")
    
    # Set ocman globals
    ocman.OPENCODE_DB_PATH = db_path
    ocman.OPENCODE_HISTORY_PATH = hist_path
    ocman.OPENCODE_STORAGE_DIR = mock_storage
    
    # Mock home directories / default paths
    test_config = dict(DEFAULT_CONFIG)
    test_config["db_path"] = str(db_path)
    test_config["history_path"] = str(hist_path)
    test_config["default_backup_dir"] = str(tmp_path / "backups")
    
    # Write to custom config path
    save_ocman_config(test_config, cfg_path)
    
    yield {
        "cfg_path": cfg_path,
        "db_path": db_path,
        "hist_path": hist_path,
        "tmp_path": tmp_path,
        "config": test_config,
        "storage": mock_storage
    }
    
    # Restore original paths
    ocman.OPENCODE_DB_PATH = orig_db
    ocman.OPENCODE_HISTORY_PATH = orig_hist
    ocman.OPENCODE_STORAGE_DIR = orig_storage


def test_load_save_config(temp_env):
    cfg_path = temp_env["cfg_path"]
    cfg = load_ocman_config(cfg_path)
    assert cfg["db_path"] == str(temp_env["db_path"])
    assert cfg["default_retention_days"] == 5
    
    cfg["default_retention_days"] = 10
    save_ocman_config(cfg, cfg_path)
    
    new_cfg = load_ocman_config(cfg_path)
    assert new_cfg["default_retention_days"] == 10

def test_create_config_non_interactive(temp_env, monkeypatch):
    # Mock isatty to return False (non-interactive)
    monkeypatch.setattr(ocman.sys.stdin, "isatty", lambda: False)
    
    cfg_path = temp_env["cfg_path"]
    if cfg_path.exists():
        cfg_path.unlink()
        
    cli_create_config(force=True)
    assert cfg_path.exists()
    
    cfg = load_ocman_config(cfg_path)
    assert cfg["db_path"].endswith("opencode.db")

def test_backup_opencode(temp_env):
    tmp_path = temp_env["tmp_path"]
    dest_zip = tmp_path / "test_backup.zip"
    
    archive = cli_backup(str(dest_zip))
    assert archive.exists()
    assert zipfile.is_zipfile(archive)
    
    with zipfile.ZipFile(archive, "r") as zf:
        namelist = zf.namelist()
        assert "opencode.db" in namelist
        assert "ocman_history.json" in namelist
        assert "ocman.toml" in namelist

def test_restore_from_zip(temp_env):
    tmp_path = temp_env["tmp_path"]
    dest_zip = tmp_path / "test_backup.zip"
    
    # 1. Create a backup of the current state
    cli_backup(str(dest_zip))
    
    # 2. Modify the active database to simulate change
    conn = sqlite3.connect(str(temp_env["db_path"]))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO project VALUES ('p2', 'New Project')")
    conn.commit()
    conn.close()
    
    # Verify p2 exists
    conn = sqlite3.connect(str(temp_env["db_path"]))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM project")
    assert cursor.fetchone()[0] == 2
    conn.close()
    
    # 3. Restore from backup (which only has p1)
    cli_restore(str(dest_zip))
    
    # 4. Verify database has been restored (p2 should be gone)
    conn = sqlite3.connect(str(temp_env["db_path"]))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM project")
    assert cursor.fetchone()[0] == 1
    conn.close()

def test_restore_rollback_safety(temp_env, monkeypatch):
    tmp_path = temp_env["tmp_path"]
    dest_zip = tmp_path / "test_backup.zip"
    
    # 1. Create a backup
    cli_backup(str(dest_zip))
    
    # 2. Mock shutil.copy2 to fail midway to trigger rollback
    original_copy2 = ocman.shutil.copy2
    def mock_copy_fail(src, dst):
        if "active_opencode.db" in str(dst) or "opencode.db" in str(dst):
            raise IOError("Simulated write failure")
        return original_copy2(src, dst)
        
    monkeypatch.setattr(ocman.shutil, "copy2", mock_copy_fail)
    
    # 3. Restoring should raise RecoveryError due to simulated copy failure
    with pytest.raises(RecoveryError, match="Restoration failed and rolled back"):
        cli_restore(str(dest_zip))
        
    # 4. Ensure original state is intact (rollback succeeded)
    conn = sqlite3.connect(str(temp_env["db_path"]))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM project")
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_restore_rejects_zip_slip(temp_env, tmp_path):
    """Regression (20260703-134213-S2-S1): a restore ZIP containing a path-traversal
    member must be rejected rather than extracted outside the destination."""
    malicious_zip = tmp_path / "malicious_backup.zip"
    with zipfile.ZipFile(malicious_zip, "w") as zf:
        # A valid-looking db so structure checks are not the first failure...
        zf.writestr("opencode.db", "dummy")
        # ...and a traversal member that would escape the extraction dir.
        zf.writestr("../../evil.txt", "pwned")

    with pytest.raises(RecoveryError, match="unsafe archive member"):
        cli_restore(str(malicious_zip))

    # Ensure nothing was written outside the intended area.
    assert not (tmp_path.parent / "evil.txt").exists()


def test_history_runs_capped_on_save(temp_env, monkeypatch):
    """PERF-4: _save_history trims the runs list to history_max_runs (oldest dropped),
    preserves cumulative totals, and load does not mutate an over-cap file."""
    from ocman import _load_history, _save_history

    # Set a small cap via the config the code reads at save time.
    cfg = load_ocman_config(temp_env["cfg_path"])
    cfg["history_max_runs"] = 5
    save_ocman_config(cfg, temp_env["cfg_path"])
    monkeypatch.setattr(ocman, "OCMAN_CONFIG_PATH", temp_env["cfg_path"])

    data = _load_history()
    data["cumulative"]["sessions_deleted"] = 42
    data["runs"] = [{"n": i} for i in range(20)]  # 20 > cap of 5
    _save_history(data)

    reloaded = _load_history()
    assert len(reloaded["runs"]) == 5
    # Newest kept (15..19), oldest dropped.
    assert reloaded["runs"][0]["n"] == 15
    assert reloaded["runs"][-1]["n"] == 19
    # Cumulative totals untouched by trimming.
    assert reloaded["cumulative"]["sessions_deleted"] == 42


def test_history_max_runs_zero_means_unlimited(temp_env, monkeypatch):
    """PERF-4: history_max_runs = 0 disables trimming."""
    from ocman import _load_history, _save_history

    cfg = load_ocman_config(temp_env["cfg_path"])
    cfg["history_max_runs"] = 0
    save_ocman_config(cfg, temp_env["cfg_path"])
    monkeypatch.setattr(ocman, "OCMAN_CONFIG_PATH", temp_env["cfg_path"])

    data = _load_history()
    data["runs"] = [{"n": i} for i in range(30)]
    _save_history(data)
    assert len(_load_history()["runs"]) == 30


def test_clean_backups(temp_env, monkeypatch):
    import time
    
    backup_dir = Path(temp_env["config"]["default_backup_dir"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some mock backup files and directories
    zip_old = backup_dir / "opencode-backup-20260101-120000.zip"
    zip_new = backup_dir / "opencode-backup-20260624-120000.zip"
    dir_old = backup_dir / "opencode-db-cleanup-20260101-120000"
    dir_old.mkdir(exist_ok=True)
    (dir_old / "opencode.db").write_text("dummy", encoding="utf-8")
    
    zip_old.write_text("old", encoding="utf-8")
    zip_new.write_text("new", encoding="utf-8")
    
    # Modify mtimes to make some old and some new
    now = time.time()
    os.utime(zip_old, (now - 10 * 86400, now - 10 * 86400)) # 10 days old
    os.utime(dir_old, (now - 10 * 86400, now - 10 * 86400)) # 10 days old
    os.utime(zip_new, (now - 2 * 86400, now - 2 * 86400))   # 2 days old
    
    # Mock input to confirm deletion
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    
    # Clean backups older than 5 days
    cli_clean_backups(days=5, dry_run=False, verbosity=0)
    
    # Check that old backups are deleted, new one remains
    assert not zip_old.exists()
    assert not dir_old.exists()
    assert zip_new.exists()


def _seed_backups(backup_dir):
    """Seed one old + one new backup; return (old, new) paths."""
    import time
    backup_dir.mkdir(parents=True, exist_ok=True)
    old = backup_dir / "opencode-db-cleanup-20260101-120000"
    old.mkdir(exist_ok=True)
    (old / "opencode.db").write_text("x" * 100, encoding="utf-8")
    new = backup_dir / "opencode-backup-20260624-120000.zip"
    new.write_text("new", encoding="utf-8")
    now = time.time()
    os.utime(old, (now - 10 * 86400, now - 10 * 86400))
    os.utime(new, (now - 2 * 86400, now - 2 * 86400))
    return old, new


def test_clean_backups_cancel_on_non_yes(temp_env, monkeypatch):
    """Characterization: any non-'yes' confirmation cancels; nothing is deleted."""
    backup_dir = Path(temp_env["config"]["default_backup_dir"])
    old, new = _seed_backups(backup_dir)
    monkeypatch.setattr("builtins.input", lambda _: "no")
    cli_clean_backups(days=5, dry_run=False, verbosity=0)
    assert old.exists() and new.exists()  # nothing deleted on cancel


def test_clean_backups_dry_run_deletes_nothing(temp_env, monkeypatch):
    """Characterization: dry-run never prompts and never deletes."""
    backup_dir = Path(temp_env["config"]["default_backup_dir"])
    old, new = _seed_backups(backup_dir)
    def _no_input(_):
        raise AssertionError("dry-run must not prompt")
    monkeypatch.setattr("builtins.input", _no_input)
    cli_clean_backups(days=5, dry_run=True, verbosity=0)
    assert old.exists() and new.exists()  # nothing deleted in dry-run


def test_clean_backups_preview_shows_keep_and_delete(temp_env, monkeypatch, capsys):
    """CB-1/CB-9/CB-10: preview shows a header, both KEEP and DELETE rows, and right-aligned Size."""
    backup_dir = Path(temp_env["config"]["default_backup_dir"])
    old, new = _seed_backups(backup_dir)
    monkeypatch.setattr("builtins.input", lambda _: "no")
    cli_clean_backups(days=5, dry_run=True, verbosity=0)
    out = capsys.readouterr().out
    assert "Action" in out and "Modified" in out and "Backups" in out  # header (CB-9)
    assert "DELETE" in out and "KEEP" in out                            # both partitions (CB-1)
    assert "backups to delete" in out and "kept" in out                 # summary


def test_clean_backups_all_deleted_warning(temp_env, monkeypatch, capsys):
    """CB-2: when every backup is past the cutoff, a forceful all-backups warning appears."""
    import time
    backup_dir = Path(temp_env["config"]["default_backup_dir"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    b = backup_dir / "opencode-db-cleanup-20260101-120000"
    b.mkdir(exist_ok=True)
    (b / "opencode.db").write_text("x", encoding="utf-8")
    now = time.time()
    os.utime(b, (now - 10 * 86400, now - 10 * 86400))
    monkeypatch.setattr("builtins.input", lambda _: "no")
    cli_clean_backups(days=5, dry_run=True, verbosity=0)
    out = capsys.readouterr().out
    assert "ALL 1 backups" in out and "nothing will remain" in out


def test_render_destructive_preview_days_column():
    """Days column: shown when show_age, header 'Days', values right-aligned to 2 decimals."""
    from ocman import DestructivePreview, PreviewItem, render_destructive_preview
    p = DestructivePreview(
        remove=[PreviewItem("big", 4_760_000_000, "d1", age_days=1.2345),
                PreviewItem("small", 57344, "d2", age_days=0.07)],
        keep=[], action_verb="delete", noun="backups", detail_header="Modified",
        show_age=True, age_header="Days",
    )
    out = render_destructive_preview(p)
    assert "Days" in out.splitlines()[0]          # header present
    assert "1.23" in out and "0.07" in out         # 2-decimal formatting (rounds 1.2345 -> 1.23)
    # Right-aligned: the two age tokens end at the same column.
    import re
    data_rows = [ln for ln in out.splitlines() if "d1" in ln or "d2" in ln]
    edges = []
    for ln in data_rows:
        m = re.search(r"\b\d+\.\d{2}\b", ln)
        assert m is not None
        edges.append(m.end())
    assert edges[0] == edges[1]


def test_render_destructive_preview_no_days_when_disabled():
    """Days column is absent when show_age is False (other ops)."""
    from ocman import DestructivePreview, PreviewItem, render_destructive_preview
    p = DestructivePreview(
        remove=[PreviewItem("x", 1, "d")], keep=[],
        action_verb="delete", noun="items", detail_header="Detail",
    )
    assert "Days" not in render_destructive_preview(p).splitlines()[0]


def test_render_destructive_preview_right_aligned_size():
    """CB-10: the Size column is right-aligned (values share a right edge)."""
    from ocman import DestructivePreview, PreviewItem, render_destructive_preview
    p = DestructivePreview(
        remove=[PreviewItem("big", 4_760_000_000, "d1"), PreviewItem("small", 57344, "d2")],
        keep=[], action_verb="delete", noun="backups", detail_header="Modified",
    )
    lines = render_destructive_preview(p).splitlines()
    # Find the two data rows and confirm the size token ends at the same column.
    data_rows = [ln for ln in lines if "d1" in ln or "d2" in ln]
    assert len(data_rows) == 2
    def size_right_edge(ln):
        # size cell is the second whitespace-separated field group; locate "GB"/"KB"/"B"
        import re
        m = list(re.finditer(r"\d[\d.]* (?:GB|MB|KB|B)", ln))
        return m[0].end()
    assert size_right_edge(data_rows[0]) == size_right_edge(data_rows[1])
