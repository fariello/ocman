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


