"""Shared pytest fixtures for the ocman test suite."""

import pytest
import ocman


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "real_process_detection: opt OUT of the autouse running-OpenCode guard "
        "neutralizer (test drives detection itself, e.g. by mocking ps/ss).")


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
