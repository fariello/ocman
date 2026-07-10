# Implementation Plan 02 - Batch multi-target resolver & ambiguity engine

Status: PROPOSED (not yet executed)

Foundation for the multi-target work. Introduces a single place that turns a
list of raw user specs into resolved targets (sessions, projects, models),
validates the whole set up front, and handles no-match / ambiguity with a
consistent, user-friendly policy. This is IPD 02 in the execution order; it uses
`resolve_model_spec` from IPD 01 and is depended on by IPD 03.

---

## Motivation

Several requested features (multi-session compact/recover/show/delete,
"all sessions in a project", model matching for compact, strict no-match and
ambiguity reporting) share one need: resolve many specs at once, classify each,
and fail helpfully before doing anything. Today resolution is single-spec,
returns `None`/`"ambiguous"` silently, and runs during arg normalization
(`_apply_move_or_export`, `ocman.py:5473`; `resolve_target`, `ocman.py:4520`;
`resolve_session_spec`, `ocman.py:4461`), which cannot prompt or print rich
errors.

---

## User Review Required

> [!IMPORTANT]
> - Resolution moves OUT of the parse/normalize layer INTO the command handlers
>   in `main()` (decided in review): normalization only captures the raw spec
>   list; handlers resolve so they can prompt on a TTY and print rich errors.
> - Common case stays friction-free: kind is auto-detected. The user is only
>   ever bothered when a spec is genuinely ambiguous.
> - Ambiguity policy: on a TTY, prompt the user to choose; non-interactively,
>   exit with a verbose error naming the offending spec(s) and how to override.
> - Deterministic override for scripts and disambiguation: kind-qualified specs
>   `session:SPEC`, `project:SPEC`, `model:SPEC` force interpretation with no
>   prompt, and work everywhere (interactive or not).

---

## Design

### New: `resolve_targets(specs, *, kinds, allow_project_expansion, interactive)`

A batch resolver returning a structured result. `kinds` is the set a given
command accepts (e.g. compact accepts `{session, model, project}`; delete accepts
`{session, project}`).

- **Kind-qualified prefix.** A spec is treated as kind-qualified ONLY when it
  begins with exactly `session:`, `project:`, or `model:` (the whole leading
  token before the first colon equals one of those three words). Any other colon
  is left untouched, so session titles containing a colon ("Fix: the bug"),
  Windows-style paths (`C:\...`), and `provider/model:variant` forms are NOT
  mis-parsed. When qualified, the prefix is stripped and only that kind is
  matched (no ambiguity, no prompt). This is the non-TTY override.
- **Auto-detect.** Otherwise, match `rest` against each allowed kind:
  - session via `resolve_session_spec` (id, list number, title substring),
  - project via `resolve_project` (id, number, path, substring),
  - model via a NEW `resolve_model_spec` (see IPD 01; exact
    `provider/model`, `model.name`, or unique substring over
    `extract_models_from_config`, `ocman.py:585`).
- **Outcomes per spec:** exactly one match across allowed kinds -> resolved;
  zero matches -> `unmatched`; more than one match (within or across kinds) ->
  `ambiguous` (carrying the candidate list).
- **Bare integer** stays kind-specific and is only accepted with a qualifier or
  when the command accepts a single kind; otherwise it is `ambiguous` (preserves
  current `resolve_target` guard, `ocman.py:4539`).

### Ambiguity / no-match handling (single policy, reused everywhere)

Given the full classified set, BEFORE any action:

1. **Any `unmatched`:** print each offending spec and the suggestion to run
   `ocman list sessions` / `ocman list projects` / `ocman list models` (whichever
   kinds the command accepts). Exit non-zero. No action taken.
2. **Any `ambiguous`:**
   - On a TTY: for each ambiguous spec, print the candidates and prompt the user
     to choose one (or re-enter). If the user cancels, abort with no action.
   - Non-TTY: print each offending spec with its candidates and the suggestion
     to use the full model name and the exact `ses_XXXX` id, or the
     `session:`/`project:`/`model:` qualifier; add the note "if that does not
     resolve it, please file a bug report." Exit non-zero, telling the user to
     re-run on a TTY or pass a qualifier.
3. **Project expansion** (only when `allow_project_expansion` and a spec resolves
   to a project): expand to the project's sessions (root-only by default; all
   with `-A`), via `db_list_sessions(project_id)` filtered like
   `list sessions` (`ocman.py:10293`).

The resolver never prints secret/sensitive data. Candidate previews show id +
truncated title only.

### Performance (fetch candidate lists once per batch)

`resolve_target` today calls `db_list_sessions(None)` per spec (`ocman.py:4546`),
which returns EVERY session (expensive on a multi-GB DB). `resolve_targets` MUST
fetch each needed candidate list at most once for the whole batch:
`db_list_sessions(None)` (sessions), `db_list_projects()` (projects), and
`extract_models_from_config(load_opencode_config())` (models), then classify all
specs against those in-memory lists. Only fetch a list if `kinds` includes it.

### Where it lives / refactor

- Add `resolve_targets(...)` and a small `TargetSet` result type near
  `resolve_target` (`ocman.py:4520`).
- Move the per-command resolution calls into `main()` handlers (after parse).
  `_apply_move_or_export` (`ocman.py:5473`) and `_apply_search`
  (`ocman.py:5382`) stop resolving during normalization; they only stash raw
  specs. This also fixes the latent bug that normalization-time resolution
  cannot prompt and ran before `--db` in earlier code (see the executed
  directory-scoping/`--db` fixes).

### Characterization (rubric D)

`resolve_target`, `resolve_session_spec`, and `resolve_project` currently back
`move`/`export`/`search`-scope. Before refactoring, pin their current behavior
with tests (single-spec move/export/search still resolve identically), green
after. Do not change single-spec outcomes.

---

## Tests

- Kind-qualified `session:`/`project:`/`model:` force the kind with no prompt.
- Auto-detect: unique session, unique project, unique model each resolve.
- Unmatched: offending specs printed + correct `list ...` suggestion; non-zero
  exit; nothing acted on.
- Ambiguous non-TTY: offending specs + candidates + qualifier/full-id suggestion
  + bug-report note; non-zero exit.
- Ambiguous TTY: prompt selects a candidate (input mocked); cancel aborts.
- Bare integer without a single accepted kind is ambiguous.
- Project expansion yields root sessions (and all with `-A`); empty project is a
  clear error.
- Regression: existing single-spec move/export/search resolve unchanged.

---

## Docs

- ARCHITECTURE: document `resolve_targets`, the kind-qualified prefix, and that
  resolution happens in handlers (not normalization).
- README/help: document `session:`/`project:`/`model:` qualifiers where specs
  are accepted.

---

## Non-goals

- Changing single-spec UX for commands not listed in IPD 03.
- Fuzzy/typo-tolerant matching beyond today's substring behavior.
