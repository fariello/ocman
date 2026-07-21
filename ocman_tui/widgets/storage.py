"""
Storage widget: a read-only doctor (storage checkup) view plus guarded reclaim actions.

The doctor view and the reclaim actions reuse the CLI's own logic verbatim
(`run_doctor_checks`, `reclaim_*`); this widget only presents and confirms. The reclaim
snapshot-force mode is intentionally NOT exposed here (it can break OpenCode undo/revert);
a note directs the user to the CLI for that.
"""

from __future__ import annotations
import contextlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, Button, Checkbox, Input, Label, RichLog, DataTable
from textual.screen import ModalScreen
from textual.css.query import NoMatches

from ..core import (
    discover_storage_locations,
    run_doctor_checks,
    db_family_open_by_live_pid,
    reclaim_checkpoint_vacuum,
    reclaim_temp,
    reclaim_parts,
    reclaim_backups_dir,
    load_ocman_config,
    human_size_local,
    get_db_path,
    RecoveryError,
)
from .database import TextualLogRedirector


# Doctor status label (uppercased, no ANSI; Textual styles cells itself).
def _status_label(status: str) -> str:
    return str(status or "unknown").upper()


class ReclaimConfirmModal(ModalScreen[bool]):
    """Preview + confirm for a single reclaim action. Dismisses True on confirm."""
    def __init__(self, title: str, preview: str) -> None:
        super().__init__()
        self._title = title
        self._preview = preview

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self._title, id="dialog-title"),
            VerticalScroll(Static(self._preview, classes="info-value")),
            Label("Proceed?", classes="info-label"),
            Horizontal(
                Button("Cancel", id="btn-cancel-reclaim"),
                Button("PROCEED", id="btn-confirm-reclaim", variant="error"),
                classes="horizontal-buttons",
            ),
            id="dialog-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-reclaim":
            self.dismiss(False)
        elif event.button.id == "btn-confirm-reclaim":
            self.dismiss(True)


class StorageWidget(Static):
    """Read-only doctor checkup + guarded reclaim actions."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            # Doctor checkup
            Vertical(
                Label("STORAGE CHECKUP (read-only)", classes="panel-card-title"),
                Horizontal(
                    Button("Run / Refresh Checkup", id="btn-run-doctor", variant="primary"),
                    Checkbox("Deep scan (slower)", value=False, id="check-doctor-deep"),
                    classes="search-bar-row",
                ),
                DataTable(id="doctor-table"),
                Static("", id="lbl-doctor-summary", classes="info-value"),
                classes="panel-card",
            ),
            # Reclaim
            Vertical(
                Label("RECLAIM (guarded)", classes="panel-card-title"),
                Checkbox("Proceed even if OpenCode is running (--while-running)",
                         value=False, id="check-reclaim-while-running"),
                Horizontal(
                    Button("Compact database (checkpoint + VACUUM)", id="btn-reclaim-vacuum", variant="warning"),
                    Button("Reclaim temp files", id="btn-reclaim-temp"),
                    Button("Reclaim compacted tool output (parts)", id="btn-reclaim-parts"),
                    classes="horizontal-buttons",
                ),
                Horizontal(
                    Input(placeholder="Backups dir to prune (path)", id="input-reclaim-backups-dir"),
                    Button("Prune backups dir", id="btn-reclaim-backups"),
                    classes="search-bar-row",
                ),
                Static(
                    "Note: the dangerous snapshot-force reclaim is intentionally CLI-only. "
                    "For it, run  ocman reclaim --force-snapshots <path>  and/or  ocman doctor  "
                    "on the command line.",
                    classes="info-value",
                ),
                RichLog(id="reclaim-log", max_lines=1000, classes="log-area"),
                classes="panel-card",
            ),
        )

    def on_mount(self) -> None:
        table = self.query_one("#doctor-table", DataTable)
        table.add_column("Check", width=28)
        table.add_column("Status", width=10)
        table.add_column("Size", width=12)
        table.add_column("Count", width=10)
        table.add_column("Recommended fix", width=40)
        table.cursor_type = "row"
        self.run_checkup()

    # --- doctor ---------------------------------------------------------------
    def run_checkup(self) -> None:
        deep = False
        with contextlib.suppress(Exception):
            deep = self.query_one("#check-doctor-deep", Checkbox).value
        self.app.notify("Running storage checkup...", severity="information")
        self.run_worker(lambda: self._do_checkup_worker(deep), thread=True)

    def _do_checkup_worker(self, deep: bool) -> None:
        try:
            loc = discover_storage_locations(get_db_path())
            running = False
            with contextlib.suppress(Exception):
                running = db_family_open_by_live_pid(loc.get("db_path"))
            records = run_doctor_checks(loc, running=running, deep=deep)
        except Exception as e:  # noqa: BLE001
            self.app._safe_call_from_thread(
                self.app.notify, f"Checkup failed: {e}", severity="error")
            return

        def update_ui() -> None:
            # The checkup runs in a background thread; by the time this UI callback is
            # marshalled back, the widget (and #doctor-table) may not be mounted yet or may
            # already be torn down (tab switch / app exit), so query_one would raise
            # NoMatches -> WorkerFailed. Skip safely in that case (matches DatabaseAdminWidget
            # .refresh_metrics). See .agents/plans/executed/20260721-1424-01-testing-followup.
            if not self.is_mounted:
                return
            try:
                table = self.query_one("#doctor-table", DataTable)
            except NoMatches:
                return
            table.clear()
            for rec in records:
                size = human_size_local(rec["size_bytes"]) if rec.get("size_bytes") else "-"
                count = f"{rec['count']:,}" if rec.get("count") else "-"
                table.add_row(
                    rec.get("title", ""),
                    _status_label(rec.get("status")),
                    size,
                    count,
                    rec.get("fix_cmd") or "-",
                )
            now_b = sum(r["size_bytes"] for r in records if r.get("bucket") == "now")
            optin_b = sum(r["size_bytes"] for r in records if r.get("bucket") == "optin")
            report_b = sum(r["size_bytes"] for r in records if r.get("bucket") == "report")
            self.query_one("#lbl-doctor-summary", Static).update(
                f"Reclaimable now: {human_size_local(now_b)}   |   "
                f"Opt-in (temp/parts): {human_size_local(optin_b)}   |   "
                f"Reported only: {human_size_local(report_b)}"
            )

        self.app._safe_call_from_thread(update_ui)

    # --- reclaim --------------------------------------------------------------
    def _while_running(self) -> bool:
        with contextlib.suppress(Exception):
            return bool(self.query_one("#check-reclaim-while-running", Checkbox).value)
        return False

    def _temp_min_age_hours(self) -> float:
        try:
            return float(load_ocman_config().get("reclaim_tmp_min_age_hours", 24))
        except Exception:
            return 24.0

    def _confirm_then_run(self, title: str, preview: str, worker) -> None:
        def handle(confirmed: bool) -> None:
            if confirmed:
                self.run_worker(worker, thread=True)
        self.app.push_screen(ReclaimConfirmModal(title, preview), handle)

    def _run_reclaim(self, fn) -> None:
        """Run a reclaim callable with stdout captured to the log; surface refusals.

        fn() calls the underlying reclaim_* function. A RecoveryError (e.g. the
        refuse-while-running guard) is reported as a NON-success, and no false
        'done' notification is shown.
        """
        log_widget = self.query_one("#reclaim-log", RichLog)
        import builtins
        original_input = builtins.input
        builtins.input = lambda *a, **k: "yes"
        ok = False
        refusal = None
        try:
            with contextlib.redirect_stdout(TextualLogRedirector(log_widget)):
                fn()
            ok = True
        except RecoveryError as e:
            refusal = str(e)
            log_widget.app._safe_call_from_thread(log_widget.write, f"REFUSED: {e}")
        except Exception as e:  # noqa: BLE001
            refusal = str(e)
            log_widget.app._safe_call_from_thread(log_widget.write, f"ERROR: {e}")
        finally:
            builtins.input = original_input

        if ok:
            self.app._safe_call_from_thread(
                self.app.notify, "Reclaim finished.", severity="information")
        else:
            self.app._safe_call_from_thread(
                self.app.notify,
                f"Reclaim did not run: {refusal}", severity="warning")
        # Refresh the checkup either way.
        self.app._safe_call_from_thread(self.run_checkup)

    def _loc(self) -> dict:
        return discover_storage_locations(get_db_path())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-run-doctor":
            self.run_checkup()
        elif bid == "btn-reclaim-vacuum":
            wr = self._while_running()
            self._confirm_then_run(
                "CHECKPOINT + VACUUM",
                "Offline WAL checkpoint(TRUNCATE) + VACUUM. A backup is taken first. "
                "Refused if OpenCode holds the DB open unless 'while running' is checked.",
                lambda: self._run_reclaim(lambda: reclaim_checkpoint_vacuum(
                    self._loc(), dry_run=False, while_running=wr, assume_yes=True, verbosity=0)),
            )
        elif bid == "btn-reclaim-temp":
            self._confirm_then_run(
                "RECLAIM TEMP FILES",
                "Delete leaked opencode-wal-*.db and /tmp/*.so owned by you and older than "
                "the configured minimum age. Never touches files held by a live process.",
                lambda: self._run_reclaim(lambda: reclaim_temp(
                    self._loc(), dry_run=False, force=self._while_running(),
                    min_age_hours=self._temp_min_age_hours(), assume_yes=True, verbosity=0)),
            )
        elif bid == "btn-reclaim-parts":
            wr = self._while_running()
            self._confirm_then_run(
                "RECLAIM COMPACTED PARTS",
                "Empty the output of already-compacted tool parts (verify-or-skip). "
                "Never touches the event log. Refused if OpenCode holds the DB open unless "
                "'while running' is checked.",
                lambda: self._run_reclaim(lambda: reclaim_parts(
                    self._loc(), dry_run=False, while_running=wr, assume_yes=True, verbosity=0)),
            )
        elif bid == "btn-reclaim-backups":
            raw = self.query_one("#input-reclaim-backups-dir", Input).value.strip()
            if not raw:
                self.app.notify("Enter a backups directory to prune.", severity="warning")
                return
            self._confirm_then_run(
                "PRUNE BACKUPS DIR",
                f"Delete backup files older than the retention window within:\n  {raw}",
                lambda: self._run_reclaim(lambda: reclaim_backups_dir(
                    raw, self._loc(), dry_run=False, assume_yes=True,
                    min_age_hours=self._temp_min_age_hours(), verbosity=0)),
            )
