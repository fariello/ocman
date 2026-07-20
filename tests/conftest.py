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
