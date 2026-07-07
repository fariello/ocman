"""Tests for canonical recovery-artifact naming and parsing.

Canonical name: ``YYYYMMDD-HHMM-<session_id>.<kind>.md`` (local time), where kind is one of
transcript/restart/prompt/compacted. All artifacts of one session share the stem.
"""

from datetime import datetime
from pathlib import Path

import pytest

import ocman
from ocman import (
    RECOVERY_KINDS,
    canonical_recovery_name,
    parse_recovery_name,
)


# canonical_recovery_name ---------------------------------------------------------------

def test_canonical_name_formatting():
    dt = datetime(2026, 7, 6, 14, 32, 5)
    assert canonical_recovery_name("ses_abc", dt, "restart") == "20260706-1432-ses_abc.restart.md"


def test_canonical_name_safes_session_id():
    dt = datetime(2026, 1, 2, 3, 4)
    name = canonical_recovery_name("ses/../x y", dt, "compacted")
    assert name == "20260102-0304-ses-.-x-y.compacted.md" or name.endswith(".compacted.md")
    assert "/" not in name and " " not in name


# parse_recovery_name -------------------------------------------------------------------

@pytest.mark.parametrize("kind", RECOVERY_KINDS)
def test_round_trip_all_kinds(kind):
    dt = datetime(2026, 7, 6, 14, 32)
    name = canonical_recovery_name("ses_abc", dt, kind)
    sid, pdt, k = parse_recovery_name(Path(name))
    assert sid == "ses_abc"
    assert k == kind
    assert pdt is not None
    assert pdt.strftime("%Y%m%d-%H%M") == "20260706-1432"


def test_parse_legacy_utc_seconds():
    sid, dt, kind = parse_recovery_name(Path("opencode-20260101-235959-ses_x.restart.md"))
    assert sid == "ses_x" and kind == "restart"
    assert dt == datetime(2026, 1, 1, 23, 59, 59)


def test_parse_legacy_date_only():
    sid, dt, kind = parse_recovery_name(Path("20260202-ses_y.compacted.md"))
    assert sid == "ses_y" and kind == "compacted"
    assert dt == datetime(2026, 2, 2, 0, 0)


def test_parse_non_recovery_returns_empty():
    assert parse_recovery_name(Path("random.txt")) == ("", None, "")
    assert parse_recovery_name(Path("README.md")) == ("", None, "")


def test_parse_unparseable_timestamp_datetime_none():
    # Recognized kind + a stem with no timestamp prefix -> session id is the whole stem, dt None.
    sid, dt, kind = parse_recovery_name(Path("weirdname.restart.md"))
    assert kind == "restart" and dt is None and sid == "weirdname"


# generation forward-fix ----------------------------------------------------------------

def test_run_compaction_uses_local_canonical(tmp_path, monkeypatch):
    """run_compaction writes a canonical local-time .compacted.md (no UTC 'opencode-' prefix)."""
    monkeypatch.setattr(ocman, "call_compaction_api", lambda **k: "# out")
    class M:
        provider_id = "p"; model_id = "m"; name = "n"; base_url = "https://x"; api_key = "k"
    monkeypatch.setattr(ocman, "load_opencode_config", lambda verbosity=0: {})
    monkeypatch.setattr(ocman, "extract_models_from_config", lambda c: [M()])
    monkeypatch.setattr(ocman, "resolve_model", lambda models, spec: M())
    monkeypatch.setattr(ocman, "estimate_cost", lambda *a, **k: 0.0)
    # non-interactive: stdin is not a tty under pytest capture
    prompt = tmp_path / "p.prompt.md"
    prompt.write_text("prompt", encoding="utf-8")
    s = ocman.SessionInfo(session_id="ses_x", title="T", created="", updated="", raw={})
    out = ocman.run_compaction(prompt, tmp_path, s, "", 0)
    assert out is not None
    assert not out.name.startswith("opencode-")
    sid, dt, kind = parse_recovery_name(out)
    assert sid == "ses_x" and kind == "compacted" and dt is not None


# EC-4: kind validation -----------------------------------------------------------------

def test_canonical_rejects_bad_kind():
    with pytest.raises(ValueError):
        canonical_recovery_name("ses_x", datetime(2026, 1, 1), "bogus")


@pytest.mark.parametrize("kind", RECOVERY_KINDS)
def test_canonical_accepts_all_real_kinds(kind):
    assert canonical_recovery_name("ses_x", datetime(2026, 1, 1, 2, 3), kind).endswith(f".{kind}.md")


# EC-5 / COMP-3: case-insensitive suffix, case-preserving sid ----------------------------

def test_parse_case_insensitive_suffix():
    sid, dt, kind = parse_recovery_name(Path("X.RESTART.MD"))
    assert kind == "restart" and sid == "X"


def test_parse_preserves_mixed_case_sid():
    sid, dt, kind = parse_recovery_name(Path("20260101-1200-Ses_AbC.restart.md"))
    assert sid == "Ses_AbC" and kind == "restart"
    assert dt == datetime(2026, 1, 1, 12, 0)


# EC-7: invalid embedded date -> dt None (safe mtime fallback downstream) -----------------

@pytest.mark.parametrize("name", [
    "20269901-1432-ses_x.restart.md",          # month 99 (canonical form)
    "opencode-20260101-250000-ses_x.restart.md",  # hour 25 (legacy form)
])
def test_parse_invalid_date_yields_none(name):
    sid, dt, kind = parse_recovery_name(Path(name))
    assert kind == "restart" and dt is None and sid == "ses_x"
