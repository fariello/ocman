# Implementation Plan 05 - restore multiple files & import session-id rename

Status: EXECUTED

IPD 05 in the execution order (independent of 01-04). Two small changes:
`backup restore` accepts multiple input files, and `session import` can
regenerate the session id.

---

## Motivation

- Restoring often means applying several backups; today `backup restore` takes
  one `path` (`build_parser`, restore action).
- On import, a user may want a fresh session id rather than reusing the bundle's
  id (or the auto-UUID only-on-collision behavior).

---

## User Review Required

> [!IMPORTANT]
> - `session import --new-session-id` takes NO argument. ocman GENERATES a fresh,
>   opencode-conforming `ses_...` id. Arbitrary user-supplied ids are NOT
>   allowed: the id flows into opencode's agent-accessible system and unknown
>   strings are a safety risk.
> - `--new-session-id` applies to single-session bundles only. Project bundles /
>   multi-root bundles are refused (no unambiguous single id to rename).
> - `backup restore FILE...` applies multiple archives in the given order.
>   Restore already has rollback safety; multi-file must define what happens if a
>   later file fails after earlier ones applied (see below).

---

## Design

### `backup restore` multiple files

- Change the `path` positional to `paths` (`nargs="+"`).
- **Do NOT naively loop `cli_restore(source)`.** `cli_restore` (`ocman.py`,
  "Creating rollback safety backup of current state...") makes its OWN
  pre-op rollback ZIP, applies, and on success DELETES that backup. Looping it N
  times gives N independent per-file atomic restores, NOT a batch-atomic one: if
  file 3 fails, files 1-2 are already committed and only file 3 rolls back.
- **Batch-atomic design (decided):** factor `cli_restore`'s core into an internal
  `_restore_one(source, *, take_backup, restore_on_fail)` (or equivalent) so the
  batch can: (1) take ONE pre-batch rollback backup of current state; (2) apply
  each file in order WITHOUT each making/deleting its own batch backup;
  (3) on ANY file's failure, restore from the single pre-batch backup so the
  system returns to its original state (all-or-nothing across the batch), then
  report which file failed; (4) delete the pre-batch backup only after all files
  succeed. Preserve `cli_restore(single)` behavior for the one-file case (verify
  with the existing restore tests, rubric D).
- Validate every archive up front (existence + `zipfile.is_zipfile`, mirroring
  the current single-file validation) BEFORE touching state, so a bad file in the
  set fails fast without a partial apply.
- Print a per-file progress line and a final summary.

### `session import --new-session-id`

- Add a boolean flag `--new-session-id` to `session import`.
- When set and the bundle is a single-session bundle (has a `main_session_id`
  and one root), force id regeneration even without a collision: generate a
  fresh `ses_<uuid.hex>` conforming to opencode's id shape, and route through the
  EXISTING structural id-remap path used on collision (so all cross-table and
  in-diff references are rewritten consistently; this path already exists for the
  collision case in `extract_and_import_session`).
- Refuse with a clear error if the bundle is a project bundle (`kind == project`)
  or otherwise has more than one root session: "session-id rename applies to a
  single-session bundle only."
- Validate the generated id against the same `^[a-zA-Z0-9_\-]+$` guard already
  enforced on import; never accept user free text (no argument is taken).

---

## Tests

- restore: two valid archives apply in order; final state reflects the last.
- restore: file 2 invalid -> whole batch rolled back to the pre-batch state
  (assert state == original), file 1's changes NOT left applied, error names
  file 2.
- import `--new-session-id`: single-session bundle imports under a fresh
  `ses_...` id (different from the bundle's), all references remapped, diff file
  restored under the new id.
- import `--new-session-id` on a project bundle -> clear refusal.
- generated id matches the id format guard.

---

## Docs

- README + help: `backup restore FILE...` (multiple, all-or-nothing batch);
  `session import --new-session-id` (regenerates the id; single-session only).
- ARCHITECTURE: note the multi-file restore atomicity model and that import id
  regeneration reuses the collision remap path.

---

## Non-goals

- Merging/deduping across multiple restored archives (last-writer-wins per the
  existing single restore semantics).
- User-supplied arbitrary session ids (explicitly disallowed for safety).
