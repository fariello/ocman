"""Shared pytest fixtures for the ocman test suite."""

import os
import sys
from pathlib import Path

import pytest
import ocman

_IS_LINUX = sys.platform.startswith("linux")
_IS_WINDOWS = os.name == "nt"

# Drive letter used to anchor POSIX-looking test paths on Windows so that
# Path(...).is_absolute() is True (ocman refuses non-absolute worktrees).
_WIN_TEST_DRIVE = "C:"


def abs_path(posix_like: str) -> str:
    """Return an OS-appropriate ABSOLUTE path from a POSIX-looking string.

    Many tests seed worktrees / session directories with POSIX-absolute
    strings like "/home/me/proj" or "/new/path". On Windows those are NOT
    absolute (Path("/home/me/proj").is_absolute() is False), so ocman's
    importer correctly refuses them. This helper keeps such a path unchanged
    on POSIX and drive-anchors it on Windows so it stays absolute and uses the
    native separator (so it matches the value ocman stores/derives via
    str(Path(...))).

    Examples:
      POSIX:   abs_path("/home/me/proj") -> "/home/me/proj"
      Windows: abs_path("/home/me/proj") -> "C:\\home\\me\\proj"
    """
    if not posix_like:
        return posix_like
    if not _IS_WINDOWS:
        return posix_like
    if not posix_like.startswith("/"):
        # Not a POSIX-absolute segment; leave as-is (e.g. already drive-anchored).
        return posix_like
    return str(Path(_WIN_TEST_DRIVE + posix_like))


def norm_real(path: str) -> str:
    """Case- and separator-normalized realpath, for cross-platform comparisons."""
    return os.path.normcase(os.path.realpath(path))


def _probe_symlink_support() -> bool:
    """Return True if this process can actually create a symlink on disk.

    On Windows, os.symlink() needs SeCreateSymbolicLinkPrivilege (Administrator,
    or Developer Mode enabled); an unprivileged account raises OSError WinError
    1314. GitHub's windows-latest runner is privileged so it succeeds there, but
    a plain developer shell or a hardened runner is not. Probe the real syscall
    rather than guessing from sys.platform, so we create a genuine symlink
    wherever the OS allows it and fall back to simulation only where it does not.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "probe_target"
        target.write_text("x", encoding="utf-8")
        link = Path(d) / "probe_link"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            return False
        return link.is_symlink()


SYMLINKS_SUPPORTED = _probe_symlink_support()


def make_symlink(link: Path, target: Path, monkeypatch) -> Path:
    """Make ``link`` behave as a symlink to ``target`` for the code under test.

    Two regimes, chosen by actual OS capability (never by guessing):

    * Where the OS lets us create one (Linux, macOS, privileged Windows) we
      create a REAL on-disk symlink. This gives full-fidelity coverage: it proves
      ocman's guard fires against a genuine link, that ``Path.is_symlink()`` is
      the detector actually being called, and that real symlink mechanics behave.

    * Where creation is forbidden (an unprivileged Windows user, which is the
      normal way ocman runs, and the only regime where this fallback triggers) we
      create a regular file at ``link`` and monkeypatch ``Path.is_symlink`` to
      report True for THAT path only, delegating to the real implementation for
      every other path. This is not a coverage dodge: it faithfully models the
      production scenario ocman is guarding against, a non-admin process meeting a
      symlink it did not (and could not) create, and it keeps the guard under test
      on Windows instead of skipping it.

    Decision record (see DECISIONS.md, "Symlink guard tests run on unprivileged
    Windows", for the full write-up). The
    guards under test are real ocman security behavior: cli.py refuses to write
    through a symlink at the output path, and scripts/migrate_recovery_names.py
    skips symlinks when planning/applying renames (with a TOCTOU re-check). Only
    creating the fixture needs privilege, never the guard itself. Rejected
    alternatives:

    * Skip on Windows (``pytest.mark.skipif``): rejected. It silently drops
      coverage of a security guard on an OS where the guard still applies; a green
      check would then hide untested behavior, and coverage would vanish entirely
      if CI moved to a hardened/unprivileged Windows runner.
    * Monkeypatch ``is_symlink`` on every OS: rejected. It would weaken all
      platforms by never verifying ocman calls the right detector against a
      genuine on-disk link, so a regression (e.g. swapping ``is_symlink()`` for
      ``exists()``) could pass everywhere. We keep the real link where the OS
      allows it and simulate only where it does not.

    The simulation was mutation-checked (temporarily disabling the guard makes the
    tests fail), confirming it exercises the branch rather than passing vacuously.

    Returns ``link``.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text("x", encoding="utf-8")

    if SYMLINKS_SUPPORTED:
        os.symlink(target, link)
        return link

    # Simulated symlink: real file on disk + a path-scoped is_symlink() override.
    link.write_text("x", encoding="utf-8")
    _link_real = os.path.realpath(str(link))
    _orig_is_symlink = Path.is_symlink

    def _fake_is_symlink(self):
        if os.path.realpath(str(self)) == _link_real:
            return True
        return _orig_is_symlink(self)

    monkeypatch.setattr(Path, "is_symlink", _fake_is_symlink)
    return link


@pytest.fixture
def abspath():
    """Fixture exposing abs_path() to tests that prefer fixtures over imports."""
    return abs_path


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "real_process_detection: opt OUT of the autouse running-OpenCode guard "
        "neutralizer (test drives detection itself, e.g. by mocking ps/ss). Also "
        "marks a test as Linux-only, since it exercises the ps/ss/-proc detection "
        "path whose parsing/semantics are Linux-specific.")


def pytest_collection_modifyitems(config, items):
    """Skip Linux-only detection tests off Linux.

    Tests marked `real_process_detection` drive the running-OpenCode detector by mocking
    the Linux `ps`/`ss` output and `/proc` reads; that parsing is Linux-specific (the
    detector itself is documented Linux-only), so on macOS/Windows they would assert
    against an empty result. Skip them there rather than fail. The feature stays covered
    on the Linux CI cells."""
    if _IS_LINUX:
        return
    skip = pytest.mark.skip(reason="Linux-only: real process/`/proc` detection path")
    for item in items:
        if item.get_closest_marker("real_process_detection"):
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def _no_running_opencode_by_default(request, monkeypatch):
    """Neutralize the running-OpenCode mutation guard by default.

    ocman's destructive commands now refuse (or prompt) when OpenCode instances are
    running (`require_safe_to_mutate` / `detect_running_opencode_status`). Tests must
    not depend on the developer's ambient process list, so by default we report
    "none running" (state 'none', no procs). Tests that specifically exercise the
    detector/guard mark themselves `@pytest.mark.real_process_detection` to opt out
    and drive detection via their own `ps`/`ss` mocks.
    """
    if request.node.get_closest_marker("real_process_detection"):
        yield
        return
    import ocman.cli as _cli
    monkeypatch.setattr(_cli, "detect_running_opencode_status",
                        lambda *a, **k: ("none", []))
    monkeypatch.setattr(_cli, "detect_running_opencode", lambda *a, **k: [])
    yield
