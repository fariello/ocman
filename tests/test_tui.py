import os
import sqlite3
import pytest
from pathlib import Path
import ocman
from ocman_tui.app import OrsessionApp, DeletionSafetyModal, PostExecutionSummaryModal
from ocman_tui.widgets.sidebar import SidebarWidget
from ocman_tui.widgets.database import DatabaseAdminWidget
from textual.widgets import Tree, DataTable, Markdown, Input, Checkbox, RichLog, Button, Select

@pytest.fixture
def tui_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_opencode.db"
    
    # Mock config path to a temp location
    cfg_path = tmp_path / "ocman_test.toml"
    monkeypatch.setattr(ocman, "OCMAN_CONFIG_PATH", cfg_path)
    
    # Write default test config
    test_config = dict(ocman.DEFAULT_CONFIG)
    test_config["db_path"] = str(db_path)
    test_config["history_path"] = str(tmp_path / "test_ocman_history.json")
    test_config["default_backup_dir"] = str(tmp_path / "backups")
    ocman.save_ocman_config(test_config, cfg_path)
    
    # Save original DB and history path
    orig_path = ocman.OPENCODE_DB_PATH
    orig_history_path = ocman.OPENCODE_HISTORY_PATH
    
    ocman.OPENCODE_DB_PATH = db_path
    ocman.OPENCODE_HISTORY_PATH = tmp_path / "test_ocman_history.json"

    # Isolate the rollback-backup family: destructive ops compute their backup dir
    # inline as Path.home()/.local/share/opencode/backups/..., so redirect Path.home()
    # to tmp_path to avoid writing real backup directories into the developer's HOME.
    fake_home = tmp_path / "home"
    fake_home.mkdir(exist_ok=True)
    monkeypatch.setattr(ocman.Path, "home", staticmethod(lambda: fake_home))
    
    # Wrap deletion functions to print exceptions to stderr
    orig_del_session = ocman.db_delete_session_recursive
    def debug_del_session(*args, **kwargs):
        try:
            return orig_del_session(*args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
    
    import ocman_tui.app
    import ocman_tui.core
    monkeypatch.setattr(ocman, "db_delete_session_recursive", debug_del_session)
    monkeypatch.setattr(ocman_tui.app, "db_delete_session_recursive", debug_del_session)
    monkeypatch.setattr(ocman_tui.core, "db_delete_session_recursive", debug_del_session)

    orig_del_project = ocman.db_delete_project_recursive
    def debug_del_project(*args, **kwargs):
        try:
            return orig_del_project(*args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
    monkeypatch.setattr(ocman, "db_delete_project_recursive", debug_del_project)
    monkeypatch.setattr(ocman_tui.app, "db_delete_project_recursive", debug_del_project)
    monkeypatch.setattr(ocman_tui.core, "db_delete_project_recursive", debug_del_project)
    
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
    for table, col in ocman.SESSION_RELATIONAL_TABLES:
        if table == "session":
            continue
        cursor.execute(f"CREATE TABLE {table} (id TEXT, {col} TEXT)")
        
    # Seed mock data
    cursor.execute("INSERT INTO project (id, worktree, name) VALUES ('proj1', '/path/to/proj', 'Proj 1')")
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
    
    yield db_path
    
    # Restore original paths
    ocman.OPENCODE_DB_PATH = orig_path
    ocman.OPENCODE_HISTORY_PATH = orig_history_path


def _seed_tui_conversation(db_path):
    """Upgrade the stub message/part tables to the real schema and seed a conversation
    for 'sess1' so extract-on-delete has something to render."""
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS message")
    cur.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, "
                "time_created INTEGER, time_updated INTEGER, data TEXT)")
    cur.execute("DROP TABLE IF EXISTS part")
    cur.execute("CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, "
                "time_created INTEGER, time_updated INTEGER, data TEXT)")
    cur.execute("INSERT INTO message VALUES ('m1','sess1',1000,1000,?)", ('{"role":"user"}',))
    cur.execute("INSERT INTO message VALUES ('m2','sess1',1001,1001,?)", ('{"role":"assistant"}',))
    cur.execute("INSERT INTO part VALUES ('p1','m1','sess1',1000,1000,?)",
                ('{"type":"text","text":"Please add a login button."}',))
    cur.execute("INSERT INTO part VALUES ('p2','m2','sess1',1001,1001,?)",
                ('{"type":"text","text":"Added the login button and handler."}',))
    conn.commit()
    conn.close()


@pytest.mark.anyio
async def test_tui_delete_writes_extracts_when_checked(tui_db, tmp_path, monkeypatch):
    """Phase 1: TUI session delete writes recovery extracts by default (checkbox on)."""
    _seed_tui_conversation(tui_db)
    out = tmp_path / "tui-recovery"
    # Point the recovery out-dir at a temp location via config.
    cfg = ocman.load_ocman_config()
    cfg["default_out_dir"] = str(out)
    ocman.save_ocman_config(cfg, ocman.OCMAN_CONFIG_PATH)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        app.selected_session_id = "sess1"
        app.selected_session_title = "Session 1"
        app.confirm_and_delete_session()
        await pilot.pause()
        assert isinstance(app.screen, DeletionSafetyModal)
        # Checkbox defaults to ON.
        assert app.screen.query_one("#check-del-extracts", Checkbox).value is True
        await pilot.click("#input-confirm-yes")
        await pilot.press(*"yes")
        await pilot.pause()
        await pilot.click("#btn-confirm-del")
        for _ in range(50):
            if isinstance(app.screen, PostExecutionSummaryModal):
                break
            await pilot.pause(0.1)
        assert isinstance(app.screen, PostExecutionSummaryModal)

    assert out.exists()
    names = [p.name for p in out.iterdir()]
    assert any(n.endswith(".restart.md") for n in names)
    assert any(n.endswith(".transcript.md") for n in names)
    assert any(n.endswith(".prompt.md") for n in names)


@pytest.mark.anyio
async def test_tui_delete_skips_extracts_when_unchecked(tui_db, tmp_path, monkeypatch):
    """Phase 1: unchecking the extracts box skips recovery-file writing."""
    _seed_tui_conversation(tui_db)
    out = tmp_path / "tui-recovery-off"
    cfg = ocman.load_ocman_config()
    cfg["default_out_dir"] = str(out)
    ocman.save_ocman_config(cfg, ocman.OCMAN_CONFIG_PATH)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        app.selected_session_id = "sess1"
        app.selected_session_title = "Session 1"
        app.confirm_and_delete_session()
        await pilot.pause()
        assert isinstance(app.screen, DeletionSafetyModal)
        await pilot.click("#check-del-extracts")  # toggle OFF
        await pilot.pause()
        assert app.screen.query_one("#check-del-extracts", Checkbox).value is False
        await pilot.click("#input-confirm-yes")
        await pilot.press(*"yes")
        await pilot.pause()
        await pilot.click("#btn-confirm-del")
        for _ in range(50):
            if isinstance(app.screen, PostExecutionSummaryModal):
                break
            await pilot.pause(0.1)
        assert isinstance(app.screen, PostExecutionSummaryModal)

    assert not out.exists()


@pytest.mark.anyio
async def test_tui_clear_history(tui_db):
    """Phase 1: the clear-history button wipes the ledger (runs + cumulative totals)."""
    from ocman_tui.app import ClearHistoryModal
    # Seed a non-empty ledger.
    ocman._save_history({
        "cumulative": {"sessions_deleted": 3, "cost_deleted": 1.5},
        "runs": [{"action": "delete"}],
    })
    app = OrsessionApp()
    async with app.run_test() as pilot:
        app.query_one("#btn-clear-history-log", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, ClearHistoryModal)
        await pilot.click("#input-clear-history-yes")
        await pilot.press(*"yes")
        await pilot.pause()
        await pilot.click("#btn-confirm-clear-history")
        await pilot.pause()

    hist = ocman._load_history()
    assert hist["runs"] == []
    assert hist["cumulative"]["sessions_deleted"] == 0
    assert hist["cumulative"]["cost_deleted"] == 0.0


def test_safe_call_from_thread_swallows_stopped_app():
    """Regression (20260703-134213-S2-B2): background workers that outlive the app
    must not crash when marshalling a callback into a stopped event loop."""
    app = OrsessionApp()

    # 1. When shutting down, the callback is dropped and nothing is called.
    app._shutting_down = True
    calls = []
    app._safe_call_from_thread(lambda: calls.append("x"))
    assert calls == []

    # 2. When call_from_thread raises "App is not running", it is swallowed.
    app._shutting_down = False

    def boom(*_a, **_k):
        raise RuntimeError("App is not running")

    app.call_from_thread = boom  # type: ignore[assignment]
    # Must not raise:
    app._safe_call_from_thread(lambda: calls.append("y"))


@pytest.mark.anyio
async def test_tui_app_startup(tui_db):
    """Test that OrsessionApp starts up without errors and populates the sidebar and workspace."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        # Check app metadata title
        assert "Ocman TUI" in app.title

        # Check that sidebar widget is compose-loaded
        sidebar = app.query_one("#sidebar", SidebarWidget)
        assert sidebar is not None
        
        # Check that tree root contains project node
        assert len(sidebar.root.children) == 1
        project_node = sidebar.root.children[0]
        assert "Proj 1" in str(project_node.label)


@pytest.mark.anyio
async def test_tui_database_admin_widget(tui_db):
    """Test the Database Administration widget metrics refresh."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        db_admin = app.query_one(DatabaseAdminWidget)
        assert db_admin is not None
        
        # Verify labels update
        proj_label = db_admin.query_one("#lbl-total-projects").render()
        sess_label = db_admin.query_one("#lbl-total-sessions").render()
        assert str(proj_label) == "1"
        assert str(sess_label) == "2"


@pytest.mark.anyio
async def test_tui_models_widget(tui_db):
    """Test the Models Library table displays available models."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        # Switch to models tab/pane
        app.query_one("TabbedContent").active = "tab-models"
        await pilot.pause()
        
        # Verify DataTable is populated
        table = app.query_one("#models-table", DataTable)
        assert table is not None


@pytest.mark.anyio
async def test_tui_app_deletion(tui_db):
    """Test that the session deletion flow successfully invokes the background worker and deletes a session."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        # Select session in the app
        app.selected_session_id = "sess1"
        app.selected_session_title = "Session 1"
        
        # Trigger confirmation modal
        app.confirm_and_delete_session()
        await pilot.pause()
        
        # Check that the DeletionSafetyModal is active
        assert isinstance(app.screen, DeletionSafetyModal)
        
        # Enter "yes" in the input field
        await pilot.click("#input-confirm-yes")
        await pilot.press(*"yes")
        await pilot.pause()
        
        # Click the confirm button
        await pilot.click("#btn-confirm-del")
        await pilot.pause()
        
        # Wait for the background worker thread to complete and UI to update
        for _ in range(50):
            if isinstance(app.screen, PostExecutionSummaryModal):
                break
            await pilot.pause(0.1)
        assert isinstance(app.screen, PostExecutionSummaryModal)
        
        # Verify that the session has been deleted from the database
        sqlite3 = ocman._get_sqlite()
        conn = sqlite3.connect(str(tui_db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM session WHERE id = 'sess1'")
        assert cursor.fetchone()[0] == 0
        conn.close()


@pytest.mark.anyio
async def test_tui_app_deletion_metadata_fetch_fails(tui_db, monkeypatch):
    """Regression (20260703-134213-S2-E1): if fetching session metadata for the
    summary fails, the successful deletion must still render the summary rather
    than crash with UnboundLocalError on the (previously) unbound summary locals."""
    # Force the metadata formatting to raise so the summary locals would be unbound
    # under the old code, while the delete itself (separate query) still succeeds.
    import ocman_tui.app as tui_app_mod
    monkeypatch.setattr(ocman, "_fmt_ts", lambda *_a, **_k: (_ for _ in ()).throw(ValueError("boom")))

    app = OrsessionApp()
    async with app.run_test() as pilot:
        app.selected_session_id = "sess1"
        app.selected_session_title = "Session 1"

        app.confirm_and_delete_session()
        await pilot.pause()
        assert isinstance(app.screen, DeletionSafetyModal)

        await pilot.click("#input-confirm-yes")
        await pilot.press(*"yes")
        await pilot.pause()
        await pilot.click("#btn-confirm-del")
        await pilot.pause()

        # The worker must reach the summary modal (no UnboundLocalError crash).
        for _ in range(50):
            if isinstance(app.screen, PostExecutionSummaryModal):
                break
            await pilot.pause(0.1)
        assert isinstance(app.screen, PostExecutionSummaryModal)


@pytest.mark.anyio
async def test_tui_compaction_end_to_end_network_mocked(tui_db, tmp_path, monkeypatch):
    """TEST-1 (assess-testing): drive the TUI compaction path with ONLY the network mocked
    (not the ocman functions), so the real render_compact_prompt/call_compaction_api calls
    execute. This is red on the pre-fix code (wrong arity + str-treated-as-dict) and green
    after the fix. Asserts a .compacted.md file is written and success (not failure) notified.
    """
    import json as _json
    import ocman_tui.app as app_mod
    from ocman import ModelInfo

    # Compaction writes to Path("opencode-recovery") relative to cwd.
    monkeypatch.chdir(tmp_path)

    # Provide a resolvable model without touching the real opencode config (config/model
    # resolution is prerequisite plumbing, not the code under test).
    fake_model = ModelInfo("prov", "m1", "Model 1", "https://api.example.com/v1", "sk-test", 1.0, 2.0, True)
    monkeypatch.setattr(app_mod, "load_opencode_config", lambda *a, **k: {})
    monkeypatch.setattr(app_mod, "extract_models_from_config", lambda *a, **k: [fake_model])
    monkeypatch.setattr(app_mod, "resolve_model", lambda *a, **k: fake_model)

    # Mock ONLY the network: a valid completions payload.
    class _Resp:
        def __init__(self, payload):
            self._d = _json.dumps(payload).encode("utf-8")
        def read(self):
            return self._d
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    import ocman as ocman_mod
    monkeypatch.setattr(
        ocman_mod.urllib.request,
        "urlopen",
        lambda *a, **k: _Resp({"choices": [{"message": {"content": "COMPACTED OUTPUT"}}], "usage": {}}),
    )

    app = OrsessionApp()
    async with app.run_test() as pilot:
        # Set up the state run_llm_compaction requires.
        app.selected_session_id = "sess1"
        app.selected_session_title = "Session 1"
        app.current_turns = [ocman.Turn("user", "hi", 1, "s"), ocman.Turn("assistant", "hello", 2, "s")]
        # Point the model Select at our fake model spec.
        sel = app.query_one("#select-compaction-model", Select)
        sel.set_options([("Model 1", "prov/m1")])
        sel.value = "prov/m1"

        notes = []
        monkeypatch.setattr(app, "notify", lambda msg, **k: notes.append(msg))

        app.run_llm_compaction()

        # Wait for the background worker to finish.
        for _ in range(50):
            if not app.compaction_running:
                break
            await pilot.pause(0.1)

        out_files = list((tmp_path / "opencode-recovery").glob("*.compacted.md"))
        assert out_files, f"no compacted file written; notes={notes}"
        assert out_files[0].read_text(encoding="utf-8") == "COMPACTED OUTPUT"
        assert any("successfully" in n.lower() for n in notes), f"expected success notice, got {notes}"
        assert not any("failed" in n.lower() for n in notes), f"unexpected failure notice: {notes}"
        # S3-T1: pin TUI/CLI naming parity - the TUI must use the canonical scheme with the FULL
        # session id (not truncated), parseable by the CLI's parse_recovery_name as a compacted kind.
        sid, dt, kind = ocman.parse_recovery_name(out_files[0])
        assert kind == "compacted" and sid == "sess1" and dt is not None, out_files[0].name


@pytest.mark.anyio
async def test_tui_compaction_honors_out_dir_and_copies_to_project(tui_db, tmp_path, monkeypatch):
    """S3-T1 (release-review): the TUI compaction path honors the configured default_out_dir and
    invokes maybe_copy_compacted_to_project (CLI parity), with the network mocked."""
    import json as _json
    import ocman_tui.app as app_mod
    import ocman as ocman_mod
    from ocman import ModelInfo

    out_dir = tmp_path / "custom-out"
    monkeypatch.chdir(tmp_path)
    # Configured out dir differs from the old hardcoded "opencode-recovery".
    monkeypatch.setattr(app_mod, "load_ocman_config", lambda *a, **k: {
        "default_out_dir": str(out_dir), "copy_restart_to_project_prompts": True,
    })
    monkeypatch.setattr(app_mod, "load_opencode_config", lambda *a, **k: {})
    fake_model = ModelInfo("prov", "m1", "Model 1", "https://api.example.com/v1", "sk-test", 1.0, 2.0, True)
    monkeypatch.setattr(app_mod, "extract_models_from_config", lambda *a, **k: [fake_model])
    monkeypatch.setattr(app_mod, "resolve_model", lambda *a, **k: fake_model)

    class _Resp:
        def __init__(self, payload): self._d = _json.dumps(payload).encode("utf-8")
        def read(self): return self._d
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(ocman_mod.urllib.request, "urlopen",
                        lambda *a, **k: _Resp({"choices": [{"message": {"content": "OUT"}}], "usage": {}}))

    # Capture the compacted-copy parity call.
    copied = {}
    monkeypatch.setattr(ocman_mod, "maybe_copy_compacted_to_project",
                        lambda path, session, project_dir, enabled, verbosity=0: copied.update(
                            path=path, sid=session.session_id, enabled=enabled) or None)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        app.selected_session_id = "sess1"
        app.selected_session_title = "Session 1"
        app.current_turns = [ocman.Turn("user", "hi", 1, "s"), ocman.Turn("assistant", "hello", 2, "s")]
        sel = app.query_one("#select-compaction-model", Select)
        sel.set_options([("Model 1", "prov/m1")]); sel.value = "prov/m1"
        monkeypatch.setattr(app, "notify", lambda msg, **k: None)
        app.run_llm_compaction()
        for _ in range(50):
            if not app.compaction_running:
                break
            await pilot.pause(0.1)

    # Honors configured out dir (not the hardcoded "opencode-recovery").
    out_files = list(out_dir.glob("*.compacted.md"))
    assert out_files, f"expected output in {out_dir}"
    assert not (tmp_path / "opencode-recovery").exists()
    # Invoked the compacted-copy parity with the full session id.
    assert copied.get("sid") == "sess1" and copied.get("enabled") is True


@pytest.mark.anyio
async def test_tui_app_pruning(tui_db):
    """Test that the database admin prune operation completes successfully in the background."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        # Switch to database administration tab/pane
        app.query_one("TabbedContent").active = "tab-admin"
        await pilot.pause()
        
        # Verify we are on Database widget
        db_admin = app.query_one(DatabaseAdminWidget)
        assert db_admin is not None
        
        # Set retention days to 5 to trigger cleanup of old seed data
        db_admin.query_one("#input-retention-days", Input).value = "5"
        
        # Uncheck dry run so it performs actual deletions
        db_admin.query_one("#check-dry-run", Checkbox).value = False
        
        # Check force to bypass active process checks
        db_admin.query_one("#check-force", Checkbox).value = True
        
        # Trigger prune programmatically
        db_admin.query_one("#btn-run-prune").press()
        await pilot.pause()
        
        # Wait for the worker thread to finish
        for _ in range(50):
            sqlite3 = ocman._get_sqlite()
            conn = sqlite3.connect(str(tui_db))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM session")
            cnt = cursor.fetchone()[0]
            conn.close()
            if cnt == 0:
                break
            await pilot.pause(0.1)
        
        # Verify metrics updated and sessions are deleted
        sqlite3 = ocman._get_sqlite()
        conn = sqlite3.connect(str(tui_db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM session")
        assert cursor.fetchone()[0] == 0
        conn.close()


@pytest.mark.anyio
async def test_tui_config_tab(tui_db, tmp_path):
    """Test TUI configuration settings load, save, reset, and auto-save on submit/change."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        # Switch to config tab
        app.query_one("TabbedContent").active = "tab-config"
        await pilot.pause()

        # Check default value is loaded
        db_input = app.query_one("#cfg-db-path", Input)
        assert db_input.value == str(tui_db)

        # Modify values and trigger auto-save via submit
        new_db_path = tmp_path / "new_opencode.db"
        db_input.focus()
        db_input.value = str(new_db_path)
        
        # Fire submitted event
        await pilot.press("enter")
        await pilot.pause()

        # Verify configuration was saved to the custom OCMAN_CONFIG_PATH
        config = ocman.load_ocman_config()
        assert config["db_path"] == str(new_db_path)

        # Modify values and test auto-save via tab activation
        tab_db_path = tmp_path / "tab_opencode.db"
        db_input.value = str(tab_db_path)
        app.query_one("TabbedContent").active = "tab-details"
        await pilot.pause()

        config = ocman.load_ocman_config()
        assert config["db_path"] == str(tab_db_path)

        # Toggle a checkbox and verify silent auto-save
        app.query_one("TabbedContent").active = "tab-config"
        await pilot.pause()
        keep_temp_check = app.query_one("#cfg-keep-temp", Checkbox)
        assert keep_temp_check.value is False
        keep_temp_check.focus()
        await pilot.press("space")
        await pilot.pause()
        
        config = ocman.load_ocman_config()
        assert config["keep_temp"] is True

        # Test Reset to Defaults
        await pilot.click("#btn-reset-config")
        await pilot.pause()
        assert keep_temp_check.value is False


@pytest.mark.anyio
async def test_tui_app_project_deletion(tui_db):
    """Test that the project deletion flow successfully invokes the background worker and deletes a project recursively."""
    from ocman_tui.app import ProjectDeletionSafetyModal
    app = OrsessionApp()
    async with app.run_test() as pilot:
        # Set selected project context
        app.selected_project_id = "proj1"
        app.selected_project_name = "Proj 1"
        
        # Trigger project deletion flow
        app.confirm_and_delete_project()
        await pilot.pause()
        
        # Check that ProjectDeletionSafetyModal is active
        assert isinstance(app.screen, ProjectDeletionSafetyModal)
        
        # Enter "yes" in the input field
        await pilot.click("#input-confirm-yes")
        await pilot.press(*"yes")
        await pilot.pause()
        
        # Click the confirm button
        await pilot.click("#btn-confirm-del")
        
        # Wait for background worker to complete
        for _ in range(50):
            if isinstance(app.screen, PostExecutionSummaryModal):
                break
            await pilot.pause(0.1)
        assert isinstance(app.screen, PostExecutionSummaryModal)
        
        # Verify that project and its sessions are deleted from DB
        sqlite3 = ocman._get_sqlite()
        conn = sqlite3.connect(str(tui_db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM project WHERE id = 'proj1'")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM session")
        assert cursor.fetchone()[0] == 0
        conn.close()


# --- Phase 2: Storage tab (doctor view + guarded reclaim) --------------------

async def _wait_doctor_rows(pilot, sw, tries=60):
    for _ in range(tries):
        if sw.query_one("#doctor-table", DataTable).row_count > 0:
            return
        await pilot.pause(0.1)


@pytest.mark.anyio
async def test_tui_storage_doctor_renders_and_totals(tui_db):
    """Phase 2: the Storage tab runs the checkup and its bucket totals match
    run_doctor_checks on the same DB."""
    from textual.widgets import TabbedContent
    from ocman_tui.widgets.storage import StorageWidget
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-storage"
        await pilot.pause()
        sw = app.query_one(StorageWidget)
        await _wait_doctor_rows(pilot, sw)
        tbl = sw.query_one("#doctor-table", DataTable)
        assert tbl.row_count > 0

        # Parity: recompute the expected 'now' bucket total directly.
        loc = ocman.discover_storage_locations(tui_db)
        recs = ocman.run_doctor_checks(loc, running=False, deep=False)
        expected_now = sum(r["size_bytes"] for r in recs if r.get("bucket") == "now")
        summary = str(sw.query_one("#lbl-doctor-summary").render())
        assert ocman.human_size_local(expected_now) in summary


@pytest.mark.anyio
async def test_tui_storage_no_snapshot_control(tui_db):
    """Phase 2 (OQ-2): the TUI Storage tab exposes no snapshot-force control; a note
    points to the CLI instead."""
    from textual.widgets import TabbedContent, Button
    from ocman_tui.widgets.storage import StorageWidget
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-storage"
        await pilot.pause()
        sw = app.query_one(StorageWidget)
        btn_ids = {b.id for b in sw.query(Button)}
        assert not any("snapshot" in (bid or "") for bid in btn_ids)
        texts = " ".join(str(s.render()) for s in sw.query("Static"))
        assert "--force-snapshots" in texts


@pytest.mark.anyio
async def test_tui_storage_checkpoint_vacuum(tui_db):
    """Phase 2: the checkpoint+VACUUM reclaim action runs and reports success."""
    from textual.widgets import TabbedContent
    from ocman_tui.widgets.storage import StorageWidget, ReclaimConfirmModal
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-storage"
        await pilot.pause()
        sw = app.query_one(StorageWidget)
        await _wait_doctor_rows(pilot, sw)
        sw.query_one("#btn-reclaim-vacuum", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, ReclaimConfirmModal)
        app.screen.query_one("#btn-confirm-reclaim", Button).press()
        for _ in range(60):
            await pilot.pause(0.1)
        # DB still present and readable (VACUUM succeeded, not corrupted).
        sqlite3_ = ocman._get_sqlite()
        conn = sqlite3_.connect(str(tui_db))
        conn.execute("PRAGMA integrity_check;")
        conn.close()
        log = str(sw.query_one("#reclaim-log", RichLog).lines)
        assert "REFUSED" not in log  # not running -> not refused


@pytest.mark.anyio
async def test_tui_storage_reclaim_refuses_while_running(tui_db, monkeypatch):
    """Phase 2 (validation d): if OpenCode holds the DB open, a reclaim action reports the
    refusal and does NOT claim success."""
    from textual.widgets import TabbedContent
    from ocman_tui.widgets.storage import StorageWidget, ReclaimConfirmModal
    import ocman_tui.widgets.storage as storage_mod

    # Simulate a live process holding the DB family open (the guard trips).
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *_a, **_k: True)
    monkeypatch.setattr(storage_mod, "db_family_open_by_live_pid", lambda *_a, **_k: True)

    notes = []
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        orig_notify = app.notify
        monkeypatch.setattr(app, "notify",
                            lambda msg, *a, **k: (notes.append((msg, k.get("severity"))), None)[1])
        app.query_one(TabbedContent).active = "tab-storage"
        await pilot.pause()
        sw = app.query_one(StorageWidget)
        await _wait_doctor_rows(pilot, sw)
        sw.query_one("#btn-reclaim-vacuum", Button).press()
        await pilot.pause()
        assert isinstance(app.screen, ReclaimConfirmModal)
        app.screen.query_one("#btn-confirm-reclaim", Button).press()
        for _ in range(60):
            await pilot.pause(0.1)
        log = str(sw.query_one("#reclaim-log", RichLog).lines)
    assert "REFUSED" in log
    # No success notification was emitted for the reclaim.
    assert not any(sev == "information" and "finished" in str(msg).lower() for msg, sev in notes)


# --- Phase 3: Spend + Running tabs -------------------------------------------

@pytest.mark.anyio
async def test_tui_spend_tab_renders_and_totals(tui_db):
    """Phase 3: the Spend tab table/totals match gather_spend() on the same DB."""
    from textual.widgets import TabbedContent
    from ocman_tui.widgets.spend import SpendWidget
    # Give sess1 a cost so a project row appears.
    conn = sqlite3.connect(str(tui_db)); cur = conn.cursor()
    cur.execute("UPDATE session SET cost=3.5, tokens_input=200, tokens_output=100, "
                "tokens_cache_read=20 WHERE id='sess1'")
    conn.commit(); conn.close()

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-spend"
        await pilot.pause()
        sw = app.query_one(SpendWidget)
        for _ in range(50):
            if sw.query_one("#spend-table", DataTable).row_count > 0:
                break
            await pilot.pause(0.1)
        assert sw.query_one("#spend-table", DataTable).row_count >= 1
        totals = str(sw.query_one("#lbl-spend-totals").render())
        expected = ocman.gather_spend(historical=False)
        assert ocman.fmt_cost(expected["live_total"]) in totals


@pytest.mark.anyio
async def test_tui_spend_historical_toggle(tui_db):
    """Phase 3: the historical toggle adds the ledger's deleted spend."""
    from textual.widgets import TabbedContent
    from ocman_tui.widgets.spend import SpendWidget
    hist = ocman._load_history()
    hist["cumulative"].update({"cost_deleted": 9.0, "tokens_input_deleted": 10,
                               "tokens_output_deleted": 5, "tokens_cache_read_deleted": 1})
    ocman._save_history(hist)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-spend"
        await pilot.pause()
        sw = app.query_one(SpendWidget)
        for _ in range(30):
            await pilot.pause(0.1)
        sw.query_one("#check-spend-historical", Checkbox).value = True
        for _ in range(30):
            await pilot.pause(0.1)
        totals = str(sw.query_one("#lbl-spend-totals").render())
        assert "Historically saved" in totals
        assert ocman.fmt_cost(9.0) in totals


@pytest.mark.anyio
async def test_tui_running_tab_renders_instances_and_banner(tui_db, monkeypatch):
    """Phase 3: the Running tab renders instances and raises the insecure banner."""
    from textual.widgets import TabbedContent
    from ocman_tui.widgets.running import RunningWidget
    import ocman_tui.widgets.running as running_mod

    fake = [{
        "pid": 4242, "user": "me", "elapsed": "01:23", "kind": "serve",
        "listeners": ["0.0.0.0:7777"], "auth": "unsecured", "vulnerable": True,
        "exposed": True, "cwd": "/w/proj", "project": "proj",
        "session": {"id": None, "provenance": "?"},
    }]
    monkeypatch.setattr(running_mod, "detect_running_instances", lambda **k: list(fake))

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-running"
        await pilot.pause()
        rw = app.query_one(RunningWidget)
        for _ in range(40):
            if rw.query_one("#running-table", DataTable).row_count > 0:
                break
            await pilot.pause(0.1)
        assert rw.query_one("#running-table", DataTable).row_count == 1
        banner = str(rw.query_one("#lbl-running-banner").render())
        assert "SECURITY WARNING" in banner and "4242" in banner


@pytest.mark.anyio
async def test_tui_running_tab_fail_loud(tui_db, monkeypatch):
    """Phase 3 (PR-001): when detection is unreliable, the Running tab shows a loud
    'NOT an all-clear' state, never an empty table."""
    from textual.widgets import TabbedContent
    from ocman_tui.widgets.running import RunningWidget
    import ocman_tui.widgets.running as running_mod

    def _boom(**k):
        raise ocman.RunningDetectionError("ss unavailable")
    monkeypatch.setattr(running_mod, "detect_running_instances", _boom)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-running"
        await pilot.pause()
        rw = app.query_one(RunningWidget)
        for _ in range(40):
            if "NOT an all-clear" in str(rw.query_one("#lbl-running-status").render()):
                break
            await pilot.pause(0.1)
        status = str(rw.query_one("#lbl-running-status").render())
        assert "NOT an all-clear" in status
        assert rw.query_one("#running-table", DataTable).row_count == 0


