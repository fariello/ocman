"""
Database Administration widget and Orphaned File Inspector dialog.
"""

from __future__ import annotations
import io
import contextlib
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from ocman import load_ocman_config

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Button, Checkbox, Input, Label, RichLog, DataTable
from textual.screen import ModalScreen
from textual.binding import Binding

from ..core import (
    db_run_cleanup,
    get_db_path,
    get_history_path,
    _load_history,
    _get_sqlite,
    human_size_local,
    get_file_size_local,
    db_list_sessions,
)

class TextualLogRedirector(io.TextIOBase):
    """Redirects stdout writes to a textual RichLog widget in real time."""
    def __init__(self, log_widget: RichLog) -> None:
        self.log_widget = log_widget

    def write(self, s: str) -> int:
        if s:
            # Strip ANSI escape sequences if any
            clean_s = s.replace("\x1b[1m", "").replace("\x1b[22m", "")
            clean_s = clean_s.replace("\x1b[32m", "").replace("\x1b[39m", "")
            clean_s = clean_s.replace("\x1b[33m", "").replace("\x1b[31m", "")
            clean_s = clean_s.replace("\x1b[36m", "")
            # Ensure thread safety when writing to widget from background thread
            self.log_widget.app._safe_call_from_thread(self.log_widget.write, clean_s.rstrip("\n"))
        return len(s)

    def flush(self) -> None:
        pass


class OrphanInspectorModal(ModalScreen[None]):
    """Modal dialog to inspect and delete orphaned session JSON files on disk."""

    CSS = """
    #dialog-container {
        width: 80;
        height: 35;
        background: #1e1e2e;
        border: round #cba6f7;
        padding: 1 2;
    }
    #dialog-title {
        color: #cba6f7;
        text-style: bold;
        content-align: center middle;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.orphans: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Container(
            Label("ORPHANED FILE INSPECTOR", id="dialog-title"),
            Label("The following session diff JSON files on disk are orphaned (no corresponding database session):", classes="info-label"),
            DataTable(id="orphan-table"),
            Horizontal(
                Label("Selected: 0 files | Total Size: 0 B", id="selection-summary", classes="info-label"),
                classes="margin-vertical"
            ),
            Horizontal(
                Button("Refresh List", id="btn-refresh-orphans"),
                Button("Cancel", id="btn-cancel-orphans"),
                Button("DELETE SELECTED", id="btn-delete-orphans", variant="error"),
                classes="horizontal-buttons"
            ),
            id="dialog-container"
        )

    def on_mount(self) -> None:
        table = self.query_one("#orphan-table", DataTable)
        table.add_column("Select", width=6)
        table.add_column("Filename", width=25)
        table.add_column("Size", width=12)
        table.add_column("Created Date", width=22)
        table.cursor_type = "row"
        self.scan_orphans()

    def scan_orphans(self) -> None:
        """Find JSON files in session_diff that are not referenced in SQLite."""
        self.orphans = []
        table = self.query_one("#orphan-table", DataTable)
        table.clear()

        storage_dir = (Path.home() / ".local" / "share" / "opencode" / "storage" / "session_diff").resolve()
        if not storage_dir.exists():
            self.query_one("#selection-summary", Label).update("No storage directory found.")
            return

        # Fetch active session IDs from DB
        try:
            active_sessions = db_list_sessions()
            active_ids = {s["id"] for s in active_sessions}
        except Exception:
            active_ids = set()

        try:
            for entry in storage_dir.iterdir():
                if entry.is_file() and entry.suffix == ".json":
                    sid = entry.stem
                    if sid not in active_ids:
                        stat = entry.stat()
                        created_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        self.orphans.append({
                            "path": entry,
                            "filename": entry.name,
                            "size": stat.st_size,
                            "created": created_time,
                            "selected": False
                        })
        except OSError:
            pass

        # Sort by creation time (newest first)
        self.orphans.sort(key=lambda x: x["created"], reverse=True)

        for idx, item in enumerate(self.orphans):
            table.add_row(
                "[ ]",
                item["filename"],
                human_size_local(item["size"]),
                item["created"],
                key=str(idx)
            )

        self.update_summary()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Toggle selection of the selected row."""
        row_key = event.row_key.value
        if row_key is not None:
            idx = int(row_key)
            self.orphans[idx]["selected"] = not self.orphans[idx]["selected"]
            
            # Update cell display
            checkbox = "[x]" if self.orphans[idx]["selected"] else "[ ]"
            table = self.query_one("#orphan-table", DataTable)
            table.update_cell(event.row_key, table.columns[0].key, checkbox)
            
            self.update_summary()

    def update_summary(self) -> None:
        selected_count = sum(1 for item in self.orphans if item["selected"])
        selected_size = sum(item["size"] for item in self.orphans if item["selected"])
        summary_label = self.query_one("#selection-summary", Label)
        summary_label.update(
            f"Selected: {selected_count} file(s) | Total Size: {human_size_local(selected_size)}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-orphans":
            self.scan_orphans()
        elif event.button.id == "btn-cancel-orphans":
            self.dismiss()
        elif event.button.id == "btn-delete-orphans":
            self.delete_selected()

    def delete_selected(self) -> None:
        selected_items = [item for item in self.orphans if item["selected"]]
        if not selected_items:
            self.app.notify("No files selected for deletion.", severity="warning")
            return

        deleted_count = 0
        freed_space = 0
        for item in selected_items:
            try:
                item["path"].unlink()
                deleted_count += 1
                freed_space += item["size"]
            except OSError as e:
                self.app.notify(f"Could not delete {item['filename']}: {e}", severity="error")

        self.app.notify(
            f"Deleted {deleted_count} orphaned files. Freed {human_size_local(freed_space)}.",
            severity="information"
        )
        self.scan_orphans()


class DatabaseAdminWidget(Static):
    """The main Database Administration layout."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="grid-container"):
            # Left side: Metrics Card
            with Vertical(classes="panel-card"):
                yield Label("SYSTEM METRICS", classes="panel-card-title")
                yield VerticalScroll(
                    Horizontal(Label("Database Path:", classes="info-label"), Static("", id="lbl-db-path", classes="info-value")),
                    Horizontal(Label("DB File Size:", classes="info-label"), Static("", id="lbl-db-size", classes="info-value")),
                    Horizontal(Label("SQLite Version:", classes="info-label"), Static("", id="lbl-sqlite-ver", classes="info-value")),
                    Horizontal(Label("Total Projects:", classes="info-label"), Static("", id="lbl-total-projects", classes="info-value")),
                    Horizontal(Label("Total Sessions:", classes="info-label"), Static("", id="lbl-total-sessions", classes="info-value")),
                    Horizontal(Label("Historical Cost Saved:", classes="info-label"), Static("", id="lbl-hist-cost", classes="info-value")),
                    Horizontal(Label("Historical Msg Deleted:", classes="info-label"), Static("", id="lbl-hist-msg", classes="info-value")),
                    id="metrics-fields"
                )
                yield Button("Refresh Metrics", id="btn-refresh-metrics", variant="primary")

            # Right side: Operations Card
            with Vertical(classes="panel-card"):
                yield Label("DATABASE OPERATIONS", classes="panel-card-title")
                yield VerticalScroll(
                    Horizontal(
                        Label("Retention Days:", classes="info-label"),
                        Input("5", id="input-retention-days", placeholder="e.g. 5"),
                    ),
                    Horizontal(
                        Label("Or duration:", classes="info-label"),
                        Input("", id="input-retention-duration",
                              placeholder="e.g. 2h, 6w, 6mo, 1y (overrides days)"),
                    ),
                    Horizontal(
                        Label("Project scope (optional):", classes="info-label"),
                        Input("", id="input-prune-project",
                              placeholder="project name/number/id/path; blank = all"),
                    ),
                    Horizontal(
                        Checkbox("Dry Run (Preview changes)", value=True, id="check-dry-run"),
                    ),
                    Horizontal(
                        Checkbox("Force (Bypass active process checks)", value=False, id="check-force"),
                    ),
                    Horizontal(
                        Checkbox("Sweep Orphans", value=True, id="check-sweep-orphans"),
                    ),
                    Horizontal(
                        Checkbox("Write recovery extracts first", value=True, id="check-prune-extracts"),
                    ),
                    id="ops-fields"
                )
                with Horizontal():
                    yield Button("Run Prune / Clean", id="btn-run-prune", variant="error")
                    yield Button("Inspect Orphans", id="btn-inspect-orphans", variant="primary")
                    yield Button("Import Session", id="btn-import-session", variant="success")

            # Backup & Restore Card
            with Vertical(classes="panel-card"):
                yield Label("BACKUP & RESTORE", classes="panel-card-title")
                yield VerticalScroll(
                    Label("Manage entire system-wide state snapshots:", classes="info-label"),
                    Horizontal(
                        Label("Backup Target:", classes="info-label"),
                        Static("", id="lbl-backup-target-dir", classes="info-value"),
                    ),
                    Horizontal(
                        Label("Prune backups older than (days):", classes="info-label"),
                        Input("30", id="input-backup-clean-days", placeholder="e.g. 30"),
                    ),
                    id="backup-fields"
                )
                with Horizontal():
                    yield Button("Create Backup", id="btn-create-backup", variant="success")
                    yield Button("Restore Backup", id="btn-restore-backup", variant="primary")
                    yield Button("Prune Old Backups", id="btn-clean-backups", variant="error")

        # Bottom section: Logs Output Console
        yield Label("LIVE OPERATIONS LOG OUTPUT:", classes="info-label")
        yield RichLog(id="live-log-output", max_lines=1000, classes="log-area")

    def on_mount(self) -> None:
        self.refresh_metrics()

    def refresh_metrics(self) -> None:
        """Update system statistics dynamically."""
        # A background worker (e.g. prune / backup-clean) calls this on completion; if the
        # app is tearing down or this widget is no longer mounted, its child widgets are
        # gone and query_one would raise NoMatches. Skip safely in that case.
        if not self.is_mounted:
            return
        db_path = get_db_path()
        history = _load_history()
        cum = history.get("cumulative", {})

        # Database Path
        self.query_one("#lbl-db-path", Static).update(str(db_path))

        # Size on disk
        if db_path.exists():
            db_size = get_file_size_local(db_path)
            self.query_one("#lbl-db-size", Static).update(human_size_local(db_size))
        else:
            self.query_one("#lbl-db-size", Static).update("Not found")

        # SQLite Version and queries
        sqlite3 = _get_sqlite()
        if sqlite3 and db_path.exists():
            self.query_one("#lbl-sqlite-ver", Static).update(sqlite3.sqlite_version)
            conn = None
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM project")
                proj_cnt = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM session")
                sess_cnt = cursor.fetchone()[0]
            except Exception:
                proj_cnt, sess_cnt = 0, 0
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
            self.query_one("#lbl-total-projects", Static).update(str(proj_cnt))
            self.query_one("#lbl-total-sessions", Static).update(str(sess_cnt))
        else:
            self.query_one("#lbl-sqlite-ver", Static).update("N/A")
            self.query_one("#lbl-total-projects", Static).update("N/A")
            self.query_one("#lbl-total-sessions", Static).update("N/A")

        # Historical saved metrics from sidecar
        cost_saved = cum.get("cost_deleted", 0.0)
        msg_deleted = cum.get("messages_deleted", 0)
        self.query_one("#lbl-hist-cost", Static).update(f"${cost_saved:.4f}")
        self.query_one("#lbl-hist-msg", Static).update(f"{msg_deleted:,}")

        # Update backup target directory path
        with contextlib.suppress(Exception):
            cfg = load_ocman_config()
            self.query_one("#lbl-backup-target-dir", Static).update(str(cfg.get("default_backup_dir", "")))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-metrics":
            self.refresh_metrics()
        elif event.button.id == "btn-inspect-orphans":
            self.app.push_screen(OrphanInspectorModal())
        elif event.button.id == "btn-run-prune":
            self.run_prune_operation()
        elif event.button.id == "btn-create-backup":
            self.run_backup_operation()
        elif event.button.id == "btn-clean-backups":
            self.run_clean_backups_operation()
        elif event.button.id == "btn-restore-backup":
            from ..app import RestoreBackupModal
            self.app.push_screen(RestoreBackupModal(), self.handle_restore_result)
        elif event.button.id == "btn-import-session":
            from ..app import ImportSessionModal
            self.app.push_screen(ImportSessionModal(), self.handle_import_result)

    def handle_import_result(self, imported: bool) -> None:
        if imported:
            self.refresh_metrics()
            self.app.post_message(self.app.RefreshSidebar())

    def run_prune_operation(self) -> None:
        """Run prune clean operation and redirect prints to textual log."""
        from .. import core
        log_widget = self.query_one("#live-log-output", RichLog)
        log_widget.clear()

        # Resolve the retention window: a duration string (2h/6w/6mo/1y/"30 days")
        # overrides the integer-days field when present.
        duration = self.query_one("#input-retention-duration", Input).value.strip()
        if duration:
            try:
                days = core.parse_duration_to_days(duration)
            except Exception as e:  # noqa: BLE001
                self.app.notify(f"Invalid duration '{duration}': {e}", severity="error")
                return
        else:
            try:
                days = int(self.query_one("#input-retention-days", Input).value)
            except ValueError:
                self.app.notify("Retention Days must be an integer (or set a duration).",
                                severity="error")
                return

        dry_run = self.query_one("#check-dry-run", Checkbox).value
        force = self.query_one("#check-force", Checkbox).value
        sweep_orphans = self.query_one("#check-sweep-orphans", Checkbox).value
        extracts = self.query_one("#check-prune-extracts", Checkbox).value

        # Optional project scope.
        project_spec = self.query_one("#input-prune-project", Input).value.strip()
        project_id = None
        project_dir = None
        if project_spec:
            found = core.db_find_project(project_spec)
            if not found:
                self.app.notify(f"Project '{project_spec}' not found.", severity="error")
                return
            project_id, project_dir = found

        self.app.notify("Running prune operation in background...", severity="information")
        self.run_worker(
            lambda: self._do_prune_worker(days, dry_run, force, sweep_orphans,
                                          project_id, project_dir, extracts, log_widget),
            thread=True
        )

    def _do_prune_worker(self, days, dry_run: bool, force: bool, sweep_orphans: bool,
                         project_id, project_dir, extracts: bool, log_widget: RichLog) -> None:
        import builtins
        original_input = builtins.input
        builtins.input = lambda *args, **kwargs: "yes"

        try:
            with contextlib.redirect_stdout(TextualLogRedirector(log_widget)):
                db_run_cleanup(
                    days=days,
                    project_id=project_id,
                    project_dir=project_dir,
                    dry_run=dry_run,
                    force=force,
                    clean_orphans=sweep_orphans,
                    verbosity=0,
                    assume_yes=True,
                    extracts=extracts,
                )
            self.app._safe_call_from_thread(self.app.notify, "Prune operation finished.", severity="information")
        except Exception as e:
            log_widget.app._safe_call_from_thread(log_widget.write, f"ERROR: {e}")
            self.app._safe_call_from_thread(self.app.notify, f"Cleanup failed: {e}", severity="error")
        finally:
            builtins.input = original_input

        # Refresh UI back on main thread
        def update_ui() -> None:
            self.refresh_metrics()
            self.app.post_message(self.app.RefreshSidebar())

        self.app._safe_call_from_thread(update_ui)

    def run_backup_operation(self) -> None:
        """Run system backup in a background worker thread."""
        log_widget = self.query_one("#live-log-output", RichLog)
        log_widget.clear()

        self.app.notify("Creating system backup in background...", severity="information")

        from ocman import cli_backup

        def do_backup():
            try:
                with contextlib.redirect_stdout(TextualLogRedirector(log_widget)):
                    dest = cli_backup()
                self.app._safe_call_from_thread(self.app.notify, f"Backup created: {dest.name}", severity="information")
            except Exception as e:
                log_widget.app._safe_call_from_thread(log_widget.write, f"ERROR: {e}")
                self.app._safe_call_from_thread(self.app.notify, f"Backup failed: {e}", severity="error")
            finally:
                self.app._safe_call_from_thread(self.refresh_metrics)

        self.run_worker(do_backup, thread=True)

    def run_clean_backups_operation(self) -> None:
        """Prune backup archives older than the given age (days), reusing cli_clean_backups."""
        from ..core import cli_clean_backups
        log_widget = self.query_one("#live-log-output", RichLog)
        log_widget.clear()
        try:
            days = float(self.query_one("#input-backup-clean-days", Input).value.strip())
        except ValueError:
            self.app.notify("Backup age (days) must be a number.", severity="error")
            return

        self.app.notify("Pruning old backups in background...", severity="information")

        def do_clean():
            import builtins
            original_input = builtins.input
            builtins.input = lambda *a, **k: "yes"
            try:
                with contextlib.redirect_stdout(TextualLogRedirector(log_widget)):
                    cli_clean_backups(days=days, dry_run=False, verbosity=0, assume_yes=True)
                self.app._safe_call_from_thread(
                    self.app.notify, "Backup prune finished.", severity="information")
            except Exception as e:  # noqa: BLE001
                log_widget.app._safe_call_from_thread(log_widget.write, f"ERROR: {e}")
                self.app._safe_call_from_thread(
                    self.app.notify, f"Backup prune failed: {e}", severity="error")
            finally:
                builtins.input = original_input
                self.app._safe_call_from_thread(self.refresh_metrics)

        self.run_worker(do_clean, thread=True)

    def handle_restore_result(self, path: Optional[str]) -> None:
        """Handle the path input from the RestoreBackupModal dialog."""
        if not path:
            return

        log_widget = self.query_one("#live-log-output", RichLog)
        log_widget.clear()

        self.app.notify("Restoring system state in background...", severity="information")

        from ocman import cli_restore

        def do_restore():
            try:
                with contextlib.redirect_stdout(TextualLogRedirector(log_widget)):
                    cli_restore(path)
                self.app._safe_call_from_thread(self.app.notify, "System restoration completed.", severity="information")
            except Exception as e:
                log_widget.app._safe_call_from_thread(log_widget.write, f"ERROR: {e}")
                self.app._safe_call_from_thread(self.app.notify, f"Restoration failed: {e}", severity="error")
            finally:
                def update_ui():
                    self.refresh_metrics()
                    self.app.post_message(self.app.RefreshSidebar())
                    with contextlib.suppress(Exception):
                        self.app.load_tui_config()
                self.app._safe_call_from_thread(update_ui)

        self.run_worker(do_restore, thread=True)
