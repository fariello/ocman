"""Tests for copying the compacted file into a project's .agents/prompts/pending/.

The compacted file (`*.compacted.md`, produced by --compact) is the document a fresh
opencode agent reads, so it is the one copied into the project. A plain recovery (no
--compact) produces no compacted file and copies nothing.
"""

from pathlib import Path
import pytest

import ocman
from ocman import (
    SessionInfo,
    resolve_project_dir,
    project_prompt_copy_name,
    _backup_compacted_bu,
    maybe_copy_compacted_to_project,
)


def _session(sid="ses_abcd1234", updated="unknown"):
    return SessionInfo(session_id=sid, title="T", created="", updated=updated, raw={})


# resolve_project_dir -------------------------------------------------------------------

def test_resolve_project_dir_prefers_session_dir(tmp_path):
    sd = tmp_path / "explicit"; sd.mkdir()
    assert resolve_project_dir(_session(), sd) == sd.resolve()


def test_resolve_project_dir_falls_back_to_session_directory(tmp_path):
    d = tmp_path / "sessdir"; d.mkdir()
    s = SessionInfo("s1", "T", "", "", raw={"directory": str(d)})
    assert resolve_project_dir(s, None) == d.resolve()


def test_resolve_project_dir_placeholder_raw_no_keyerror(tmp_path, monkeypatch):
    # raw={} must not KeyError; falls through to CWD.
    monkeypatch.chdir(tmp_path)
    assert resolve_project_dir(_session(), None) == tmp_path.resolve()


# project_prompt_copy_name --------------------------------------------------------------

def test_copy_name_from_epoch_ms_local():
    import time
    from datetime import datetime
    epoch_ms = int(time.time() * 1000)
    # Date and HHMM both derive from the same (session-updated) source, in local time.
    expected = datetime.fromtimestamp(epoch_ms / 1000.0).strftime("%Y%m%d-%H%M")
    name = project_prompt_copy_name(_session(sid="ses_x", updated=str(epoch_ms)))
    assert name == f"{expected}-ses_x.compacted.md"


def test_copy_name_unknown_falls_back_to_startup_time():
    name = project_prompt_copy_name(_session(sid="ses_y", updated="unknown"))
    assert name.endswith("-ses_y.compacted.md")
    # Canonical prefix is YYYYMMDD-HHMM
    parts = name.split("-")
    assert len(parts[0]) == 8 and len(parts[1]) == 4


# _backup_compacted_bu ------------------------------------------------------------------

def test_backup_compacted_bu_increments(tmp_path):
    f = tmp_path / "20260101-ses_x.compacted.md"
    f.write_text("v1", encoding="utf-8")
    bu1 = _backup_compacted_bu(f)
    assert bu1 is not None
    assert bu1 == tmp_path / "20260101-ses_x.compacted.bu.001.md"
    assert not f.exists() and bu1.exists()
    # write a new one and back up again -> 002
    f.write_text("v2", encoding="utf-8")
    bu2 = _backup_compacted_bu(f)
    assert bu2 == tmp_path / "20260101-ses_x.compacted.bu.002.md"
    assert _backup_compacted_bu(tmp_path / "missing.compacted.md") is None


# maybe_copy_compacted_to_project -------------------------------------------------------

def _make_compacted(tmp_path):
    src = tmp_path / "out"; src.mkdir()
    r = src / "opencode-ts-ses_x.compacted.md"
    r.write_text("COMPACTED", encoding="utf-8")
    return r


def test_copy_triggers_on_agents_plans(tmp_path):
    proj = tmp_path / "proj"; (proj / ".agents" / "plans").mkdir(parents=True)
    compacted = _make_compacted(tmp_path)
    dest = maybe_copy_compacted_to_project(compacted, _session(sid="ses_x"), proj, enabled=True)
    assert dest is not None
    assert dest.parent == (proj / ".agents" / "prompts" / "pending").resolve()
    assert dest.read_text(encoding="utf-8") == "COMPACTED"
    assert dest.name.endswith("-ses_x.compacted.md")


def test_copy_skips_when_no_agents_convention(tmp_path):
    proj = tmp_path / "proj"; proj.mkdir()  # no .agents
    compacted = _make_compacted(tmp_path)
    assert maybe_copy_compacted_to_project(compacted, _session(), proj, enabled=True) is None


def test_copy_disabled(tmp_path):
    proj = tmp_path / "proj"; (proj / ".agents" / "prompts").mkdir(parents=True)
    compacted = _make_compacted(tmp_path)
    assert maybe_copy_compacted_to_project(compacted, _session(), proj, enabled=False) is None


def test_copy_backs_up_existing(tmp_path):
    proj = tmp_path / "proj"; (proj / ".agents" / "prompts" / "pending").mkdir(parents=True)
    compacted = _make_compacted(tmp_path)
    s = _session(sid="ses_x")
    d1 = maybe_copy_compacted_to_project(compacted, s, proj, enabled=True)
    compacted.write_text("COMPACTED2", encoding="utf-8")
    d2 = maybe_copy_compacted_to_project(compacted, s, proj, enabled=True)
    assert d1 is not None and d2 is not None
    assert d1 == d2  # same canonical name
    assert d2.read_text(encoding="utf-8") == "COMPACTED2"     # new content at canonical name
    bu = d2.parent / (d2.name[: -len(".compacted.md")] + ".compacted.bu.001.md")
    assert bu.exists() and bu.read_text(encoding="utf-8") == "COMPACTED"  # old backed up


def test_copy_is_fail_soft(tmp_path, monkeypatch):
    """A copy failure must not raise (never breaks the primary recovery output)."""
    proj = tmp_path / "proj"; (proj / ".agents" / "plans").mkdir(parents=True)
    compacted = _make_compacted(tmp_path)
    import shutil
    monkeypatch.setattr(shutil, "copy2", lambda *a, **k: (_ for _ in ()).throw(OSError("boom")))
    # must return None, not raise
    assert maybe_copy_compacted_to_project(compacted, _session(), proj, enabled=True) is None
