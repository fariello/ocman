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

## Resolved decisions (were Open Questions)

These were reviewed against the shipped import path (`extract_and_import_session`,
`ocman.py:7359-7605`) and resolved rather than left open, because leaving them
open would let the implementation inherit surprising or unsafe defaults.

1. **Colliding-project-worktree / colliding-project-id on import.** The current
   session importer does NOT "refuse and require a flag": if the bundle's
   original `project.id` already exists on the target, it silently reuses
   (merges into) that project (`ocman.py:7426-7433`); otherwise it requires
   `--new-project-path`. For a *project* bundle this silent merge is more
   consequential (a whole project's sessions fold into an existing project).
   **Decision:** never merge implicitly. When the bundle's `project.id` (or its
   worktree path) already matches an existing project on the target, and the
   user has not disambiguated up front with `--to-project ID` or
   `--new-project-path PATH`, **prompt interactively** with these choices:
     1. Back up the existing project first, then import (**strongly recommended;
        default `Y`**). Uses `bundle_project_data` on the existing project to a
        timestamped `.ocbox` under the backup dir before proceeding.
     2. Delete the existing project, then import in its place.
     3. Move the existing project to a different worktree path (prompt for the
        path), then import.
     4. Merge into the existing project (print an explicit "this may corrupt the
        project" warning and require confirmation).
     5. Import as a new project at a different worktree path (prompt for it).
     6. Abort (no changes).
   Non-interactive runs (no TTY) MUST NOT pick a destructive default: they fail
   with an actionable error telling the user to pass `--to-project` (merge),
   `--new-project-path` (new project), or `--force`-equivalent opt-in, mirroring
   how the rest of ocman gates destructive actions (`confirm_destructive`,
   `ocman.py:8209`). This diverges intentionally from the session importer's
   silent merge and MUST be covered by tests (interactive selection paths mocked,
   plus the non-interactive refusal).
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

1. **`bundle_project_data(project_id, bundle_path, progress_callback=None)`.**
   - Resolve every session for the project directly: `SELECT id FROM session
     WHERE project_id = ?` (this is the union of all root subtrees and is
     simpler than iterating `db_get_session_subtree` per root; a project's
     subagents share its `project_id`). Refuse an empty project with a clear
     error rather than writing an empty bundle.
   - Factor the shared packing core out of `bundle_session_data`
     (`ocman.py:7222-7332`) so both call it: metadata write, per-table JSONL
     dump over `SESSION_RELATIONAL_TABLES` (parameterized `IN`, batched
     `fetchmany(1000)`), and `session_diffs/<sid>.json` packing. Do not fork a
     second packer.
   - **Metadata / back-compat (required).** Existing session bundles write
     `meta.json` with `export_version: "2.0"`, `main_session_id`,
     `all_session_ids`, `source_project` and NO `kind` field
     (`ocman.py:7272-7279`). A project bundle MUST:
       - populate `all_session_ids` with every session id (the import diff-copy
         loop and collision check key off it, `ocman.py:7408`, `7561`);
       - add `kind: "project"` and set `main_session_id: null` (a project has no
         single main session);
       - bump `export_version` (e.g. `"3.0"`) OR leave `"2.0"` and rely on
         `kind`, but pick one and document it.
     Import MUST treat a **missing `kind` as `"session"`** so all existing
     `.ocbox` files keep importing unchanged (regression guard).

2. **`extract_and_import_project(bundle_path, target_project_id=None, new_project_path=None, progress_callback=None)`.**
   - Reuse the session-import machinery (collision detection + all-or-nothing id
     rewrite, path rebasing, rollback backup) from
     `extract_and_import_session` (`ocman.py:7359-7605`). Factor the shared body
     into a helper rather than copy-pasting.
   - **Transaction integrity (required).** The current importer creates the
     project row (`INSERT INTO project`) BEFORE `BEGIN TRANSACTION`
     (`ocman.py:7440-7443` vs `7476`), so a mid-import failure can leave an
     orphan project row. The project importer MUST insert the `project` row
     INSIDE the same transaction as the sessions (or explicitly delete it on the
     rollback path), so a failed import leaves the DB unchanged. Verify with a
     rollback test (F-below).
   - **Do not depend on `main_session_id`.** `extract_and_import_session` ends
     `return id_map[meta["main_session_id"]]` (`ocman.py:7605`); the project
     importer must return the (possibly remapped) `project.id` instead and not
     index `id_map` by a null main session.
   - **Existing-project collision (Resolved decision 1).** Never silently reuse
     an existing project id. If the bundle's `project.id`/worktree already
     exists and the user did not pass `--to-project`/`--new-project-path`, and
     stdin is a TTY, present the interactive menu from Resolved decision 1
     (default: back up existing then import). Non-interactive runs refuse with an
     actionable error rather than defaulting to any destructive action.
   - **Validate the project row from the bundle.** The session importer
     validates session-id format against `^[a-zA-Z0-9_\-]+$` (`ocman.py:7387`)
     but does not validate the bundled `project` row. Validate the imported
     `project.id` format and resolve/normalize its worktree path safely (reject a
     worktree that is not an absolute path or that escapes via traversal), since
     the worktree is used to rebase `session.directory` (`ocman.py:7490-7498`)
     and could otherwise plant paths outside the intended tree.

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

### Tests (all new; run against the production-equivalent sqlite via the temp DB fixture)

- **Round-trip:** project with N root sessions + subagents in a temp DB; export;
  wipe; import; assert every session row, related-table row
  (`SESSION_RELATIONAL_TABLES`), and `session_diff` file is restored, and the
  `project` row exists.
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
- **Collision matrix:** session-id collision rewrites all ids; project-id
  collision is handled per the default-deny decision. Assert both.
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
