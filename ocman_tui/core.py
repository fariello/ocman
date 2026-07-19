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
    db_delete_project_recursive,
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
    SessionInfo,
    expand_env_vars,
    db_create_rollback_backup,
    db_restore_rollback_backup,
    move_directory_structure,
    db_move_project_metadata,
    db_move_session_metadata,
    db_rebase_paths,
    db_get_session_subtree,
    bundle_session_data,
    extract_and_import_session,
    extract_sessions_before_delete,
    resolve_extract_output_dir,
    clear_history_ledger,
    discover_storage_locations,
    run_doctor_checks,
    db_family_open_by_live_pid,
    reclaim_checkpoint_vacuum,
    reclaim_temp,
    reclaim_parts,
    reclaim_backups_dir,
    load_ocman_config,
    gather_spend,
    db_find_project,
    detect_running_instances,
    RunningDetectionError,
    fmt_cost,
    fmt_int,
)

expand_config_refs = expand_env_vars

def extract_turns_from_export(data: Any, include_tools: bool = False) -> List[Any]:
    return find_turns(data, include_tools, 0)

def get_db_path() -> Path:
    return ocman.OPENCODE_DB_PATH

def get_history_path() -> Path:
    return ocman.OPENCODE_HISTORY_PATH
