# Extract-on-delete: preserve recovery files before deletion

Status: EXECUTED

Executed 2026-07-18. Implemented `db_export_session_data`,
`extract_sessions_before_delete`, `resolve_extract_choice`,
`resolve_extract_output_dir`, and `run_delete_extracts`; added `--extracts` /
`--no-extracts` / `-o` on `session delete`, `project delete`, and `db clean`;
wired extraction (after confirmation, before backup/delete) into all four delete
flows. Also added the bare-word `help` -> `--help` argv rewrite. 15 new tests;
full suite: 380 passed, 2 skipped.

## Problem

Deleting a session is irreversible (a DB backup is kept, but that is a raw
opencode.db copy, not a readable record). Users want the human-readable
recovery artifacts (`prompt` / `restart` / `transcript` Markdown) captured
automatically before a delete, so the content is not lost.

The existing `recover` pipeline builds those artifacts from `opencode export`
JSON, but `opencode export` launches OpenCode, and deletion requires OpenCode
to be stopped (the mutation guard). Running the two together is a conflict, and
in bulk (`db clean --older-than`) it would spawn one export per session.

## Decisions (from maintainer)

1. Extraction defaults ON across all delete paths.
2. It is offered through the existing delete confirmation as a single combined
   prompt: `Delete N session(s)? Extract recovery files first? [Y/n]`.
   - `--extracts` forces yes and skips the extract question.
   - `--no-extracts` forces no and skips the extract question.
   - `-y/--yes` (assume-yes) implies extract=yes with no prompt.
3. Extracts are built by reading the session directly from SQLite (no
   `opencode export`, no launching OpenCode), so the whole operation works with
   OpenCode stopped and is fast in bulk.
4. Files are written to the recovery out-dir (default `./opencode-recovery`,
   overridable with `-o`), reusing the standard `recover` renderers.

## Design

### New: `db_export_session_data(session_id, conn) -> dict`
Reconstruct the same JSON shape `opencode export` emits and that
`extract_opencode_turns` consumes:
`{"info": {...}, "messages": [{"info": {"role": ...}, "parts": [...]}, ...]}`.
- `message` rows: `id, session_id, time_created, data` (data JSON has `role`).
  Order by `time_created`. Each becomes `{"info": <data>, "parts": [...]}`.
- `part` rows: `id, message_id, session_id, time_created, data` (data JSON has
  `type`/`text`/`state`). Order by `time_created`, grouped under their message.
- No opencode subprocess; reuses the already-open delete connection.

### New: `extract_before_delete(session_ids, out_dir, conn, ...)`
For each session id: build data via `db_export_session_data`, write it to a
temp JSON file, then call the existing `recover_from_export(...)` with
non-interactive settings (quiet=True, preview=False, chunk=True so oversized
sessions never block on `prompt_for_truncation`). Best-effort per session: a
failure to render one session warns and continues (the delete still proceeds).

### Flag + prompt plumbing
- Add `--extracts` / `--no-extracts` (mutually exclusive) and `-o/--output-dir`
  to the delete entrypoints.
- Resolve an `extract` tri-state (yes / no / ask) before the destructive
  confirmation, fold the extract question into the single confirm line, and run
  extraction after confirmation but before the DB backup/delete.

### Affected delete flows
- `db_delete_session_recursive` (8013)
- `db_delete_sessions_batch` (8319)
- `db_delete_project_recursive` (8518)
- `db_run_cleanup` (10544, the `db clean --older-than` path)

## Tests
- `db_export_session_data` returns the expected messages/parts shape from a
  seeded temp DB, and `find_turns` extracts turns from it.
- Extraction writes prompt/restart/transcript files to the out-dir before a
  delete; `--no-extracts` skips; `--extracts` skips the prompt; `-y` implies
  extract.
- A session that cannot render does not block the delete.

## Non-goals
- No `opencode export` invocation anywhere in the delete path.
- No new "delete projects older than X" command (project age is ill-defined;
  deleting a project's sessions already removes the empty project).
