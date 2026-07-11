# Schema Validation - 20260617-173940

This document summarizes the schema and data contract analysis for the `ocman` repository.

## Discovered Schemas & Contracts

### 1. SQLite Database Schema (`opencode.db`)
- **Tables**: `project`, `session`, `event`, `event_sequence`, `part`, `session_message`, `session_input`, `session_share`, `session_context_epoch`, `todo`, `message`.
- **Primary interactions**:
  - Pruning operations: `db_delete_session_recursive` and `db_run_cleanup`. These query session IDs and run cascading deletes on relational keys.
  - Session and project lists: `db_list_projects`, `db_list_sessions`, and `list_sessions_for_project` query and format rows as dictionaries/objects.

### 2. Configuration Schema (`opencode.json` / `opencode.jsonc`)
- **Location**: `~/.config/opencode/opencode.json` or `~/.config/opencode/opencode.jsonc`.
- **Structure**:
  - `provider` key: maps provider string identifiers to provider configuration dictionaries.
  - Provider options: contains `npm` package names, `options` (`apiKey`, `baseURL`), and `models` mapping model identifiers to metadata.
  - API compatibility check: the tool checks if the provider's `npm` name matches `@ai-sdk/openai` or `@ai-sdk/openai-compatible`.

### 3. Session Export Format (opencode session json)
- **Primary keys**:
  - `info`: Session metadata (e.g. `slug`, `model`, `cost`, `tokens`, `summary`, `directory`).
  - `messages`: List of message objects. Each message contains `info` (with `role` and `parts` list of part objects).
- **Fallback parsing**: Falls back to walking arbitrary JSON payloads looking for role-bearing key-value pairs (`role`, `author`, `speaker`) and content fields.

## Schema Validation & Compatibility Risks

- **SQLite Database Drift**: If the upstream `opencode` application updates its database schema (e.g., changes foreign key relationships or removes/adds tables), `ocman`'s pruning logic `SESSION_RELATIONAL_TABLES` (hardcoded mapping) might get out of sync, leading to partial prunes or SQL errors.
  - *Mitigation*: Ensure database integrity checks are run, and capture SQL exceptions during cleanup.
- **Malformed Session JSON exports**: If an export JSON is truncated or invalid, the tool uses a regex-based fallback `_extract_turns_from_raw_text` which parses key-value pairs heuristically.
- **Config Key Formats**: Config can contain variable expansions (`{file:PATH}`, `{env:VAR}`, `${VAR}`, `$VAR`). Tested and working in `expand_config_refs`.

## Action ID Mapping
- **20260617-173940-S6-SCH1**: Add backward-compatibility logging or validation checks when database pruning tables do not exist or throw errors (captured via transaction exception handling improvements in Section 2).
