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
