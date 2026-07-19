"""
Running widget: read-only list of running OpenCode instances, flagging insecure servers.

Reuses the CLI's `detect_running_instances()`. It FAILS LOUD: if detection is unreliable
(`RunningDetectionError`), the tab shows an explicit "NOT an all-clear" message rather than
an empty table that would read as "nothing running". Observe-only; never mutates.
"""

from __future__ import annotations
import contextlib

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, Checkbox, Label, DataTable

from ..core import detect_running_instances, RunningDetectionError


class RunningWidget(Static):
    """Read-only running-instance list with a loud insecure-server banner."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("RUNNING OPENCODE INSTANCES (observe-only)", classes="panel-card-title"),
            Horizontal(
                Button("Refresh", id="btn-refresh-running", variant="primary"),
                Checkbox("All users", value=False, id="check-running-all-users"),
                classes="search-bar-row",
            ),
            Static("", id="lbl-running-status", classes="info-value"),
            DataTable(id="running-table"),
            Static("", id="lbl-running-banner", classes="info-value"),
            classes="panel-card",
        )

    def on_mount(self) -> None:
        table = self.query_one("#running-table", DataTable)
        table.add_column("PID", width=8)
        table.add_column("User", width=12)
        table.add_column("Uptime", width=10)
        table.add_column("Kind", width=12)
        table.add_column("Listener", width=24)
        table.add_column("Auth?", width=6)
        table.add_column("Project", width=36)
        table.cursor_type = "row"
        self.refresh_running()

    def refresh_running(self) -> None:
        all_users = False
        with contextlib.suppress(Exception):
            all_users = self.query_one("#check-running-all-users", Checkbox).value
        self.run_worker(lambda: self._do_running_worker(all_users), thread=True)

    def _do_running_worker(self, all_users: bool) -> None:
        error = None
        instances = []
        try:
            instances = detect_running_instances(all_users=all_users, probe=False, verbosity=0)
        except RunningDetectionError as e:
            error = str(e)
        except Exception as e:  # noqa: BLE001 - any failure is treated as unreliable, never all-clear
            error = str(e)

        def update_ui() -> None:
            table = self.query_one("#running-table", DataTable)
            table.clear()
            status = self.query_one("#lbl-running-status", Static)
            banner = self.query_one("#lbl-running-banner", Static)
            if error is not None:
                # FAIL LOUD: never imply all-clear.
                status.update(
                    "Could not reliably determine running instances: "
                    f"{error}\nThis is NOT an all-clear. Re-run on Linux with 'ss' available, "
                    "or use 'ocman list running' on the command line.")
                banner.update("")
                return
            if not instances:
                status.update("No running OpenCode instances found.")
                banner.update("")
                return
            status.update(f"{len(instances)} running instance(s).")
            for it in instances:
                listener = ", ".join(it.get("listeners") or []) or "none"
                if it.get("exposed"):
                    listener = f"{listener} (NON-LOOPBACK)"
                auth = {"secured": "YES", "unsecured": "NO", "unknown": "???"}.get(
                    it.get("auth"), "n/a")
                proj = it.get("cwd") or it.get("project") or "?"
                table.add_row(
                    str(it.get("pid", "?")),
                    it.get("user", "?"),
                    it.get("elapsed", "?"),
                    it.get("kind", "?"),
                    listener,
                    auth,
                    proj,
                )
            vulns = [it for it in instances if it.get("vulnerable")]
            exposed = [it for it in instances if it.get("exposed")]
            if vulns or exposed:
                lines = ["SECURITY WARNING: insecure OpenCode server(s) detected"]
                for it in vulns:
                    lines.append(f"  VULNERABLE (no auth): pid {it['pid']} on "
                                 f"{', '.join(it.get('listeners') or [])}")
                for it in exposed:
                    lines.append(f"  NETWORK-EXPOSED bind: pid {it['pid']} on "
                                 f"{', '.join(it.get('listeners') or [])}")
                lines.append("  Remediation: set OPENCODE_SERVER_PASSWORD before launch; "
                             "bind 127.0.0.1; avoid --mdns on shared hosts.")
                banner.update("\n".join(lines))
            else:
                banner.update("")

        self.app._safe_call_from_thread(update_ui)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-running":
            self.refresh_running()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "check-running-all-users":
            self.refresh_running()
