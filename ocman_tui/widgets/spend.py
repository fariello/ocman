"""
Spend widget: a read-only per-project LLM spend report.

Reuses the CLI's `gather_spend()` so the TUI and `ocman spend` show identical numbers.
Read-only; never mutates.
"""

from __future__ import annotations
import contextlib

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, Checkbox, Label, DataTable

from ..core import gather_spend, fmt_cost, fmt_int


class SpendWidget(Static):
    """Read-only per-project LLM spend, with an optional historical (deleted) toggle."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("LLM SPEND BY PROJECT (read-only)", classes="panel-card-title"),
            Horizontal(
                Button("Refresh", id="btn-refresh-spend", variant="primary"),
                Checkbox("Include historical (deleted) spend", value=False,
                         id="check-spend-historical"),
                classes="search-bar-row",
            ),
            DataTable(id="spend-table"),
            Static("", id="lbl-spend-totals", classes="info-value"),
            classes="panel-card",
        )

    def on_mount(self) -> None:
        table = self.query_one("#spend-table", DataTable)
        table.add_column("Project", width=44)
        table.add_column("Cost", width=12)
        table.add_column("Tokens In", width=14)
        table.add_column("Tokens Out", width=14)
        table.add_column("Cache", width=14)
        table.cursor_type = "row"
        self.refresh_spend()

    def refresh_spend(self) -> None:
        historical = False
        with contextlib.suppress(Exception):
            historical = self.query_one("#check-spend-historical", Checkbox).value
        self.run_worker(lambda: self._do_spend_worker(historical), thread=True)

    def _do_spend_worker(self, historical: bool) -> None:
        try:
            data = gather_spend(historical=historical)
        except Exception as e:  # noqa: BLE001
            self.app._safe_call_from_thread(
                self.app.notify, f"Spend query failed: {e}", severity="error")
            return

        def update_ui() -> None:
            table = self.query_one("#spend-table", DataTable)
            table.clear()
            rows = data["projects"]
            if not rows:
                self.query_one("#lbl-spend-totals", Static).update(
                    "No projects with recorded spend.")
                return
            for r in rows:
                table.add_row(
                    r["directory"],
                    fmt_cost(r["cost"]),
                    fmt_int(r["tokens_input"]),
                    fmt_int(r["tokens_output"]),
                    fmt_int(r["tokens_cache_read"]),
                )
            lt = data["live_total"]
            ltok = data["live_tokens"]
            lines = [
                f"Live total (active sessions): {fmt_cost(lt)}  "
                f"[{fmt_int(ltok['input'])} in / {fmt_int(ltok['output'])} out / "
                f"{fmt_int(ltok['cache_read'])} cache]"
            ]
            if historical and data.get("historical_total") is not None:
                ht = data["historical_total"]
                htok = data["historical_tokens"] or {"input": 0, "output": 0, "cache_read": 0}
                gt = data["grand_total"]
                gtok = data["grand_tokens"] or {"input": 0, "output": 0, "cache_read": 0}
                lines.append(
                    f"Historically saved (deleted): {fmt_cost(ht)}  "
                    f"[{fmt_int(htok['input'])} in / {fmt_int(htok['output'])} out / "
                    f"{fmt_int(htok['cache_read'])} cache]  (global; not per project)")
                lines.append(
                    f"Grand total (live + historical): {fmt_cost(gt)}  "
                    f"[{fmt_int(gtok['input'])} in / {fmt_int(gtok['output'])} out / "
                    f"{fmt_int(gtok['cache_read'])} cache]")
            self.query_one("#lbl-spend-totals", Static).update("\n".join(lines))

        self.app._safe_call_from_thread(update_ui)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-refresh-spend":
            self.refresh_spend()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "check-spend-historical":
            self.refresh_spend()
