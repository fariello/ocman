"""Tests for the `ocman filter` command (LLM scope re-summarize)."""

from datetime import datetime
from pathlib import Path

import pytest

import ocman
from ocman import cli_filter, SessionInfo


class _Model:
    provider_id = "p"; model_id = "m"; name = "n"; base_url = "https://x"; api_key = "k"


@pytest.fixture
def mock_llm(monkeypatch):
    """Mock the model resolution + API so filter runs offline. Records the prompt sent."""
    captured = {}

    def fake_api(model, prompt, verbosity):
        captured["prompt"] = prompt
        return "# Filtered\nkept in-scope content"

    monkeypatch.setattr(ocman, "call_compaction_api", fake_api)
    monkeypatch.setattr(ocman, "load_opencode_config", lambda verbosity=0: {})
    monkeypatch.setattr(ocman, "extract_models_from_config", lambda c: [_Model()])
    monkeypatch.setattr(ocman, "resolve_model", lambda models, spec: _Model())
    monkeypatch.setattr(ocman, "estimate_cost", lambda *a, **k: 0.01)
    return captured


def _src(tmp_path, name="opencode-20260101-120000-ses_x.restart.md", text="ocman keep; pubrun drop"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_filter_writes_scoped_output_beside_source(tmp_path, mock_llm):
    src = _src(tmp_path)
    out = cli_filter(src, project=None, scope="ocman only", model_spec="", out_path=None, verbosity=0)
    assert out is not None
    assert out.parent == tmp_path.resolve()
    assert out.name == "20260101-1200-ses_x.ocman-only.compacted.md"
    assert out.read_text(encoding="utf-8").startswith("# Filtered")
    # source untouched
    assert src.read_text(encoding="utf-8") == "ocman keep; pubrun drop"


def test_filter_uses_filter_template_and_system_prompt(tmp_path, mock_llm, monkeypatch):
    # Confirm the dedicated filter user prompt is sent (contains the scope + our marker text).
    src = _src(tmp_path)
    cli_filter(src, project=None, scope="only ocman stuff", model_spec="", out_path=None, verbosity=0)
    assert "only ocman stuff" in mock_llm["prompt"]
    assert "Scoped Restart Document Filter" in mock_llm["prompt"]
    assert "ocman keep; pubrun drop" in mock_llm["prompt"]  # source content embedded


def test_filter_requires_scope_or_project(tmp_path, mock_llm):
    src = _src(tmp_path)
    with pytest.raises(ocman.RecoveryError, match="at least one of --project or --scope"):
        cli_filter(src, project=None, scope=None, model_spec="", out_path=None, verbosity=0)


def test_filter_missing_input(tmp_path, mock_llm):
    with pytest.raises(ocman.RecoveryError, match="Input file not found"):
        cli_filter(tmp_path / "nope.md", project=None, scope="x", model_spec="", out_path=None, verbosity=0)


def test_filter_unparseable_name_uses_unknown_and_mtime(tmp_path, mock_llm):
    src = _src(tmp_path, name="somebackup.md", text="content")
    out = cli_filter(src, project=None, scope="ocman", model_spec="", out_path=None, verbosity=0)
    assert out is not None
    # session id falls back to 'unknown'; timestamp from mtime -> YYYYMMDD-HHMM prefix present
    assert "-unknown.ocman.compacted.md" in out.name
    prefix = out.name.split("-unknown")[0]
    assert len(prefix.split("-")[0]) == 8 and len(prefix.split("-")[1]) == 4


def test_filter_collision_backs_up(tmp_path, mock_llm):
    src = _src(tmp_path)
    out1 = cli_filter(src, project=None, scope="ocman only", model_spec="", out_path=None, verbosity=0)
    out2 = cli_filter(src, project=None, scope="ocman only", model_spec="", out_path=None, verbosity=0)
    assert out1 is not None and out2 is not None
    assert out1 == out2
    bu = out2.parent / (out2.name[: -len(".compacted.md")] + ".compacted.bu.001.md")
    assert bu.exists()


def test_filter_rejects_symlink_output(tmp_path, mock_llm):
    src = _src(tmp_path)
    # Point -oc at a symlink; _safe_destination must refuse to write through it.
    real = tmp_path / "real.compacted.md"
    real.write_text("x", encoding="utf-8")
    link = tmp_path / "link.compacted.md"
    link.symlink_to(real)
    with pytest.raises(ocman.RecoveryError, match="symlink"):
        cli_filter(src, project=None, scope="ocman", model_spec="", out_path=link, verbosity=0)
