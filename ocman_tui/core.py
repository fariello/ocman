"""
Core interface to the ocman database and settings for the TUI.
"""

from pathlib import Path
from typing import Any, List, Dict, Optional

# Import everything from the main ocman CLI module.
import ocman
from ocman import (
    db_list_projects,
    db_list_sessions,
    db_delete_session_recursive,
    db_run_cleanup,
    load_opencode_config,
    extract_models_from_config,
    resolve_model,
    estimate_tokens,
    estimate_cost,
    call_compaction_api,
    write_export_to_temp,
    load_export_file,
    filter_conversation_turns,
    consolidate_turns,
    render_compact_prompt,
    render_transcript,
    render_restart_context,
    write_text,
    OPENCODE_DB_PATH,
    OPENCODE_HISTORY_PATH,
    _load_history,
    _save_history,
    RecoveryError,
    SESSION_RELATIONAL_TABLES,
    find_turns,
    _get_sqlite,
    human_size_local,
    get_file_size_local,
    truncate_turns_by_interactions,
    truncate_turns_by_lines,
    Turn,
    ModelInfo,
    expand_env_vars,
)

expand_config_refs = expand_env_vars

def extract_turns_from_export(data: Any, include_tools: bool = False) -> List[Any]:
    return find_turns(data, include_tools, 0)

def get_db_path() -> Path:
    return ocman.OPENCODE_DB_PATH

def get_history_path() -> Path:
    return ocman.OPENCODE_HISTORY_PATH
