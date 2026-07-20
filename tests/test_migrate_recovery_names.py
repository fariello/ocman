"""Tests for scripts/migrate_recovery_names.py (legacy filename normalization)."""

import importlib.util
import os
from pathlib import Path

import pytest

from conftest import make_symlink

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


def test_symlink_skipped(tmp_path, monkeypatch):
    real = tmp_path / "notrecovery.txt"
    real.write_text("d", encoding="utf-8")
    # A real symlink where the OS allows it; a faithfully simulated one on
    # unprivileged Windows. See DECISIONS.md and conftest.make_symlink (why
    # real+simulate, vs skip-on-Windows / vs monkeypatch-everywhere).
    make_symlink(tmp_path / "opencode-20260404-010101-ses_link.restart.md", real, monkeypatch)
    renames = mig.plan_migration(tmp_path)
    assert renames == []  # the symlink is not planned for rename


def test_no_recursion(tmp_path):
    sub = tmp_path / "sub"; sub.mkdir()
    (sub / "opencode-20260101-235959-ses_deep.restart.md").write_text("x", encoding="utf-8")
    renames = mig.plan_migration(tmp_path)
    assert renames == []  # nested files are not touched


def test_in_plan_duplicate_targets_surfaced(tmp_path):
    # Two legacy files differing only in seconds -> same minute-precision target.
    (tmp_path / "opencode-20260101-120000-ses_x.restart.md").write_text("A", encoding="utf-8")
    (tmp_path / "opencode-20260101-120059-ses_x.restart.md").write_text("B", encoding="utf-8")
    # Dry-run must report the collision, not two plain renames.
    dry = mig.migrate_dir(tmp_path, apply=False, force=False, log=lambda *a, **k: None)
    assert dry["skipped_collision"] == 1 and dry["planned"] == 2
    # Apply: exactly one renamed, the other skipped, BOTH sources still present.
    res = mig.migrate_dir(tmp_path, apply=True, force=False, log=lambda *a, **k: None)
    assert res["renamed"] == 1 and res["skipped_collision"] == 1
    names = {p.name for p in tmp_path.iterdir()}
    assert "20260101-1200-ses_x.restart.md" in names
    assert "opencode-20260101-120059-ses_x.restart.md" in names  # loser preserved


def test_symlink_introduced_before_apply_not_renamed(tmp_path, monkeypatch):
    # A legacy file that plan_migration accepts, then becomes a symlink before apply.
    src = tmp_path / "opencode-20260101-120000-ses_z.restart.md"
    # Simulate: the path is (or becomes) a symlink before apply. migrate_dir
    # re-checks is_symlink() just before os.rename, so it must skip. make_symlink
    # plants a real link where possible, or a simulated one on unprivileged
    # Windows. See DECISIONS.md and conftest.make_symlink (why real+simulate, vs
    # skip-on-Windows / vs monkeypatch-everywhere).
    real = tmp_path / "target.txt"; real.write_text("x", encoding="utf-8")
    make_symlink(src, real, monkeypatch)
    res = mig.migrate_dir(tmp_path, apply=True, force=False, log=lambda *a, **k: None)
    # The symlink is skipped by plan_migration (is_symlink) so nothing renamed.
    assert res["renamed"] == 0
