"""
Models Library widget with real-time searching and pricing DataTable.
"""

from __future__ import annotations
from typing import List

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, DataTable, Label

from ..core import load_opencode_config, extract_models_from_config

class ModelsWidget(Static):
    """A search-filterable grid view displaying all known models and their pricing."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Label("Search Models:", classes="info-label"),
                Input(placeholder="Type to filter models (e.g. qwen, claude)...", id="input-model-search"),
                classes="search-bar-row"
            ),
            DataTable(id="models-table"),
            classes="panel-card"
        )

    def on_mount(self) -> None:
        table = self.query_one("#models-table", DataTable)
        table.add_column("Model Name", width=30)
        table.add_column("Provider / ID", width=35)
        table.add_column("Compatible API", width=16)
        table.add_column("Input Cost ($/1M)", width=18)
        table.add_column("Output Cost ($/1M)", width=18)
        table.cursor_type = "row"

        self.load_models()

    def load_models(self, filter_text: str = "") -> None:
        """Load and display models from config, applying search filter if provided."""
        table = self.query_one("#models-table", DataTable)
        table.clear()

        try:
            config = load_opencode_config()
            models = extract_models_from_config(config)
        except Exception:
            models = []

        filter_text = filter_text.strip().lower()

        for m in models:
            # Check filter match
            full_spec = f"{m.provider_id}/{m.model_id}"
            match = (
                not filter_text
                or filter_text in m.name.lower()
                or filter_text in m.model_id.lower()
                or filter_text in m.provider_id.lower()
            )
            if not match:
                continue

            comp_str = "Yes (OpenAI)" if m.compatible else "No (Unsupported)"
            cost_in_str = f"${m.cost_input:.2f}" if m.cost_input is not None else "N/A"
            cost_out_str = f"${m.cost_output:.2f}" if m.cost_output is not None else "N/A"

            table.add_row(
                m.name,
                full_spec,
                comp_str,
                cost_in_str,
                cost_out_str
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-model-search":
            self.load_models(event.value)
