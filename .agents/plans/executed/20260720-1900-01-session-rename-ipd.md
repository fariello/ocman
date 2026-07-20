# IPD: rename a session from the command line

- Date: 2026-07-20
- Concern: feature (CLI: set a session's display title)
- Scope: `ocman/cli.py` (new `session rename` action + top-level `rename` sugar +
  `db_rename_session` helper + preprocess sugar + help), tests, README, CHANGELOG. No TUI in
  this IPD (a TUI retitle modal is deferred). No DB schema change.
- Status: executed (2026-07-20)
- Target version: part of the in-flight 1.3.0 line (candidate `v1.3.0-rc1` already cut; this
  adds to it, so the next candidate is `v1.3.0-rc2`; final `1.3.0` still gated on a
  release-review and explicit maintainer GO, per the standing "not promoting yet" decision).
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-20 created (its_direct/pt3-claude-opus-4.8): from a maintainer request to rename a
  session from the CLI. Syntax + safety settled via Q&A (see Design decisions).

## Goal

Let a user change a session's human-readable **title** (the `session.title` column) from the
command line. Today nothing in ocman (CLI or TUI) writes `session.title`; this is a net-new
capability.

## Design decisions (settled with maintainer)

- **Surfaces (both):**
  - Canonical: `ocman session rename <SESSION> --to "New title"` (mirrors `session move`).
  - Top-level sugar: `ocman rename <SESSION> to "New title"` and `ocman rename <SESSION> "New title"`.
- **`<SESSION>` specifier:** the SAME resolution every session command uses
  (`resolve_session_spec`): list number from `ocman ls`, `ses_...` id, or a unique
  case-insensitive title substring. Ambiguous/no-match reports candidates (interactive) or a
  clear error (non-interactive), never a silent guess.
- **New title validation:** any non-empty string; trim surrounding whitespace; reject
  empty/whitespace-only. No length cap, no newline stripping (titles are free-form display
  text; keep it KISS and consistent with how OpenCode itself treats titles).
- **Safety:**
  - Guard the DB mutation with `require_safe_to_mutate("rename session", ...)` (cli.py:7821),
    with `--force` / `--while-running` escape, exactly like other DB mutations. That guard
    already prints the running listing AND does its own typed-'yes' confirm in the
    while-running path, so the rename does NOT add a second typed-yes prompt (avoid
    double-prompting).
  - **Honesty note (maintainer MUST):** the running-guard is about the DATABASE AS A WHOLE.
    OpenCode does NOT record which process is attached to which session, so ocman CANNOT tell
    whether the SPECIFIC target session is in use. The rename's preview/guard text must say so
    plainly (e.g. "ocman cannot tell if this particular session is open in OpenCode; the check
    above is for the database as a whole"). Do not imply per-session safety.
  - Always print a clear `Renamed: "<old>" -> "<new>" (<ses_id>)` line on success.
  - `--dry-run` prints the intended change and makes no write.
  - Transaction envelope (BEGIN / UPDATE / commit; rollback + RecoveryError on error;
    close in finally), template `db_move_session_metadata` (cli.py:9834). A physical rollback
    backup is NOT required for a single-column reversible title change (KISS); the transaction
    envelope is sufficient. (If review disagrees, the safe upgrade is to add
    `db_create_rollback_backup()`; recorded as the fallback.)

## Project conventions discovered (Step 0)

- Guiding principles: universal fallback. No em/en dashes in authored prose. Plans:
  `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`.
- Contract: path-scoped commits, never push without approval, paste REAL pytest output.
- `session.title` is read at cli.py:4152/4163/4176 (via `db_list_sessions`), 4519/4524
  (`db_find_session_by_title_or_id`), 4546/4600 (single-session detail). NO existing write.
- Session actions registered under `p_session`/`s_sub` via `new_action` (cli.py:6205, 6211-6212).
  Single-target mutating commands (`export` 6274, `move` 6291) take a `session` positional +
  required `--to`. `move` is the closest analog.
- Specifier resolution: `resolve_session_spec` (cli.py:5003; number/id/title-substring),
  `resolve_targets` (5129), `resolve_and_expand_targets` (5252; exits on unmatched
  non-interactively). `db_find_session` used by single-target `move` (cli.py:15151).
- `move`/`export` `to`-keyword sugar strips EVERY `to` (cli.py:5861-5863) because a path never
  contains "to"; a TITLE can ("... to use tokens"), so rename needs a POSITIONAL-AWARE strip
  (only a standalone leading `to` between spec and title), like the `backup create` block
  (cli.py:5864-5874). Do NOT reuse the blanket move/export strip for rename.
- Mutation safety: `require_safe_to_mutate` (7821); transaction template
  `db_move_session_metadata` (9834); `db_create_rollback_backup` (9061).
- Top-level `move` sugar shape: `new_sub("move")` with `kind`/`spec`/`dst`/`--to` (6397-6411),
  normalized by `_apply_move_or_export` (6592). `rename` top-level mirrors a subset.

## Findings / requirements

| ID | Requirement | Evidence |
|----|-------------|----------|
| RN-01 | `session rename <S> --to "title"` updates `session.title` | no writer exists; move template cli.py:9834 |
| RN-07 | handler needs the OLD title (for `old -> new` preview + unchanged no-op), but `db_find_session` returns only `(id, directory, project_id)` (cli.py:9739-9751), NO title | `db_find_session` cli.py:9739; title read paths cli.py:4152/4176 |
| RN-02 | top-level `rename <S> [to] "title"` sugar, positional-aware `to` strip | move/export blanket strip unsafe for titles (cli.py:5861-5863) |
| RN-03 | resolve `<S>` via the standard resolver (number/id/title-substring) | resolve_session_spec cli.py:5003 |
| RN-04 | guard-while-running + honest "no per-session tracking" note; typed-yes only via the guard | require_safe_to_mutate cli.py:7821 (already prompts while-running) |
| RN-05 | non-empty trimmed title; reject empty/whitespace-only | new validation |
| RN-06 | `--dry-run` (no write), success line `old -> new`, `--force`/`--while-running` | move flags cli.py:6291-6302 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | RN-01,RN-07 | Add `db_rename_session(session_id: str, new_title: str) -> str` that RETURNS THE OLD TITLE (resolving RN-07, since `db_find_session` lacks title): open conn; `BEGIN`; `SELECT title FROM session WHERE id = ?` (fetch old title; if no row, rollback + `RecoveryError("session not found: <id>")`); `UPDATE session SET title = ? WHERE id = ?` (title is a BOUND `?` parameter, NEVER string-formatted, RN-04-sql); commit; return the old title. On error rollback + raise `RecoveryError`; close in finally. Read-then-update in ONE connection/transaction so the reported old title is the value actually replaced (no race). Template: `db_move_session_metadata` (cli.py:9834). | cli.py | Low | unit test: returns old title + new title persisted; missing id raises; other rows untouched; title bound not interpolated |
| 2 | RN-01,RN-03,RN-06 | Register `session rename` action (near cli.py:6291): positional `session` (required), positional `dst` (nargs="?", the new title), `--to` (dest `to_flag`, hidden or shown), `--dry-run`, `--force`, `--while-running`, `-y/--yes`. Normalize (near cli.py:6735) to `out["rename_session"]=g("session")`, `out["rename_to"]=g("to_flag") or g("dst")`. | cli.py | Low | argparse accepts `session rename S --to T` and `S T` |
| 3 | RN-02 | Top-level `rename` sugar: `new_sub("rename")` with `spec` + `dst` (nargs="?") + hidden `--to`; normalize to the same `rename_session`/`rename_to`. In `preprocess_argv`, REUSE THE EXACT `backup create` idiom (cli.py:5864-5874) for `rename`: walk tokens and convert a standalone `to <next>` (where `<next>` is not a flag) into `--to <next>`. Because the title is always a SINGLE argv token (a shell-quoted `dst`), this converts only the keyword `to` that precedes the title and never touches a `to` INSIDE the title. Do NOT use the blanket move/export strip (cli.py:5861-5863). | cli.py | Medium | `rename S to "a to b"` -> title "a to b"; `rename S "x"` works; `rename S to x` works; the `to` inside a quoted title survives |
| 4 | RN-01,RN-03,RN-04,RN-05,RN-06,RN-07 | Handler: resolve `<S>` to a single session id (via `resolve_and_expand_targets`/`db_find_session`); validate new title (`.strip()`; reject empty/whitespace-only -> `RecoveryError` with a usage hint); `require_safe_to_mutate("rename session", while_running=force_or_flag, interactive=..., verbosity=...)`; print the honest caveat that ocman CANNOT tell if THIS session specifically is open (OpenCode does not track process<->session; the guard covers the DB as a whole); if `--dry-run`, print the intended `"<old>" -> "<new>"` and return WITHOUT writing (get old title via a read, or via a dry `db`-less SELECT); else call `old = db_rename_session(id, new)`; if `old == new` (exact, case- and whitespace-sensitive) print "unchanged" (still exit 0); print `Renamed: "<old>" -> "<new>" (<id>)`. Note: the unchanged check is exact so a capitalization-only rename (e.g. "fix" -> "Fix") DOES write. | cli.py | Medium | rename by id/number/title; dry-run writes nothing; empty title rejected; capitalization-only rename writes; success prints old->new |
| 5 | RN-01..06 | Help text: add `session rename` to the reference/help lists and a top-level `rename` example in the browse overview; document `--to`, `--dry-run`, `--force`. | cli.py | Low | `ocman help` shows rename |
| 6 | all | CHANGELOG `[1.3.0]` Added entry (rename); README command reference. | CHANGELOG.md, README.md | Low | docs accurate |

## Deferred / out of scope

- **TUI retitle modal:** deferred to a separate IPD (this is CLI-only). Note it as a known
  follow-up so CLI/TUI parity stays tracked.
- Renaming multiple sessions at once / batch rename: out of scope (single-target, like move).
- Editing `slug` or any other column: out of scope; rename touches `title` only.
- Templated/auto titles (e.g. from first message): out of scope.

## Anti-regression / invariants

- No existing command changes behavior; this is purely additive (new action + new top-level verb).
- The blanket move/export `to`-strip (cli.py:5861-5863) is NOT modified; rename gets its own
  positional-aware strip so titles containing "to" survive.
- `require_safe_to_mutate` semantics unchanged; rename is just a new caller.
- Only `session.title` is written; `slug`/`directory`/`project_id` untouched.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE ACTUAL output.
- New tests: `db_rename_session` (RETURNS the old title; persists the new title; missing id
  raises `RecoveryError`; other rows untouched; title passed as a bound `?` param, e.g. a title
  containing a quote or `;` is stored verbatim, proving no string interpolation);
  `session rename S --to T` end-to-end (by id, by list number, by title substring); top-level
  `rename S to "a to b"` PRESERVES the literal title "a to b" (the positional-aware-strip
  regression test); `rename S "x"` and `rename S to x`; empty/whitespace title rejected;
  capitalization-only rename ("fix" -> "Fix") DOES write; `--dry-run` makes no DB change;
  running-guard path is exercised (mocked running state) and the honest "cannot tell if this
  session specifically is in use" caveat text is present in output.
- Cross-platform: no path seeding needed here (title-only); no new skips. Use `abs_path` only
  if a test seeds a project/session directory.

## Spec / documentation sync

- CHANGELOG `[1.3.0]` Added: "Rename a session from the CLI (`session rename` / `rename ... to`)".
- README: add to the session command reference + the alias/word-order list.
- Help text (`build_help` overview + reference).

## Open questions

None. Syntax, validation, and safety settled with maintainer; the per-session-tracking honesty
requirement is captured as RN-04. The one /plan-review finding-driven question (how the handler
obtains the OLD title, since `db_find_session` lacks it) was resolved from repository evidence:
`db_rename_session` returns the old title from an atomic read-then-update (RN-07), not the human.

## Workflow history

- 2026-07-20 created (its_direct/pt3-claude-opus-4.8): authored from maintainer request.
- 2026-07-20 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED.
  PR-001/RN-07 (db_find_session returns no title -> db_rename_session now returns the old title
  via atomic read-then-update), PR-002 (reuse the exact `backup create` positional `to`->`--to`
  idiom rather than a bespoke strip), PR-003 (rowcount==0 is a defensive not-found guard;
  transaction-safe), PR-004 (title is a bound `?` param, never interpolated; + a stored-verbatim
  test). No open questions; no unfixed BLOCKER/HIGH. GO - PENDING HUMAN APPROVAL.
- 2026-07-20 approved by maintainer; executed (its_direct/pt3-claude-opus-4.8). All 6 steps done.

## Post-execution summary

- Step 1: `db_rename_session(session_id, new_title) -> str` added after `db_move_session_metadata`.
  Atomic read-then-update in one transaction: SELECTs the old title (raises
  `RecoveryError("Session not found: <id>")` if absent), UPDATEs `title` via a BOUND `?` param,
  commits, returns the old title; rollback + raise on error; close in finally.
- Step 2: `session rename` action (session positional + optional `dst` + `--to` (dest `to_flag`)
  + `--dry-run`/`--while-running`/`--force`/`-y`); normalized to `rename_session`/`rename_to`.
- Step 3: top-level `rename` sub (spec + dst + hidden `--to` + same flags), normalized identically
  (uses `g("spec")` and deliberately does NOT set `out["spec"]`, so the top-level move/export
  spec-resolver does not mis-route it, verified). `preprocess_argv` extends the `backup create`
  positional `to <next>`->`--to <next>` idiom to `rename` and `session rename`; a `to` inside a
  single quoted title token is preserved.
- Step 4: handler after `move_session`: validate (`.strip()`, reject empty), resolve via
  `resolve_and_expand_targets(kinds={"session"})`, `require_safe_to_mutate("rename this session",
  while_running=force_or_while)`, ALWAYS print the honest "OpenCode does not track which process
  uses which session ... check is for the database as a whole" caveat, `--dry-run` short-circuits,
  else `old = db_rename_session(...)`, unchanged-title no-op (exact compare), then
  `Renamed: "<old>" -> "<new>" (<id>)`.
- Step 5: help text (browse overview, session reference, other-verbs).
- Step 6: CHANGELOG `[1.3.0]` Added (rename) + README session table + top-level verbs table.
- Tests: 11 new (db_rename_session return/missing/bound-param; e2e by id/number/title; top-level
  `to`-in-title preserved; positional-without-`to`; empty rejected; capitalization-only writes;
  dry-run no write; running-guard caveat printed). Full suite: **426 passed, 2 skipped** (was 415).
- Release: rides the 1.3.0 line; NOT promoted to final `1.3.0` (maintainer still adding features).

## Approval and execution gate

- Execution checklist (MUST): before coding, create a TodoWrite step-granular checklist tracking
  each of Steps 1-6, the new tests (incl. the "title containing 'to'" regression), the
  full-suite run with pasted output, README+CHANGELOG+help sync, the path-scoped commit(s), and
  the Status-executed + `git mv` to `executed/`.
- Scope fence: ONLY the rename surface (db_rename_session, session rename action + top-level
  rename sugar + preprocess strip, help, README/CHANGELOG, tests). No TUI, no DB schema, no new
  runtime dependency, no change to move/export sugar.
- Honesty rule (hard MUST): paste ACTUAL `pytest -q` output; never claim a pass not run. AND
  the product-level honesty MUST (RN-04): never imply ocman can tell if the specific target
  session is in use.
- Commits: path-scoped, NEVER push without approval, NEVER tag outside an approved release step.
- Lifecycle: on completion set `Status: executed` and `git mv` this IPD to `executed/`.
- Release: this rides the 1.3.0 line; do NOT promote to final `1.3.0` (maintainer is still
  adding functionality). A refreshed candidate (`v1.3.0-rc2`) may be cut after green CI on
  explicit request.

Next: human review (optionally `/plan-review`) sets `Status: approved`; then execute per the above.
