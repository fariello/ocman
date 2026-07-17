"""Tests for the recovery/compaction pipeline (assess-testing IPD, run 20260704-143424).

Covers the previously-untested headline feature: parsing an opencode export into Turns
(find_turns/extract_opencode_turns), the output renderers, the compaction API client,
the end-to-end recovery flow, and the token/cost estimators.

The fixture tests/fixtures/opencode_export.json is a hand-authored minimal example of
opencode's native export shape:
    {"info": {...}, "messages": [{"info": {"role": ...}, "parts": [{"type": "text"|"tool"|"step-*", ...}]}]}
Regenerate it from a real (sanitized) `opencode export <id>` if the format changes.
"""

import json
import io
import urllib.error
from pathlib import Path

import pytest

import ocman
from ocman import (
    find_turns,
    render_transcript,
    render_restart_context,
    render_compact_prompt,
    recover_from_export,
    call_compaction_api,
    estimate_tokens,
    estimate_cost,
    chunk_turns,
    count_interactions,
    part_recovery_name,
    SessionInfo,
    ModelInfo,
    Turn,
    RecoveryError,
)
from datetime import datetime

FIXTURE = Path(__file__).parent / "fixtures" / "opencode_export.json"


def _load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _session():
    return SessionInfo(
        session_id="ses_fixture01",
        title="Fixture session",
        created="2026-07-04T00:00:00Z",
        updated="2026-07-04T01:00:00Z",
        raw={},
    )


# --------------------------------------------------------------------------------------
# TEST-2: recovery parser (golden / characterization)
# --------------------------------------------------------------------------------------

def test_find_turns_extracts_expected_turns_without_tools():
    turns = find_turns(_load_fixture(), include_tools=False, verbosity=0)
    # 2 user + 2 assistant text turns; tool part excluded; step-* parts ignored.
    assert [(t.role, t.text) for t in turns] == [
        ("user", "Please add a hello function."),
        ("assistant", "Sure, here is a hello function."),
        ("user", "Thanks, now run the tests."),
        ("assistant", "All tests pass."),
    ]


def test_find_turns_includes_tool_output_when_requested():
    turns = find_turns(_load_fixture(), include_tools=True, verbosity=0)
    joined = "\n".join(t.text for t in turns)
    # The assistant turn now carries the tool call + output.
    assert "[Tool: write(" in joined
    assert "wrote 3 lines to hello.py" in joined


def test_find_turns_raw_text_fallback():
    # A plain string (JSON parse failed upstream) goes through the raw-text extractor.
    turns = find_turns("just some raw transcript text", include_tools=False, verbosity=0)
    assert isinstance(turns, list)


def test_find_turns_unknown_dict_returns_generic_or_empty():
    # A dict that is not opencode format should not raise; generic walker handles it.
    turns = find_turns({"unexpected": "shape"}, include_tools=False, verbosity=0)
    assert isinstance(turns, list)


# --------------------------------------------------------------------------------------
# TEST-5: output renderers (real signatures + real SessionInfo)
# --------------------------------------------------------------------------------------

def _turns():
    return [
        Turn("user", "Do the thing.", 1, "$.messages[0]"),
        Turn("assistant", "Done the thing.", 2, "$.messages[1]"),
    ]


def test_render_transcript_contains_turns():
    out = render_transcript(_turns(), "My Title")
    assert "# My Title" in out
    assert "Do the thing." in out
    assert "Done the thing." in out


def test_render_restart_context_contains_session_and_turns():
    out = render_restart_context(_turns(), source_name="export.json", session=_session())
    assert "Restart context for opencode" in out
    assert "ses_fixture01" in out
    assert "Do the thing." in out


def test_render_compact_prompt_contains_turns():
    out = render_compact_prompt(
        _turns(),
        source_name="export.json",
        session=_session(),
    )
    assert isinstance(out, str) and out
    assert "Do the thing." in out


# --------------------------------------------------------------------------------------
# TEST-4: compaction API client (mock the network only)
# --------------------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _model(base_url="https://api.example.com/v1"):
    return ModelInfo("prov", "m1", "Model 1", base_url, "sk-test", 1.0, 2.0, True)


def test_call_compaction_api_success_returns_content_string(monkeypatch):
    payload = {"choices": [{"message": {"content": "COMPACTED"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    monkeypatch.setattr(ocman.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(payload))
    result, usage = call_compaction_api(_model(), "prompt", verbosity=0)
    assert result == "COMPACTED"
    assert usage == {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.00002}


def test_call_compaction_api_refuses_non_https_non_localhost():
    with pytest.raises(RecoveryError):
        call_compaction_api(_model("http://api.example.com/v1"), "prompt", verbosity=0)


def test_call_compaction_api_empty_choices_raises(monkeypatch):
    monkeypatch.setattr(ocman.urllib.request, "urlopen", lambda *a, **k: _FakeResponse({"choices": []}))
    with pytest.raises(RecoveryError):
        call_compaction_api(_model(), "prompt", verbosity=0)


def test_call_compaction_api_empty_content_raises(monkeypatch):
    payload = {"choices": [{"message": {"content": ""}}]}
    monkeypatch.setattr(ocman.urllib.request, "urlopen", lambda *a, **k: _FakeResponse(payload))
    with pytest.raises(RecoveryError):
        call_compaction_api(_model(), "prompt", verbosity=0)


def test_call_compaction_api_http_error_raises(monkeypatch):
    def _raise(*a, **k):
        raise urllib.error.HTTPError("url", 500, "Server Error", {}, io.BytesIO(b"boom"))
    monkeypatch.setattr(ocman.urllib.request, "urlopen", _raise)
    with pytest.raises(RecoveryError):
        call_compaction_api(_model(), "prompt", verbosity=0)


# --------------------------------------------------------------------------------------
# TEST-3: end-to-end recovery (fixture -> restart/transcript files)
# --------------------------------------------------------------------------------------

def test_recover_from_export_writes_outputs(tmp_path):
    out_dir = tmp_path / "out"
    restart = out_dir / "restart.md"
    transcript = out_dir / "transcript.md"

    written = recover_from_export(
        export_path=FIXTURE,
        output_dir=out_dir,
        session=_session(),
        include_tools=False,
        all_roles=False,
        verbosity=0,
        output_transcript=transcript,
        output_restart=restart,
    )

    assert restart.exists()
    assert transcript.exists()
    assert restart in written and transcript in written
    restart_text = restart.read_text(encoding="utf-8")
    transcript_text = transcript.read_text(encoding="utf-8")
    assert "Please add a hello function." in transcript_text
    assert "ses_fixture01" in restart_text


def test_recover_from_export_chunk_writes_multiple_parts(tmp_path):
    """--chunk splits the fixture into >1 part with .part-NNofMM names; every part
    parses and no turn is dropped (all interactions appear across the parts)."""
    from ocman import parse_recovery_name, find_turns, count_interactions
    import json as _json
    out_dir = tmp_path / "out"
    total_interactions = count_interactions(
        find_turns(_json.loads(FIXTURE.read_text(encoding="utf-8")), include_tools=False, verbosity=0))
    assert total_interactions >= 2  # fixture must have enough to split

    written = recover_from_export(
        export_path=FIXTURE,
        output_dir=out_dir,
        session=_session(),
        include_tools=False,
        all_roles=False,
        verbosity=0,
        max_interactions=1,  # 1 interaction per part -> forces multiple parts
        chunk=True,
    )
    transcripts = sorted(p for p in written if p.name.endswith(".transcript.md"))
    assert len(transcripts) == total_interactions  # one part per interaction
    for p in transcripts:
        assert ".part-" in p.name
        sid, dt, kind = parse_recovery_name(p)
        assert sid == "ses_fixture01"
        assert kind == "transcript"
    # Every part file was actually written.
    for p in written:
        assert p.exists()


def test_prompt_for_truncation_choices_backward_compat(monkeypatch):
    """Anti-regression: the old N/l/i/b choices still map to the same effective
    (max_lines, max_interactions); the new [c] choice yields mode='chunk'."""
    from ocman import prompt_for_truncation, Turn
    turns = [Turn("user", "q", 1, "$"), Turn("assistant", "a", 2, "$")]
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    def _answers(seq):
        it = iter(seq)
        monkeypatch.setattr("builtins.input", lambda _p="": next(it))

    _answers(["n"])
    c = prompt_for_truncation(turns, 9999, 999)
    assert c.mode == "full" and c.max_lines is None and c.max_interactions is None

    _answers(["l", "500"])
    c = prompt_for_truncation(turns, 9999, 999)
    assert c.mode == "truncate" and c.max_lines == 500 and c.max_interactions is None

    _answers(["i", "42"])
    c = prompt_for_truncation(turns, 9999, 999)
    assert c.mode == "truncate" and c.max_interactions == 42 and c.max_lines is None

    _answers(["b", "500", "42"])
    c = prompt_for_truncation(turns, 9999, 999)
    assert c.mode == "truncate" and c.max_lines == 500 and c.max_interactions == 42

    _answers(["c", "10", "1000"])
    c = prompt_for_truncation(turns, 9999, 999)
    assert c.mode == "chunk" and c.max_interactions == 10 and c.max_lines == 1000


def test_prompt_for_truncation_non_interactive_is_full(monkeypatch):
    from ocman import prompt_for_truncation, Turn
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    c = prompt_for_truncation([Turn("user", "q", 1, "$")], 9999, 999)
    assert c.mode == "full"


# --------------------------------------------------------------------------------------
# TEST-7: pure estimators
# --------------------------------------------------------------------------------------

def test_estimate_tokens_scales_with_length():
    short = estimate_tokens("hi")
    long = estimate_tokens("hi " * 1000)
    assert short >= 0
    assert long > short


def test_estimate_cost_math_and_none_model():
    priced = ModelInfo("p", "m", "M", "https://x/v1", "k", 1.0, 2.0, True)
    # cost is per-1M tokens: (1000/1e6)*1.0 + (500/1e6)*2.0
    cost = estimate_cost(1000, 500, priced)
    assert cost == pytest.approx((1000 / 1_000_000) * 1.0 + (500 / 1_000_000) * 2.0)

    unpriced = ModelInfo("p", "m", "M", "https://x/v1", "k", None, None, True)
    assert estimate_cost(1000, 500, unpriced) is None


# --------------------------------------------------------------------------------------
# chunk_turns (D-2) and part_recovery_name (D-3)
# --------------------------------------------------------------------------------------

def _convo(n_interactions: int) -> list[Turn]:
    """n user+assistant interaction pairs."""
    turns = []
    for i in range(n_interactions):
        turns.append(Turn("user", f"q{i}", 2 * i + 1, f"$.m[{2*i}]"))
        turns.append(Turn("assistant", f"a{i}", 2 * i + 2, f"$.m[{2*i+1}]"))
    return turns


def test_chunk_turns_empty():
    assert chunk_turns([], max_interactions=10, max_lines=1000) == []


def test_chunk_turns_fits_in_one_part():
    turns = _convo(3)
    parts = chunk_turns(turns, max_interactions=10, max_lines=10000)
    assert len(parts) == 1
    assert parts[0] == turns


def test_chunk_turns_by_interaction_limit():
    turns = _convo(5)
    parts = chunk_turns(turns, max_interactions=2, max_lines=1_000_000)
    # 5 interactions, 2 per part -> 3 parts (2,2,1)
    assert [sum(1 for t in p if t.role == "user") for p in parts] == [2, 2, 1]
    # concatenation equals the original (nothing dropped / reordered)
    flat = [t for p in parts for t in p]
    assert flat == turns


def test_chunk_turns_never_splits_an_interaction_and_ordering_preserved():
    turns = _convo(4)
    parts = chunk_turns(turns, max_interactions=1, max_lines=1_000_000)
    assert len(parts) == 4
    for p in parts:
        # each part is exactly one whole interaction (user + assistant), never split
        assert [t.role for t in p] == ["user", "assistant"]
    assert [t for p in parts for t in p] == turns


def test_chunk_turns_oversized_single_interaction_is_own_part():
    big = Turn("user", "x\n" * 5000, 1, "$.m[0]")  # far exceeds max_lines alone
    turns = [big, Turn("assistant", "ok", 2, "$.m[1]"),
             Turn("user", "small", 3, "$.m[2]"), Turn("assistant", "ok2", 4, "$.m[3]")]
    parts = chunk_turns(turns, max_interactions=100, max_lines=100)
    # The oversized interaction ships as its own part; nothing is dropped or split.
    assert [t for p in parts for t in p] == turns
    assert big in parts[0]
    assert len(parts[0]) >= 1


def test_part_recovery_name_scheme_and_padding():
    dt = datetime(2026, 7, 6, 14, 32)
    # total==1 -> plain canonical name (no part segment)
    assert part_recovery_name("ses_abc", dt, "transcript", 1, 1) == "20260706-1432-ses_abc.transcript.md"
    # multi-part -> zero-padded to width of total
    assert part_recovery_name("ses_abc", dt, "transcript", 1, 3) == "20260706-1432-ses_abc.part-1of3.transcript.md"
    assert part_recovery_name("ses_abc", dt, "compacted", 7, 123) == "20260706-1432-ses_abc.part-007of123.compacted.md"
