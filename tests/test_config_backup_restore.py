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
