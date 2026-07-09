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
> - Import remapping: on import, the project is recreated from the bundle, or
>   redirected via `--to-project ID` / `--new-project-path PATH`. On a collision
>   with an existing project, ocman does NOT silently merge; it prompts (or
>   refuses non-interactively). See Resolved decision 1 for the full policy.
> - Collision safety: reuse the existing session-ID collision detection and
>   rewrite path for session ids (Axis B), handled independently of project
>   identity (Axis A).

---

## Bundle fidelity and scope (what a project bundle must contain)

Verified against the live schema (`sqlite_master`, `PRAGMA table_info`). This
pins exactly what a "whole project" bundle captures so the round-trip does not
silently drop data.

- **Full `project` row (all columns).** The `project` table has more than
  `id/worktree/name`: it also has `vcs, icon_url, icon_color, time_created,
  time_updated, time_initialized, sandboxes, commands, icon_url_override`. The
  existing session export only captures `id, name, worktree` into
  `meta.json.source_project` (`ocman.py:7250`) and the session importer only
  writes `id, worktree, name` (`ocman.py:7441`). A project bundle MUST capture
  and restore the **complete `project` row** (schema-driven `SELECT *`, insert
  by column name, matching the dynamic-column approach already used for session
  tables at `ocman.py:7500-7506`), so project metadata is not lost on transfer.
- **`project_directory` rows (in scope).** `project_directory` is project-scoped
  (`FK project_id -> project(id) ON DELETE CASCADE`, PK `(project_id,
  directory)`) and populated in real DBs. It is NOT in
  `SESSION_RELATIONAL_TABLES`. A project bundle MUST include this table's rows
  for the project (dumped and restored with `project_id` remapped to the target
  project id).
- **`workspace` rows (in scope, defensively).** `workspace` is also
  project-scoped (`FK project_id -> project(id)`), though empty in the current
  DB and `session.workspace_id` is unused here. Include workspace rows for the
  project in the bundle and restore them (remapping `project_id`); this is cheap
  and future-proofs the round-trip. If a workspace row references a session-level
  id it is covered by the session id_map remap.
- **Session set.** Every session with `project_id = <project>` (this already
  includes subagents, which share the parent's `project_id`), plus all
  `SESSION_RELATIONAL_TABLES` rows keyed to those session ids (unchanged from
  session export).
- **`session_diff` files.** One `session_diffs/<sid>.json` per session id
  (unchanged from session export).

The bundle therefore has three row scopes: project-scoped tables (`project`,
`project_directory`, `workspace`), session-scoped tables
(`SESSION_RELATIONAL_TABLES`), and on-disk diff files. Define the project-scoped
set once as a constant, e.g. `PROJECT_RELATIONAL_TABLES = [("project","id"),
("project_directory","project_id"), ("workspace","project_id")]`, mirroring the
existing `SESSION_RELATIONAL_TABLES` pattern (`ocman.py:372-383`).

---

## Resolved decisions (were Open Questions)

These were reviewed against the shipped import path (`extract_and_import_session`,
`ocman.py:7359-7605`) and resolved rather than left open, because leaving them
open would let the implementation inherit surprising or unsafe defaults.

1. **Collision handling on project import.** There are TWO independent collision
   axes; the plan previously conflated them. They must be handled separately and
   in a fixed order.

   **Axis A - project identity.** Does the target already have this project? A
   collision is when the bundle's `project.id` exists on the target OR an
   existing project has the same worktree path. This is resolved FIRST, and it
   decides the destination `project.id` (call it `dest_proj_id`) and whether any
   existing data is touched:

   | User input (up front) | Project collision? | Behavior |
   |---|---|---|
   | `--to-project ID` | n/a | Import into project `ID` (explicit merge). `dest_proj_id = ID`. |
   | `--new-project-path PATH` | n/a | Create a fresh project row (new generated id) with worktree `PATH`. `dest_proj_id = new id`. |
   | neither | no | Create the project from the bundle's own row/id. `dest_proj_id = bundle id`. |
   | neither | yes, TTY | Prompt with the menu below (default: back up existing, then import in place). |
   | neither | yes, non-TTY | REFUSE with an actionable error (name the colliding project; tell the user to pass `--to-project`, `--new-project-path`, or re-run interactively). Never pick a destructive default. |

   Interactive menu (only on a real collision with no up-front flag; stdin is a
   TTY):
     1. Back up the existing project, then import in place (**recommended;
        default**). Backs up via `bundle_project_data` on the existing project to
        a timestamped `.ocbox` under the backup dir, then proceeds as if
        "delete existing, import in place".
     2. Delete the existing project (reuse `db_delete_project_recursive`), then
        import in its place.
     3. Move the existing project to a different worktree (prompt for the path;
        reuse the `project move` path), then import the bundle in place.
     4. Merge into the existing project (explicit "this may create duplicate or
        conflicting sessions" warning + typed confirm via `confirm_destructive`,
        `ocman.py:8209`). `dest_proj_id = existing id`.
     5. Import as a new project at a different worktree (prompt for path; same as
        `--new-project-path`).
     6. Abort (no changes).

   **Axis B - session ids.** Independently, do any of the bundle's session ids
   already exist on the target? This is the EXISTING all-or-nothing rewrite
   (`ocman.py:7407-7416`): if any collide, all session ids in the bundle are
   remapped to fresh `ses_<uuid>` and remapped structurally in the diffs. Reuse
   this unchanged. Session-id rewriting is orthogonal to Axis A: it happens
   inside the transaction after `dest_proj_id` is decided, and every imported
   `session.project_id` is set to `dest_proj_id` regardless.

   **Ordering (required):** resolve Axis A (may back up / delete / move / create
   the destination project), then open the import transaction, then apply Axis B
   (session id remap) and insert all rows with `project_id = dest_proj_id`. Any
   Axis A destructive step (delete/move/backup) that happens before the
   transaction MUST itself be safe (delete via the existing recursive delete
   which takes its own rollback backup) and MUST be reflected in the tests.

   This diverges intentionally from the session importer's silent
   project-merge; it MUST be covered by tests (each menu branch with prompts
   mocked, the non-interactive refusal, and the two flag paths).
2. **Size-guard / chunking for multi-GB projects.** **Decision:** do NOT add
   chunking (over-scope for a single-maintainer, stdlib-only tool; KISS). Reuse
   the existing streaming JSONL export (batched `fetchmany(1000)`,
   `ocman.py:7304-7311`) which already keeps memory flat, and thread the
   existing `progress_callback` so the CLI shows progress. No new size cap
   beyond what session export already does.

---

## Proposed Changes

Evidence anchors below are `file:line` in the current tree, verified during plan
review; re-verify before editing since line numbers drift.

0. **Shared packing seam (refactor first, verify green, then build on it).**
   Extract the ZIP-writing core of `bundle_session_data` (`ocman.py:7222-7332`)
   into a private helper so both exporters use one packer. Proposed signature:

   ```
   _write_ocbox(bundle_path, *, meta: dict,
                session_ids: list[str],
                project_scoped: list[tuple[str, str, str]] | None = None,
                progress_callback=None) -> None
   ```
   where it: writes `meta.json`; for each `(table, col)` in
   `SESSION_RELATIONAL_TABLES` dumps rows `WHERE col IN (session_ids)` to
   `db_data/<table>.jsonl` (batched `fetchmany(1000)`); for each
   `(table, col, id_value)` in `project_scoped` dumps rows `WHERE col = id_value`
   to the same `db_data/<table>.jsonl` path; and packs `session_diffs/<sid>.json`
   for each session id. `bundle_session_data` becomes a thin caller with
   `project_scoped=None` and the existing meta. This refactor must be a
   behavior-preserving no-op for session export, verified by the existing
   `tests/test_export_import.py` staying green BEFORE the project path is added
   (characterization discipline, rubric D).

1. **`bundle_project_data(project_id, bundle_path, progress_callback=None)`.**
   - Resolve every session for the project directly: `SELECT id FROM session
     WHERE project_id = ?` (subagents share the parent `project_id`). Refuse an
     empty project with a clear error rather than writing an empty bundle.
   - Capture the **full `project` row** and the project-scoped tables via
     `PROJECT_RELATIONAL_TABLES` (see Bundle fidelity), passing them as
     `project_scoped` to `_write_ocbox`. `db_data/project.jsonl` etc. sit
     alongside the session tables; import distinguishes them by table name, not
     by directory.
   - **Metadata / back-compat (required).** Existing session bundles write
     `meta.json` with `export_version: "2.0"`, `main_session_id`,
     `all_session_ids`, `source_project` and NO `kind` field
     (`ocman.py:7272-7279`). A project bundle MUST:
        - populate `all_session_ids` with every session id (the import diff-copy
          loop and collision check key off it, `ocman.py:7408`, `7561`);
        - add `kind: "project"`, set `main_session_id: null`, and record
          `project_id` (the source project id) in `meta`;
        - keep `source_project` as the full project row for display/back-compat;
        - bump `export_version` to `"3.0"`. Import keys off `kind` (see below),
          not the version, but the bump makes the format change explicit.
      Import MUST treat a **missing `kind` as `"session"`** so all existing
      `.ocbox` files keep importing unchanged (regression guard).

2. **`extract_and_import_project(bundle_path, target_project_id=None, new_project_path=None, progress_callback=None, interactive=None)`.**
   Structure it as three phases so Axis A and Axis B (Resolved decision 1)
   compose cleanly:

   - **Phase 1 - pre-flight (no writes).** Read+validate `meta.json`, validate
     all session ids (reuse the `^[a-zA-Z0-9_\-]+$` check, `ocman.py:7387`) AND
     the bundled `project` row: validate `project.id` format and that the
     worktree is an absolute, non-traversing path (it rebases
     `session.directory`, `ocman.py:7490-7498`). Determine Axis A: does the
     bundle's `project.id`/worktree collide on the target? Compute `dest_proj_id`
     and the collision action per the Resolved-decision-1 table. Compute the
     Axis B session `id_map` (all-or-nothing) from a collision probe.
   - **Phase 2 - resolve Axis A destructive step (each with its own safety).**
     If the chosen action is back-up / delete / move existing, perform it via the
     existing safe helpers (`bundle_project_data` for backup;
     `db_delete_project_recursive` for delete, which takes its own rollback
     backup; the `project move` metadata path for move) BEFORE opening the import
     transaction. Abort short-circuits here with no changes.
   - **Phase 3 - import transaction.** Take a rollback backup
     (`db_create_rollback_backup`), `BEGIN`, `PRAGMA foreign_keys=OFF`, then:
     insert the project-scoped rows (`project`, `project_directory`, `workspace`)
     with `project_id`/`id` remapped to `dest_proj_id`, then the session-scoped
     rows with the Axis B `id_map` applied and `session.project_id =
     dest_proj_id` (reuse the existing `process_and_insert_row` logic,
     `ocman.py:7481-7507`, extended to the project-scoped tables), then restore
     the diff files. Commit; on any error rollback + restore backup + clean
     written diffs (as the session importer already does, `ocman.py:7584-7600`).
   - **Transaction integrity (required).** The current session importer INSERTs
     the project row BEFORE `BEGIN TRANSACTION` (`ocman.py:7440-7443` vs `7476`),
     risking an orphan project row on failure. In the project importer the
     `project` INSERT MUST be inside the Phase-3 transaction. Verify with the
     rollback test.
   - **Return value.** Return `dest_proj_id` (not a session id);
     `extract_and_import_session` returns `id_map[meta["main_session_id"]]`
     (`ocman.py:7605`) which is meaningless for a null main session.
   - **Shared body.** Factor the row-insert/diff-restore/rollback core out of
     `extract_and_import_session` so both importers share it; the session
     importer keeps its current external behavior (verified by existing tests
     green before the project path is added).
   - `interactive` defaults to "stdin is a TTY"; tests inject it and mock the
     menu input.

3. **Namespace + normalize layer.** Export currently normalizes only to
   `out["export_session"]` and `_apply_move_or_export` has TWO guards that reject
   `export project` (`ocman.py:5467-5469` and `5487-5489`). Add an
   `export_project` legacy-namespace field (default `None` in
   `_legacy_defaults`), remove BOTH guards, and set `out["export_project"] =
   res.project["id"]` when `res.kind == "project"`.

4. **CLI dispatch.**
   - Export: add a `main()` branch mirroring the session-export branch
     (`ocman.py:9408-9426`): when `export_project` is set, require `--to` and
     call `bundle_project_data`.
   - Import: `ocman session import FILE` (and the plain importer at
     `ocman.py:9428-9444`) must peek `meta.json` `kind` and dispatch to
     `extract_and_import_project` for project bundles, else the session importer.
     Prefer auto-detect by `kind` over a separate `project import` subcommand
     (fewer commands, KISS), but keep the error messages specific about which
     kind was detected.

### Test-fixture prerequisite

The `temp_db` fixtures in `tests/test_ocman.py:17` and
`tests/test_export_import.py:17` create `project` with only `(id, worktree,
name)` and do NOT create `project_directory` or `workspace`. Executing this plan
requires extending those fixtures (or adding a project-export-specific fixture)
to build the full-column `project` table plus `project_directory` and
`workspace`, matching the real schema, so the fidelity tests below are
meaningful. Keep the change additive so existing tests are unaffected.

### Tests (all new; run against the production-equivalent sqlite via the temp DB fixture)

- **Refactor no-op (do first):** after extracting `_write_ocbox` and the shared
  import body, the existing `tests/test_export_import.py` passes unchanged,
  proving the session path is behavior-preserving before the project path is
  added.
- **Round-trip (full fidelity):** project with N root sessions + subagents, plus
  `project_directory` and `workspace` rows and a full multi-column `project` row,
  in a temp DB; export; wipe; import; assert every session row,
  `SESSION_RELATIONAL_TABLES` row, `session_diff` file, ALL `project` columns
  (not just id/name/worktree), and the `project_directory`/`workspace` rows are
  restored with `project_id` remapped.
- **Back-compat (regression):** an existing session `.ocbox` (no `kind` field)
  still imports as a session unchanged. Pin this so the `kind` branch cannot
  break the shipped format.
- **Existing-project collision:** with a colliding `project.id`/worktree,
  a non-interactive import refuses (no destructive default); the interactive
  menu selects each branch (backup-then-import, delete, move-existing, merge with
  warning, new-project, abort) with prompts mocked; and `--to-project` /
  `--new-project-path` still work up front without prompting.
- **Directory rebasing:** import with `--new-project-path` different from the
  source worktree rebases each `session.directory` correctly
  (mirrors `ocman.py:7490-7498`).
- **Collision matrix (Axis A x Axis B):** session-id collision rewrites all ids
  (Axis B) independently of project identity; project-identity collision (Axis A)
  follows Resolved decision 1. Assert the two axes compose: e.g. a bundle that
  collides on session ids but resolves Axis A to "new project" ends with remapped
  session ids all pointing at the new `dest_proj_id`.
- **Transaction rollback:** force a mid-import failure and assert NO partial
  state remains, specifically no orphan `project` row (guards the F3 fix).
- **Security:** malformed/mixed bundle rejection; a bundle with a bad
  `project.id` format or a traversal/relative worktree is rejected (extends the
  existing session path-traversal test, `tests/test_export_import.py:396`).
- **Empty project:** exporting a project with zero sessions errors clearly.

### Docs (spec-sync; user-visible behavior change)

- README Command Reference: `ocman export project SPEC to FILE` and the import
  behavior (auto-detect by bundle kind; `--to-project`/`--new-project-path`).
- `ARCHITECTURE.md`: it documents the CLI grammar and lists export/import; update
  it so it does not claim project export is unsupported.
- Help renderer (`build_help` / `build_help_reference` in `ocman.py`): update the
  `export`/`move` rows and any "project export not supported" wording.

---

## Non-goals

- Cross-version schema migration inside a bundle.
- Deduplicating shared storage across bundles.
