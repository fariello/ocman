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
    Header, Footer, Static, Button, Checkbox, Input, Label, Select, TabbedContent, TabPane, Markdown, RichLog, Tree, DataTable
)
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.message import Message

from ocman import load_ocman_config, save_ocman_config, DEFAULT_CONFIG

from . import __version__
from .core import (
    db_list_sessions,
    db_delete_session_recursive,
    db_delete_project_recursive,
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
    SessionInfo,
    write_text,
    _load_history,
    _get_sqlite,
    human_size_local,
    get_file_size_local,
    SESSION_RELATIONAL_TABLES,
    get_db_path,
    truncate_turns_by_interactions,
    truncate_turns_by_lines,
    db_create_rollback_backup,
    db_restore_rollback_backup,
    move_directory_structure,
    db_move_project_metadata,
    bundle_session_data,
    extract_and_import_session,
    bundle_project_data,
    extract_and_import_project,
    extract_sessions_before_delete,
    resolve_extract_output_dir,
    clear_history_ledger,
    db_delete_sessions_batch,
    chunk_turns,
    part_recovery_name,
)
from .widgets.sidebar import SidebarWidget
from .widgets.database import DatabaseAdminWidget
from .widgets.models import ModelsWidget
from .widgets.storage import StorageWidget
from .widgets.spend import SpendWidget
from .widgets.running import RunningWidget


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


class ClearHistoryModal(ModalScreen[bool]):
    """Typed-yes confirmation for wiping the activity ledger (runs + all-time totals)."""
    def compose(self) -> ComposeResult:
        yield Container(
            Label("CLEAR ACTIVITY HISTORY", id="dialog-title"),
            Label(
                "This erases the entire activity ledger (all run records) and resets ALL "
                "all-time totals. This cannot be undone.",
                classes="info-value"
            ),
            Label("Type 'yes' below to confirm:", classes="info-label"),
            Input(placeholder="Type 'yes' to confirm", id="input-clear-history-yes"),
            Horizontal(
                Button("Cancel", id="btn-cancel-clear-history"),
                Button("CLEAR HISTORY", id="btn-confirm-clear-history", variant="error", disabled=True),
                classes="horizontal-buttons"
            ),
            id="dialog-container"
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-clear-history-yes":
            self.query_one("#btn-confirm-clear-history", Button).disabled = (
                event.value.strip().lower() != "yes"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-clear-history":
            self.dismiss(False)
        elif event.button.id == "btn-confirm-clear-history":
            self.dismiss(True)


class BatchDeleteModal(ModalScreen[Optional[dict]]):
    """Typed-yes confirmation for deleting MANY selected sessions in one batch.

    Dismisses None on cancel, or {"extracts": bool} on confirm (whether to write recovery
    extracts for the selected sessions first). db_delete_sessions_batch does not confirm on
    its own, so this modal is the required gate.
    """
    def __init__(self, count: int) -> None:
        super().__init__()
        self._count = count

    def compose(self) -> ComposeResult:
        yield Container(
            Label("CONFIRM BATCH SESSION DELETION", id="dialog-title"),
            Label(f"You are about to delete {self._count} selected session(s) and their "
                  "subagent descendants, in one consolidated operation. A single rollback "
                  "backup is taken first. This is irreversible.", classes="info-value"),
            Checkbox("Write recovery extracts first (.prompt/.restart/.transcript)",
                     value=True, id="check-batch-extracts"),
            Label("Type 'yes' below to confirm:", classes="info-label"),
            Input(placeholder="Type 'yes' to confirm", id="input-batch-yes"),
            Horizontal(
                Button("Cancel", id="btn-cancel-batch-del"),
                Button("CONFIRM BATCH DELETE", id="btn-confirm-batch-del",
                       variant="error", disabled=True),
                classes="horizontal-buttons",
            ),
            id="dialog-container",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-batch-yes":
            self.query_one("#btn-confirm-batch-del", Button).disabled = (
                event.value.strip().lower() != "yes")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-batch-del":
            self.dismiss(None)
        elif event.button.id == "btn-confirm-batch-del":
            extracts = True
            with contextlib.suppress(Exception):
                extracts = self.query_one("#check-batch-extracts", Checkbox).value
            self.dismiss({"extracts": bool(extracts)})


class DeletionSafetyModal(ModalScreen[Optional[dict]]):
    """Safety modal confirming recursive deletion of sessions and related data.

    Dismisses with None on cancel, or a dict ``{"extracts": bool}`` on confirm, so the
    caller learns whether to write recovery extracts (prompt/restart/transcript) first.
    """
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
            Checkbox("Write recovery extracts first (.prompt/.restart/.transcript)",
                     value=True, id="check-del-extracts"),
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
            self.dismiss(None)
            return

        conn = None
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
        except Exception as e:
            self.app.notify(f"Failed to gather deletion details: {e}", severity="error")
            self.dismiss(None)
            return
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

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
            self.dismiss(None)
        elif event.button.id == "btn-confirm-del":
            extracts = True
            with contextlib.suppress(Exception):
                extracts = self.query_one("#check-del-extracts", Checkbox).value
            self.dismiss({"extracts": bool(extracts)})


class ProjectDeletionSafetyModal(ModalScreen[Optional[dict]]):
    """Safety modal confirming deletion of projects and related data."""
    def __init__(self, project_id: str, name: str) -> None:
        super().__init__()
        self.project_id = project_id
        self.project_name = name
        self.descendants_info: List[Dict[str, Any]] = []
        self.counts: Dict[str, int] = {}
        self.files_to_delete: List[Path] = []

    def compose(self) -> ComposeResult:
        yield Container(
            Label("CONFIRM PROJECT DELETION", id="dialog-title"),
            VerticalScroll(
                Label("You are about to delete the following project and all its sessions:", classes="info-label"),
                Static(id="lbl-del-project-info", classes="margin-vertical"),
                Label("Sessions that will be recursively deleted:", classes="info-label"),
                Static(id="lbl-del-hierarchy", classes="margin-vertical"),
                Label("Database rows to be deleted:", classes="info-label"),
                Static(id="lbl-del-db-rows", classes="margin-vertical"),
                Label("Disk files to be deleted:", classes="info-label"),
                Static(id="lbl-del-files", classes="margin-vertical"),
                id="del-safety-scroll"
            ),
            Checkbox("Write recovery extracts first (.prompt/.restart/.transcript)",
                     value=True, id="check-del-extracts"),
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
            self.dismiss(None)
            return

        conn = None
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Fetch project directory/name details
            cursor.execute("SELECT name, worktree FROM project WHERE id = ?", (self.project_id,))
            row = cursor.fetchone()
            proj_name = row[0] or "(unnamed)" if row else self.project_name
            proj_dir = row[1] or "(no worktree)" if row else "N/A"
            self.query_one("#lbl-del-project-info", Static).update(
                f"  Name: {proj_name}\n  Directory: {proj_dir}\n  ID: {self.project_id}"
            )

            # Recursive session search (all sessions associated with the project and any child subagent sessions)
            cursor.execute("""
                WITH RECURSIVE session_tree(id) AS (
                    SELECT id FROM session WHERE project_id = ?
                    UNION
                    SELECT s.id FROM session s JOIN session_tree st ON s.parent_id = st.id
                )
                SELECT id FROM session_tree;
            """, (self.project_id,))
            session_ids = [r[0] for r in cursor.fetchall()]
            
            # Get table counts
            if session_ids:
                placeholders = ",".join("?" for _ in session_ids)
                for table, col in SESSION_RELATIONAL_TABLES:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IN ({placeholders})", session_ids)
                    self.counts[table] = cursor.fetchone()[0]

                # Get session details
                cursor.execute(f"SELECT id, title FROM session WHERE id IN ({placeholders})", session_ids)
                for r in cursor.fetchall():
                    self.descendants_info.append({
                        "id": r[0],
                        "title": r[1] or "(untitled)"
                    })
            else:
                for table, col in SESSION_RELATIONAL_TABLES:
                    self.counts[table] = 0
            
        except Exception as e:
            self.app.notify(f"Failed to gather project deletion details: {e}", severity="error")
            self.dismiss(None)
            return
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        # Find disk files
        storage_dir = (Path.home() / ".local" / "share" / "opencode" / "storage" / "session_diff").resolve()
        for sid in session_ids:
            if sid:
                diff_file = storage_dir / f"{sid.strip()}.json"
                if diff_file.exists():
                    self.files_to_delete.append(diff_file)

        # Update text displays
        hierarchy_text = ""
        if self.descendants_info:
            for s in self.descendants_info:
                hierarchy_text += f"  - {s['title']} (ID: {s['id']})\n"
        else:
            hierarchy_text = "  None\n"
        self.query_one("#lbl-del-hierarchy", Static).update(hierarchy_text)

        rows_text = ""
        for table, col in SESSION_RELATIONAL_TABLES:
            count = self.counts.get(table, 0)
            rows_text += f"  {table:<25}: {count:,}\n"
        rows_text += f"  {'project':<25}: 1\n"
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
            self.dismiss(None)
        elif event.button.id == "btn-confirm-del":
            extracts = True
            with contextlib.suppress(Exception):
                extracts = self.query_one("#check-del-extracts", Checkbox).value
            self.dismiss({"extracts": bool(extracts)})


class MoveProjectModal(ModalScreen[bool]):
    """Modal screen for moving a project (physically or metadata-only)."""
    def __init__(self, project_id: str, name: str) -> None:
        super().__init__()
        self.project_id = project_id
        self.project_name = name
        self.old_path = ""
        self.src_exists = False

    def compose(self) -> ComposeResult:
        yield Container(
            Label("MOVE PROJECT / UPDATE PATH", id="dialog-title"),
            VerticalScroll(
                Label(f"Project ID: {self.project_id}", classes="info-label"),
                Label(f"Project Name: {self.project_name}", classes="info-label"),
                Label("Old Path (Read Only):", classes="info-label"),
                Input(id="input-old-path", disabled=True),
                Label("New Path:", classes="info-label"),
                Input(placeholder="Enter new absolute path", id="input-new-path"),
                Checkbox("Perform physical directory move on disk", value=True, id="check-physical-move"),
                Static("", id="lbl-status-warning", classes="margin-vertical"),
                id="move-project-scroll"
            ),
            Horizontal(
                Button("Cancel", id="btn-cancel-move"),
                Button("SUBMIT", id="btn-submit-move", variant="success"),
                classes="horizontal-buttons"
            ),
            id="dialog-container"
        )

    def on_mount(self) -> None:
        # Fetch current project directory from database
        sqlite3 = _get_sqlite()
        db_path = get_db_path()
        if not sqlite3 or not db_path.exists():
            self.dismiss(False)
            return

        conn = None
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT worktree FROM project WHERE id = ?", (self.project_id,))
            row = cursor.fetchone()
            if row and row[0]:
                self.old_path = row[0]
            else:
                self.old_path = ""
        except Exception as e:
            self.app.notify(f"Error querying project directory: {e}", severity="error")
            self.dismiss(False)
            return
        finally:
            if conn:
                conn.close()

        self.query_one("#input-old-path", Input).value = self.old_path

        # Check if old_path exists on disk
        if self.old_path:
            try:
                p = Path(self.old_path).expanduser().resolve()
                self.src_exists = p.exists() and p.is_dir()
            except Exception:
                self.src_exists = False

        warning_lbl = self.query_one("#lbl-status-warning", Static)
        physical_checkbox = self.query_one("#check-physical-move", Checkbox)

        if not self.src_exists:
            physical_checkbox.value = False
            physical_checkbox.disabled = True
            warning_lbl.update("[yellow][*] Source directory does not exist on disk. Metadata-only update will be performed.[/]")
        else:
            warning_lbl.update("[green][*] Source directory found on disk. Physical move is recommended.[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-move":
            self.dismiss(False)
        elif event.button.id == "btn-submit-move":
            new_path_str = self.query_one("#input-new-path", Input).value.strip()
            if not new_path_str:
                self.app.notify("New path cannot be empty.", severity="warning")
                return

            physical_move = self.query_one("#check-physical-move", Checkbox).value

            # Pre-flight checks
            if physical_move:
                try:
                    dest = Path(new_path_str).expanduser().resolve()
                    if dest.exists():
                        self.app.notify("Destination path already exists.", severity="error")
                        return
                except Exception as e:
                    self.app.notify(f"Invalid destination path: {e}", severity="error")
                    return

            self.app.notify("Processing move in background...", severity="information")
            self.run_worker(
                lambda: self._do_move_worker(new_path_str, physical_move),
                thread=True
            )

    def _do_move_worker(self, new_path_str: str, physical_move: bool) -> None:
        old_path_obj = Path(self.old_path)
        new_path_obj = Path(new_path_str)

        backup_file = None
        physical_moved = False
        try:
            # Create DB rollback backup
            backup_file = db_create_rollback_backup()

            # Physical move if requested
            if physical_move:
                move_directory_structure(old_path_obj, new_path_obj)
                physical_moved = True

            # Database update
            db_move_project_metadata(self.project_id, self.old_path, new_path_str)

            # Cleanup backup on success
            if backup_file and backup_file.exists():
                try:
                    backup_file.unlink()
                    wal_backup = backup_file.parent / f"{backup_file.name}-wal"
                    shm_backup = backup_file.parent / f"{backup_file.name}-shm"
                    if wal_backup.exists():
                        wal_backup.unlink()
                    if shm_backup.exists():
                        shm_backup.unlink()
                except Exception:
                    pass

            def update_success() -> None:
                self.app.notify("Project successfully moved!", severity="information")
                self.dismiss(True)

            self.app._safe_call_from_thread(update_success)

        except Exception as e:
            # Rollback DB
            if backup_file and backup_file.exists():
                db_restore_rollback_backup(backup_file)
                try:
                    backup_file.unlink()
                    wal_backup = backup_file.parent / f"{backup_file.name}-wal"
                    shm_backup = backup_file.parent / f"{backup_file.name}-shm"
                    if wal_backup.exists():
                        wal_backup.unlink()
                    if shm_backup.exists():
                        shm_backup.unlink()
                except Exception:
                    pass

            # Rollback Physical Move
            if physical_moved:
                try:
                    import shutil
                    shutil.move(str(new_path_obj.expanduser().resolve()), str(old_path_obj.expanduser().resolve()))
                except Exception as re:
                    print(f"[-] Critical: Failed to restore physical directory: {re}")

            def update_failure() -> None:
                self.app.notify(f"Move failed: {e}", severity="error")

            self.app._safe_call_from_thread(update_failure)


class MoveSessionModal(ModalScreen[bool]):
    """Local session move: update the session's working directory in the DB (metadata-only).

    Remote/git-aware move stays on the CLI (`ocman session move ID --to host:/path`); a note
    says so. This modal performs the local DB metadata update via db_move_session_metadata.
    """
    def __init__(self, session_id: str, title: str, current_dir: str) -> None:
        super().__init__()
        self.session_id = session_id
        self.session_title = title
        self.current_dir = current_dir or ""

    def compose(self) -> ComposeResult:
        yield Container(
            Label("MOVE SESSION (local, metadata)", id="dialog-title"),
            VerticalScroll(
                Label(f"Session: {self.session_title} [{self.session_id[:8]}]", classes="info-label"),
                Label(f"Current directory: {self.current_dir or '(unknown)'}", classes="info-label"),
                Label("New directory:", classes="info-label"),
                Input(value=self.current_dir, placeholder="e.g. ~/VC/moved-project", id="input-move-session-dir"),
                Label("Remote / git-aware moves stay on the CLI: "
                      "ocman session move <id> --to host:/path", classes="info-value"),
                id="move-session-scroll",
            ),
            Horizontal(
                Button("Cancel", id="btn-cancel-move-session"),
                Button("MOVE", id="btn-submit-move-session", variant="primary"),
                classes="horizontal-buttons",
            ),
            id="dialog-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-move-session":
            self.dismiss(False)
        elif event.button.id == "btn-submit-move-session":
            new_dir = self.query_one("#input-move-session-dir", Input).value.strip()
            if not new_dir:
                self.app.notify("New directory cannot be empty.", severity="warning")
                return
            self.app.notify("Moving session (metadata) in background...", severity="information")
            self.run_worker(lambda: self._do_move_worker(new_dir), thread=True)

    def _do_move_worker(self, new_dir: str) -> None:
        from .core import db_move_session_metadata
        try:
            db_move_session_metadata(self.session_id, self.current_dir, new_dir)

            def ok() -> None:
                self.app.notify("Session directory updated.", severity="information")
                self.dismiss(True)
            self.app._safe_call_from_thread(ok)
        except Exception as e:  # noqa: BLE001
            self.app._safe_call_from_thread(
                self.app.notify, f"Session move failed: {e}", severity="error")


class FilterModal(ModalScreen[bool]):
    """LLM re-scope a recovery/compacted document to a project/scope (CLI `filter` parity).

    Reuses cli_filter, which enforces the same egress guards as compaction (size cap
    filter_max_bytes + secret/PII scan). Runs in a worker; the cost confirmation is
    auto-accepted (the user opted in by launching it) and output is captured to a log.
    """
    def compose(self) -> ComposeResult:
        from textual.widgets import Select
        yield Container(
            Label("FILTER (LLM RE-SCOPE A DOCUMENT)", id="dialog-title"),
            VerticalScroll(
                Label("Input document (.md/.txt recovery or compacted file):", classes="info-label"),
                Input(placeholder="e.g. ./opencode-recovery/...restart.md", id="input-filter-src"),
                Label("Scope (free text describing what to keep):", classes="info-label"),
                Input(placeholder="e.g. only the auth refactor", id="input-filter-scope"),
                Label("Model:", classes="info-label"),
                Select([], prompt="Choose model...", id="select-filter-model"),
                Static("Egress guards apply (size cap + secret scan), same as compaction.",
                       classes="info-value"),
                id="filter-scroll",
            ),
            Horizontal(
                Button("Cancel", id="btn-cancel-filter"),
                Button("RUN FILTER", id="btn-submit-filter", variant="success"),
                classes="horizontal-buttons",
            ),
            id="dialog-container",
        )

    def on_mount(self) -> None:
        from textual.widgets import Select
        opts = []
        try:
            config = load_opencode_config()
            models = extract_models_from_config(config)
            opts = [(m.name, f"{m.provider_id}/{m.model_id}")
                    for m in models if m.compatible and m.api_key and m.base_url]
        except Exception:
            opts = []
        self.query_one("#select-filter-model", Select).set_options(opts)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from textual.widgets import Select
        if event.button.id == "btn-cancel-filter":
            self.dismiss(False)
        elif event.button.id == "btn-submit-filter":
            src = self.query_one("#input-filter-src", Input).value.strip()
            scope = self.query_one("#input-filter-scope", Input).value.strip()
            model = self.query_one("#select-filter-model", Select).value
            if not src:
                self.app.notify("Input document path is required.", severity="warning")
                return
            if not scope:
                self.app.notify("A scope is required.", severity="warning")
                return
            if not model or model == Select.BLANK:
                self.app.notify("Choose a model.", severity="warning")
                return
            self.app.notify("Running filter in background...", severity="information")
            self.run_worker(
                lambda: self._do_filter_worker(Path(src).expanduser(), scope, str(model)),
                thread=True)

    def _do_filter_worker(self, src: Path, scope: str, model_spec: str) -> None:
        from .core import cli_filter
        import builtins
        original_input = builtins.input
        builtins.input = lambda *a, **k: "yes"  # auto-accept the cost confirmation
        try:
            out = cli_filter(src, project=None, scope=scope, model_spec=model_spec,
                             out_path=None, verbosity=0)
            def ok() -> None:
                if out:
                    self.app.notify(f"Filter wrote {Path(out).name}", severity="information")
                else:
                    self.app.notify("Filter cancelled or produced no output.", severity="warning")
                self.dismiss(True)
            self.app._safe_call_from_thread(ok)
        except Exception as e:  # noqa: BLE001
            self.app._safe_call_from_thread(
                self.app.notify, f"Filter failed: {e}", severity="error")
        finally:
            builtins.input = original_input


class ExportSessionModal(ModalScreen[bool]):
    """Modal screen for exporting a session (or a whole project) to an .ocbox bundle."""
    def __init__(self, target_id: str, title: str, is_project: bool = False) -> None:
        super().__init__()
        self.session_id = target_id  # session id OR project id (see is_project)
        self.session_title = title
        self.is_project = is_project

    def compose(self) -> ComposeResult:
        default_name = f"{self.session_id}.ocbox"
        default_path = str(Path.home() / default_name)
        kind = "PROJECT" if self.is_project else "SESSION"
        id_label = "Project ID" if self.is_project else "Session ID"
        title_label = "Project" if self.is_project else "Session Title"
        yield Container(
            Label(f"EXPORT {kind} BUNDLE", id="dialog-title"),
            VerticalScroll(
                Label(f"{id_label}: {self.session_id}", classes="info-label"),
                Label(f"{title_label}: {self.session_title}", classes="info-label"),
                Label("Export File Target Path:", classes="info-label"),
                Input(value=default_path, placeholder="e.g. ~/my_bundle.ocbox", id="input-export-path"),
                id="export-session-scroll"
            ),
            Horizontal(
                Button("Cancel", id="btn-cancel-export"),
                Button("EXPORT", id="btn-submit-export", variant="success"),
                classes="horizontal-buttons"
            ),
            id="dialog-container"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-export":
            self.dismiss(False)
        elif event.button.id == "btn-submit-export":
            export_path_str = self.query_one("#input-export-path", Input).value.strip()
            if not export_path_str:
                self.app.notify("Export path cannot be empty.", severity="warning")
                return

            dest_path = Path(export_path_str).expanduser().resolve()
            if dest_path.exists():
                self.app.notify("Target file already exists. It will be overwritten.", severity="warning")

            self.app.notify("Exporting session in background...", severity="information")
            self.run_worker(
                lambda: self._do_export_worker(dest_path),
                thread=True
            )

    def _do_export_worker(self, dest_path: Path) -> None:
        try:
            if self.is_project:
                from .core import bundle_project_data
                bundle_project_data(self.session_id, dest_path)
                noun = "project"
            else:
                bundle_session_data(self.session_id, dest_path)
                noun = "session"

            def on_success() -> None:
                self.app.notify(f"Successfully exported {noun} to {dest_path.name}!",
                                severity="information")
                self.dismiss(True)
            self.app._safe_call_from_thread(on_success)
        except Exception as e:
            def on_failure() -> None:
                self.app.notify(f"Export failed: {e}", severity="error")
            self.app._safe_call_from_thread(on_failure)


class ImportSessionModal(ModalScreen[bool]):
    """Modal screen for importing a session from an .ocbox bundle."""
    def compose(self) -> ComposeResult:
        from textual.widgets import Select
        yield Container(
            Label("IMPORT SESSION BUNDLE", id="dialog-title"),
            VerticalScroll(
                Label("Session Bundle Path (.ocbox):", classes="info-label"),
                Input(placeholder="e.g. ~/backup.ocbox", id="input-import-bundle-path"),
                Label("Target Project Mapping:", classes="info-label"),
                Select([], prompt="Select existing project (or choose Create New)...", id="select-import-project"),
                Label("New Project Workspace Path (if creating new):", classes="info-label"),
                Input(placeholder="e.g. ~/VC/my-new-project", id="input-import-new-project-path"),
                id="import-session-scroll"
            ),
            Horizontal(
                Button("Cancel", id="btn-cancel-import"),
                Button("IMPORT", id="btn-submit-import", variant="success"),
                classes="horizontal-buttons"
            ),
            id="dialog-container"
        )

    def on_mount(self) -> None:
        from textual.widgets import Select
        projects_list = []
        try:
            from .core import db_list_projects
            projects = db_list_projects()
            for p in projects:
                name = p.get("name") or p.get("id") or "Unnamed"
                projects_list.append((f"{name} ({p['directory']})", p["id"]))
        except Exception:
            pass

        projects_list.insert(0, ("[Create New Project workspace]", "NEW_PROJECT"))

        select_widget = self.query_one("#select-import-project", Select)
        select_widget.set_options(projects_list)
        select_widget.value = "NEW_PROJECT"

    def on_select_changed(self, event: Select.Changed) -> None:
        new_proj_input = self.query_one("#input-import-new-project-path", Input)
        if event.value == "NEW_PROJECT":
            new_proj_input.disabled = False
        else:
            new_proj_input.disabled = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-import":
            self.dismiss(False)
        elif event.button.id == "btn-submit-import":
            bundle_path_str = self.query_one("#input-import-bundle-path", Input).value.strip()
            if not bundle_path_str:
                self.app.notify("Bundle path cannot be empty.", severity="warning")
                return

            bundle_path = Path(bundle_path_str).expanduser().resolve()
            if not bundle_path.exists():
                self.app.notify("Bundle file does not exist.", severity="error")
                return

            from textual.widgets import Select
            proj_val = self.query_one("#select-import-project", Select).value
            
            target_project_id = None
            new_project_path = None

            if proj_val == "NEW_PROJECT":
                new_project_path_str = self.query_one("#input-import-new-project-path", Input).value.strip()
                if not new_project_path_str:
                    self.app.notify("Please specify workspace path for the new project.", severity="warning")
                    return
                new_project_path = new_project_path_str
            else:
                target_project_id = proj_val

            self.app.notify("Importing session in background...", severity="information")
            self.run_worker(
                lambda: self._do_import_worker(bundle_path, target_project_id, new_project_path),
                thread=True
            )

    def _do_import_worker(self, bundle_path: Path, target_project_id: str | None, new_project_path: str | None) -> None:
        try:
            # Auto-detect bundle kind from meta.json (mirrors the CLI import): a project
            # bundle routes to the project importer; anything else is a session import.
            kind = None
            try:
                import zipfile as _zf, json as _json
                with _zf.ZipFile(bundle_path, "r") as zf:
                    kind = _json.loads(zf.read("meta.json").decode("utf-8")).get("kind")
            except Exception:
                kind = None

            if kind == "project":
                imported_id = extract_and_import_project(
                    bundle_path,
                    target_project_id=target_project_id,
                    new_project_path=new_project_path,
                )
                noun = "project"
            else:
                imported_id = extract_and_import_session(
                    bundle_path,
                    target_project_id=target_project_id,
                    new_project_path=new_project_path,
                )
                noun = "session"

            def on_success() -> None:
                self.app.notify(f"Successfully imported {noun} as {imported_id}!",
                                severity="information")
                self.dismiss(True)
            self.app._safe_call_from_thread(on_success)
        except Exception as e:
            def on_failure() -> None:
                self.app.notify(f"Import failed: {e}", severity="error")
            self.app._safe_call_from_thread(on_failure)


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


# ---------------------------------------------------------------------------
# Footer-command overlays: Doctor (Storage), Running, and Config.
# These were formerly TabPanes; they now open as full-screen overlays reached
# from the footer command bar (^d / ^r / ^g) and dismissed with ^m / Esc.
# Each hosts a FRESH widget that self-loads on mount, so no tab-pane state is
# re-parented (the storage-worker lifecycle stays as-is).
# ---------------------------------------------------------------------------
class _FooterOverlay(ModalScreen[None]):
    """Base for the footer-command overlays: a large centered panel that dismisses
    on Escape or Ctrl+M (Main)."""

    BINDINGS = [
        # Esc dismisses the overlay. No ctrl+m: in many terminals ctrl+m IS Enter (CR),
        # so binding it risked hijacking Enter. The footer "Esc Main" button is the click path.
        Binding("escape", "dismiss_overlay", "Main", show=False),
    ]

    CSS = """
    _FooterOverlay {
        align: center middle;
    }
    .overlay-panel {
        width: 90%;
        height: 90%;
        background: #1e1e2e;
        border: round #cba6f7;
        padding: 1 2;
    }
    .overlay-title {
        color: #cba6f7;
        text-style: bold;
        margin-bottom: 1;
    }
    #overlay-close-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """

    title_text: str = "OVERLAY"

    def action_dismiss_overlay(self) -> None:
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-overlay-close":
            self.dismiss()


class DoctorOverlay(_FooterOverlay):
    """`^d` Doctor: the read-only storage checkup (a fresh StorageWidget)."""
    title_text = "🩺 STORAGE / DOCTOR CHECKUP  (Esc or ^m to return)"

    def compose(self) -> ComposeResult:
        with Vertical(classes="overlay-panel"):
            yield Label(self.title_text, classes="overlay-title")
            yield StorageWidget()
            with Horizontal(id="overlay-close-row"):
                yield Button("Esc Main", id="btn-overlay-close", variant="primary")


class RunningOverlay(_FooterOverlay):
    """`^r` Running: observe-only running OpenCode instances (a fresh RunningWidget)."""
    title_text = "▶ RUNNING OPENCODE INSTANCES  (Esc or ^m to return)"

    def compose(self) -> ComposeResult:
        with Vertical(classes="overlay-panel"):
            yield Label(self.title_text, classes="overlay-title")
            yield RunningWidget()
            with Horizontal(id="overlay-close-row"):
                yield Button("Esc Main", id="btn-overlay-close", variant="primary")


class ConfigOverlay(_FooterOverlay):
    """`^g` Config: the configuration form. Loads on mount; auto-saves on change
    (the app-level cfg-* handlers) and, critically, saves on dismiss (replacing the
    old auto-save-on-tab-switch that no longer fires now that Config is not a tab)."""
    title_text = "⚙ CONFIGURATION SETTINGS  (Esc or ^m to return)"

    def compose(self) -> ComposeResult:
        with Vertical(classes="overlay-panel"):
            yield Label(self.title_text, classes="overlay-title")
            with VerticalScroll(classes="panel-card"):
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
            with Horizontal(id="overlay-close-row"):
                yield Button("Esc Main", id="btn-overlay-close", variant="primary")

    def on_mount(self) -> None:
        # Load current config into THIS overlay's fields.
        with contextlib.suppress(Exception):
            self.app.load_tui_config(root=self)

    def action_dismiss_overlay(self) -> None:
        # Save-on-dismiss: replaces the old auto-save-on-tab-switch path.
        with contextlib.suppress(Exception):
            self.app.save_tui_config(notify=False, root=self)
        self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-overlay-close":
            with contextlib.suppress(Exception):
                self.app.save_tui_config(notify=False, root=self)
            self.dismiss()
        elif event.button.id == "btn-save-config":
            with contextlib.suppress(Exception):
                self.app.save_tui_config(notify=True, root=self)
        elif event.button.id == "btn-reset-config":
            with contextlib.suppress(Exception):
                self.app.reset_tui_config(root=self)


class OrsessionApp(App):
    """The main interactive TUI manager application."""

    CSS_PATH = "css/style.css"

    BINDINGS = [
        # Select (space) is NOT priority: it must yield to a focused Input/typing.
        Binding("space", "toggle_select", "Select session", show=False),
        # The footer command keys are priority=True so a focused Input/DataTable (which has its
        # own ctrl+d/ctrl+u/etc. bindings) cannot swallow them; these are app-global commands.
        Binding("ctrl+q", "quit", "Quit", show=False, priority=True),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar", show=False, priority=True),
        Binding("ctrl+u", "refresh_data", "Update", show=False, priority=True),
        Binding("ctrl+d", "show_doctor", "Doctor", show=False, priority=True),
        Binding("ctrl+r", "show_running", "Running", show=False, priority=True),
        Binding("ctrl+g", "show_config", "Config", show=False, priority=True),
        # No ctrl+m for Main: ctrl+m == Enter (CR) in many terminals. Overlays close with Esc
        # (or the footer/overlay "Esc Main" button); the main screen has no overlay to close.
    ]

    # Custom messages
    class RefreshSidebar(Message):
        """Instructs the sidebar widget to reload projects and sessions."""
        pass

    def __init__(self) -> None:
        super().__init__()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ocman-tui-"))
        self.selected_session_ids: set[str] = set()  # multi-select batch set
        self.selected_session_id: Optional[str] = None
        self.selected_session_title: str = ""
        self.selected_session_dir: str = ""
        self.selected_project_id: Optional[str] = None
        self.selected_project_name: Optional[str] = None
        self.session_turn_cache: Dict[str, int] = {}
        self.current_export: Optional[Any] = None
        self.current_turns: List[Any] = []
        self.export_lock = threading.Lock()
        self.compaction_running = False
        self.config_loaded = False
        # Set once the app begins tearing down, so background worker threads that
        # outlive the app do not try to marshal callbacks into a stopped event loop.
        self._shutting_down = False
        # B2-07: the active search/filter query (drives tree + transcript-line filtering).
        self._active_query = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar-pane"):
                yield Input(placeholder="Filter tree + transcript (content/title), Enter to apply",
                            id="input-session-search")
                yield SidebarWidget(id="sidebar")
            with Container(id="workspace"):
                with TabbedContent():
                    # Tab 1: Details & Transcript
                    with TabPane("Details", id="tab-details"):
                        with Vertical():
                            # B2-03a: metadata (fills width) with the narrow FORMAT CONTROLS
                            # pane to its RIGHT.
                            with Horizontal(id="details-top"):
                                with Vertical(classes="panel-card", id="metadata-panel"):
                                    yield Label("SESSION METADATA", classes="panel-card-title")
                                    yield Static("Select a session in the sidebar to view details.", id="lbl-metadata-grid")
                                with Vertical(classes="panel-card", id="controls-panel"):
                                    yield Label("FORMAT CONTROLS", classes="panel-card-title")
                                    yield Checkbox("Include Tools", value=False, id="check-include-tools")
                                    yield Checkbox("All Roles", value=False, id="check-all-roles")
                                    yield Checkbox("Full lines", value=False, id="check-full-lines")
                                    # B2-03b: say what these limit.
                                    yield Label("Max interactions shown:", classes="info-label")
                                    yield Input("100", id="input-max-interactions")
                                    yield Label("Max lines (when not Full):", classes="info-label")
                                    yield Input("2500", id="input-max-lines")
                                    yield Button("Refresh View", id="btn-refresh-transcript", variant="primary")

                            # Transcript fills the rest of the tab, full width.
                            with Vertical(classes="panel-card", id="transcript-container"):
                                yield Label("TRANSCRIPT LOG", classes="panel-card-title")
                                yield VerticalScroll(Markdown("", id="transcript-md"), classes="transcript-area")
                    
                    # Tab 2: Actions & Recovery
                    with TabPane("Actions", id="tab-actions"):
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
                                    yield Checkbox("Split into parts (chunk) instead of one file",
                                                   value=False, id="check-chunk")
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
                                    yield Button("Filter (LLM re-scope a doc)", id="btn-filter-doc")
                                    yield Static("Idle", id="lbl-compaction-status")

                            # Danger Zone Card
                            with Vertical(classes="panel-card margin-vertical"):
                                yield Label("DANGER ZONE", classes="panel-card-title")
                                yield Label("Delete selected session/project and all related data from database and disk:", classes="info-label")
                                with Horizontal():
                                    yield Button("Delete Session & Descendants", id="btn-delete-session-rec", variant="error", disabled=True)
                                    yield Button("Delete Project & All Sessions", id="btn-delete-project", variant="error", disabled=True)
                                    yield Button("Move/Update Path", id="btn-move-project", disabled=True)
                                    yield Button("Export Session Bundle", id="btn-export-session", disabled=True)
                                # Multi-select batch actions (press Space on a session in the
                                # sidebar to add/remove it from the selection).
                                yield Static("No sessions selected for batch actions. "
                                             "Press Space on a session in the sidebar to select.",
                                             id="lbl-batch-selection", classes="info-label")
                                with Horizontal():
                                    yield Button("Batch Delete Selected", id="btn-batch-delete",
                                                 variant="error", disabled=True)
                                    yield Button("Batch Export Selected", id="btn-batch-export",
                                                 disabled=True)
                    
                    # Tab 3: Database Admin
                    with TabPane("Database", id="tab-admin"):
                        yield DatabaseAdminWidget()

                    # Storage (Doctor), Running, and Config were formerly tabs here; they now
                    # open as footer-command overlays (^d / ^r / ^g), dismissed with ^m / Esc.

                    # Tab: Spend (per-project LLM spend, read-only)
                    with TabPane("Spend", id="tab-spend"):
                        yield SpendWidget()

                    # Tab 4: Models Library
                    with TabPane("Models", id="tab-models"):
                        yield ModelsWidget()

                    # Tab 5: Activity Log
                    with TabPane("Log", id="tab-activity"):
                        with Vertical(classes="panel-card"):
                            yield Label("AUDIT TRAIL / ACTIVITY LOG", classes="panel-card-title")
                            yield RichLog(id="activity-audit-log", max_lines=1000, classes="log-area")
                            # B2-12: prune old log entries using the SAME "Clean Older Than"
                            # duration approach as Database Operations. Historical cumulative
                            # spend is kept; only old action-log entries are removed.
                            with Horizontal(id="log-prune-row"):
                                yield Label("Clean Older Than:", classes="info-label")
                                yield Input("30d", id="input-log-prune-duration",
                                            placeholder="example: 2h or 3mo")
                                yield Button("[b red]⚠[/]DELETE old log entries",
                                             id="btn-clear-history-log", variant="error")
                            yield Label("h = hours, d = days, w = weeks, mo = months, y = years",
                                        classes="info-label")

                    # Configuration Settings moved to the ^g Config overlay (ConfigOverlay).
        with Horizontal(id="footer-bar"):
            # B2-01: Space (Select) and ^q (Quit) are clickable buttons like the rest.
            # B2-02: no space between the glyph and the label.
            yield Button("[b]␣[/b]Select", id="foot-select", classes="footer-btn")
            yield Button("[b]^q[/b]Quit", id="foot-quit", classes="footer-btn")
            yield Button(self._sidebar_footer_label(), id="foot-sidebar", classes="footer-btn")
            yield Button("[b]^u[/b]↻Update", id="foot-update", classes="footer-btn")
            yield Button("[b]^d[/b]🩺Doctor", id="foot-doctor", classes="footer-btn")
            yield Button("[b]^r[/b]▶Running", id="foot-running", classes="footer-btn")
            yield Button("[b]^g[/b]⚙Config", id="foot-config", classes="footer-btn")
            yield Button("⌂Main", id="foot-main", classes="footer-btn")

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
        # Config fields now live in the ^g Config overlay; ConfigOverlay.on_mount loads them
        # when the overlay opens (config_loaded flips to True then). Not loaded at app mount.
        # Refresh the Database Admin metrics once the full tree is mounted. The widget's own
        # on_mount can fire before its child Statics are queryable (mount ordering), so drive a
        # deterministic refresh here from the app (mirrors action_refresh_data).
        with contextlib.suppress(Exception):
            self.query_one(DatabaseAdminWidget).refresh_metrics()
    def run_session_search(self, query: str) -> None:
        """B2-07: apply the search query as a TREE + TRANSCRIPT filter (Enter only).

        Empty query clears the filter (full tree, full transcript). A query re-filters the
        sidebar tree to matching projects/sessions and re-renders the current transcript with
        only matching lines.
        """
        self._active_query = (query or "").strip()
        with contextlib.suppress(Exception):
            self.query_one("#sidebar", SidebarWidget).load_data(self._active_query or None)
        # Re-render the transcript so its line filter reflects the new query.
        with contextlib.suppress(Exception):
            if self.current_turns:
                self.render_current_transcript()
        if self._active_query:
            self.app.notify(f"Filtering by {self._active_query!r} (clear the box + Enter to reset).",
                            severity="information")

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
        else:
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

        # Always write grand totals at the end of the activity log (after printing all runs)
        c = history.get("cumulative", {})
        projects_deleted = c.get("projects_deleted", 0)
        sessions_deleted = c.get("sessions_deleted", 0)
        subagents_deleted = c.get("subagents_deleted", 0)
        messages_deleted = c.get("messages_deleted", 0)
        cost_deleted = c.get("cost_deleted", 0.0)
        space_saved_deleted = c.get("space_saved_deleted", 0)

        from ocman import human_size_local
        grand_totals_str = (
            "\n"
            "========================================================\n"
            "GRAND TOTALS (ALL-TIME HISTORICAL RECOVERY):\n"
            f"  - Projects Deleted:        {projects_deleted}\n"
            f"  - Sessions Deleted:        {sessions_deleted}\n"
            f"  - Subagent Sessions:       {subagents_deleted}\n"
            f"  - Messages Deleted:        {messages_deleted}\n"
            f"  - Total Cost Reclaimed:    ${cost_deleted:.4f}\n"
            f"  - Total Disk Space Saved:  {human_size_local(space_saved_deleted)}\n"
            "========================================================\n"
        )
        audit_log.write(grand_totals_str)

    def _sidebar_footer_label(self, visible: bool = True) -> str:
        """Footer label for the sidebar toggle: a checked box when the sidebar is visible.

        The letter 'b' (the ^b hotkey target) is bold so the accelerator is discoverable.
        """
        box = "🗹" if visible else "☐"
        return f"[b]^b[/b] {box} Side[b]b[/b]ar"

    def action_toggle_sidebar(self) -> None:
        # Toggle the whole sidebar PANE (search box + tree + search-results), not just the
        # tree: the search Input and #search-results are siblings of #sidebar inside
        # #sidebar-pane, so toggling only #sidebar would leave the search box floating.
        pane = self.query_one("#sidebar-pane", Vertical)
        pane.display = not pane.display
        with contextlib.suppress(Exception):
            self.query_one("#foot-sidebar", Button).label = self._sidebar_footer_label(pane.display)

    def _overlay_active(self) -> bool:
        """True if a footer-command overlay is currently on top of the screen stack."""
        return isinstance(self.screen, _FooterOverlay)

    def action_show_doctor(self) -> None:
        """Open the Doctor (Storage checkup) overlay."""
        if not self._overlay_active():
            self.push_screen(DoctorOverlay())

    def action_show_running(self) -> None:
        """Open the Running-instances overlay."""
        if not self._overlay_active():
            self.push_screen(RunningOverlay())

    def action_show_config(self) -> None:
        """Open the Configuration overlay."""
        if not self._overlay_active():
            self.push_screen(ConfigOverlay())

    def action_show_main(self) -> None:
        """Return to the main workspace by dismissing any open footer overlay.

        Delegate to the overlay's own dismiss so per-overlay teardown runs (e.g. the Config
        overlay saves on dismiss). Falls back to pop_screen if the screen lacks the hook.
        """
        if self._overlay_active():
            screen = self.screen
            dismisser = getattr(screen, "action_dismiss_overlay", None)
            if callable(dismisser):
                dismisser()
            else:
                self.pop_screen()

    def action_refresh_data(self) -> None:
        # Preserve any active search filter across a refresh (B2-07).
        self.query_one("#sidebar", SidebarWidget).load_data(getattr(self, "_active_query", "") or None)
        self.load_audit_trail()
        self.selected_session_ids.clear()
        self._refresh_batch_ui()
        with contextlib.suppress(Exception):
            self.query_one(DatabaseAdminWidget).refresh_metrics()

    def action_toggle_select(self) -> None:
        """Toggle the highlighted sidebar session into/out of the batch selection set."""
        sidebar = self.query_one("#sidebar", SidebarWidget)
        node = getattr(sidebar, "cursor_node", None)
        data = getattr(node, "data", None) if node else None
        if not data or data.get("type") != "session":
            self.notify("Highlight a session in the sidebar, then press Space to select it.",
                        severity="warning")
            return
        sid = data["id"]
        if sid in self.selected_session_ids:
            self.selected_session_ids.discard(sid)
        else:
            self.selected_session_ids.add(sid)
        self._refresh_batch_ui()

    def _refresh_batch_ui(self) -> None:
        """Reflect the batch selection count in the label + enable/disable batch buttons."""
        n = len(self.selected_session_ids)
        with contextlib.suppress(Exception):
            lbl = self.query_one("#lbl-batch-selection", Static)
            if n == 0:
                lbl.update("No sessions selected for batch actions. "
                           "Press Space on a session in the sidebar to select.")
            else:
                lbl.update(f"{n} session(s) selected for batch actions.")
        with contextlib.suppress(Exception):
            self.query_one("#btn-batch-delete", Button).disabled = (n == 0)
            self.query_one("#btn-batch-export", Button).disabled = (n == 0)

    def on_orsession_app_refresh_sidebar(self, event: RefreshSidebar) -> None:
        self.query_one("#sidebar", SidebarWidget).load_data()
        self.load_audit_trail()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if node_data and node_data.get("type") == "session":
            s = node_data["data"]
            self.selected_session_id = node_data["id"]
            self.selected_session_title = s.get("title") or "(untitled)"
            self.selected_session_dir = s.get("directory") or ""
            self.selected_project_id = None
            self.selected_project_name = None
            self.update_metadata_view(s)
            self.start_session_export()
            with contextlib.suppress(Exception):
                self.query_one("#btn-delete-session-rec", Button).disabled = False
                self.query_one("#btn-delete-project", Button).disabled = True
                # Move now supports sessions too (local metadata move).
                self.query_one("#btn-move-project", Button).disabled = False
                self.query_one("#btn-export-session", Button).disabled = False
        elif node_data and node_data.get("type") == "project":
            self.selected_session_id = None
            self.selected_session_title = ""
            self.selected_project_id = node_data["id"]
            self.selected_project_name = node_data.get("id") or "Unnamed Project"
            
            proj_name = self.selected_project_name
            proj_dir = node_data.get("dir", "N/A")
            try:
                from .core import db_list_projects
                projects = db_list_projects()
                for p in projects:
                    if p["id"] == self.selected_project_id:
                        proj_name = p["name"] or "Unnamed Project"
                        proj_dir = p["directory"]
                        break
            except Exception:
                pass
            self.selected_project_name = proj_name

            metadata_str = (
                f"Project:  [bold]{proj_name}[/]\n"
                f"ID:       {self.selected_project_id}\n"
                f"Path:     {proj_dir}"
            )
            self.query_one("#lbl-metadata-grid", Static).update(metadata_str)
            with contextlib.suppress(Exception):
                self.query_one("#lbl-actions-metadata-grid", Static).update(metadata_str)
            
            with contextlib.suppress(Exception):
                self.query_one("#btn-delete-session-rec", Button).disabled = True
                self.query_one("#btn-delete-project", Button).disabled = False
                self.query_one("#btn-move-project", Button).disabled = False
                # Export now supports projects too (a project .ocbox bundle).
                self.query_one("#btn-export-session", Button).disabled = False

    @staticmethod
    def _model_display(raw) -> str:
        """Return just the model id for display.

        The DB `session.model` field is usually a JSON object like
        {"id": "...", "providerID": "..."}; show only the id (not the provider suffix the CLI
        adds). Older rows may store a plain string; show it as-is. Empty -> 'N/A'.
        """
        if not raw:
            return "N/A"
        text = str(raw).strip()
        if text.startswith("{"):
            try:
                import json
                obj = json.loads(text)
                if isinstance(obj, dict):
                    return str(obj.get("id") or obj.get("modelID") or text) or "N/A"
            except Exception:
                pass
        return text

    def on_click(self, event) -> None:
        """B2-11: click-to-copy. Clicking the session-metadata block copies its plain text to
        the clipboard (terminal OSC-52; works in most modern terminals). We store the raw text
        on the widget so the copy is the unformatted value, not the markup."""
        widget = getattr(event, "widget", None)
        wid = getattr(widget, "id", None) if widget is not None else None
        if wid in ("lbl-metadata-grid", "lbl-actions-metadata-grid"):
            text = getattr(self, "_metadata_copy_text", "").strip()
            if text:
                with contextlib.suppress(Exception):
                    self.copy_to_clipboard(text)
                    self.notify("Copied session details to the clipboard.",
                                severity="information")

    def update_metadata_view(self, s: dict) -> None:
        """Update the top metadata card with session info.

        B2-04/FU-2 field layout: Project (project root), Session ID, Model, Created, Updated
        (+ duration), Cost, and finally Directory (session dir) ONLY when it differs from the
        project root. Labels are left-aligned in a fixed column; no leading blank line.
        Click the block to copy it (B2-11).
        """
        from ocman import _fmt_ts, _fmt_duration
        model_disp = self._model_display(s.get("model"))
        created_raw = s.get("created")
        updated_raw = s.get("updated")
        created_str = _fmt_ts(created_raw) if created_raw else "N/A"
        updated_str = _fmt_ts(updated_raw) if updated_raw else "N/A"
        duration = _fmt_duration(created_raw, updated_raw)
        project_dir = (s.get("project_dir") or "").strip()
        session_dir = (s.get("directory") or "").strip()
        # Fall back to session dir for the Project line if the project root is unknown.
        project_display = project_dir or session_dir or "N/A"

        lines = [
            f"Project:    {project_display}",
            f"Session ID: {s.get('id', 'N/A')}",
            f"Model:      {model_disp}",
            f"Created:    {created_str}",
            f"Updated:    {updated_str} ({duration})",
            f"Cost:       ${s.get('cost', 0.0):.4f}",
        ]
        # Directory line ONLY if the session dir differs from the project root (FU-2).
        if session_dir and session_dir != project_dir:
            lines.append(f"Directory:  {session_dir}")
        metadata_str = "\n".join(lines)
        # B2-11: keep the plain text for click-to-copy.
        self._metadata_copy_text = metadata_str
        display_str = metadata_str + "\n[dim](click to copy)[/dim]"
        self.query_one("#lbl-metadata-grid", Static).update(display_str)
        with contextlib.suppress(Exception):
            self.query_one("#lbl-actions-metadata-grid", Static).update(display_str)

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
                    self._safe_call_from_thread(self.render_current_transcript)
                except Exception as e:
                    self._safe_call_from_thread(self.app.notify, f"Export failed: {e}", severity="error")
                    # Marshal the transcript-error render onto the UI thread and guard the
                    # widget lookup: a modal screen (or teardown) may mean #transcript-md is
                    # not currently mounted, and query_one must not run in the worker thread.
                    def _show_error() -> None:
                        with contextlib.suppress(Exception):
                            self.query_one("#transcript-md", Markdown).update(
                                f"**Error loading transcript:** {e}")
                    self._safe_call_from_thread(_show_error)

        threading.Thread(target=export_worker, daemon=True).start()

    def render_current_transcript(self) -> None:
        """Format and render extracted turns in the transcript Markdown widget."""
        if not self.current_turns:
            self.query_one("#transcript-md", Markdown).update("No turns found in this session.")
            return

        # Fetch control filter configurations
        include_tools = self.query_one("#check-include-tools", Checkbox).value
        all_roles = self.query_one("#check-all-roles", Checkbox).value
        full_lines = self.query_one("#check-full-lines", Checkbox).value

        try:
            max_interactions = int(self.query_one("#input-max-interactions", Input).value)
        except ValueError:
            max_interactions = 100
        try:
            max_lines = int(self.query_one("#input-max-lines", Input).value)
        except ValueError:
            max_lines = 2500

        # Filter turns
        turns = self.current_turns
        if not include_tools:
            turns = [t for t in turns if t.role != "tool"]
        if not all_roles:
            turns = filter_conversation_turns(turns)

        # Consolidate sequential roles
        turns = consolidate_turns(turns)

        # Truncate by interactions
        if max_interactions > 0:
            turns = truncate_turns_by_interactions(turns, max_interactions)

        # PB-06: by default show CLI-style TRUNCATED lines (per the "Max Lines" budget); only
        # when "Full lines" is toggled do we render every line, and then warn if the rendered
        # transcript is very large.
        if not full_lines and max_lines > 0:
            turns = truncate_turns_by_lines(turns, max_lines)

        # Estimate compaction cost info based on chosen model
        self.update_estimated_cost(turns)

        # Render Markdown
        transcript_markdown = render_transcript(turns, self.selected_session_title)
        if full_lines:
            line_count = transcript_markdown.count("\n") + 1
            if line_count > 2500:
                self.app.notify(
                    f"Full transcript is {line_count:,} lines (over 2,500). Untick 'Full lines' "
                    "to show truncated lines.",
                    severity="warning",
                )
        # B2-07c: when a search query is active, keep only matching lines (case-insensitive
        # substring), driven by the SAME query as the tree filter.
        active_query = getattr(self, "_active_query", "").strip()
        if active_query:
            ql = active_query.lower()
            kept = [ln for ln in transcript_markdown.splitlines() if ql in ln.lower()]
            if kept:
                transcript_markdown = (f"_Showing {len(kept)} line(s) matching "
                                       f"`{active_query}`._\n\n" + "\n".join(kept))
            else:
                transcript_markdown = f"_No transcript lines match `{active_query}`._"
        self.query_one("#transcript-md", Markdown).update(transcript_markdown)

    def update_estimated_cost(self, turns: list) -> None:
        """Estimate token sizes and compaction API billing."""
        selected_model_spec = self.query_one("#select-compaction-model", Select).value
        if not selected_model_spec or selected_model_spec == Select.BLANK:
            self.query_one("#lbl-est-cost", Label).update("Est Cost: Select a model to estimate")
            return

        # B2-15: distinguish config-load failure from model-not-resolvable so the message names
        # the real cause instead of a misleading generic "Config load error".
        try:
            config = load_opencode_config()
            models = extract_models_from_config(config)
        except Exception as e:
            self.query_one("#lbl-est-cost", Label).update(f"Est Cost: could not load model config ({e})")
            return
        try:
            model_info = resolve_model(models, selected_model_spec)
        except Exception:
            model_info = None
        if model_info is None:
            self.query_one("#lbl-est-cost", Label).update(
                f"Est Cost: model not found for '{selected_model_spec}' "
                "(is it configured with an API key and base URL?)")
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
        # Footer bar (clickable equivalents of the ^-key bindings)
        if event.button.id == "foot-select":
            self.action_toggle_select()
            return
        elif event.button.id == "foot-quit":
            self.action_quit()
            return
        elif event.button.id == "foot-sidebar":
            self.action_toggle_sidebar()
            return
        elif event.button.id == "foot-update":
            self.action_refresh_data()
            return
        elif event.button.id == "foot-doctor":
            self.action_show_doctor()
            return
        elif event.button.id == "foot-running":
            self.action_show_running()
            return
        elif event.button.id == "foot-config":
            self.action_show_config()
            return
        elif event.button.id == "foot-main":
            self.action_show_main()
            return

        # Transcript reload controls
        if event.button.id == "btn-refresh-transcript":
            self.render_current_transcript()
        
        # Recovery file generation
        elif event.button.id in ("btn-write-transcript", "btn-write-restart", "btn-write-prompt"):
            self.generate_recovery_files(event.button.id)
            
        # LLM Compaction Execution
        elif event.button.id == "btn-run-compaction":
            self.run_llm_compaction()
        elif event.button.id == "btn-filter-doc":
            self.app.push_screen(FilterModal())
            
        # Recursive session deletion
        elif event.button.id == "btn-delete-session-rec":
            self.confirm_and_delete_session()
        elif event.button.id == "btn-delete-project":
            self.confirm_and_delete_project()
        elif event.button.id == "btn-move-project":
            self.confirm_and_move_project()
        elif event.button.id == "btn-export-session":
            self.confirm_and_export_session()
        elif event.button.id == "btn-batch-delete":
            self.confirm_and_batch_delete()
        elif event.button.id == "btn-batch-export":
            self.batch_export_selected()

        # B2-12: prune activity-LOG entries older than the given duration (runs[] only; the
        # all-time cumulative spend/metadata is kept). Typed-yes confirm.
        elif event.button.id == "btn-clear-history-log":
            from ocman import parse_duration_to_days, prune_history_runs_older_than
            duration = self.query_one("#input-log-prune-duration", Input).value.strip()
            if not duration:
                self.app.notify("Enter a duration in 'Clean Older Than' (e.g. 2h or 3mo).",
                                severity="error")
                return
            try:
                days = parse_duration_to_days(duration)
            except Exception as e:  # noqa: BLE001
                self.app.notify(f"Invalid duration '{duration}': {e}", severity="error")
                return

            def handle_clear(confirmed: bool) -> None:
                if not confirmed:
                    return
                try:
                    removed = prune_history_runs_older_than(days)
                    self.app.notify(
                        f"Removed {removed} log entr{'y' if removed == 1 else 'ies'} older than "
                        f"{duration}. Historical spend totals were kept.",
                        severity="information")
                except Exception as e:  # noqa: BLE001
                    self.app.notify(f"Failed to prune log: {e}", severity="error")
                    return
                self.action_refresh_data()
            self.app.push_screen(ClearHistoryModal(), handle_clear)

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

        # Establish paths. Use the CLI's canonical naming scheme and the configured output
        # directory so CLI and TUI produce identical, migratable artifact names.
        from ocman import canonical_recovery_name
        now = datetime.now()  # a datetime object (canonical_recovery_name needs the object)

        out_dir = Path(load_ocman_config().get("default_out_dir", "opencode-recovery"))
        out_dir.mkdir(parents=True, exist_ok=True)

        session_info = self.current_export.info if self.current_export else {}
        from dataclasses import dataclass, field
        @dataclass
        class DummySession:
            session_id: str
            title: str
            created: str
            updated: str
            raw: dict = field(default_factory=dict)
        dummy_sess = DummySession(self.selected_session_id, self.selected_session_title, "", "")

        kind = {"btn-write-transcript": "transcript",
                "btn-write-restart": "restart",
                "btn-write-prompt": "prompt"}.get(button_id)
        if kind is None:
            return
        src = f"session_export_{self.selected_session_id[:8]}"

        def _render(kind_: str, part_turns: list) -> str:
            if kind_ == "transcript":
                return render_transcript(part_turns, self.selected_session_title)
            if kind_ == "restart":
                return render_restart_context(part_turns, src, dummy_sess)
            return render_compact_prompt(part_turns, source_name=src, session=dummy_sess)

        chunk = False
        with contextlib.suppress(Exception):
            chunk = self.query_one("#check-chunk", Checkbox).value

        if chunk:
            cfg = load_ocman_config()
            max_i = int(cfg.get("chunk_max_interactions", 100))
            max_l = int(cfg.get("chunk_max_lines", 2500))
            parts = chunk_turns(turns, max_interactions=max_i, max_lines=max_l)
            total = len(parts)
            written = []
            for idx, part in enumerate(parts, start=1):
                path = out_dir / part_recovery_name(self.selected_session_id, now, kind, idx, total)
                write_text(path, _render(kind, part))
                written.append(path)
            self.app.notify(
                f"Wrote {len(written)} {kind} part file(s) (.part-NNof{total:02d}) to {out_dir}",
                severity="information")
        else:
            path = out_dir / canonical_recovery_name(self.selected_session_id, now, kind)
            write_text(path, _render(kind, turns))
            self.app.notify(f"{kind.capitalize()} written to: {path}", severity="information")

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

        # Generate the prompt content. render_compact_prompt requires a real SessionInfo
        # and a source_name; build a proper SessionInfo rather than a duck-typed stub.
        session_obj = SessionInfo(
            session_id=self.selected_session_id,
            title=self.selected_session_title or "",
            created="",
            updated="",
            raw={},
        )
        prompt_content = render_compact_prompt(
            self.current_turns,
            source_name=f"session_export_{self.selected_session_id[:8]}",
            session=session_obj,
        )

        def compaction_worker():
            try:
                # Load configuration and resolve model details
                config = load_opencode_config()
                models = extract_models_from_config(config)
                model_info = resolve_model(models, model_spec)

                self._safe_call_from_thread(status_lbl.update, f"Calling completions API ({model_info.name})...")
                
                # Execute API Call. call_compaction_api(model, prompt, verbosity) returns
                # the response content and usage metadata as a tuple (str, dict).
                compacted_text, _usage_info = call_compaction_api(model_info, prompt_content, verbosity=0)

                # Write compacted result file, using the CLI's canonical naming + configured
                # output dir so CLI and TUI produce identical, migratable names.
                from ocman import (
                    canonical_recovery_name,
                    resolve_recovery_collision,
                    maybe_copy_compacted_to_project,
                    resolve_project_dir,
                )
                ocman_cfg = load_ocman_config()
                out_dir = Path(ocman_cfg.get("default_out_dir", "opencode-recovery"))
                out_dir.mkdir(parents=True, exist_ok=True)
                dest_path = out_dir / canonical_recovery_name(
                    self.selected_session_id, datetime.now(), "compacted"
                )
                # Collision handling shared with the CLI (safety-check then backup/delete).
                # In the TUI, stdin is not a TTY, so this defaults to safe backup; if an
                # instance is running it raises and the worker's except-clause reports it.
                resolve_recovery_collision(dest_path, force=False, verbosity=0)
                write_text(dest_path, compacted_text)

                # Compacted-copy parity with the CLI: drop the compacted file into the
                # project's .agents/prompts/pending/ when enabled (fail-soft).
                try:
                    project_dir = resolve_project_dir(session_obj, None)
                    maybe_copy_compacted_to_project(
                        dest_path, session_obj, project_dir,
                        bool(ocman_cfg.get("copy_restart_to_project_prompts", True)), 0,
                    )
                except Exception:
                    pass  # fail-soft: never break the TUI compaction on the optional copy

                # Log compaction run to history sidecar
                self.log_compaction_to_history(model_spec, dest_path)

                # Update UI
                self._safe_call_from_thread(self.app.notify, f"Compaction completed successfully! Written to {dest_path}", severity="information")
                self._safe_call_from_thread(status_lbl.update, f"Success! Written to {dest_path.name}")
                self._safe_call_from_thread(self.load_audit_trail)
            except Exception as e:
                self._safe_call_from_thread(self.app.notify, f"Compaction failed: {e}", severity="error")
                self._safe_call_from_thread(status_lbl.update, f"Failed: {e}")
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

        def handle_confirmation(result: Optional[dict]) -> None:
            if not result:
                return
            extracts = bool(result.get("extracts", True))
            sid = self.selected_session_id
            self.app.notify("Deleting session in background...", severity="information")
            self.run_worker(
                lambda: self._do_delete_session_worker(sid, extracts),
                thread=True
            )

        self.app.push_screen(
            DeletionSafetyModal(self.selected_session_id, self.selected_session_title),
            handle_confirmation
        )

    def _write_delete_extracts(self, session_ids: list, *, expand_descendants: bool) -> None:
        """Write recovery extracts for session_ids before a delete (best-effort).

        Reads the sessions directly from the DB (never launches OpenCode) and writes
        prompt/restart/transcript files to the configured recovery out-dir. Runs in the
        delete worker thread; any failure is reported but never blocks the delete.
        """
        sqlite3 = _get_sqlite()
        db_path = get_db_path()
        if not sqlite3 or not db_path.exists() or not session_ids:
            return
        conn = None
        try:
            conn = sqlite3.connect(str(db_path))
            ids = list(session_ids)
            if expand_descendants:
                cursor = conn.cursor()
                expanded: list = []
                for sid in ids:
                    cursor.execute(
                        """
                        WITH RECURSIVE session_tree(id) AS (
                            SELECT id FROM session WHERE id = ?
                            UNION
                            SELECT s.id FROM session s JOIN session_tree st ON s.parent_id = st.id
                        )
                        SELECT id FROM session_tree;
                        """,
                        (sid,),
                    )
                    expanded.extend(row[0] for row in cursor.fetchall())
                ids = list(dict.fromkeys(expanded)) or ids
            out_dir = resolve_extract_output_dir(None)
            written = extract_sessions_before_delete(ids, out_dir, conn, 0)
            if written:
                self._safe_call_from_thread(
                    self.app.notify,
                    f"Wrote {len(written)} recovery file(s) to {out_dir}",
                    severity="information",
                )
        except Exception as e:  # noqa: BLE001 - extraction must never block a delete
            self._safe_call_from_thread(
                self.app.notify, f"Recovery extraction failed: {e}", severity="warning"
            )
        finally:
            if conn:
                with contextlib.suppress(Exception):
                    conn.close()

    def _do_delete_session_worker(self, session_id: str, extracts: bool = True) -> None:
        db_path = get_db_path()

        # Initialize summary fields to safe defaults so the post-deletion summary
        # never crashes with UnboundLocalError when session metadata cannot be
        # fetched (DB missing, row absent, or query error).
        session_title = "Untitled"
        time_created_str = "-"
        time_updated_str = "-"

        conn = None
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
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        try:
            # Pre-size of DB
            size_before = get_file_size_local(db_path)

            # Write recovery extracts BEFORE the destructive delete (best-effort;
            # never blocks the delete). Reads the DB directly, does not launch OpenCode.
            if extracts:
                self._write_delete_extracts([session_id], expand_descendants=True)

            db_delete_session_recursive(
                session_id=session_id,
                dry_run=False,
                force=True, # bypass locks because user confirmed in TUI
                verbosity=0,
                confirm=False
            )

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
                    with contextlib.suppress(Exception):
                        self.query_one("#btn-delete-session-rec", Button).disabled = True
                        self.query_one("#btn-export-session", Button).disabled = True

                # Refresh trees & stats
                self.action_refresh_data()

            self._safe_call_from_thread(update_ui)
        except Exception as e:
            self._safe_call_from_thread(self.app.notify, f"Deletion failed: {e}", severity="error")

    def confirm_and_delete_project(self) -> None:
        """Spawn safety check confirmation modal overlay before project deletion."""
        if not self.selected_project_id:
            self.app.notify("Please select a project in the sidebar tree first.", severity="warning")
            return

        def handle_confirmation(result: Optional[dict]) -> None:
            if not result:
                return
            extracts = bool(result.get("extracts", True))
            pid = self.selected_project_id
            pname = self.selected_project_name
            self.app.notify("Deleting project in background...", severity="information")
            self.run_worker(
                lambda: self._do_delete_project_worker(pid, pname, extracts),
                thread=True
            )

        self.app.push_screen(
            ProjectDeletionSafetyModal(self.selected_project_id, self.selected_project_name),
            handle_confirmation
        )

    def confirm_and_move_project(self) -> None:
        """Relocate the selected project (local) OR session (local metadata move)."""
        if self.selected_session_id:
            def handle_session_move(success: bool) -> None:
                if success:
                    self.action_refresh_data()
            self.app.push_screen(
                MoveSessionModal(self.selected_session_id, self.selected_session_title,
                                 self.selected_session_dir),
                handle_session_move,
            )
            return
        if not self.selected_project_id:
            self.app.notify("Please select a project or session in the sidebar first.",
                            severity="warning")
            return

        def handle_move_completion(success: bool) -> None:
            if success:
                # Clear selection context and reload
                self.selected_project_id = None
                self.selected_project_name = None
                self.query_one("#lbl-metadata-grid", Static).update("Select a session in the sidebar to view details.")
                with contextlib.suppress(Exception):
                    self.query_one("#lbl-actions-metadata-grid", Static).update("Select a session in the sidebar to view details.")
                with contextlib.suppress(Exception):
                    self.query_one("#btn-delete-project", Button).disabled = True
                    self.query_one("#btn-move-project", Button).disabled = True
                self.action_refresh_data()

        self.app.push_screen(
            MoveProjectModal(self.selected_project_id, self.selected_project_name),
            handle_move_completion
        )

    def confirm_and_export_session(self) -> None:
        """Spawn ExportSessionModal for the selected session OR project (.ocbox bundle)."""
        def handle_export_completion(success: bool) -> None:
            if success:
                pass

        if self.selected_session_id:
            self.app.push_screen(
                ExportSessionModal(self.selected_session_id, self.selected_session_title,
                                   is_project=False),
                handle_export_completion,
            )
        elif self.selected_project_id:
            self.app.push_screen(
                ExportSessionModal(self.selected_project_id,
                                   self.selected_project_name or self.selected_project_id,
                                   is_project=True),
                handle_export_completion,
            )
        else:
            self.app.notify("Please select a session or project in the sidebar first.",
                            severity="warning")

    def confirm_and_batch_delete(self) -> None:
        """Confirm, then delete all selected sessions in one consolidated batch."""
        ids = sorted(self.selected_session_ids)
        if not ids:
            self.app.notify("No sessions selected. Press Space on sessions in the sidebar.",
                            severity="warning")
            return

        def handle(result: Optional[dict]) -> None:
            if not result:
                return
            extracts = bool(result.get("extracts", True))
            self.app.notify(f"Batch-deleting {len(ids)} session(s) in background...",
                            severity="information")
            self.run_worker(lambda: self._do_batch_delete_worker(ids, extracts), thread=True)

        self.app.push_screen(BatchDeleteModal(len(ids)), handle)

    def _do_batch_delete_worker(self, session_ids: list, extracts: bool) -> None:
        try:
            if extracts:
                # Reuse the Phase 1 helper: expand each id's subtree, extract, best-effort.
                self._write_delete_extracts(session_ids, expand_descendants=True)
            db_delete_sessions_batch(
                session_ids, dry_run=False, force=True, verbosity=0,
            )
            def done() -> None:
                self.app.notify(f"Batch-deleted {len(session_ids)} session(s).",
                                severity="information")
                self.selected_session_ids.clear()
                self._refresh_batch_ui()
                self.action_refresh_data()
            self._safe_call_from_thread(done)
        except Exception as e:  # noqa: BLE001
            self._safe_call_from_thread(self.app.notify,
                                        f"Batch deletion failed: {e}", severity="error")

    def batch_export_selected(self) -> None:
        """Export each selected session to its own .ocbox in the configured out-dir."""
        ids = sorted(self.selected_session_ids)
        if not ids:
            self.app.notify("No sessions selected. Press Space on sessions in the sidebar.",
                            severity="warning")
            return
        self.app.notify(f"Exporting {len(ids)} session(s) in background...",
                        severity="information")
        self.run_worker(lambda: self._do_batch_export_worker(ids), thread=True)

    def _do_batch_export_worker(self, session_ids: list) -> None:
        from .core import load_ocman_config, bundle_session_data
        out_dir = Path(load_ocman_config().get("default_out_dir", "opencode-recovery"))
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._safe_call_from_thread(self.app.notify,
                                        f"Cannot create export dir: {e}", severity="error")
            return
        written = 0
        for sid in session_ids:
            try:
                dest = out_dir / f"{sid}.ocbox"
                bundle_session_data(sid, dest)
                written += 1
            except Exception as e:  # noqa: BLE001 - one failure should not stop the rest
                self._safe_call_from_thread(
                    self.app.notify, f"Export failed for {sid[:8]}: {e}", severity="warning")
        self._safe_call_from_thread(
            self.app.notify, f"Exported {written} of {len(session_ids)} session(s) to {out_dir}",
            severity="information")

    def _do_delete_project_worker(self, project_id: str, project_name: str, extracts: bool = True) -> None:
        db_path = get_db_path()
        
        try:
            # Pre-size of DB
            size_before = get_file_size_local(db_path)

            # extracts is an explicit bool here (the user chose in the modal), so the CLI
            # function writes/skips extracts without prompting. It reads the DB directly
            # and never launches OpenCode.
            db_delete_project_recursive(
                project_id=project_id,
                dry_run=False,
                force=True, # bypass locks because user confirmed in TUI
                verbosity=0,
                confirm=False,
                extracts=extracts,
            )

            # Post-size of DB after VACUUM
            size_after = get_file_size_local(db_path)
            saved_space = max(0, size_before - size_after)

            # Schedule UI updates on main thread
            def update_ui() -> None:
                self.app.notify(f"Deleted project {project_name}", severity="information")
                summary = {
                    "session_id": project_id,
                    "session_title": project_name,
                    "start_date": "N/A (All Sessions)",
                    "end_date": "N/A",
                    "db_rows": "Project row and associated sessions/messages removed successfully (foreign keys off, committed).",
                    "files": "Session diff JSON files unlinked on disk.",
                    "space": f"SQLite File Shrunk: {human_size_local(saved_space)} (post-VACUUM)"
                }
                self.app.push_screen(PostExecutionSummaryModal(summary))

                # Clear selection context and reload
                if self.selected_project_id == project_id:
                    self.selected_project_id = None
                    self.selected_project_name = None
                    self.query_one("#lbl-metadata-grid", Static).update("Select a session in the sidebar to view details.")
                    with contextlib.suppress(Exception):
                        self.query_one("#lbl-actions-metadata-grid", Static).update("Select a session in the sidebar to view details.")
                    with contextlib.suppress(Exception):
                        self.query_one("#btn-delete-project", Button).disabled = True
                        self.query_one("#btn-move-project", Button).disabled = True

                # Refresh trees & stats
                self.action_refresh_data()

            self._safe_call_from_thread(update_ui)
        except Exception as e:
            self._safe_call_from_thread(self.app.notify, f"Deletion failed: {e}", severity="error")

    def _cfg_root(self, root=None):
        """Where the #cfg-* widgets live. They now live in the ConfigOverlay screen, not the
        app's default screen, so App.query_one cannot see them. Query within the overlay when
        it is open; fall back to self otherwise."""
        if root is not None:
            return root
        if isinstance(self.screen, ConfigOverlay):
            return self.screen
        return self

    def load_tui_config(self, root=None) -> None:
        """Load TOML configuration settings into input widgets (within ``root``, default the
        open ConfigOverlay)."""
        q = self._cfg_root(root)
        try:
            config = load_ocman_config()
            q.query_one("#cfg-db-path", Input).value = str(config.get("db_path", ""))
            q.query_one("#cfg-history-path", Input).value = str(config.get("history_path", ""))
            q.query_one("#cfg-out-dir", Input).value = str(config.get("default_out_dir", ""))
            q.query_one("#cfg-backup-dir", Input).value = str(config.get("default_backup_dir", ""))
            q.query_one("#cfg-compaction-model", Input).value = str(config.get("default_compaction_model", ""))
            q.query_one("#cfg-retention-days", Input).value = str(config.get("default_retention_days", ""))
            q.query_one("#cfg-keep-temp", Checkbox).value = bool(config.get("keep_temp", False))
            q.query_one("#cfg-include-tools", Checkbox).value = bool(config.get("include_tools", False))
            q.query_one("#cfg-all-roles", Checkbox).value = bool(config.get("all_roles", False))
            self.config_loaded = True
        except Exception as e:
            self.notify(f"Failed to load configuration: {e}", severity="error")

    def save_tui_config(self, notify: bool = True, root=None) -> None:
        """Save form field values back to the TOML configuration file (querying within
        ``root``, default the open ConfigOverlay)."""
        if not getattr(self, "config_loaded", False):
            return
        q = self._cfg_root(root)
        try:
            db_path = q.query_one("#cfg-db-path", Input).value.strip()
            history_path = q.query_one("#cfg-history-path", Input).value.strip()
            out_dir = q.query_one("#cfg-out-dir", Input).value.strip()
            backup_dir = q.query_one("#cfg-backup-dir", Input).value.strip()
            compaction_model = q.query_one("#cfg-compaction-model", Input).value.strip()

            try:
                retention_days = int(q.query_one("#cfg-retention-days", Input).value.strip())
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
                "keep_temp": q.query_one("#cfg-keep-temp", Checkbox).value,
                "include_tools": q.query_one("#cfg-include-tools", Checkbox).value,
                "all_roles": q.query_one("#cfg-all-roles", Checkbox).value,
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

    def reset_tui_config(self, root=None) -> None:
        """Reset form inputs to defaults and save (reloading fields within ``root``)."""
        try:
            save_ocman_config(DEFAULT_CONFIG)

            # Immediately update active settings
            import ocman
            ocman.OPENCODE_DB_PATH = Path(DEFAULT_CONFIG["db_path"]).expanduser()
            ocman.OPENCODE_HISTORY_PATH = Path(DEFAULT_CONFIG["history_path"]).expanduser()

            self.load_tui_config(root=root)
            self.notify("Configuration reset to defaults.", severity="information")

            self.query_one("#sidebar", SidebarWidget).load_data()
            self.load_audit_trail()
            with contextlib.suppress(Exception):
                admin_widget = self.query_one(DatabaseAdminWidget)
                admin_widget.refresh_metrics()
        except Exception as e:
            self.notify(f"Reset failed: {e}", severity="error")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Auto-save config on Enter in config inputs; run a session search on Enter in the box."""
        if event.input.id == "input-session-search":
            self.run_session_search(event.value)
            return
        if event.input.id and event.input.id.startswith("cfg-") and getattr(self, "config_loaded", False):
            self.save_tui_config(notify=True)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Auto-save configuration settings when user toggles any configuration checkbox."""
        if event.checkbox.id and event.checkbox.id.startswith("cfg-") and getattr(self, "config_loaded", False):
            self.save_tui_config(notify=False)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """No-op: configuration is no longer a tab. The ^g Config overlay saves on change
        and on dismiss (ConfigOverlay), so switching workspace tabs must not touch config."""
        return

    def _safe_call_from_thread(self, callback, *args, **kwargs) -> None:
        """Marshal ``callback`` onto the UI thread, tolerating a stopped app.

        Background worker threads are daemonic and can outlive the app (for
        example, an export or delete worker still running when the user quits or
        starts another operation). Once the app has stopped, ``call_from_thread``
        raises ``RuntimeError("App is not running")``. Such late callbacks are
        pure UI updates with nothing left to update, so they are safely dropped
        rather than allowed to crash the worker thread with an unhandled
        traceback.
        """
        if getattr(self, "_shutting_down", False):
            return
        try:
            self.call_from_thread(callback, *args, **kwargs)
        except RuntimeError:
            # App already stopped between the check above and the call, or the
            # worker outlived the event loop. Nothing to update; drop the callback.
            pass

    def on_unmount(self) -> None:
        self._shutting_down = True
        # Auto-save before quitting
        if getattr(self, "config_loaded", False):
            with contextlib.suppress(Exception):
                self.save_tui_config(notify=False)
        # Delete the temp session export directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
