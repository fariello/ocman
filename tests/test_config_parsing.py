"""Tests for the opencode-config parsing helpers (assess-testing IPD, TEST-6).

Covers strip_jsonc_comments, parse_json_text (lenient + strict), _read_file_ref, and
expand_env_vars ({file:}/{env:}/${VAR}/$VAR forms + malformed input).
"""

import os
import pytest

import ocman
from ocman import (
    strip_jsonc_comments,
    parse_json_text,
    _read_file_ref,
    expand_env_vars,
    RecoveryError,
)


# strip_jsonc_comments -----------------------------------------------------------------

def test_strip_jsonc_line_and_block_comments():
    text = '{\n  // line comment\n  "a": 1, /* block */ "b": 2\n}'
    stripped = strip_jsonc_comments(text)
    assert "//" not in stripped
    assert "/*" not in stripped
    # Result is valid JSON once comments are gone.
    import json
    assert json.loads(stripped) == {"a": 1, "b": 2}


# parse_json_text ----------------------------------------------------------------------

def test_parse_json_text_valid():
    assert parse_json_text('{"x": 1}', "test") == {"x": 1}


def test_parse_json_text_strict_failure_raises():
    with pytest.raises(RecoveryError):
        parse_json_text("{not json", "test", strict_failure=True)


def test_parse_json_text_non_strict_returns_none():
    assert parse_json_text("{not json", "test", strict_failure=False) is None


# _read_file_ref -----------------------------------------------------------------------

def test_read_file_ref_reads_and_strips(tmp_path):
    f = tmp_path / "secret.txt"
    f.write_text("  my_secret\n", encoding="utf-8")
    assert _read_file_ref(str(f)) == "my_secret"


def test_read_file_ref_missing_returns_empty():
    assert _read_file_ref("/no/such/file/anywhere") == ""


# expand_env_vars ----------------------------------------------------------------------

def test_expand_env_vars_env_and_shell_forms(monkeypatch):
    monkeypatch.setenv("OCMAN_TEST_VAR", "env_value")
    assert expand_env_vars("{env:OCMAN_TEST_VAR}") == "env_value"
    assert expand_env_vars("${OCMAN_TEST_VAR}") == "env_value"
    assert expand_env_vars("$OCMAN_TEST_VAR") == "env_value"


def test_expand_env_vars_file_form(tmp_path):
    f = tmp_path / "key.txt"
    f.write_text("file_secret", encoding="utf-8")
    assert expand_env_vars(f"{{file:{f}}}") == "file_secret"


def test_expand_env_vars_missing_file_ref_left_untouched():
    # A file ref that can't be read is left as-is (fallback), not blanked.
    val = "{file:/non/existent/path}"
    assert expand_env_vars(val) == val


def test_expand_env_vars_non_string_or_empty_passthrough():
    assert expand_env_vars("") == ""
    assert expand_env_vars("plain string") == "plain string"
