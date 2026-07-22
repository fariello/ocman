import os
import sqlite3
import pytest
from pathlib import Path
import ocman
from ocman_tui.app import OrsessionApp, DeletionSafetyModal, PostExecutionSummaryModal
from ocman_tui.widgets.sidebar import SidebarWidget
from ocman_tui.widgets.database import DatabaseAdminWidget
from textual.widgets import Tree, DataTable, Markdown, Input, Checkbox, RichLog, Button, Select


async def await_screen(pilot, app, screen_cls, timeout: float = 5.0):
    """Poll until the app's active screen is an instance of ``screen_cls``, then assert it.

    `push_screen` takes more than one frame on slower runners (notably Windows CI on Python
    3.10), so a bare `await pilot.pause()` + immediate `isinstance(app.screen, X)` races the
    mount and flakes. This waits (in short pauses) up to ``timeout`` for the modal to become
    the active screen, then asserts it is there. Assertion strength is preserved: it still
    fails if the screen never mounts. Returns the screen for convenience.
    """
    import time as _t
    deadline = _t.monotonic() + timeout
    while _t.monotonic() < deadline:
        if isinstance(app.screen, screen_cls):
            return app.screen
        await pilot.pause(0.05)
    assert isinstance(app.screen, screen_cls), (
        f"expected screen {screen_cls.__name__}, got {type(app.screen).__name__} after {timeout}s")
    return app.screen


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
        await await_screen(pilot, app, DeletionSafetyModal)
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
        await await_screen(pilot, app, PostExecutionSummaryModal)

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
        await await_screen(pilot, app, DeletionSafetyModal)
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
        await await_screen(pilot, app, PostExecutionSummaryModal)

    assert not out.exists()


@pytest.mark.anyio
async def test_tui_clear_history(tui_db):
    """B2-12: the Log-tab DELETE button prunes runs older than the 'Clean Older Than' duration
    (keeping newer runs) and NEVER touches the cumulative historical totals."""
    from ocman_tui.app import ClearHistoryModal
    from datetime import datetime, timedelta
    old = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d %H:%M:%S")
    new = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    ocman._save_history({
        "cumulative": {"sessions_deleted": 3, "cost_deleted": 1.5},
        "runs": [{"timestamp": old, "action": "old"}, {"timestamp": new, "action": "new"}],
    })
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one("#input-log-prune-duration", Input).value = "30d"
        app.query_one("#btn-clear-history-log", Button).press()
        await await_screen(pilot, app, ClearHistoryModal)
        for _ in range(50):
            if app.screen.query("#input-clear-history-yes"):
                break
            await pilot.pause(0.1)
        await pilot.click("#input-clear-history-yes")
        await pilot.press(*"yes")
        await pilot.pause()
        await pilot.click("#btn-confirm-clear-history")
        await pilot.pause()

    hist = ocman._load_history()
    # Old run dropped, new run kept.
    assert [r["action"] for r in hist["runs"]] == ["new"]
    # Cumulative totals kept in perpetuity (B2-12).
    assert hist["cumulative"]["sessions_deleted"] == 3
    assert hist["cumulative"]["cost_deleted"] == 1.5


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
        await pilot.pause()  # let DatabaseAdminWidget.on_mount -> refresh_metrics complete
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
        await await_screen(pilot, app, DeletionSafetyModal)
        
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
        await await_screen(pilot, app, PostExecutionSummaryModal)
        
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
        await await_screen(pilot, app, DeletionSafetyModal)

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
        await await_screen(pilot, app, PostExecutionSummaryModal)


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
        
        # Set "Clean Older Than" to 5 days to trigger cleanup of old seed data (B2-10a)
        db_admin.query_one("#input-retention-duration", Input).value = "5d"
        
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
    """Config OVERLAY (formerly a tab): load on open, auto-save on submit/change, save on
    dismiss (replaces the old auto-save-on-tab-switch), and Reset to Defaults."""
    from ocman_tui.app import ConfigOverlay
    app = OrsessionApp()
    async with app.run_test() as pilot:
        # Open the Config overlay (^g / footer button both call this action).
        app.action_show_config()
        await pilot.pause()
        assert isinstance(app.screen, ConfigOverlay)
        overlay = app.screen

        # Check default value is loaded into the overlay's fields.
        db_input = overlay.query_one("#cfg-db-path", Input)
        assert db_input.value == str(tui_db)

        # Modify values and trigger auto-save via submit (the app-level cfg-* handler).
        new_db_path = tmp_path / "new_opencode.db"
        db_input.focus()
        db_input.value = str(new_db_path)
        await pilot.press("enter")
        await pilot.pause()
        config = ocman.load_ocman_config()
        assert config["db_path"] == str(new_db_path)

        # Toggle a checkbox and verify silent auto-save (cfg-* Changed handler).
        keep_temp_check = overlay.query_one("#cfg-keep-temp", Checkbox)
        assert keep_temp_check.value is False
        keep_temp_check.focus()
        await pilot.press("space")
        await pilot.pause()
        config = ocman.load_ocman_config()
        assert config["keep_temp"] is True

        # SAVE-ON-DISMISS: change a value, dismiss the overlay (^m), and confirm it persisted.
        # This replaces the old auto-save-on-tab-switch path that no longer exists.
        dismiss_db_path = tmp_path / "dismiss_opencode.db"
        db_input.value = str(dismiss_db_path)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, ConfigOverlay)
        config = ocman.load_ocman_config()
        assert config["db_path"] == str(dismiss_db_path)

        # Reopen and test Reset to Defaults.
        app.action_show_config()
        await pilot.pause()
        overlay = app.screen
        assert isinstance(overlay, ConfigOverlay)
        keep_temp_check = overlay.query_one("#cfg-keep-temp", Checkbox)
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
        await await_screen(pilot, app, ProjectDeletionSafetyModal)
        
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
        await await_screen(pilot, app, PostExecutionSummaryModal)
        
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
        app.action_show_doctor()
        await pilot.pause()
        sw = app.screen.query_one(StorageWidget)
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
        app.action_show_doctor()
        await pilot.pause()
        sw = app.screen.query_one(StorageWidget)
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
        app.action_show_doctor()
        await pilot.pause()
        sw = app.screen.query_one(StorageWidget)
        await _wait_doctor_rows(pilot, sw)
        sw.query_one("#btn-reclaim-vacuum", Button).press()
        await pilot.pause()
        await await_screen(pilot, app, ReclaimConfirmModal)
        # Wait for the confirm button to mount before pressing (Windows CI is
        # slower to mount the modal); harmless where already mounted.
        for _ in range(50):
            if app.screen.query("#btn-confirm-reclaim"):
                break
            await pilot.pause(0.1)
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
        app.action_show_doctor()
        await pilot.pause()
        sw = app.screen.query_one(StorageWidget)
        await _wait_doctor_rows(pilot, sw)
        sw.query_one("#btn-reclaim-vacuum", Button).press()
        await pilot.pause()
        await await_screen(pilot, app, ReclaimConfirmModal)
        # Wait for the confirm button to mount before pressing (Windows CI is
        # slower to mount the modal); harmless where already mounted.
        for _ in range(50):
            if app.screen.query("#btn-confirm-reclaim"):
                break
            await pilot.pause(0.1)
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
        app.action_show_running()
        await pilot.pause()
        rw = app.screen.query_one(RunningWidget)
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
        app.action_show_running()
        await pilot.pause()
        rw = app.screen.query_one(RunningWidget)
        for _ in range(40):
            if "NOT an all-clear" in str(rw.query_one("#lbl-running-status").render()):
                break
            await pilot.pause(0.1)
        status = str(rw.query_one("#lbl-running-status").render())
        assert "NOT an all-clear" in status
        assert rw.query_one("#running-table", DataTable).row_count == 0


# --- Phase 4: bulk multi-select, db-clean duration/scope, chunk --------------

@pytest.mark.anyio
async def test_tui_multiselect_and_batch_delete(tui_db, tmp_path):
    """Phase 4: multi-select two sessions, confirm batch delete, both are removed in one
    pass and recovery extracts are written first."""
    from ocman_tui.app import BatchDeleteModal
    _seed_tui_conversation(tui_db)  # gives sess1 a conversation
    # Add a second deletable root session with a conversation.
    conn = sqlite3.connect(str(tui_db)); cur = conn.cursor()
    cur.execute("INSERT INTO session (id, project_id, title, time_created, time_updated, "
                "directory, parent_id) VALUES ('sessX','proj1','SX',1000,2000,'/path/to/proj','')")
    cur.execute("INSERT INTO message VALUES ('mx','sessX',1000,1000,?)", ('{"role":"user"}',))
    cur.execute("INSERT INTO part VALUES ('px','mx','sessX',1000,1000,?)",
                ('{"type":"text","text":"second session content"}',))
    conn.commit(); conn.close()

    out = tmp_path / "batch-recovery"
    cfg = ocman.load_ocman_config(); cfg["default_out_dir"] = str(out)
    ocman.save_ocman_config(cfg, ocman.OCMAN_CONFIG_PATH)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.selected_session_ids = {"sess1", "sessX"}
        app._refresh_batch_ui()
        await pilot.pause()
        assert app.query_one("#btn-batch-delete", Button).disabled is False
        app.confirm_and_batch_delete()
        await pilot.pause()
        await await_screen(pilot, app, BatchDeleteModal)
        app.screen.query_one("#input-batch-yes", Input).value = "yes"
        await pilot.pause()
        app.screen.query_one("#btn-confirm-batch-del", Button).press()
        # Wait for the batch worker to FINISH via an APP-STATE signal (it clears
        # selected_session_ids and refreshes on completion), NOT by polling the DB file with
        # fresh connections during the worker's VACUUM - a concurrent reader opening mid-VACUUM
        # intermittently hit "disk I/O error"/"database is locked" (the test raced its subject).
        for _ in range(80):
            if not app.selected_session_ids:
                break
            await pilot.pause(0.1)
        assert not app.selected_session_ids, "batch delete did not complete in time"
    conn = sqlite3.connect(str(tui_db)); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM session WHERE id IN ('sess1','sessX')")
    assert cur.fetchone()[0] == 0
    conn.close()
    # Extracts written for the batch.
    assert out.exists() and any(p.name.endswith(".restart.md") for p in out.iterdir())


@pytest.mark.anyio
async def test_tui_batch_delete_cancel_deletes_nothing(tui_db):
    """Phase 4: cancelling the batch-delete confirm deletes nothing."""
    from ocman_tui.app import BatchDeleteModal
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.selected_session_ids = {"sess1"}
        app._refresh_batch_ui()
        app.confirm_and_batch_delete()
        await pilot.pause()
        await await_screen(pilot, app, BatchDeleteModal)
        app.screen.query_one("#btn-cancel-batch-del", Button).press()
        await pilot.pause()
    conn = sqlite3.connect(str(tui_db)); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM session WHERE id='sess1'")
    assert cur.fetchone()[0] == 1  # still there
    conn.close()


@pytest.mark.anyio
async def test_tui_batch_export(tui_db, tmp_path):
    """Phase 4: batch export writes one .ocbox per selected session."""
    _seed_tui_conversation(tui_db)
    out = tmp_path / "batch-export"
    cfg = ocman.load_ocman_config(); cfg["default_out_dir"] = str(out)
    ocman.save_ocman_config(cfg, ocman.OCMAN_CONFIG_PATH)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.selected_session_ids = {"sess1"}
        app._refresh_batch_ui()
        app.batch_export_selected()
        for _ in range(60):
            if out.exists() and any(p.suffix == ".ocbox" for p in out.iterdir()):
                break
            await pilot.pause(0.1)
    assert out.exists()
    assert any(p.name == "sess1.ocbox" for p in out.iterdir())


@pytest.mark.anyio
async def test_tui_prune_duration_and_scope(tui_db):
    """Phase 4: the prune UI parses a duration string and honors it (delegates to
    db_run_cleanup with the parsed days)."""
    from textual.widgets import TabbedContent
    captured = {}

    def fake_cleanup(**kwargs):
        captured.update(kwargs)
    import ocman_tui.widgets.database as dbmod

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-admin"
        await pilot.pause()
        widget = app.query_one(DatabaseAdminWidget)
        # Patch the cleanup entry point the widget calls.
        orig = dbmod.db_run_cleanup
        dbmod.db_run_cleanup = lambda **k: fake_cleanup(**k)
        try:
            widget.query_one("#input-retention-duration", Input).value = "6w"
            widget.query_one("#check-dry-run", Checkbox).value = True
            widget.run_prune_operation()
            for _ in range(40):
                if captured:
                    break
                await pilot.pause(0.1)
        finally:
            dbmod.db_run_cleanup = orig
    assert captured, "db_run_cleanup was not called"
    assert abs(captured["days"] - 42.0) < 0.001  # 6 weeks = 42 days


@pytest.mark.anyio
async def test_tui_recovery_chunk_writes_parts(tui_db, tmp_path):
    """Phase 4: the chunk checkbox produces multiple .part-NNofMM files covering all turns.

    Uses > default chunk_max_interactions (100) worth of interactions so the split does not
    depend on custom caps (the TUI's config auto-save does not persist chunk_max_* keys).
    """
    from ocman.cli import Turn

    out = tmp_path / "chunk-out"
    cfg = ocman.load_ocman_config()
    cfg["default_out_dir"] = str(out)
    ocman.save_ocman_config(cfg, ocman.OCMAN_CONFIG_PATH)

    # 150 user+assistant interactions -> exceeds the default 100/part cap -> >=2 parts.
    many = []
    for i in range(150):
        many.append(Turn(role="user", text=f"user message number {i} asking to do a thing",
                         index=2 * i + 1, source="x"))
        many.append(Turn(role="assistant", text=f"assistant reply number {i} doing the thing",
                         index=2 * i + 2, source="x"))

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.selected_session_id = "sess1"
        app.selected_session_title = "S1"
        app.current_turns = many
        app.query_one("#check-chunk", Checkbox).value = True
        await pilot.pause()
        app.generate_recovery_files("btn-write-transcript")
        await pilot.pause()
    parts = sorted(p.name for p in out.iterdir()
                   if ".part-" in p.name and p.name.endswith(".transcript.md"))
    assert len(parts) >= 2


# --- Phase 5: breadth (bundles, move, backup clean, search, filter) ----------

import zipfile
import json as _json


def _make_ocbox(path: Path, kind: str) -> None:
    """Write a minimal .ocbox with a meta.json declaring the given kind (for auto-detect)."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("meta.json", _json.dumps({"kind": kind}))


@pytest.mark.anyio
async def test_tui_import_autodetect_routes_by_kind(tui_db, tmp_path, monkeypatch):
    """Phase 5: the import worker reads meta.json 'kind' and routes to the project vs
    session importer."""
    from ocman_tui.app import ImportSessionModal
    import ocman_tui.app as app_mod

    called = {"project": 0, "session": 0}
    monkeypatch.setattr(app_mod, "extract_and_import_project",
                        lambda *a, **k: called.__setitem__("project", called["project"] + 1) or "proj_new")
    monkeypatch.setattr(app_mod, "extract_and_import_session",
                        lambda *a, **k: called.__setitem__("session", called["session"] + 1) or "ses_new")

    proj_box = tmp_path / "p.ocbox"; _make_ocbox(proj_box, "project")
    sess_box = tmp_path / "s.ocbox"; _make_ocbox(sess_box, "session")

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        modal = ImportSessionModal()
        await app.push_screen(modal)
        await pilot.pause()
        modal._do_import_worker(proj_box, None, None)
        modal._do_import_worker(sess_box, None, None)
        for _ in range(30):
            if called["project"] and called["session"]:
                break
            await pilot.pause(0.1)
    assert called["project"] == 1
    assert called["session"] == 1


@pytest.mark.anyio
async def test_tui_local_session_move(tui_db):
    """Phase 5: the local session-move modal updates the session's directory in the DB."""
    from ocman_tui.app import MoveSessionModal
    from conftest import abs_path, norm_real
    # OS-appropriate absolute source/dest (drive-anchored on Windows) so the
    # move actually resolves to an absolute path on every platform.
    src_dir = abs_path("/path/to/proj")
    new_dir = abs_path("/new/location")
    expected = norm_real(new_dir)
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        modal = MoveSessionModal("sess1", "S1", src_dir)
        await app.push_screen(modal)
        await pilot.pause()
        modal._do_move_worker(new_dir)
        for _ in range(40):
            conn = sqlite3.connect(str(tui_db)); cur = conn.cursor()
            cur.execute("SELECT directory FROM session WHERE id='sess1'")
            d = cur.fetchone()[0]; conn.close()
            # The stored dir is db_move_session_metadata's resolved new dir; compare
            # normalized realpaths so backslashes/drive/symlinks do not break it.
            if d and norm_real(d) == expected:
                break
            await pilot.pause(0.1)
    conn = sqlite3.connect(str(tui_db)); cur = conn.cursor()
    cur.execute("SELECT directory FROM session WHERE id='sess1'")
    stored = cur.fetchone()[0]
    conn.close()
    # Proves the move updated the directory to the new location.
    assert norm_real(stored) == expected


@pytest.mark.anyio
async def test_tui_backup_clean(tui_db, tmp_path, monkeypatch):
    """Phase 5: prune old backups removes an old archive and keeps a recent one."""
    from textual.widgets import TabbedContent
    import time
    backups = tmp_path / "backups"
    backups.mkdir()
    # cli_clean_backups only prunes files named like ocman's own backups.
    old = backups / "opencode-backup-20200101-000000.zip"; old.write_text("x")
    recent = backups / "opencode-backup-20990101-000000.zip"; recent.write_text("y")
    # Age the old file ~100 days.
    old_ts = time.time() - 100 * 86400
    os.utime(old, (old_ts, old_ts))

    cfg = ocman.load_ocman_config()
    cfg["default_backup_dir"] = str(backups)
    ocman.save_ocman_config(cfg, ocman.OCMAN_CONFIG_PATH)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-admin"
        await pilot.pause()
        widget = app.query_one(DatabaseAdminWidget)
        widget.query_one("#input-backup-clean-days", Input).value = "30"
        widget.run_clean_backups_operation()
        for _ in range(60):
            if not old.exists():
                break
            await pilot.pause(0.1)
    assert not old.exists()      # older than 30 days -> pruned
    assert recent.exists()       # recent -> kept


@pytest.mark.anyio
async def test_tui_search_filters_tree(tui_db):
    """B2-07: a content search filters the sidebar TREE to matching sessions (no separate
    results box), and the transcript-line filter is driven by the same query."""
    from ocman_tui.widgets.sidebar import SidebarWidget
    from textual.css.query import NoMatches
    _seed_tui_conversation(tui_db)  # sess1 has 'login button' content
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # No separate results table exists anymore.
        try:
            app.query_one("#search-results")
            assert False, "#search-results should have been removed"
        except NoMatches:
            pass
        # Apply the filter (Enter path).
        app.run_session_search("login button")
        await pilot.pause()
        assert app._active_query == "login button"
        sidebar = app.query_one("#sidebar", SidebarWidget)
        # The tree now contains the matching session node.
        session_ids = []
        def _walk(node):
            data = getattr(node, "data", None)
            if data and data.get("type") == "session":
                session_ids.append(data["id"])
            for c in node.children:
                _walk(c)
        _walk(sidebar.root)
        assert "sess1" in session_ids, session_ids
        # Clearing the query restores the full tree.
        app.run_session_search("")
        await pilot.pause()
        assert app._active_query == ""


@pytest.mark.anyio
async def test_tui_filter_runs(tui_db, tmp_path, monkeypatch):
    """Phase 5: the filter modal invokes cli_filter with the chosen input/scope/model."""
    from ocman_tui.app import FilterModal
    import ocman_tui.app as app_mod

    src = tmp_path / "doc.restart.md"
    src.write_text("# a document about the auth refactor and other things")
    captured = {}

    def fake_filter(input_path, project, scope, model_spec, out_path, verbosity, **kw):
        captured.update(dict(input_path=str(input_path), scope=scope, model=model_spec))
        result = tmp_path / "doc.scoped.compacted.md"
        result.write_text("scoped")
        return result
    # The worker imports cli_filter from .core at call time, so patch it there.
    import ocman_tui.core as core_mod
    monkeypatch.setattr(core_mod, "cli_filter", fake_filter)

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        modal = FilterModal()
        await app.push_screen(modal)
        await pilot.pause()
        modal._do_filter_worker(src, "only the auth refactor", "uri/test/model")
        for _ in range(40):
            if captured:
                break
            await pilot.pause(0.1)
    assert captured.get("scope") == "only the auth refactor"
    assert captured.get("model") == "uri/test/model"




# --- TF-02 (follow-up IPD): Storage worker #doctor-table mount-race guard ------

def test_storage_checkup_worker_skips_when_unmounted(monkeypatch):
    """Deterministic guard test: the checkup worker's UI callback must NOT raise
    NoMatches/WorkerFailed when the widget is not mounted (the race we hit under load).
    Mutation-check: removing the `if not self.is_mounted: return` guard makes this raise."""
    from ocman_tui.widgets.storage import StorageWidget
    import ocman

    sw = StorageWidget()               # constructed, NOT mounted -> is_mounted is False
    assert not sw.is_mounted

    # The worker marshals its UI update via self.app._safe_call_from_thread(fn); run it inline.
    class _FakeApp:
        def notify(self, *a, **k):
            pass
        def _safe_call_from_thread(self, fn, *a, **k):
            return fn(*a, **k)   # execute the update_ui callback synchronously
    monkeypatch.setattr(type(sw), "app", property(lambda self: _FakeApp()))

    # A checkup record so update_ui has something to render if it (wrongly) proceeds.
    monkeypatch.setattr(ocman, "discover_storage_locations", lambda *a, **k: {})
    monkeypatch.setattr(ocman, "db_family_open_by_live_pid", lambda *a, **k: False)
    monkeypatch.setattr(ocman, "run_doctor_checks",
                        lambda *a, **k: [{"key": "x", "title": "X", "status": "ok",
                                          "size_bytes": 0, "count": 0, "fix_cmd": None,
                                          "bucket": "report"}])
    # Must not raise: the guard returns early because the widget/#doctor-table is not mounted.
    sw._do_checkup_worker(deep=False)


# --- TF-03/04 (follow-up IPD): database.py worker ERROR path ------------------

@pytest.mark.anyio
async def test_tui_prune_worker_error_is_surfaced_not_crashed(tui_db, monkeypatch):
    """The prune worker's off-thread failure must surface via an error notify and NOT crash
    the app / worker (covers the except branch in _do_prune_worker)."""
    from textual.widgets import TabbedContent
    import ocman_tui.widgets.database as dbmod

    notifications = []

    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.query_one(TabbedContent).active = "tab-admin"
        await pilot.pause()
        widget = app.query_one(DatabaseAdminWidget)
        # Capture notifications; make the cleanup entry point raise.
        monkeypatch.setattr(app, "notify",
                            lambda msg, **k: notifications.append((msg, k.get("severity"))))
        monkeypatch.setattr(dbmod, "db_run_cleanup",
                            lambda **k: (_ for _ in ()).throw(RuntimeError("boom in cleanup")))
        widget.query_one("#check-dry-run", Checkbox).value = True
        widget.run_prune_operation()
        # Wait for the worker to surface the error (no crash).
        for _ in range(50):
            if any(sev == "error" for _, sev in notifications):
                break
            await pilot.pause(0.1)
    assert any(sev == "error" and "boom in cleanup" in msg for msg, sev in notifications), \
        f"expected an error notify surfacing the failure; got {notifications}"


# ---------------------------------------------------------------------------
# Footer command bar + Doctor/Running/Config overlays + sidebar-pane toggle
# (IPD 20260721-1925-01, TF-01..TF-15)
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_tui_footer_bar_buttons_present(tui_db):
    """The custom footer bar exposes the clickable command buttons."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        for bid in ("foot-select", "foot-quit", "foot-sidebar", "foot-update",
                    "foot-doctor", "foot-running", "foot-config", "foot-main"):
            assert app.query_one("#" + bid, Button) is not None
        # B2-08: the Search footer button is gone.
        from textual.css.query import NoMatches
        try:
            app.query_one("#foot-search", Button)
            assert False, "foot-search should have been removed"
        except NoMatches:
            pass


@pytest.mark.anyio
async def test_tui_sidebar_pane_toggle_hides_search(tui_db):
    """Toggling the sidebar hides the whole pane (search box + tree + results), not just the
    tree, and the footer glyph flips checked/unchecked (TF-15)."""
    from textual.containers import Vertical
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        pane = app.query_one("#sidebar-pane", Vertical)
        search = app.query_one("#input-session-search", Input)
        assert pane.display is True
        # hide
        app.action_toggle_sidebar()
        await pilot.pause()
        assert pane.display is False
        assert search.size.width == 0 and search.size.height == 0
        assert "\u2610" in str(app.query_one("#foot-sidebar", Button).label)
        # show
        app.action_toggle_sidebar()
        await pilot.pause()
        assert pane.display is True and search.size.width > 0
        assert "\U0001f5f9" in str(app.query_one("#foot-sidebar", Button).label)


@pytest.mark.anyio
async def test_tui_no_search_footer_or_binding(tui_db):
    """B2-08: the ^s Search footer button, ctrl+s binding, and action_focus_search are gone
    (the search box is always visible in the sidebar)."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert not any(b.key == "ctrl+s" for b in app.BINDINGS)
        assert not hasattr(app, "action_focus_search")


@pytest.mark.anyio
async def test_tui_doctor_running_config_overlays_open_and_close(tui_db):
    """^d/^r/^g open the Doctor/Running/Config overlays; ^m and Esc return to main."""
    from ocman_tui.app import DoctorOverlay, RunningOverlay, ConfigOverlay, _FooterOverlay
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Doctor via key
        await pilot.press("ctrl+d")
        await pilot.pause()
        assert isinstance(app.screen, DoctorOverlay)
        await pilot.press("escape")  # Main (Esc)
        await pilot.pause()
        assert not isinstance(app.screen, _FooterOverlay)
        # Running via key, close with Esc
        await pilot.press("ctrl+r")
        await pilot.pause()
        assert isinstance(app.screen, RunningOverlay)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, _FooterOverlay)
        # Config via key
        await pilot.press("ctrl+g")
        await pilot.pause()
        assert isinstance(app.screen, ConfigOverlay)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, _FooterOverlay)


@pytest.mark.anyio
async def test_tui_removed_tabs_absent(tui_db):
    """Storage/Running/Config are no longer TabPanes (they are overlays now)."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        tab_ids = {tp.id for tp in app.query("TabPane")}
        assert "tab-storage" not in tab_ids
        assert "tab-running" not in tab_ids
        assert "tab-config" not in tab_ids
        # the surviving tabs are still there
        assert "tab-details" in tab_ids and "tab-admin" in tab_ids and "tab-spend" in tab_ids


@pytest.mark.anyio
async def test_tui_config_g_binding_and_quit_intact(tui_db):
    """^g opens Config (not ^c), and ^q remains the quit binding (not remapped)."""
    from ocman_tui.app import ConfigOverlay
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("ctrl+g")
        await pilot.pause()
        assert isinstance(app.screen, ConfigOverlay)
        # ^q is still bound to quit
        quit_keys = {b.key for b in app.BINDINGS if b.action == "quit"}
        assert "ctrl+q" in quit_keys
        # nothing binds ctrl+c to an action (freed from the surprising Config mapping)
        assert not any(b.key == "ctrl+c" for b in app.BINDINGS)


# ---------------------------------------------------------------------------
# TUI polish batch (IPD 20260721-2138-01, PB-01..PB-10)
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_tui_no_ctrl_m_binding_esc_dismisses(tui_db):
    """PB-01: ctrl+m is gone (it collides with Enter); Esc dismisses overlays; footer relabeled."""
    from ocman_tui.app import DoctorOverlay, _FooterOverlay
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert not any(b.key == "ctrl+m" for b in app.BINDINGS)
        assert "Main" in str(app.query_one("#foot-main", Button).label)
        app.action_show_doctor()
        await pilot.pause()
        assert isinstance(app.screen, DoctorOverlay)
        # the overlay has no ctrl+m binding either
        assert not any(b.key == "ctrl+m" for b in app.screen.BINDINGS)
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, _FooterOverlay)


@pytest.mark.anyio
async def test_tui_tab_titles_renamed(tui_db):
    """PB-04b/05b/07a: Details, Database, Models tab titles."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        labels = {str(t.label) for t in app.query("Tab")}
        assert "Details" in labels
        assert "Database" in labels
        assert "Models" in labels
        assert "Details & Transcript" not in labels
        assert "Database Admin" not in labels
        assert "Models Library" not in labels


@pytest.mark.anyio
async def test_tui_full_lines_checkbox_present(tui_db):
    """PB-06: the transcript controls include a 'Full lines' checkbox, default off (truncated)."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        cb = app.query_one("#check-full-lines", Checkbox)
        assert cb.value is False  # default = truncated (CLI-style)


def test_tui_model_display_helper():
    """PB-09: session metadata shows the bare model id, not JSON (and tolerates plain strings)."""
    assert OrsessionApp._model_display('{"id": "gpt-x", "providerID": "openai"}') == "gpt-x"
    assert OrsessionApp._model_display("plain-model-id") == "plain-model-id"
    assert OrsessionApp._model_display("") == "N/A"
    assert OrsessionApp._model_display(None) == "N/A"
    # malformed JSON falls back to the raw (stripped) text
    assert OrsessionApp._model_display('{"id": ') == '{"id":'


def test_tui_accessibility_css_present():
    """PB-02/08/10 regression guard: the status-toast colors, high-contrast inputs, and compact
    (zero-vertical-padding) widget rules are present in the stylesheet, so a later edit cannot
    silently revert the accessibility fix."""
    from pathlib import Path as _P
    css = (_P(__file__).parent.parent / "ocman_tui" / "css" / "style.css").read_text()
    # PB-02 toast colors
    assert "Toast.-information" in css and "Toast.-warning" in css and "Toast.-error" in css
    # PB-08 high-contrast input text
    assert "#f5f5f5" in css
    # PB-10 compact controls (no tall border on Input/Button -> height 1)
    assert "height: 1;" in css
    # PB-03/04a fill tables
    assert "#spend-table" in css and "#models-table" in css


# ---------------------------------------------------------------------------
# TUI polish batch 2 - part 2 (B2-09 metrics, B2-11 copy, B2-12 log prune, B2-GEN)
# ---------------------------------------------------------------------------
def test_prune_history_runs_older_than(tmp_path, monkeypatch):
    """B2-12: age-prune drops old runs, keeps newer ones, and NEVER touches cumulative."""
    import json
    from datetime import datetime, timedelta
    hist = tmp_path / "hist.json"
    monkeypatch.setattr(ocman, "OPENCODE_HISTORY_PATH", hist)
    old = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d %H:%M:%S")
    new = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    hist.write_text(json.dumps({
        "cumulative": {"cost_deleted": 12.34, "messages_deleted": 5},
        "runs": [{"timestamp": old, "reason": "old"}, {"timestamp": new, "reason": "new"}],
    }))
    removed = ocman.prune_history_runs_older_than(30)
    data = json.loads(hist.read_text())
    assert removed == 1
    assert [r["reason"] for r in data["runs"]] == ["new"]
    # cumulative kept in perpetuity
    assert data["cumulative"]["cost_deleted"] == 12.34
    assert data["cumulative"]["messages_deleted"] == 5


def test_prune_history_keeps_unparseable_timestamps(tmp_path, monkeypatch):
    """B2-12: a run whose timestamp cannot be parsed is kept (never dropped on ambiguity)."""
    import json
    hist = tmp_path / "hist.json"
    monkeypatch.setattr(ocman, "OPENCODE_HISTORY_PATH", hist)
    hist.write_text(json.dumps({"cumulative": {}, "runs": [{"reason": "no-ts"},
                                                            {"timestamp": "garbage", "reason": "bad-ts"}]}))
    removed = ocman.prune_history_runs_older_than(1)
    data = json.loads(hist.read_text())
    assert removed == 0 and len(data["runs"]) == 2


@pytest.mark.anyio
async def test_tui_database_expanded_metrics(tui_db):
    """B2-09: SYSTEM METRICS shows the expanded, bounded metric set."""
    from ocman_tui.widgets.database import DatabaseAdminWidget
    from textual.widgets import Static
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        w = app.query_one(DatabaseAdminWidget)
        for wid in ("#lbl-wal-size", "#lbl-page-info", "#lbl-freelist",
                    "#lbl-total-messages", "#lbl-total-parts", "#lbl-largest-table"):
            assert w.query_one(wid, Static) is not None
        # page-info is populated (not empty) after mount refresh
        assert str(w.query_one("#lbl-page-info", Static).render()).strip() != ""


@pytest.mark.anyio
async def test_tui_metadata_click_to_copy(tui_db):
    """B2-11: the metadata block stores plain copy text and copies on click."""
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.update_metadata_view({"id": "ses_abc", "title": "T", "model": '{"id":"m"}',
                                  "cost": 1.0, "created": 1000, "updated": 2000,
                                  "project_dir": "/p", "directory": "/p"})
        await pilot.pause()
        assert "ses_abc" in app._metadata_copy_text
        assert "(click to copy)" not in app._metadata_copy_text  # raw text excludes the hint

        copied = {}
        app.copy_to_clipboard = lambda text: copied.setdefault("text", text)

        class _Evt:
            widget = app.query_one("#lbl-metadata-grid")
        app.on_click(_Evt())
        assert "ses_abc" in copied.get("text", "")


def test_tui_one_color_button_css():
    """B2-GEN regression guard: buttons share one color (xterm 215 -> #ffd75f) with black text;
    the footer buttons use the same theme."""
    from pathlib import Path as _P
    css = (_P(__file__).parent.parent / "ocman_tui" / "css" / "style.css").read_text()
    assert "#ffd75f" in css          # the single button color
    assert ".footer-btn" in css and "#ffd75f" in css


@pytest.mark.anyio
async def test_tui_destructive_buttons_carry_warn_glyph(tui_db):
    """B2-GEN: with one uniform button color, every destructive button must carry the
    bold-red warn glyph in its label so danger is still conveyed."""
    from ocman_tui.widgets.database import DatabaseAdminWidget
    app = OrsessionApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        # Destructive buttons mounted on the main screen (delete/prune/log-prune).
        for bid in ("btn-delete-session-rec", "btn-delete-project", "btn-batch-delete",
                    "btn-clear-history-log", "btn-run-prune", "btn-clean-backups"):
            label = str(app.query_one("#" + bid, Button).label)
            assert "\u26a0" in label, f"{bid} missing warn glyph: {label!r}"
    # Buttons that live inside overlays/modals (reset-config, delete-orphans, reclaim PROCEED,
    # confirm-delete) are verified by a static source scan.
    from pathlib import Path as _P
    src = "\n".join((_P(__file__).parent.parent / "ocman_tui" / f).read_text()
                    for f in ("app.py", "widgets/database.py", "widgets/storage.py"))
    import re
    destructive = re.findall(r'Button\((?:\n\s*)?"([^"]*)",\s*id="[^"]*",\s*variant="(?:error|warning)"', src)
    for lbl in destructive:
        assert "\u26a0" in lbl, f"destructive button label missing warn glyph: {lbl!r}"
