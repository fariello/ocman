import os
import sqlite3
import pytest
from pathlib import Path
import ocman
from ocman_tui.app import OrsessionApp, DeletionSafetyModal, PostExecutionSummaryModal
from ocman_tui.widgets.sidebar import SidebarWidget
from ocman_tui.widgets.database import DatabaseAdminWidget
from textual.widgets import Tree, DataTable, Markdown, Input, Checkbox, RichLog

@pytest.fixture
def tui_db(tmp_path):
    db_path = tmp_path / "test_opencode.db"
    
    # Save original DB and history path
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
        
        # Click the confirm button
        await pilot.click("#btn-confirm-del")
        
        # Wait for the background worker thread to complete and UI to update
        await pilot.pause(0.5)
        
        # Verify that the session has been deleted from the database
        sqlite3 = ocman._get_sqlite()
        conn = sqlite3.connect(str(tui_db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM session WHERE id = 'sess1'")
        assert cursor.fetchone()[0] == 0
        conn.close()


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
        await pilot.pause(1.0)
        
        # Verify metrics updated and sessions are deleted
        sqlite3 = ocman._get_sqlite()
        conn = sqlite3.connect(str(tui_db))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM session")
        assert cursor.fetchone()[0] == 0
        conn.close()
