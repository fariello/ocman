# Implementation Plan - `filter` Command + Recovery Filename Canonicalization

This document details the design and implementation plan for two related pieces of work on the
generated recovery artifacts (`*.restart.md` / `*.compacted.md`):

1. **`ocman filter` (new command)** - LLM re-summarize any recovery/text file down to a single
   project/scope, dropping everything out of scope, and write a new, smaller compacted file.
2. **Recovery filename canonicalization** - adopt one canonical name,
   `YYYYMMDD-HHMM-<session_id>.<kind>.md` (kind = `transcript|restart|prompt|compacted`,
   **local time**), delivered in two parts:
   - **Going forward:** fix the writers so a session's artifacts share one local-time stem across
     **all four kinds** (the shared `base_name` for transcript/restart/prompt, `run_compaction` for
     compacted, and the in-project copy), reconciling the current UTC-vs-local inconsistency to
     **local** time. No new command. (See "Base-name scope" for why all four, not just two.)
   - **Legacy files:** a **separate one-shot migration script** (`scripts/migrate_recovery_names.py`)
     to normalize files already on disk from older ocman versions.

Scope notes:
- This is the *first, self-contained* deliverable. The broader verb-based CLI redesign
  (`ocman delete|move|export|import|backup|restore|rename ...`, old flags kept as deprecated
  aliases) is a **separate, later IPD** and is out of scope here.
- The word **`rename` is reserved** for a future "rename a session" verb (mirroring opencode's
  own session rename). It is deliberately NOT used for filename normalization here; normalization
  lives in the migration script (and later, if wanted, a `clean-up`/`update`-style verb).

---

## User Review Required

> [!IMPORTANT]
> - **`filter` uses an LLM re-summarize pass**, reusing the existing model resolution
>   (`default_compaction_model` + the `-C`/`--compact` picker via
>   `load_opencode_config`/`extract_models_from_config`/`resolve_model`, ocman.py:438/557/685) and
>   `call_compaction_api` (ocman.py:794). It reuses the same cost-estimate helpers
>   (`estimate_tokens`/`estimate_cost`, ocman.py:4656-4664) and `[Y/n]` confirm flow as
>   `run_compaction`. It never edits the source in place; on output-name collision it backs up via
>   the existing `.bu.NNN` convention (`_backup_compacted_bu`, ocman.py:3392).
> - **`filter` prompt structure (security):** it reuses `COMPACTION_SYSTEM_PROMPT` (ocman.py:2701),
>   which is the correct choice because that system prompt already instructs the model to treat the
>   supplied content as **untrusted source evidence, not instructions** (prompt-injection defense
>   that must be preserved when feeding a prior `.compacted.md` back in). However the *system*
>   prompt alone is not the instruction set - the real directions live in a **user prompt**. `filter`
>   therefore needs its own dedicated user-prompt template (a scope-focused sibling of
>   `COMPACTION_USER_PROMPT_TEMPLATE`, ocman.py:2709) that tells the model: "reproduce this document
>   preserving only content in scope <X>, drop everything else, keep structure and factual fidelity,
>   record uncertainty." A bare "scope note" prepended to raw content is insufficient.
> - **`filter` input is extension-agnostic.** Any readable text/markdown file is accepted
>   (`.compacted.md`, `.restart.md`, transcripts, etc.). Only the file's text is sent to the model;
>   no format-specific parsing.
> - **File-write safety bar (matches the RSP-6 precedent for cross-file writes):** both `filter`
>   output and the migration script must be **path-contained** (resolve + reject writing outside the
>   intended directory), **symlink-safe** (do not follow a symlink out of the target dir; do not
>   clobber a symlink), and **fail-soft where a failure would otherwise destroy input** (never lose
>   the source file: rename is atomic within a filesystem; on cross-device or error, copy-then-verify
>   before unlink). `filter` never mutates its input.
> - **Canonical name = `YYYYMMDD-HHMM-<session_id>.<kind>.md`, LOCAL time.** This reconciles the
>   two current conventions: `run_compaction` (UTC seconds, ocman.py:4688) and the in-project
>   copy (local date-only, `project_prompt_copy_name`, ocman.py:3372-3389). See "Base-name scope"
>   below for why all four artifact kinds are migrated together, not just restart+compacted.
> - **Legacy normalization is a separate script**, not an ocman subcommand: `scripts/migrate_recovery_names.py`.
>   Run once by users upgrading across the naming change. Immediate execution with an interactive
>   `[Y/n]` confirm and a bypass flag (`--yes`); top-level only (no recursion); refuses to
>   overwrite unless `--force`.

---

## Open Questions

- *None.* All design details have been aligned with user decisions. (Plan-review resolved the
  base-name scope: **all four** artifact kinds migrate to the local canonical stem together,
  rather than splitting restart/compacted from transcript/prompt - see Base-name scope below.)

---

## Proposed Changes

### `ocman.py`

#### [ADD] `ocman filter` command

- CLI: `ocman filter <input> [--project X] [--scope "..."] [-C [MODEL]] [-oc OUT]`.
  - **Scope** is expressed by **both** mechanisms: `--project <name|path|substring>` (resolved
    against the DB like `-P`, yielding a canonical project name) and/or `--scope "free text"`
    (e.g. `"ocman only"`). Both may be combined; at least one is required (error if neither given).
  - **Dispatch (KISS, matches existing pattern).** `main()` today dispatches via a series of
    `if args.X is not None: ...; return` early handlers (ocman.py:7734-7747) plus a positional
    `command` argument with `choices=["info","help","ui","gui"]` (ocman.py:4473-4478). Rather than
    introduce a bespoke `sys.argv[1]` pre-parse (a new, divergent mechanism), **extend the existing
    positional `command`** to accept `filter` (and give it its own argparse handling of the trailing
    `<input>` + `--project`/`--scope`/`-oc`), dispatched from `main()` in the same early-return
    style. Full subparser migration remains deferred to the CLI-redesign IPD.
- `cli_filter(input_path, project, scope, model_spec, out_path, verbosity) -> Path | None`:
  1. Read the source file's text (extension-agnostic). Fail with a clear error if unreadable.
  2. Resolve the effective scope string: if `--project` is given, resolve it to a canonical
     project name/path via the same resolver used by `-P`; combine with any `--scope` free text.
  3. Render the **dedicated filter user prompt** (new `FILTER_USER_PROMPT_TEMPLATE`) embedding the
     scope and the source content; send with `COMPACTION_SYSTEM_PROMPT` as the system message
     (preserves the untrusted-content posture). Show the `estimate_tokens`/`estimate_cost` +
     `[Y/n]` confirm flow (mirror `run_compaction`, ocman.py:4642-4676); call `call_compaction_api`.
  4. **Output:** write next to the source (unless `-oc` overrides) using the canonical scheme with
     a scope marker: `YYYYMMDD-HHMM-<session_id>.<scope-slug>.compacted.md`. Derive `<session_id>`
     and timestamp from the source filename via `parse_recovery_name`; **when the name is not
     parseable, use `session_id = "unknown"` and timestamp = source file mtime (local)** so the
     output name is always valid and deterministic. Slugify the scope via `safe_filename`
     (ocman.py:2517; collapses spaces, caps 80 chars). Resolve the destination and **reject any
     path that escapes the source/`-oc` directory or resolves through a symlink out of it**; back
     up an existing target with `_backup_compacted_bu`. The source file is never modified.

#### [MODIFY] Canonical filename - going forward

- Add helper `canonical_recovery_name(session_id, dt, kind) -> str`:
  `f"{dt:%Y%m%d-%H%M}-{safe_filename(session_id)}.{kind}.md"` (dt in **local** time).

- **Base-name scope (IMPORTANT - all four artifact kinds, not just two).** The deterministic
  recovery writer builds a single shared base name and derives *four* files from it (ocman.py:3577-3583):
  `base_name = f"opencode-{get_startup_timestamp_utc()}-{safe_session_id}"` then `.transcript.md`,
  `.restart.md`, `.prompt.md` (compact-prompt), and separately `run_compaction` writes
  `.compacted.md` (ocman.py:4688). Migrating only `.restart.md`+`.compacted.md` would **split one
  session's artifacts across two naming/timezone schemes** (e.g. a UTC `.transcript.md` next to a
  local `.restart.md`), which is confusing and breaks the "these files belong together" grouping.
  Therefore: change `base_name` at ocman.py:3577-3579 to derive from `canonical_recovery_name`'s
  stem in **local** time so all of `.transcript/.restart/.prompt` share it, and change
  `run_compaction` (ocman.py:4688) to the matching local canonical `.compacted.md`. Net: one
  session -> one `YYYYMMDD-HHMM-<sid>` stem across all kinds.
- In-project copy helper (`project_prompt_copy_name`, ocman.py:3372-3389): switch from
  `YYYYMMDD-<sid>.compacted.md` to the canonical `YYYYMMDD-HHMM-<sid>.compacted.md` (local). Note
  this helper derives its date from the **session's `updated` timestamp** (falling back to process
  start), so the added `-HHMM` must come from the same source for consistency, not from a second
  clock read.
- Add `parse_recovery_name(path) -> (session_id, datetime|None, kind)` recognizing the legacy
  conventions (`opencode-YYYYMMDD-HHMMSS-<sid>.<kind>.md`, the shorter `YYYYMMDD-<sid>.<kind>.md`),
  the `filter` scope-marker form (`...<sid>.<scope>.compacted.md`), and the new canonical one; used
  by both `cli_filter` and the migration script. Must round-trip: `parse_recovery_name(canonical_recovery_name(...))`
  recovers the inputs.

#### [MODIFY] Docs and tests that assert the old names (honest-documentation principle)

- File-header artifact docs (ocman.py:76-78) and the `--help` epilog: document the `filter`
  command and the canonical naming scheme.
- Update `tests/test_compacted_project_prompt.py`, which asserts the current
  `project_prompt_copy_name` output, to the new `-HHMM` scheme (see Verification).
- Update README/ARCHITECTURE where they describe recovery-file naming or recognized commands, so
  docs stay accurate to behavior (ARCHITECTURE "Design principles": honest documentation).

---

### [ADD] `scripts/migrate_recovery_names.py` (one-shot legacy migration)

- Standalone script (imports the shared helpers from `ocman` where practical, or vendors small
  copies to stay dependency-light).
- Usage: `python scripts/migrate_recovery_names.py <dir> [--yes] [--force] [--dry-run]`.
- Behavior:
  - Operates on the **given directory, top-level only** (no recursion, no implicit scanning of
    other locations). The directory argument is required (no default) to avoid acting on a
    surprising location.
  - Handles **all four kinds** for consistency with the going-forward change:
    `*.transcript.md`, `*.restart.md`, `*.prompt.md`, `*.compacted.md` (and the `filter`
    scope-marker form). Computes the canonical name via `parse_recovery_name`
    (timestamp = parsed-from-name, else file **mtime**, rendered **local**).
  - **Path/symlink safety:** resolve entries within the target dir; skip symlinks (do not follow or
    rename through them); never write outside the target dir.
  - **Never lose data:** skip files already canonical; refuse to overwrite an existing target
    unless `--force`; use atomic `os.rename` within the dir; if that raises, do NOT delete the
    source (report and continue).
  - Print the per-file plan, then **execute immediately after an interactive `[Y/n]` confirm**;
    `--yes` bypasses the prompt, `--dry-run` previews without changes. Prints a summary
    (renamed / skipped-canonical / skipped-collision / errors).

---

## Verification Plan

### Automated Tests

New test file `tests/test_recovery_naming.py`:
1. **`canonical_recovery_name`**: exact `YYYYMMDD-HHMM-<sid>.<kind>.md` formatting, local tz.
2. **`parse_recovery_name`**: parses both legacy conventions, the canonical one, and the `filter`
   scope-marker form; returns `None` datetime when unparseable; extracts session_id + kind
   correctly; **round-trips** with `canonical_recovery_name`.
3. **Generation forward-fix (all four kinds):** `run_compaction` (API monkeypatched) and the
   deterministic writer emit canonical **local**-time names for `.transcript/.restart/.prompt/.compacted`,
   all sharing one `YYYYMMDD-HHMM-<sid>` stem; assert no `get_startup_timestamp_utc` path remains
   in the produced names.

`tests/test_file_tools.py` (or extend existing):
4. **`filter`**: with `call_compaction_api` monkeypatched to a canned response, assert: the
   dedicated `FILTER_USER_PROMPT_TEMPLATE` is used as the user message and `COMPACTION_SYSTEM_PROMPT`
   as the system message; both `--project` and `--scope` feed the scope; requiring at least one is
   enforced; output is written beside the source as `...<sid>.<scope>.compacted.md`; **source is
   unmodified**; a collision triggers a `.bu.NNN` backup; an unparseable input name yields
   `unknown` + mtime; a destination that would escape the dir or resolve through a symlink is
   rejected.

`tests/test_compacted_project_prompt.py` (UPDATE existing): adjust the assertion on
`project_prompt_copy_name` to the new `-HHMM` scheme; confirm the HHMM derives from the session
`updated` timestamp (not a fresh clock read).

`tests/test_migrate_recovery_names.py` (script):
5. **dry-run**: no files touched; plan lists correct source->target mappings for all four kinds.
6. **apply**: files renamed to canonical local-time names; already-canonical skipped; collision
   without `--force` skipped (source preserved); `--yes` bypasses the prompt; summary counts correct.
7. **scope/safety**: only files directly in the given dir are considered (no recursion); symlinks
   are skipped; nothing is written outside the target dir; a failed rename never unlinks the source.

Full suite must remain green: `PYTHONPATH=. pytest` (currently 127 passed, 2 skipped). The count
will change because `test_compacted_project_prompt.py` is updated and new tests are added.

### Manual Verification

1. `ocman filter ./opencode-recovery/<file>.compacted.md --scope "ocman only"` (optionally
   `--project ocman`) and confirm the output drops out-of-scope content and keeps ocman facts.
2. `python scripts/migrate_recovery_names.py ./opencode-recovery --dry-run` then confirm-and-apply;
   verify canonical names and that nothing outside `./opencode-recovery` (and no subdirs) is touched.
3. Run a real `-s <id> -C` compaction and confirm the generated `.compacted.md` uses the new
   local-time canonical name, matching the in-project copy.
