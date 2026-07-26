# IPD: defer destructive actions to a "pending" manifest when OpenCode is running

- Date: 2026-07-25
- Concern: feature (CLI + TUI) - deferred-action queue for while-running-guarded deletes
- Scope: `ocman/cli.py`, `ocman_tui/` (banner + Pending tab), `tests/test_ocman.py`,
  `tests/test_tui.py`, `README.md`, `CHANGELOG.md`, `TODO.md`
- Status: to-review
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-25 created (its_direct/pt3-claude-opus-4.8-1m-us): design decided interactively with the
  maintainer (scope, replay-safety, surfacing, manifest location); this IPD captures the agreed shape.

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
  RecoveryError (cli.py:7981). This is where the "or [d]efer to the pending list" offer hooks in,
  so all four delete-family commands gain deferral through ONE function, not four edits.
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
| PA-02 | Pending manifest storage layer | New helpers `pending_path()` (data dir, mirrors history_path resolution), `load_pending()`/`save_pending()` (atomic write like the history ledger), and a stable schema: a list of items `{id (uuid), action: "session-delete"|"project-delete"|"db-clean"|"db-clean-orphans", target: <spec/id>, snapshot: {title, preview_summary}, args: {while_running/force/extracts/older_than/...as needed}, queued_at: <iso>, queued_from_cwd}`. Structured intent, NOT a raw shell string, so drain can re-resolve and detect staleness. | cli.py:311 (history model) |
| PA-03 | Offer to defer at the running-guard | In `require_safe_to_mutate`, when state=="some" and the action is deferrable, add a `[d]efer` choice to the interactive prompt ("OpenCode is running. [d]efer to the pending list / type 'yes' to {action} anyway / anything else to cancel"), and support a non-interactive `--defer` flag. Deferring appends a structured item (built by the caller and passed in) and returns a sentinel so the command records-and-exits WITHOUT performing the action. Non-deferrable callers keep today's exact behavior. | cli.py:7934,7968-7991 |
| PA-04 | `--defer` flag on the four eligible commands | Add `--defer` to `session delete`, `project delete`, `db clean`, `db clean-orphans` (help: "If OpenCode is running, add this action to the pending list instead of refusing."). Wire each command to build its structured item and hand it to the guard. | dispatch 6798/6843/6866/6876 |
| PA-05 | `[NOTIC] X items pending` on every run | At the start of `main()` (after arg parse, before dispatch), if `load_pending()` is non-empty, print one line `f"{notice_prefix()} {n} item(s) pending (run: ocman pending run)"`. Suppressed for `--json` output and for the `pending` command itself (which shows its own detail). | main() dispatch |
| PA-06 | `ocman pending` command family | New top-level `pending` with actions: `list` (default; detailed table: #, action, target, queued-at, queue-time title, staleness marker), `run` (drain; see PA-07), `clear` (remove all or by index, with confirm). Register via `new_sub`; add to top-level help + `help` topics. | parser build ~cli.py:6199+ |
| PA-07 | `pending run` drains safely | (1) Re-check running instances via `require_safe_to_mutate("run pending actions", while_running=args.while_running)`; refuse if any up (non-Linux: warn + explicit confirm). (2) For each item in queue order: re-resolve the target against the CURRENT DB; if gone/changed-identity -> print a NOTIC skip and drop the item; else call the SAME delete path with `confirm_destructive` re-preview and the per-item confirm (honor `--yes` for the prompt only). (3) Remove successfully-run and vanished items; KEEP items the user declined at re-confirm. Print a summary (done / skipped / kept). | require_safe_to_mutate 7934; confirm_destructive; db_delete_* 8207/8937; db_run_cleanup 11072 |
| PA-08 | TUI banner + Pending tab | Add a count to a startup banner (or the footer/overlay area) and a `Pending` tab listing the manifest items (read-only view + a "Run pending" affordance that shells the same drain path with confirmation). Follows the existing tab/overlay patterns; isolated `OCMAN_CONFIG_PATH` in tests. | ocman_tui/app.py tabs |
| PA-09 | Document deferred future scope | In TODO.md, record that `rename`, `move`, `db rebase`, and `reclaim` are candidate future additions to the pending mechanism (same safety model), deferred from this IPD. | TODO.md |

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
  temp DB): (a) `--defer` on `session delete` while "running" writes a structured item and does NOT
  delete; (b) `[NOTIC] N items pending` prints on the next run and is suppressed under `--json`;
  (c) `pending list` shows the item; (d) `pending run` while still "running" REFUSES (and with
  `--while-running` proceeds); (e) `pending run` with nothing running re-previews and, on `--yes`,
  deletes, then empties the manifest; (f) a queued item whose target was already deleted is a
  logged no-op/skip and is removed; (g) an item the user declines at re-confirm is KEPT; (h) manifest
  round-trips (load/save) and tolerates a missing/empty file.
- TUI tests (120x40, isolated `OCMAN_CONFIG_PATH`): the Pending tab renders the count and items.
- Honesty rule: paste the ACTUAL pytest output and the ACTUAL `[NOTIC]`/`pending list`/`pending run`
  console output demonstrating defer -> notice -> drain.
- No em/en dashes in authored prose/help/errors.

## Spec / documentation sync
User-visible new behavior: add a "Deferring actions while OpenCode is running" section to README
(the defer prompt, `ocman pending list/run/clear`, the `[NOTIC]` reminder, the TUI Pending tab) and
a CHANGELOG `[Unreleased]` Added entry. TODO.md gets the future-scope note (PA-09).

## Open questions
- PA-06 naming: is `ocman pending` (with `list`/`run`/`clear`) the right verb, or do you prefer
  `todo` / `queue` / `deferred`? ASSUMPTION: `pending`.
- PA-03 prompt wording: confirm the three-way interactive choice ("[d]efer / type 'yes' to act now
  / else cancel") reads clearly, or should defer require the explicit `--defer` flag even at a TTY
  (no new prompt choice)? ASSUMPTION: offer `[d]efer` in the prompt AND support `--defer`.

## Approval and execution gate
This IPD is a proposal. It MUST be human-approved before execution and is NOT auto-run.
- Open questions: PA-06 (command name) and PA-03 (defer prompt vs flag-only) SHOULD be confirmed
  before executing those steps.
- Scope fence: `ocman/cli.py`, `ocman_tui/`, `tests/test_ocman.py`, `tests/test_tui.py`,
  `README.md`, `CHANGELOG.md`, `TODO.md`. Nothing else.
- Honesty rule (hard MUST): paste the ACTUAL pytest output and the ACTUAL defer/notice/drain
  console output.
- Commits: path-scoped, never `git add -A`, never push.
- Prose: no em/en dashes introduced.
- Lifecycle: on green tests + validation, set `Status: executed` and `git mv` this file to
  `.agents/plans/executed/`.
