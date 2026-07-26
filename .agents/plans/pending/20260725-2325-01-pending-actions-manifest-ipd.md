# IPD: defer destructive actions to a "pending" manifest when OpenCode is running

- Date: 2026-07-25
- Concern: feature (CLI + TUI) - deferred-action queue for while-running-guarded deletes
- Scope: `ocman/cli.py`, `ocman_tui/` (banner + Pending tab), `tests/test_ocman.py`,
  `tests/test_tui.py`, `README.md`, `CHANGELOG.md`, `TODO.md`
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-25 created (its_direct/pt3-claude-opus-4.8-1m-us): design decided interactively with the
  maintainer (scope, replay-safety, surfacing, manifest location); this IPD captures the agreed shape.
- 2026-07-25 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-01..PR-05. Gated the defer offer per-caller so it does not leak into the 5 non-deferrable callers of the shared require_safe_to_mutate (PR-01, HIGH); pinned pending_path to the config-driven history sibling (PR-02); added schema-version/corruption tolerance (PA-10), concurrent-append safety (PA-11), untrusted-input handling (PA-12), and an anti-regression clause for the shared guard. PA-06 and PA-03 open questions resolved with maintainer.

## Goal
Let a user who tries a cleanup that is blocked while OpenCode is running (deleting a session, etc.)
DEFER it to a pending manifest instead of having to remember it or kill every OpenCode. Later, when
nothing is running, `ocman pending run` replays each deferred action with the SAME preview + confirm/
`--yes` it would have had if run fresh. Every `ocman` invocation reminds the user of the count, and
the TUI surfaces it. Convenience without giving up any of today's safety.

## Design decisions (RESOLVED with maintainer 2026-07-25)
- SCOPE = the DELETE-family only: `session delete`, `project delete`, `db clean`,
  `db clean-orphans`. Other while-running-guarded mutating commands (`rename`, `move`, `db rebase`,
  `reclaim`) are OUT OF SCOPE here and are recorded as future work in TODO.md (step 9).
- REPLAY SAFETY = at drain time, per item RE-RESOLVE against the current DB, RE-PREVIEW, and
  RE-CONFIRM (honor `--yes` to skip only the typed prompt, never the re-resolution). A target that
  no longer exists (or whose identity changed) becomes a logged no-op / skip-with-warning, never a
  blind delete.
- SURFACING = every `ocman` run prints `[NOTIC] X items pending` when the manifest is non-empty
  (NOTIC yellow, brackets NOT colored, mirroring `info_prefix()` at cli.py:194; NOTIC = yellow,
  not bold, matching DOCTOR_NOTICE at cli.py:13759). `ocman pending` shows the detailed list. The
  TUI shows a banner with counts and a dedicated Pending tab. NEVER auto-runs.
- MANIFEST LOCATION = one GLOBAL file `ocman_pending.json` in the OpenCode DATA dir (default
  `~/.local/share/opencode/`, honoring `XDG_DATA_HOME`), resolved like `ocman_history.json`
  (cli.py:311). Rationale: it is machine-generated STATE tied to a specific DB, not user config, so
  it belongs beside `opencode.db`/`ocman_history.json` in `share/`, NOT in `~/.config/opencode/`
  (which holds hand-authored config: `opencode.json`, `ocman.toml`). It travels with the DB under
  `--db`/data-dir resolution; a config-dir file would not.
- DRAIN GATE = `ocman pending run` FIRST re-checks running instances via the existing
  `require_safe_to_mutate` and refuses to drain if any OpenCode is up (override `--while-running`,
  matching today's guard). On non-Linux where detection is limited, it warns it cannot fully verify
  and requires an explicit confirmation.

## Evidence
- Single choke point for the while-running refusal: `require_safe_to_mutate(action, *,
  while_running, interactive, verbosity)` (cli.py:7934); its "running + interactive TTY" branch
  (cli.py:7984-7991) prompts "Type 'yes' to {action} anyway" and its non-interactive branch raises
  RecoveryError (cli.py:7981). This is where the "or [p] add to the pending list" offer hooks in,
  so all four delete-family commands gain the option through ONE function, not four edits.
- Delete-family implementations (each already calls the guard + `confirm_destructive`):
  `db_delete_session_recursive` (cli.py:8207), `db_delete_project_recursive` (cli.py:8937),
  `db_run_cleanup` (cli.py:11072, covers both `db clean` and `db clean-orphans` via its
  `clean_orphans` arg). `confirm_destructive` is the re-preview/re-confirm primitive to reuse at
  drain time (cli.py, used at 8319/9059/9666/9771/11323).
- Dispatch keys for the eligible commands: session `delete` (cli.py:6798/6843), `db clean`
  (6866/6907), `db clean-orphans` (6876-6877).
- Prefix style to mirror: `info_prefix()` (cli.py:194) returns `f"[{color_green('INFO')}]"`; the
  new `notice_prefix()` returns `f"[{color_yellow('NOTIC')}]"`.
- Manifest neighbor: `history_path` default `~/.local/share/opencode/ocman_history.json`
  (cli.py:311); data-vs-config split confirmed (config: cli.py:218-224; data: cli.py:310-314).

## Requirements
| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| PA-01 | A `notice_prefix()` yellow NOTIC tag | Add `def notice_prefix() -> str: return f"[{color_yellow('NOTIC')}]"` next to `info_prefix()`; color-gated the same way. | cli.py:194 |
| PA-02 | Pending manifest storage layer | New `pending_path()` derived the SAME config-driven way as history (NOT hardcoded): a sibling of `OPENCODE_HISTORY_PATH` (cli.py:409, itself from `_loaded_config["history_path"]`), i.e. `OPENCODE_HISTORY_PATH.parent / "ocman_pending.json"`, so `--db`/relocated-data-dir users get a manifest next to the DB/history they are actually using. `load_pending()`/`save_pending()` reuse the history ledger's ATOMIC temp-file+replace pattern (cli.py:11774-11793). Schema (versioned, see PA-10): a top-level `{schema: 1, items: [...]}` where each item is `{id (uuid4), action: "session-delete"|"project-delete"|"db-clean"|"db-clean-orphans", target: <spec/id>, snapshot: {title, preview_summary}, args: {force/extracts/older_than/... as needed per action}, queued_at: <iso8601>, queued_from_cwd}`. Structured intent, NOT a raw shell string, so drain can re-resolve and detect staleness. | cli.py:311, 409, 11774-11793 (history model) |
| PA-03 | Offer "add to pending" at the running-guard, GATED per caller | `require_safe_to_mutate` is a SHARED guard called by 9 sites (cli.py:7999/9653/10097/10434/10770/13370/15136/15904 + the delete path), only 4 of which are in scope. So the offer MUST be opt-in per caller, NOT unconditional, or it leaks to out-of-scope actions (rebase/import/restore/rename/move) that have no manifest schema. Add an optional param, e.g. `pend_item: "PendingItem | None" = None` (the fully-built structured item the caller wants queued). ONLY when `pend_item is not None` AND state=="some": (a) interactive -> add a `[p]` choice to the prompt ("OpenCode is running. Type 'yes' to {action} now, [p] to add it to the pending list, or anything else to cancel"); (b) non-interactive with `--pend` -> auto-add-to-pending. Adding appends the item and returns a sentinel (e.g. the string `"pended"`) so the caller records-and-exits WITHOUT acting; the current `-> None` return contract stays for every existing caller (they pass no `pend_item`, get identical behavior). The 5 out-of-scope callers are UNCHANGED. | cli.py:7934 (returns None today), 7968-7991 (prompt), 9 call sites |
| PA-04 | `--pend` flag on the four eligible commands | Add `--pend` to `session delete`, `project delete`, `db clean`, `db clean-orphans` (help: "If OpenCode is running, add this action to the pending list instead of refusing (run later with 'ocman pending run')."). Wire each command to build its structured item and hand it to the guard as `pend_item`. | dispatch 6798/6843/6866/6876 |
| PA-05 | `[NOTIC] X items pending` on every run | At the start of `main()` (after arg parse, before dispatch), if `load_pending()` is non-empty, print one line `f"{notice_prefix()} {n} item(s) pending (run: ocman pending run)"`. Suppressed for `--json` output and for the `pending` command itself (which shows its own detail). | main() dispatch |
| PA-06 | `ocman pending` command family | New top-level `pending` with actions: `list` (default; detailed table: #, action, target, queued-at, queue-time title, staleness marker), `run` (drain; see PA-07), `clear` (remove all or by index, with confirm). Register via `new_sub`; add to top-level help + `help` topics. | parser build ~cli.py:6199+ |
| PA-07 | `pending run` drains safely | (1) Re-check running instances via `require_safe_to_mutate("run pending actions", while_running=args.while_running)`; refuse if any up (non-Linux: warn + explicit confirm). (2) For each item in queue order: re-resolve the target against the CURRENT DB; if gone/changed-identity -> print a NOTIC skip and drop the item; else call the SAME delete path with `confirm_destructive` re-preview and the per-item confirm (honor `--yes` for the prompt only). (3) Remove successfully-run and vanished items; KEEP items the user declined at re-confirm. Print a summary (done / skipped / kept). | require_safe_to_mutate 7934; confirm_destructive; db_delete_* 8207/8937; db_run_cleanup 11072 |
| PA-08 | TUI banner + Pending tab | Add a count to a startup banner (or the footer/overlay area) and a `Pending` tab listing the manifest items (read-only view + a "Run pending" affordance that shells the same drain path with confirmation). Follows the existing tab/overlay patterns; isolated `OCMAN_CONFIG_PATH` in tests. | ocman_tui/app.py tabs |
| PA-09 | Document deferred future scope | In TODO.md, record that `rename`, `move`, `db rebase`, and `reclaim` are candidate future additions to the pending mechanism (same safety model), deferred from this IPD. | TODO.md |
| PA-10 | Schema version + corruption tolerance (data integrity) | The manifest carries `schema: 1`. `load_pending()` must tolerate a missing/empty/corrupt file (return an empty list, like `_load_history` at cli.py:11737-11772) and an UNKNOWN `schema` or malformed item (skip-with-NOTIC, never crash and never execute a mis-shaped delete). Never raise into normal command flow because the manifest is unreadable; the `[NOTIC]` reminder degrades to silent if the file cannot be parsed (with a one-line warning). | cli.py:11737-11772 |
| PA-11 | Concurrent-append safety | Two ocman processes can defer at once (two terminals). `save_pending()` must read-modify-write under a lock (a lockfile next to the manifest, or write-then-atomic-replace after re-reading), so a second append cannot clobber the first. Reuse/extend the history atomic-write; add the re-read-before-write step. Document that `pending run` takes the same lock while draining. | cli.py:11774-11793 |
| PA-12 | Treat the manifest as UNTRUSTED input (security) | The manifest is an on-disk record that tells a later ocman run what to DELETE. It MUST never be shell/`eval`'d; each item is validated against the schema and dispatched only through the existing structured delete functions (db_delete_*/db_run_cleanup), and the re-resolve + re-preview + re-confirm at drain (PA-07) is the trust boundary (a crafted/edited item still faces the human confirm and current-DB re-resolution). No item field is ever interpolated into SQL or a subprocess. | PA-07; db_delete_* 8207/8937/11072 |

## Non-goals
- No auto-drain (never run deferred deletes without the user invoking `pending run`).
- No deferral of `kill`/`reconnect` (they act ON running processes; nonsensical to defer).
- No per-project manifests (a delete is DB-global; "no OpenCode running" is a global condition).
- No new dependency; JSON via stdlib, same as the history ledger.

## Deferred / out of scope (with reason)
| Finding | Remediation Risk | Axis | Reason | Recommended later step |
|---------|------------------|------|--------|------------------------|
| Deferring rename/move/rebase/reclaim | Medium | complexity | Each has its own staleness/replay semantics (a rename target or a path-prefix rebase can conflict with intervening edits); adding them now widens the safety surface before the delete-family pattern is proven. | Follow-up IPD once PA-01..08 ship; recorded in TODO.md (PA-09). |
| Auto-drain when no OpenCode is running | Medium-High | functionality | Auto-executing deferred DELETES is exactly the surprise-destruction risk we are avoiding. | Optional opt-in config in a later IPD if desired. |

## Scope check
- Over-scope: none. The four commands share ONE guard hook (PA-03), so the code footprint is small
  and centralized rather than duplicated per command.
- Under-scope: staleness handling at drain (PA-07) is the essential safety capability and is IN.

## Required tests / validation
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output).
- CLI tests (monkeypatch running-detection + manifest path; capsys; NO real signals/deletes beyond a
  temp DB): (a) `--pend` on `session delete` while "running" writes a structured item and does NOT
  delete; (b) `[NOTIC] N items pending` prints on the next run and is suppressed under `--json`;
  (c) `pending list` shows the item; (d) `pending run` while still "running" REFUSES (and with
  `--while-running` proceeds); (e) `pending run` with nothing running re-previews and, on `--yes`,
  deletes, then empties the manifest; (f) a queued item whose target was already deleted is a
  logged no-op/skip and is removed; (g) an item the user declines at re-confirm is KEPT; (h) manifest
  round-trips (load/save) and tolerates a missing/empty file; (i) PA-10: a corrupt or
  unknown-`schema` manifest is skipped-with-warning and does NOT crash a normal command nor execute
  a mis-shaped item; (j) PA-11: two `save_pending()` appends in sequence both survive (no lost
  append).
- ANTI-REGRESSION (PA-03 touches the SHARED `require_safe_to_mutate`): the 5 non-deferrable callers
  (rebase/import/restore/rename/move + the generic "modify the database") MUST behave exactly as
  today. Confirm the existing while-running guard tests still pass and add one asserting a
  out-of-scope action gets NO `[p]` add-to-pending option (it passes no `pend_item`).
- TUI tests (120x40, isolated `OCMAN_CONFIG_PATH`): the Pending tab renders the count and items.
- Honesty rule: paste the ACTUAL pytest output and the ACTUAL `[NOTIC]`/`pending list`/`pending run`
  console output demonstrating defer -> notice -> drain.
- No em/en dashes in authored prose/help/errors.

## Spec / documentation sync
User-visible new behavior: add a "Deferring actions while OpenCode is running" section to README
(the defer prompt, `ocman pending list/run/clear`, the `[NOTIC]` reminder, the TUI Pending tab) and
a CHANGELOG `[Unreleased]` Added entry. TODO.md gets the future-scope note (PA-09).

## Open questions
- PA-06 command name: RESOLVED with maintainer 2026-07-25 = `pending` (`ocman pending list/run/clear`).
- PA-03 action verb: RESOLVED with maintainer 2026-07-25 = "add to pending" (NOT "defer", which
  reads ambiguously at an interactive prompt as "skip for now / retry later"). Interactive prompt
  key `[p]` ("add to the pending list"), CLI flag `--pend`, TUI label "Add to Pending". The
  action-verb family matches the `pending` command noun, so the banner, prompt, flag, and TUI all
  read as one coherent feature.

## Approval and execution gate
This IPD is a proposal. It MUST be human-approved before execution and is NOT auto-run.
- Open questions: RESOLVED with maintainer 2026-07-25 (PA-06 = `pending`; PA-03 = "add to pending",
  prompt key `[p]` + flag `--pend`). None remain.
- Scope fence: `ocman/cli.py`, `ocman_tui/`, `tests/test_ocman.py`, `tests/test_tui.py`,
  `README.md`, `CHANGELOG.md`, `TODO.md`. Nothing else.
- Honesty rule (hard MUST): paste the ACTUAL pytest output and the ACTUAL defer/notice/drain
  console output.
- Commits: path-scoped, never `git add -A`, never push.
- Prose: no em/en dashes introduced.
- Lifecycle: on green tests + validation, set `Status: executed` and `git mv` this file to
  `.agents/plans/executed/`.
