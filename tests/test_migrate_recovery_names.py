"""Tests for scripts/migrate_recovery_names.py (legacy filename normalization)."""

import importlib.util
import os
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "migrate_recovery_names.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("migrate_recovery_names", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mig = _load_module()


def _populate(d: Path):
    (d / "opencode-20260101-235959-ses_x.restart.md").write_text("a", encoding="utf-8")
    (d / "20260202-ses_y.compacted.md").write_text("b", encoding="utf-8")
    (d / "20260303-1200-ses_z.transcript.md").write_text("c", encoding="utf-8")  # already canonical
    (d / "notrecovery.txt").write_text("d", encoding="utf-8")


def test_dry_run_touches_nothing(tmp_path):
    _populate(tmp_path)
    before = {p.name for p in tmp_path.iterdir()}
    summary = mig.migrate_dir(tmp_path, apply=False, force=False, log=lambda *a, **k: None)
    after = {p.name for p in tmp_path.iterdir()}
    assert before == after  # unchanged
    assert summary["planned"] == 2  # two legacy files; canonical + txt excluded
    assert summary["renamed"] == 0


def test_apply_renames_to_canonical(tmp_path):
    _populate(tmp_path)
    summary = mig.migrate_dir(tmp_path, apply=True, force=False, log=lambda *a, **k: None)
    names = {p.name for p in tmp_path.iterdir()}
    assert "20260101-2359-ses_x.restart.md" in names
    assert "20260202-0000-ses_y.compacted.md" in names
    assert "20260303-1200-ses_z.transcript.md" in names  # already canonical, untouched
    assert "notrecovery.txt" in names  # not a recovery file
    assert summary["renamed"] == 2 and summary["errors"] == 0


def test_collision_skipped_without_force(tmp_path):
    (tmp_path / "opencode-20260101-235959-ses_x.restart.md").write_text("legacy", encoding="utf-8")
    # Pre-create the canonical target so it collides.
    (tmp_path / "20260101-2359-ses_x.restart.md").write_text("existing", encoding="utf-8")
    summary = mig.migrate_dir(tmp_path, apply=True, force=False, log=lambda *a, **k: None)
    assert summary["skipped_collision"] == 1 and summary["renamed"] == 0
    # source preserved
    assert (tmp_path / "opencode-20260101-235959-ses_x.restart.md").read_text() == "legacy"
    assert (tmp_path / "20260101-2359-ses_x.restart.md").read_text() == "existing"


def test_symlink_skipped(tmp_path):
    real = tmp_path / "notrecovery.txt"
    real.write_text("d", encoding="utf-8")
    os.symlink(real, tmp_path / "opencode-20260404-010101-ses_link.restart.md")
    renames = mig.plan_migration(tmp_path)
    assert renames == []  # the symlink is not planned for rename


def test_no_recursion(tmp_path):
    sub = tmp_path / "sub"; sub.mkdir()
    (sub / "opencode-20260101-235959-ses_deep.restart.md").write_text("x", encoding="utf-8")
    renames = mig.plan_migration(tmp_path)
    assert renames == []  # nested files are not touched
