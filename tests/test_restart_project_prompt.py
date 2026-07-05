"""Tests for copying the restart file into a project's .agents/prompts/pending/
(assess-functionality restart-to-project-prompts IPD)."""

from pathlib import Path
import pytest

import ocman
from ocman import (
    SessionInfo,
    resolve_project_dir,
    project_prompt_copy_name,
    _backup_restart_bu,
    maybe_copy_restart_to_project,
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
    expected = datetime.fromtimestamp(epoch_ms / 1000.0).strftime("%Y%m%d")
    name = project_prompt_copy_name(_session(sid="ses_x", updated=str(epoch_ms)))
    assert name == f"{expected}-ses_x.restart.md"


def test_copy_name_unknown_falls_back_to_startup_date():
    name = project_prompt_copy_name(_session(sid="ses_y", updated="unknown"))
    assert name.endswith("-ses_y.restart.md")
    assert len(name.split("-")[0]) == 8  # YYYYMMDD


# _backup_restart_bu --------------------------------------------------------------------

def test_backup_restart_bu_increments(tmp_path):
    f = tmp_path / "20260101-ses_x.restart.md"
    f.write_text("v1", encoding="utf-8")
    bu1 = _backup_restart_bu(f)
    assert bu1 is not None
    assert bu1 == tmp_path / "20260101-ses_x.restart.bu.001.md"
    assert not f.exists() and bu1.exists()
    # write a new one and back up again -> 002
    f.write_text("v2", encoding="utf-8")
    bu2 = _backup_restart_bu(f)
    assert bu2 == tmp_path / "20260101-ses_x.restart.bu.002.md"
    assert _backup_restart_bu(tmp_path / "missing.restart.md") is None


# maybe_copy_restart_to_project ---------------------------------------------------------

def _make_restart(tmp_path):
    src = tmp_path / "out"; src.mkdir()
    r = src / "opencode-ts-ses_x.restart.md"
    r.write_text("RESTART", encoding="utf-8")
    return r


def test_copy_triggers_on_agents_plans(tmp_path):
    proj = tmp_path / "proj"; (proj / ".agents" / "plans").mkdir(parents=True)
    restart = _make_restart(tmp_path)
    dest = maybe_copy_restart_to_project(restart, _session(sid="ses_x"), proj, enabled=True)
    assert dest is not None
    assert dest.parent == (proj / ".agents" / "prompts" / "pending").resolve()
    assert dest.read_text(encoding="utf-8") == "RESTART"
    assert dest.name.endswith("-ses_x.restart.md")


def test_copy_skips_when_no_agents_convention(tmp_path):
    proj = tmp_path / "proj"; proj.mkdir()  # no .agents
    restart = _make_restart(tmp_path)
    assert maybe_copy_restart_to_project(restart, _session(), proj, enabled=True) is None


def test_copy_disabled(tmp_path):
    proj = tmp_path / "proj"; (proj / ".agents" / "prompts").mkdir(parents=True)
    restart = _make_restart(tmp_path)
    assert maybe_copy_restart_to_project(restart, _session(), proj, enabled=False) is None


def test_copy_backs_up_existing(tmp_path):
    proj = tmp_path / "proj"; (proj / ".agents" / "prompts" / "pending").mkdir(parents=True)
    restart = _make_restart(tmp_path)
    s = _session(sid="ses_x")
    d1 = maybe_copy_restart_to_project(restart, s, proj, enabled=True)
    restart.write_text("RESTART2", encoding="utf-8")
    d2 = maybe_copy_restart_to_project(restart, s, proj, enabled=True)
    assert d1 is not None and d2 is not None
    assert d1 == d2  # same canonical name
    assert d2.read_text(encoding="utf-8") == "RESTART2"     # new content at canonical name
    bu = d2.parent / (d2.name[: -len(".restart.md")] + ".restart.bu.001.md")
    assert bu.exists() and bu.read_text(encoding="utf-8") == "RESTART"  # old backed up


def test_copy_is_fail_soft(tmp_path, monkeypatch):
    """A copy failure must not raise (never breaks the primary recovery output)."""
    proj = tmp_path / "proj"; (proj / ".agents" / "plans").mkdir(parents=True)
    restart = _make_restart(tmp_path)
    import shutil
    monkeypatch.setattr(shutil, "copy2", lambda *a, **k: (_ for _ in ()).throw(OSError("boom")))
    # must return None, not raise
    assert maybe_copy_restart_to_project(restart, _session(), proj, enabled=True) is None
