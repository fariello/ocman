import os
import pytest
from pathlib import Path
from orsession.core import (
    expand_config_refs,
    extract_models_from_config,
    resolve_model,
    consolidate_turns,
    truncate_turns_by_interactions,
    truncate_turns_by_lines,
    Turn,
    ModelInfo,
)

def test_expand_config_refs(tmp_path):
    # Test file expansion
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("my_secret_key", encoding="utf-8")
    
    val = f"{{file:{secret_file}}}"
    expanded = expand_config_refs(val)
    assert expanded == "my_secret_key"
    
    # Test env expansion
    os.environ["TEST_ENV_VAR"] = "env_value"
    val_env = "{env:TEST_ENV_VAR}"
    assert expand_config_refs(val_env) == "env_value"
    
    # Test shell expansion ${VAR}
    assert expand_config_refs("${TEST_ENV_VAR}") == "env_value"
    
    # Test fallback
    assert expand_config_refs("{file:/non/existent/file}") == "{file:/non/existent/file}"


def test_extract_models_from_config():
    config = {
        "provider": {
            "openai": {
                "npm": "@ai-sdk/openai",
                "options": {
                    "apiKey": "sk-test",
                    "baseURL": "https://api.openai.com/v1"
                },
                "models": {
                    "gpt-4": {
                        "name": "GPT-4",
                        "cost": {"input": 10.0, "output": 30.0}
                    }
                }
            }
        }
    }
    models = extract_models_from_config(config)
    assert len(models) == 1
    m = models[0]
    assert m.provider_id == "openai"
    assert m.model_id == "gpt-4"
    assert m.name == "GPT-4"
    assert m.compatible is True
    assert m.cost_input == 10.0
    assert m.cost_output == 30.0


def test_resolve_model():
    models = [
        ModelInfo("openai", "gpt-4", "GPT-4", "https://api.openai.com/v1", "sk-test", 10.0, 30.0, True),
        ModelInfo("openai", "gpt-3.5-turbo", "GPT-3.5", "https://api.openai.com/v1", "sk-test", 1.5, 2.0, True),
    ]
    
    # Exact match
    res = resolve_model(models, "openai/gpt-4")
    assert res.model_id == "gpt-4"
    
    # Substring match
    res = resolve_model(models, "gpt-3.5")
    assert res.model_id == "gpt-3.5-turbo"
    
    # Ambiguous match
    with pytest.raises(Exception) as excinfo:
        resolve_model(models, "gpt")
    assert "Ambiguous" in str(excinfo.value)
    
    # Not found
    with pytest.raises(Exception) as excinfo:
        resolve_model(models, "claude")
    assert "Model not found" in str(excinfo.value)


def test_consolidate_turns():
    turns = [
        Turn("user", "Hello", 1, "test"),
        Turn("user", "World", 2, "test"),
        Turn("assistant", "Hi there", 3, "test"),
        Turn("assistant", "How can I help?", 4, "test"),
    ]
    consolidated = consolidate_turns(turns)
    assert len(consolidated) == 2
    assert consolidated[0].role == "user"
    assert consolidated[0].text == "Hello\n\nWorld"
    assert consolidated[1].role == "assistant"
    assert consolidated[1].text == "Hi there\n\nHow can I help?"


def test_truncate_turns_by_interactions():
    turns = [
        Turn("user", "1", 1, "test"),
        Turn("assistant", "2", 2, "test"),
        Turn("user", "3", 3, "test"),
        Turn("assistant", "4", 4, "test"),
    ]
    
    truncated = truncate_turns_by_interactions(turns, 1)
    assert len(truncated) == 2
    assert truncated[0].text == "3"
    assert truncated[1].text == "4"


def test_truncate_turns_by_lines():
    turns = [
        Turn("user", "line1\nline2", 1, "test"),
        Turn("assistant", "line3", 2, "test"),
    ]
    # Keep budget extremely small (so it only keeps the last turn)
    truncated = truncate_turns_by_lines(turns, 10)
    assert len(truncated) == 1
    assert truncated[0].text == "line3"
