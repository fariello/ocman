"""
Main Textual Application for Ocman TUI.
"""

from __future__ import annotations
import threading
import tempfile
import sys
import contextlib
import builtins
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header, Footer, Static, Button, Checkbox, Input, Label, Select, TabbedContent, TabPane, Markdown, RichLog, Tree
)
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.message import Message

from ocman import load_ocman_config, save_ocman_config, DEFAULT_CONFIG

from . import __version__
from .core import (
    db_list_sessions,
    db_delete_session_recursive,
    load_opencode_config,
    extract_models_from_config,
    resolve_model,
    estimate_tokens,
    estimate_cost,
    call_compaction_api,
    write_export_to_temp,
    load_export_file,
    extract_turns_from_export,
    filter_conversation_turns,
    consolidate_turns,
    render_compact_prompt,
    render_transcript,
    render_restart_context,
    write_text,
    _load_history,
    _get_sqlite,
    human_size_local,
    get_file_size_local,
    SESSION_RELATIONAL_TABLES,
    get_db_path,
    truncate_turns_by_interactions,
)
from .widgets.sidebar import SidebarWidget
from .widgets.database import DatabaseAdminWidget
from .widgets.models import ModelsWidget


class RestoreBackupModal(ModalScreen[Optional[str]]):
    """Modal dialog asking the user for a path to restore from."""

    CSS = """
    #dialog-container {
        width: 65;
        height: auto;
        background: #1e1e2e;
        border: round #cba6f7;
        padding: 1 2;
        align: center middle;
    }
    #dialog-title {
        color: #f38ba8;
        text-style: bold;
        content-align: center middle;
        margin-bottom: 1;
    }
    #dialog-message {
        margin-bottom: 1;
        color: #f9e2af;
        text-style: italic;
    }
    .horizontal-buttons {
        align: center middle;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Label("RESTORE SYSTEM STATE", id="dialog-title"),
            Label("Enter absolute path to backup ZIP file or directory:", classes="info-label"),
            Input("", id="input-restore-path", placeholder="e.g. /path/to/backup.zip"),
            Label("Warning: This will overwrite active database, history, and storage!", id="dialog-message"),
            Horizontal(
                Button("Restore Now", id="btn-confirm-restore", variant="error"),
                Button("Cancel", id="btn-cancel-restore", variant="primary"),
                classes="horizontal-buttons"
            ),
            id="dialog-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm-restore":
            path = self.query_one("#input-restore-path", Input).value.strip()
            self.dismiss(path)
        elif event.button.id == "btn-cancel-restore":
            self.dismiss(None)


class FutureTodoModal(ModalScreen[None]):
    """A simple stub modal for future functionality."""
    def compose(self) -> ComposeResult:
        yield Container(
            Label("FEATURE PLANNED", id="dialog-title"),
            Label(
                "Historical cleanup is planned for a future release.\n\n"
                "No files or database entries were modified by this action.",
                classes="info-value"
            ),
            Button("Dismiss", id="btn-dismiss-todo", variant="primary"),
            id="dialog-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()


class DeletionSafetyModal(ModalScreen[bool]):
    """Safety modal confirming recursive deletion of sessions and related data."""
    def __init__(self, session_id: str, title: str) -> None:
        super().__init__()
        self.session_id = session_id
        self.session_title = title
        self.descendants_info: List[Dict[str, Any]] = []
        self.counts: Dict[str, int] = {}
        self.files_to_delete: List[Path] = []

    def compose(self) -> ComposeResult:
        yield Container(
            Label("CONFIRM RECURSIVE SESSION DELETION", id="dialog-title"),
            VerticalScroll(
                Label("You are about to recursively delete this session and its subagent descendants:", classes="info-label"),
                Static(id="lbl-del-hierarchy", classes="margin-vertical"),
                Label("Database rows to be deleted:", classes="info-label"),
                Static(id="lbl-del-db-rows", classes="margin-vertical"),
                Label("Disk files to be deleted:", classes="info-label"),
                Static(id="lbl-del-files", classes="margin-vertical"),
                id="del-safety-scroll"
            ),
            Label("This action is irreversible. Please type 'yes' below to confirm:", classes="info-label"),
            Input(placeholder="Type 'yes' to confirm", id="input-confirm-yes"),
            Horizontal(
                Button("Cancel", id="btn-cancel-del"),
                Button("CONFIRM DELETE", id="btn-confirm-del", variant="error", disabled=True),
                classes="horizontal-buttons"
            ),
            id="dialog-container"
        )

    def on_mount(self) -> None:
        sqlite3 = _get_sqlite()
        db_path = get_db_path()
        if not sqlite3 or not db_path.exists():
            self.dismiss(False)
            return

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Recursive session search
            cursor.execute("""
                WITH RECURSIVE session_tree(id) AS (
                    SELECT id FROM session WHERE id = ?
                    UNION
                    SELECT s.id FROM session s JOIN session_tree st ON s.parent_id = st.id
                )
                SELECT id FROM session_tree;
            """, (self.session_id,))
            session_ids = [row[0] for row in cursor.fetchall()]
            
            # Get table counts
            placeholders = ",".join("?" for _ in session_ids)
            for table, col in SESSION_RELATIONAL_TABLES:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IN ({placeholders})", session_ids)
                self.counts[table] = cursor.fetchone()[0]

            # Get session details
            cursor.execute(f"SELECT id, title, parent_id FROM session WHERE id IN ({placeholders})", session_ids)
            for row in cursor.fetchall():
                self.descendants_info.append({
                    "id": row[0],
                    "title": row[1] or "(untitled)",
                    "parent_id": row[2]
                })
            conn.close()
        except Exception as e:
            self.app.notify(f"Failed to gather deletion details: {e}", severity="error")
            self.dismiss(False)
            return

        # Find disk files
        storage_dir = (Path.home() / ".local" / "share" / "opencode" / "storage" / "session_diff").resolve()
        for sid in session_ids:
            if sid:
                diff_file = storage_dir / f"{sid.strip()}.json"
                if diff_file.exists():
                    self.files_to_delete.append(diff_file)

        # Update text displays
        hierarchy_text = ""
        for s in self.descendants_info:
            role = "Parent" if s["id"] == self.session_id else "Child"
            hierarchy_text += f"  - [{role}] {s['title']} (ID: {s['id']})\n"
        self.query_one("#lbl-del-hierarchy", Static).update(hierarchy_text)

        rows_text = ""
        for table, col in SESSION_RELATIONAL_TABLES:
            count = self.counts.get(table, 0)
            rows_text += f"  {table:<25}: {count:,}\n"
        self.query_one("#lbl-del-db-rows", Static).update(rows_text)

        files_text = ""
        if self.files_to_delete:
            for f in self.files_to_delete:
                files_text += f"  - {f.name} ({human_size_local(f.stat().st_size)})\n"
        else:
            files_text = "  None\n"
        self.query_one("#lbl-del-files", Static).update(files_text)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-confirm-yes":
            confirm_btn = self.query_one("#btn-confirm-del", Button)
            confirm_btn.disabled = (event.value.strip().lower() != "yes")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-del":
            self.dismiss(False)
        elif event.button.id == "btn-confirm-del":
            self.dismiss(True)


class PostExecutionSummaryModal(ModalScreen[None]):
    """Displays detailed summary of deleted DB rows and space saved on disk."""
    def __init__(self, summary: Dict[str, Any]) -> None:
        super().__init__()
        self.summary = summary

    def compose(self) -> ComposeResult:
        yield Container(
            Label("OPERATION COMPLETE SUMMARY", id="dialog-title"),
            VerticalScroll(
                Label("Session Name:", classes="info-label"),
                Static(self.summary.get("session_title", "Unknown")),
                Label("Session ID:", classes="info-label"),
                Static(self.summary.get("session_id", "Unknown")),
                Label("First Interaction (Start Date):", classes="info-label"),
                Static(self.summary.get("start_date", "Unknown")),
                Label("Last Interaction (End Date):", classes="info-label"),
                Static(self.summary.get("end_date", "Unknown")),
                Label("Database rows deleted:", classes="info-label"),
                Static(self.summary.get("db_rows", "None")),
                Label("Disk storage changes:", classes="info-label"),
                Static(self.summary.get("files", "None")),
                Label("Disk space saved:", classes="info-label"),
                Static(self.summary.get("space", "None")),
                classes="margin-vertical"
            ),
            Button("OK", id="btn-ok-summary", variant="primary"),
            id="dialog-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss()


class OrsessionApp(App):
    """The main interactive TUI manager application."""

    CSS_PATH = "css/style.css"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+s", "toggle_sidebar", "Toggle Sidebar", show=True),
        Binding("ctrl+r", "refresh_data", "Refresh", show=True),
    ]

    # Custom messages
    class RefreshSidebar(Message):
        """Instructs the sidebar widget to reload projects and sessions."""
        pass

    def __init__(self) -> None:
        super().__init__()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ocman-tui-"))
        self.selected_session_id: Optional[str] = None
        self.selected_session_title: str = ""
        self.session_turn_cache: Dict[str, int] = {}
        self.current_export: Optional[Any] = None
        self.current_turns: List[Any] = []
        self.export_lock = threading.Lock()
        self.compaction_running = False
        self.config_loaded = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield SidebarWidget(id="sidebar")
            with Container(id="workspace"):
                with TabbedContent():
                    # Tab 1: Details & Transcript
                    with TabPane("Details & Transcript", id="tab-details"):
                        with Vertical():
                            # Metadata grid
                            with Vertical(classes="panel-card"):
                                yield Label("SESSION METADATA", classes="panel-card-title")
                                yield Static("Select a session in the sidebar to view details.", id="lbl-metadata-grid")
                            
                            with Horizontal():
                                # Transcript Markdown View
                                with Vertical(classes="panel-card", id="transcript-container"):
                                    yield Label("TRANSCRIPT LOG", classes="panel-card-title")
                                    yield VerticalScroll(Markdown("", id="transcript-md"), classes="transcript-area")
                                
                                # Formatting Controls
                                with Vertical(classes="panel-card", id="controls-panel"):
                                    yield Label("FORMAT CONTROLS", classes="panel-card-title")
                                    yield Checkbox("Include Tools", value=False, id="check-include-tools")
                                    yield Checkbox("All Roles", value=False, id="check-all-roles")
                                    yield Label("Max Interactions:", classes="info-label")
                                    yield Input("100", id="input-max-interactions")
                                    yield Label("Max Lines:", classes="info-label")
                                    yield Input("2500", id="input-max-lines")
                                    yield Button("Refresh View", id="btn-refresh-transcript", variant="primary")
                    
                    # Tab 2: Actions & Recovery
                    with TabPane("Actions & Recovery", id="tab-actions"):
                        with Vertical():
                            # Metadata grid
                            with Vertical(classes="panel-card"):
                                yield Label("SELECTED SESSION SUMMARY", classes="panel-card-title")
                                yield Static("Select a session in the sidebar to view details.", id="lbl-actions-metadata-grid")

                            with Horizontal(classes="grid-container"):
                                # Recovery File Generator Card
                                with Vertical(classes="panel-card"):
                                    yield Label("RECOVERY FILE GENERATOR", classes="panel-card-title")
                                    yield Label("Write raw/restart context files to disk:", classes="info-label")
                                    yield Button("Write Transcript (.transcript.md)", id="btn-write-transcript")
                                    yield Button("Write Restart Wrapper (.restart.md)", id="btn-write-restart")
                                    yield Button("Write Compaction Prompt (.compact-prompt.md)", id="btn-write-prompt")
                                
                                # LLM Compaction Card
                                with Vertical(classes="panel-card"):
                                    yield Label("LLM COMPACTION RUNNER", classes="panel-card-title")
                                    yield Label("Select Model:", classes="info-label")
                                    yield Select([], id="select-compaction-model", prompt="Choose model...")
                                    yield Label("Est Cost: $0.00", id="lbl-est-cost", classes="info-label")
                                    yield Button("Run Compaction API", id="btn-run-compaction", variant="success")
                                    yield Static("Idle", id="lbl-compaction-status")

                            # Danger Zone Card
                            with Vertical(classes="panel-card margin-vertical"):
                                yield Label("DANGER ZONE", classes="panel-card-title")
                                yield Label("Recursively delete this session and its subagent descendants from database and disk:", classes="info-label")
                                yield Button("Recursively Delete Session & Descendants", id="btn-delete-session-rec", variant="error")
                    
                    # Tab 3: Database Admin
                    with TabPane("Database Admin", id="tab-admin"):
                        yield DatabaseAdminWidget()
                    
                    # Tab 4: Models Library
                    with TabPane("Models Library", id="tab-models"):
                        yield ModelsWidget()

                    # Tab 5: Activity Log
                    with TabPane("Activity Log", id="tab-activity"):
                        with Vertical(classes="panel-card"):
                            yield Label("AUDIT TRAIL / ACTIVITY LOG", classes="panel-card-title")
                            yield RichLog(id="activity-audit-log", max_lines=1000, classes="log-area")
                            yield Button("Clear Historical Activity Log (Planned)", id="btn-clear-history-log", variant="error")

                    # Tab 6: Configuration Settings
                    with TabPane("Configuration Settings", id="tab-config"):
                        with Vertical():
                            with VerticalScroll(classes="panel-card"):
                                yield Label("CONFIGURATION SETTINGS", classes="panel-card-title")
                                yield Label("SQLite Database Path:", classes="info-label")
                                yield Input(id="cfg-db-path", placeholder="e.g. ~/.local/share/opencode/opencode.db")
                                yield Label("Historical Metrics JSON Path:", classes="info-label")
                                yield Input(id="cfg-history-path", placeholder="e.g. ~/.local/share/opencode/ocman_history.json")
                                yield Label("Default Output Directory:", classes="info-label")
                                yield Input(id="cfg-out-dir", placeholder="e.g. opencode-recovery")
                                yield Label("Default Backup Directory:", classes="info-label")
                                yield Input(id="cfg-backup-dir", placeholder="e.g. ~/.local/share/opencode/backups")
                                yield Label("Default Compaction Model:", classes="info-label")
                                yield Input(id="cfg-compaction-model", placeholder="e.g. uri/its_direct/pt1-qwen3-32b-us")
                                yield Label("Default Retention Days:", classes="info-label")
                                yield Input(id="cfg-retention-days", placeholder="e.g. 5")
                                yield Checkbox("Keep Temporary Files", value=False, id="cfg-keep-temp")
                                yield Checkbox("Include Tools in Transcripts", value=False, id="cfg-include-tools")
                                yield Checkbox("Write All Roles", value=False, id="cfg-all-roles")
                            with Horizontal(id="config-buttons-container"):
                                yield Button("Save Configuration", id="btn-save-config", variant="primary")
                                yield Button("Reset to Defaults", id="btn-reset-config", variant="error")
        yield Footer()

    def on_mount(self) -> None:
        import asyncio
        loop = asyncio.get_running_loop()
        old_handler = loop.get_exception_handler()

        def custom_handler(loop, context):
            exception = context.get("exception")
            message = context.get("message", "")
            if isinstance(exception, asyncio.CancelledError) or "CancelledError" in str(exception) or "CancelledError" in message:
                return
            if old_handler:
                old_handler(loop, context)
            else:
                loop.default_exception_handler(context)

        loop.set_exception_handler(custom_handler)

        self.title = f"Ocman TUI Controller v{__version__}"
        self.query_one("#sidebar", SidebarWidget).load_data()
        self.populate_compaction_models()
        self.load_audit_trail()
        self.load_tui_config()

    def populate_compaction_models(self) -> None:
        """Populate the LLM select dropdown with OpenAI-compatible models."""
        try:
            config = load_opencode_config()
            models = extract_models_from_config(config)
            compatible = [m for m in models if m.compatible and m.api_key and m.base_url]
        except Exception:
            compatible = []

        select_widget = self.query_one("#select-compaction-model", Select)
        options = [(m.name, f"{m.provider_id}/{m.model_id}") for m in compatible]
        select_widget.set_options(options)

    def load_audit_trail(self) -> None:
        """Read runs from ocman_history.json and print to Tab 5's RichLog."""
        audit_log = self.query_one("#activity-audit-log", RichLog)
        audit_log.clear()

        history = _load_history()
        runs = history.get("runs", [])

        if not runs:
            audit_log.write("No historical actions recorded in the sidecar ledger.")
            return

        # Print runs reversed (newest first)
        for run in reversed(runs):
            timestamp = run.get("timestamp", "unknown time")
            reason = run.get("reason", "unknown").upper()
            sess_cnt = run.get("sessions_count", 0)
            sub_cnt = run.get("subagents_count", 0)
            msg_cnt = run.get("messages_count", 0)
            cost = run.get("cost", 0.0)
            space_saved = run.get("space_saved", 0)
            deleted_sessions = run.get("sessions", [])

            run_str = f"[{timestamp}] {reason} RUN:\n"
            
            # Details of all deleted sessions
            if deleted_sessions:
                run_str += "  Deleted Sessions:\n"
                for s in deleted_sessions:
                    title = s.get("title", "(untitled)")
                    sid = s.get("id", "unknown")
                    from ocman import _fmt_ts
                    created_str = _fmt_ts(s.get("created")) if s.get("created") else "N/A"
                    updated_str = _fmt_ts(s.get("updated")) if s.get("updated") else "N/A"
                    run_str += f"    - {title} (ID: {sid[:8]}...)\n"
                    run_str += f"      Start: {created_str} | End: {updated_str}\n"
            else:
                run_str += f"  - Deleted Sessions Count: {sess_cnt}\n"

            # Totals Section
            run_str += "  Totals Reclaimed:\n"
            run_str += f"    - Database Rows Deleted: Rows removed successfully\n"
            run_str += f"    - Subagent Sessions:     {sub_cnt}\n"
            run_str += f"    - Messages Deleted:      {msg_cnt}\n"
            run_str += f"    - Accumulated Cost:      ${cost:.4f}\n"
            
            from ocman import human_size_local
            run_str += f"    - Disk Space Saved:      {human_size_local(space_saved)}\n"
            run_str += "--------------------------------------------------------\n"
            
            audit_log.write(run_str)

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar", SidebarWidget)
        sidebar.display = not sidebar.display

    def action_refresh_data(self) -> None:
        self.query_one("#sidebar", SidebarWidget).load_data()
        self.load_audit_trail()
        with contextlib.suppress(Exception):
            self.query_one(DatabaseAdminWidget).refresh_metrics()

    def on_orsession_app_refresh_sidebar(self, event: RefreshSidebar) -> None:
        self.query_one("#sidebar", SidebarWidget).load_data()
        self.load_audit_trail()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if node_data and node_data.get("type") == "session":
            s = node_data["data"]
            self.selected_session_id = node_data["id"]
            self.selected_session_title = s.get("title") or "(untitled)"
            self.update_metadata_view(s)
            self.start_session_export()

    def update_metadata_view(self, s: dict) -> None:
        """Update the top metadata card with session info."""
        metadata_str = (
            f"Title:   [bold]{s.get('title', '(untitled)')}[/]\n"
            f"ID:      {s.get('id', 'N/A')}  |  Model: {s.get('model', 'N/A')}  |  Cost: ${s.get('cost', 0.0):.4f}\n"
            f"Created: {s.get('created', 'N/A')}  |  Updated: {s.get('updated', 'N/A')}\n"
            f"Dir:     {s.get('directory', 'N/A')}"
        )
        self.query_one("#lbl-metadata-grid", Static).update(metadata_str)
        with contextlib.suppress(Exception):
            self.query_one("#lbl-actions-metadata-grid", Static).update(metadata_str)

    def start_session_export(self) -> None:
        """Trigger background export so the TUI doesn't lock up on large DB exports."""
        session_id = self.selected_session_id
        if not session_id:
            return

        self.query_one("#transcript-md", Markdown).update("Loading session transcript in background...")

        def export_worker():
            with self.export_lock:
                if self.selected_session_id != session_id:
                    return  # Cancelled by another selection
                
                try:
                    # Run export subprocess
                    export_path = write_export_to_temp(
                        session_id=session_id,
                        temp_dir=self.temp_dir,
                        verbosity=0
                    )
                    try:
                        parsed_export = load_export_file(export_path, verbosity=0)
                    finally:
                        try:
                            Path(export_path).unlink(missing_ok=True)
                        except Exception:
                            pass
                    turns = extract_turns_from_export(parsed_export)
                    
                    # Store results
                    self.current_export = parsed_export
                    self.current_turns = turns
                    
                    # Ask UI thread to render transcript
                    self.call_from_thread(self.render_current_transcript)
                except Exception as e:
                    self.call_from_thread(self.app.notify, f"Export failed: {e}", severity="error")
                    self.call_from_thread(self.query_one("#transcript-md", Markdown).update, f"**Error loading transcript:** {e}")

        threading.Thread(target=export_worker, daemon=True).start()

    def render_current_transcript(self) -> None:
        """Format and render extracted turns in the transcript Markdown widget."""
        if not self.current_turns:
            self.query_one("#transcript-md", Markdown).update("No turns found in this session.")
            return

        # Fetch control filter configurations
        include_tools = self.query_one("#check-include-tools", Checkbox).value
        all_roles = self.query_one("#check-all-roles", Checkbox).value
        
        try:
            max_interactions = int(self.query_one("#input-max-interactions", Input).value)
        except ValueError:
            max_interactions = 100

        # Filter turns
        turns = self.current_turns
        if not include_tools:
            turns = [t for t in turns if t.role != "tool"]
        if not all_roles:
            turns = filter_conversation_turns(turns)

        # Consolidate sequential roles
        turns = consolidate_turns(turns)

        # Truncate
        if max_interactions > 0:
            turns = truncate_turns_by_interactions(turns, max_interactions)

        # Estimate compaction cost info based on chosen model
        self.update_estimated_cost(turns)

        # Render Markdown
        transcript_markdown = render_transcript(turns, self.selected_session_title)
        self.query_one("#transcript-md", Markdown).update(transcript_markdown)

    def update_estimated_cost(self, turns: list) -> None:
        """Estimate token sizes and compaction API billing."""
        selected_model_spec = self.query_one("#select-compaction-model", Select).value
        if not selected_model_spec or selected_model_spec == Select.BLANK:
            self.query_one("#lbl-est-cost", Label).update("Est Cost: Select a model to estimate")
            return

        try:
            config = load_opencode_config()
            models = extract_models_from_config(config)
            model_info = resolve_model(models, selected_model_spec)
        except Exception:
            self.query_one("#lbl-est-cost", Label).update("Est Cost: Config load error")
            return

        transcript_markdown = render_transcript(turns, self.selected_session_title)
        input_tokens = estimate_tokens(transcript_markdown)
        # Compacted summaries are typically 10-20% of original context size
        est_output_tokens = max(100, int(input_tokens * 0.15))
        
        cost = estimate_cost(input_tokens, est_output_tokens, model_info)
        if cost is not None:
            self.query_one("#lbl-est-cost", Label).update(
                f"Est Cost: ${cost:.4f} (Input: {input_tokens:,} tokens, Est Output: {est_output_tokens:,} tokens)"
            )
        else:
            self.query_one("#lbl-est-cost", Label).update(
                f"Est Cost: N/A ({input_tokens:,} input tokens)"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Transcript reload controls
        if event.button.id == "btn-refresh-transcript":
            self.render_current_transcript()
        
        # Recovery file generation
        elif event.button.id in ("btn-write-transcript", "btn-write-restart", "btn-write-prompt"):
            self.generate_recovery_files(event.button.id)
            
        # LLM Compaction Execution
        elif event.button.id == "btn-run-compaction":
            self.run_llm_compaction()
            
        # Recursive session deletion
        elif event.button.id == "btn-delete-session-rec":
            self.confirm_and_delete_session()

        # Audit history log stub
        elif event.button.id == "btn-clear-history-log":
            self.app.push_screen(FutureTodoModal())

        # Config tab handlers
        elif event.button.id == "btn-save-config":
            self.save_tui_config()
        elif event.button.id == "btn-reset-config":
            self.reset_tui_config()

    def generate_recovery_files(self, button_id: str) -> None:
        """Write specific recovery Markdown files directly to current directory."""
        if not self.selected_session_id or not self.current_turns:
            self.app.notify("Please select a session with a loaded transcript first.", severity="warning")
            return

        include_tools = self.query_one("#check-include-tools", Checkbox).value
        all_roles = self.query_one("#check-all-roles", Checkbox).value

        # Filter
        turns = self.current_turns
        if not include_tools:
            turns = [t for t in turns if t.role != "tool"]
        if not all_roles:
            turns = filter_conversation_turns(turns)
        turns = consolidate_turns(turns)

        # Establish paths
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_title = self.selected_session_title.lower().replace(" ", "-")
        # clean title for filename
        import re
        safe_title = re.sub(r"[^a-z0-9_-]", "", safe_title)[:30]
        
        out_dir = Path("opencode-recovery")
        out_dir.mkdir(parents=True, exist_ok=True)

        session_info = self.current_export.info if self.current_export else {}
        from dataclasses import dataclass
        @dataclass
        class DummySession:
            session_id: str
            title: str
            created: str
            updated: str
        dummy_sess = DummySession(self.selected_session_id, self.selected_session_title, "", "")

        if button_id == "btn-write-transcript":
            path = out_dir / f"opencode-recovery-{self.selected_session_id[:8]}-{timestamp}.transcript.md"
            content = render_transcript(turns, self.selected_session_title)
            write_text(path, content)
            self.app.notify(f"Transcript written to: {path}", severity="information")

        elif button_id == "btn-write-restart":
            path = out_dir / f"opencode-recovery-{self.selected_session_id[:8]}-{timestamp}.restart.md"
            content = render_restart_context(turns, f"session_export_{self.selected_session_id[:8]}", dummy_sess)
            write_text(path, content)
            self.app.notify(f"Restart file written to: {path}", severity="information")

        elif button_id == "btn-write-prompt":
            path = out_dir / f"opencode-recovery-{self.selected_session_id[:8]}-{timestamp}.compact-prompt.md"
            content = render_compact_prompt(turns, dummy_sess)
            write_text(path, content)
            self.app.notify(f"Compaction prompt written to: {path}", severity="information")

    def run_llm_compaction(self) -> None:
        """Call external model completions API in a background thread."""
        if self.compaction_running:
            return

        if not self.selected_session_id or not self.current_turns:
            self.app.notify("Select a session with a loaded transcript first.", severity="warning")
            return

        model_spec = self.query_one("#select-compaction-model", Select).value
        if not model_spec or model_spec == Select.BLANK:
            self.app.notify("Please select a compaction model from the dropdown first.", severity="warning")
            return

        status_lbl = self.query_one("#lbl-compaction-status", Static)
        status_lbl.update("Estimating context and preparing prompt...")
        self.compaction_running = True

        # Generate the prompt content
        dummy_sess = type('Dummy', (), {"session_id": self.selected_session_id, "title": self.selected_session_title})()
        prompt_content = render_compact_prompt(self.current_turns, dummy_sess)

        def compaction_worker():
            try:
                # Load configuration and resolve model details
                config = load_opencode_config()
                models = extract_models_from_config(config)
                model_info = resolve_model(models, model_spec)

                self.call_from_thread(status_lbl.update, f"Calling completions API ({model_info.name})...")
                
                # Execute API Call
                result = call_compaction_api(model_info, prompt_content)
                compacted_text = result["content"]

                # Write compacted result file
                out_dir = Path("opencode-recovery")
                out_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                dest_path = out_dir / f"opencode-{timestamp}-{self.selected_session_id[:8]}.compacted.md"
                
                write_text(dest_path, compacted_text)

                # Log compaction run to history sidecar
                self.log_compaction_to_history(model_spec, dest_path)

                # Update UI
                self.call_from_thread(self.app.notify, f"Compaction completed successfully! Written to {dest_path}", severity="information")
                self.call_from_thread(status_lbl.update, f"Success! Written to {dest_path.name}")
                self.call_from_thread(self.load_audit_trail)
            except Exception as e:
                self.call_from_thread(self.app.notify, f"Compaction failed: {e}", severity="error")
                self.call_from_thread(status_lbl.update, f"Failed: {e}")
            finally:
                self.compaction_running = False

        threading.Thread(target=compaction_worker, daemon=True).start()

    def log_compaction_to_history(self, model_spec: str, filepath: Path) -> None:
        """Register the compaction API call details in history json ledger."""
        try:
            from .core import _load_history, _save_history
            history = _load_history()
            
            run_record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "compaction",
                "model": model_spec,
                "output_file": str(filepath)
            }
            history.setdefault("runs", []).append(run_record)
            _save_history(history)
        except Exception:
            pass

    def confirm_and_delete_session(self) -> None:
        """Spawn safety check confirmation modal overlay before recursive deletion."""
        if not self.selected_session_id:
            self.app.notify("Please select a session in the sidebar tree first.", severity="warning")
            return

        def handle_confirmation(confirmed: bool) -> None:
            if not confirmed:
                return

            self.app.notify("Deleting session in background...", severity="information")
            self.run_worker(
                lambda: self._do_delete_session_worker(self.selected_session_id),
                thread=True
            )

        self.app.push_screen(
            DeletionSafetyModal(self.selected_session_id, self.selected_session_title),
            handle_confirmation
        )

    def _do_delete_session_worker(self, session_id: str) -> None:
        db_path = get_db_path()
        
        # Query session details before deletion
        session_title = "Unknown"
        time_created_str = "Unknown"
        time_updated_str = "Unknown"
        try:
            sqlite3 = _get_sqlite()
            if sqlite3 and db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT title, time_created, time_updated FROM session WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                if row:
                    session_title = row[0] or "Untitled"
                    from ocman import _fmt_ts
                    time_created_str = _fmt_ts(row[1])
                    time_updated_str = _fmt_ts(row[2])
                conn.close()
        except Exception:
            pass

        try:
            # Pre-size of DB
            size_before = get_file_size_local(db_path)

            # Patch input check
            original_input = builtins.input
            builtins.input = lambda *args, **kwargs: "yes"

            try:
                db_delete_session_recursive(
                    session_id=session_id,
                    dry_run=False,
                    force=True, # bypass locks because user confirmed in TUI
                    verbosity=0
                )
            finally:
                builtins.input = original_input

            # Post-size of DB after VACUUM
            size_after = get_file_size_local(db_path)
            saved_space = max(0, size_before - size_after)

            # Schedule UI updates on main thread
            def update_ui() -> None:
                self.app.notify(f"Recursively deleted session {session_id[:8]}", severity="information")
                summary = {
                    "session_id": session_id,
                    "session_title": session_title,
                    "start_date": time_created_str,
                    "end_date": time_updated_str,
                    "db_rows": "Rows removed successfully (foreign keys off, committed).",
                    "files": "Session diff JSON files unlinked on disk.",
                    "space": f"SQLite File Shrunk: {human_size_local(saved_space)} (post-VACUUM)"
                }
                self.app.push_screen(PostExecutionSummaryModal(summary))

                # Clear selection context and reload
                if self.selected_session_id == session_id:
                    self.selected_session_id = None
                    self.selected_session_title = ""
                    self.query_one("#lbl-metadata-grid", Static).update("Select a session in the sidebar to view details.")
                    with contextlib.suppress(Exception):
                        self.query_one("#lbl-actions-metadata-grid", Static).update("Select a session in the sidebar to view details.")
                    self.query_one("#transcript-md", Markdown).update("")
                    self.current_turns = []
                    self.current_export = None

                # Refresh trees & stats
                self.action_refresh_data()

            self.call_from_thread(update_ui)
        except Exception as e:
            self.call_from_thread(self.app.notify, f"Deletion failed: {e}", severity="error")

    def load_tui_config(self) -> None:
        """Load TOML configuration settings into input widgets."""
        try:
            config = load_ocman_config()
            self.query_one("#cfg-db-path", Input).value = str(config.get("db_path", ""))
            self.query_one("#cfg-history-path", Input).value = str(config.get("history_path", ""))
            self.query_one("#cfg-out-dir", Input).value = str(config.get("default_out_dir", ""))
            self.query_one("#cfg-backup-dir", Input).value = str(config.get("default_backup_dir", ""))
            self.query_one("#cfg-compaction-model", Input).value = str(config.get("default_compaction_model", ""))
            self.query_one("#cfg-retention-days", Input).value = str(config.get("default_retention_days", ""))
            self.query_one("#cfg-keep-temp", Checkbox).value = bool(config.get("keep_temp", False))
            self.query_one("#cfg-include-tools", Checkbox).value = bool(config.get("include_tools", False))
            self.query_one("#cfg-all-roles", Checkbox).value = bool(config.get("all_roles", False))
            self.config_loaded = True
        except Exception as e:
            self.notify(f"Failed to load configuration: {e}", severity="error")

    def save_tui_config(self, notify: bool = True) -> None:
        """Save form field values back to the TOML configuration file."""
        if not getattr(self, "config_loaded", False):
            return
        try:
            db_path = self.query_one("#cfg-db-path", Input).value.strip()
            history_path = self.query_one("#cfg-history-path", Input).value.strip()
            out_dir = self.query_one("#cfg-out-dir", Input).value.strip()
            backup_dir = self.query_one("#cfg-backup-dir", Input).value.strip()
            compaction_model = self.query_one("#cfg-compaction-model", Input).value.strip()

            try:
                retention_days = int(self.query_one("#cfg-retention-days", Input).value.strip())
            except ValueError:
                if notify:
                    self.notify("Retention Days must be an integer.", severity="error")
                return

            config = {
                "db_path": db_path,
                "history_path": history_path,
                "default_out_dir": out_dir,
                "default_compaction_model": compaction_model,
                "default_backup_dir": backup_dir,
                "default_retention_days": retention_days,
                "keep_temp": self.query_one("#cfg-keep-temp", Checkbox).value,
                "include_tools": self.query_one("#cfg-include-tools", Checkbox).value,
                "all_roles": self.query_one("#cfg-all-roles", Checkbox).value,
            }

            save_ocman_config(config)

            # Immediately update the in-memory variables in ocman.py!
            import ocman
            ocman.OPENCODE_DB_PATH = Path(db_path).expanduser()
            ocman.OPENCODE_HISTORY_PATH = Path(history_path).expanduser()

            if notify:
                self.notify("Configuration saved successfully.", severity="information")

            # Reload data in case database path changed!
            db_path_resolved = Path(db_path).expanduser()
            if notify or (db_path_resolved.exists() and db_path_resolved.is_file()):
                self.query_one("#sidebar", SidebarWidget).load_data()
                self.load_audit_trail()

                # Update history / database metrics widget if visible
                with contextlib.suppress(Exception):
                    admin_widget = self.query_one(DatabaseAdminWidget)
                    admin_widget.refresh_metrics()
        except Exception as e:
            if notify:
                self.notify(f"Failed to save configuration: {e}", severity="error")

    def reset_tui_config(self) -> None:
        """Reset form inputs to defaults and save."""
        try:
            save_ocman_config(DEFAULT_CONFIG)

            # Immediately update active settings
            import ocman
            ocman.OPENCODE_DB_PATH = Path(DEFAULT_CONFIG["db_path"]).expanduser()
            ocman.OPENCODE_HISTORY_PATH = Path(DEFAULT_CONFIG["history_path"]).expanduser()

            self.load_tui_config()
            self.notify("Configuration reset to defaults.", severity="information")

            self.query_one("#sidebar", SidebarWidget).load_data()
            self.load_audit_trail()
            with contextlib.suppress(Exception):
                admin_widget = self.query_one(DatabaseAdminWidget)
                admin_widget.refresh_metrics()
        except Exception as e:
            self.notify(f"Reset failed: {e}", severity="error")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Auto-save configuration settings when user presses Enter on any configuration input."""
        if event.input.id and event.input.id.startswith("cfg-") and getattr(self, "config_loaded", False):
            self.save_tui_config(notify=True)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Auto-save configuration settings when user toggles any configuration checkbox."""
        if event.checkbox.id and event.checkbox.id.startswith("cfg-") and getattr(self, "config_loaded", False):
            self.save_tui_config(notify=False)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Auto-save configuration settings when switching tabs."""
        if getattr(self, "config_loaded", False):
            self.save_tui_config(notify=False)

    def on_unmount(self) -> None:
        # Auto-save before quitting
        if getattr(self, "config_loaded", False):
            with contextlib.suppress(Exception):
                self.save_tui_config(notify=False)
        # Delete the temp session export directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
