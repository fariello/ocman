# Implementation Plan - Whole-Project Export/Import (.ocbox)

Status: PROPOSED (not yet executed)

This document plans a feature deferred from the CLI usability pass: exporting an
entire project (all of its root sessions and their subtrees) as a single
portable `.ocbox` bundle, and importing it back.

Today `ocman` can only export a single session subtree (`bundle_session_data`,
via `ocman export SPEC to FILE` / `ocman session export`). The CLI already
accepts `ocman export project SPEC to FILE`, but the normalize layer rejects it
with a clear "not yet supported" message pointing here.

---

## Motivation

- Move or archive a whole project's history in one artifact.
- Seed a fresh machine or a teammate with an entire project's sessions.
- Complements `project move` (which relocates in place) with a portable transfer.

---

## User Review Required

> [!IMPORTANT]
> - Bundle format: a project bundle is a superset of the existing session
>   `.ocbox` (a ZIP with a metadata JSON, per-table row dumps, and packed
>   `session_diff` files). The plan reuses the existing packer/unpacker rather
>   than inventing a second format.
> - Scope of "project": every session whose `project_id` is the target project,
>   including subagent/child sessions (the union of all root-session subtrees),
>   plus the `project` row itself.
> - Import remapping: on import, the project is recreated (new `project.id`),
>   or merged into an existing project via `--to-project`, mirroring the current
>   session-import remap options.
> - Collision safety: reuse the existing session-ID collision detection and
>   rewrite path already implemented for session import.

---

## Open Questions

1. When importing a project whose worktree path already exists as a different
   project, do we merge, refuse, or create a second project at a suffixed path?
   (Proposed default: refuse unless `--to-project` or `--new-project-path` is
   given, matching session import.)
2. Should project export be size-guarded or chunked for very large projects
   (the DB is multi-GB)? Reuse the byte-progress helpers from the backup path.

---

## Proposed Changes

### `ocman.py`

1. `bundle_project_data(project_id, bundle_path, progress_callback=None)`:
   - Resolve all session IDs for the project (root + descendants) with a single
     recursive query (reuse `db_get_session_subtree` per root, or a direct
     `WHERE project_id = ?`).
   - Reuse the existing table-dump + `session_diff` packing logic from
     `bundle_session_data`, generalized to a set of session IDs plus the
     `project` row. Factor the shared core into a helper both call.
   - Write a metadata marker `kind: "project"` (session bundles get
     `kind: "session"`), so import can branch.

2. `extract_and_import_project(bundle_path, target_project_id=None, new_project_path=None, progress_callback=None)`:
   - Branch on the metadata `kind`. For a project bundle, recreate the project
     row (or remap to `--to-project`) and import all sessions, reusing the
     session-import collision/rewrite path.

3. Normalize layer (`_apply_move_or_export`): allow `export project SPEC` once
   the above exist; drop the "not yet supported" guard. `resolve_target` already
   returns the project row.

4. Import side: `ocman session import FILE` should detect a project bundle and
   dispatch to the project importer (or add `ocman project import FILE`). Decide
   during execution which is more intuitive; likely auto-detect by `kind`.

### Tests

- Round-trip: create a project with N sessions (+ subagents) in a temp DB,
  export to `.ocbox`, wipe, import, assert sessions/rows/diffs restored.
- Collision: import into a DB that already contains a colliding session ID.
- Remap: `--to-project` and `--new-project-path`.
- Malformed/mixed bundle rejection.

### Docs

- README Command Reference: document `ocman export project SPEC to FILE` and the
  import counterpart once shipped.

---

## Non-goals

- Cross-version schema migration inside a bundle.
- Deduplicating shared storage across bundles.
