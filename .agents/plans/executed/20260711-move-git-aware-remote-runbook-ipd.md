# Implementation Plan - Git-aware `ocman move` with remote runbook

Status: EXECUTED (2026-07-13)

Implemented in `ocman/cli.py`: `_parse_move_dest`, `git_state`/`run_git` (first git
integration, argv only), `TransferStep`/`MovePlan` with `render_runbook`,
`_build_remote_steps`, `_menu`, `_gather_git_decisions` (B1/B2 menus),
`_run_git_actions` (aborts before any move on failure), `_move_dest_backup_dir`
(`move-dest-backup-*`), and `_execute_move` (up-front gather -> single confirm ->
act; local transactional move with C2 collision menu, remote print-only runbook,
and `--confirm-remote-delete`). Both `move` handlers reduced to thin dispatchers;
`--confirm-remote-delete`/`-y`/`--force` added to both `move` subparsers. Command
safety: `shlex.quote` on all printed values, subprocess list-form for git. Tests
added in `tests/test_move.py` (parse rule, git_state states, remote runbook
quoting + no network, confirm-remote-delete gate) and the missing-source test
updated to the new menu UX. Docs updated (README, ARCHITECTURE, CHANGELOG). Full
suite: 292 passed, 2 skipped.

Enhances `ocman move SPEC to DST` to be git-aware and cross-machine-friendly.
When DST is a remote (`host:/path`), ocman gathers all decisions interactively
UP FRONT and then PRINTS a copy-paste runbook (bundle export, file/repo transfer,
remote import) rather than performing network I/O itself. When DST is local, it
keeps today's transactional dir-move + DB-rebase, adds up-front git-state handling
and destination-collision handling, and can run LOCAL git prep (commit/push/pull)
after confirmation.

No code is changed by this plan; execute only after plan-review.

Evidence lines are `ocman/cli.py:<line>` verified on 2026-07-11 against the
current package layout; line numbers drift, re-verify before editing.

---

## Motivation

Moving sessions + repos between machines is a recurring manual chore: `ocman
session export`, `scp` the `.ocbox`, `tar | ssh 'tar -x'` (or git push/pull) the
repo, then `ocman session import --new-project-path ...` on the far side, and
finally reconcile the session `directory`. It is error-prone (the
`--new-project-path` remap step is easy to forget) and repetitive. ocman already
knows the repo path (`worktree`/`directory`) and how to build the bundle; it only
lacks git-awareness and a guided flow.

## Current behavior (verified)

- `ocman move SPEC to DST` dispatches at `ocman/cli.py:11085` (project) and
  `11168` (session). Local only: takes a rollback DB backup
  (`db_create_rollback_backup`, `7875`), `shutil.move`s the directory
  (`move_directory_structure`, `7919`), rebases DB paths in a transaction
  (`db_move_project_metadata` `8039`, `db_move_session_metadata` `8086`), and
  reverses both on failure (`11145-11165`). `--metadata-only` skips the physical
  move. Destination-exists is a hard error today (`11116-11117`).
- Export bundle `_write_ocbox` (`8220`) is a ZIP (`.ocbox`) of `meta.json`,
  per-table `db_data/<table>.jsonl`, and `session_diffs/<sid>.json`. Import
  (`extract_and_import_session` `8454` / `extract_and_import_project` `8758`)
  remaps ids/paths into the CURRENT DB, with `--to-project` / `--new-project-path`
  / `--new-session-id`.
- **No network code** (zero ssh/scp/rsync/paramiko) and **no git code** (zero
  git invocations) exist anywhere today. Both are new capabilities.
- Confirm helpers to reuse: `confirm_destructive` (`9670`, typed-yes) and the
  numbered-menu pattern in `_prompt_project_collision` (`8729`).

---

## Decisions (confirmed with user 2026-07-11)

1. **Print by default; no flag required to print.** For a REMOTE destination,
   ocman NEVER performs network I/O (no ssh/scp/tar/rsync/remote-git). It gathers
   choices, then prints a runbook. (A future IPD may automate execution; see
   "Design for later execution".)
2. **Local git prep may RUN.** For a LOCAL destination (or the local half of a
   remote move), after explicit confirmation ocman may run local git commands
   (`git add`/`commit`/`push`/`pull`) because they are local and git is safe and
   verbose. Remote-side steps are always printed.
3. **Enhance the existing `move` command in place** (not a new command). A remote
   DST triggers print-runbook mode; a local DST keeps the transactional move.
4. **Never auto-delete on remote.** The remote/print flow never deletes the local
   session or repo. It prints how, and MAY offer a SEPARATE, explicitly-guarded
   "I confirm the remote import succeeded -> delete local" step. Local moves keep
   today's transactional relocate (the source dir IS moved, atomically, as now).
5. **Ask everything answerable UP FRONT.** All questions that could be asked
   before any export / backup / repo mutation / move MUST be gathered first, then
   a single confirmation, then execution proceeds without further prompts.

---

## Design

### A. Up-front decision gathering (the ordering contract)

The whole flow is: (1) inspect, (2) ask every question, (3) one final summary +
confirm, (4) act. NOTHING destructive or expensive (bundle export, DB backup,
repo mutation, directory move, printed-runbook generation for remote) happens
until after step 3. Implement as a `MovePlan` dataclass populated during (1)-(2)
and consumed in (4). This also creates the seam for later automated execution
(the same `MovePlan` could drive real ssh/scp instead of printing).

Inspection collects, before asking anything:
- DST parse: is it `host:/path` (remote) or a local path? (`_parse_move_dest`)
- Source repo path (`worktree`/`directory`) and whether it exists on disk.
- Git state of the source repo (see B): is-git, dirty set, ahead/behind counts.
- DST-collision state (see C): does DST exist (locally; for remote, whether we
  can/should assume so is a printed caveat, not a probe).

### B. Git-state handling (asked up front, local repo)

Detect a git repo with `git -C <path> rev-parse --is-inside-work-tree`
(subprocess, the first git use in the codebase). If not a git repo, skip this
section (offer bulk file copy only). If git:

Compute `git status --porcelain=v1 -b` to get: branch, ahead/behind counts, and
the dirty set classified as staged / unstaged-modified / untracked / (renamed,
deleted). Present the menu that matches the actual state; only show options that
make sense for that state.

**B1. Clean but diverged from upstream** (ahead N and/or behind M):
List the exact counts ("N to push, M to pull"). Options (logical order):
- If both ahead and behind:
  1. Push and pull all commits (Recommended before proceeding)
  2. Push only
  3. Pull only
  4. Do not push or pull (WARNING: if something goes wrong, work may be lost)
- If only ahead (N to push): options collapse to {Push all (Recommended), Do not
  push (WARNING)}.
- If only behind (M to pull): options collapse to {Pull all (Recommended), Do not
  pull (WARNING)}.
- If clean AND in sync with upstream (nothing to do): no menu; note "repo clean,
  in sync".
- If clean with NO upstream configured: note it; offer {Continue, Quit} (cannot
  push without a remote/upstream; do not guess one).

**B2. Dirty (uncommitted changes; independent of divergence):**
List file types present (e.g. "3 modified, 1 staged, 5 untracked"). Options
(logical order, warnings where relevant):
  1. Quit and fix the dirty repo myself (SAFEST)
  2. Commit staged only; leave unstaged/untracked behind (WARNING: unstaged and
     untracked changes will NOT travel with a git push; use bulk copy to include
     them)
  3. Stage untracked + all modified and commit everything, then proceed
  4. Do not commit; proceed anyway (only valid if transfer is BULK COPY, since a
     git push would omit the dirty work) (WARNING: relies on bulk copy)
If the repo is both dirty AND diverged, resolve dirty first (B2), then divergence
(B1), because pushing requires a clean/committed tree.

Chosen git actions that are LOCAL (add/commit/push/pull) run in step (4) after
the final confirm. `push`/`pull` obviously require network to the git remote;
that is the user's existing git remote, not ocman's concern, and git handles its
own auth/output. If a git action fails, ABORT before touching the move (fail
before the point of no return).

### C. Destination handling (asked up front)

**C1. DST is REMOTE (`host:/path`):** ocman cannot safely probe the remote, so it
does not guess existence. It gathers the transfer-style choice (git push+remote
clone/pull vs bulk `tar | ssh 'tar -x'`) and prints the runbook (see D). Any
"dest exists" handling on the remote is described in the printed runbook as a
caveat, not performed.

**C2. DST is LOCAL and EXISTS:** menu (logical order; today this is a hard error):
  1. Don't continue; I want to reconsider. (quit, no changes)
  2. Don't actually move (SAFEST) -- update DB metadata only (`--metadata-only`
     semantics), leaving files as-is.
  3. Back up DST to <X>, remove DST, then move source into place.
  4. Remove DST, then move source into place. (WARNING: cannot recover DST)
  5. Back up DST to <X>, then copy source files over the top (dirty overlay).
     (WARNING: may leave a repo in an unknown/mixed state)
Where `<X>` is a timestamped path under the backups dir. Backups here are
directory backups (distinct from the DB rollback backup).

**C3. DST is LOCAL and does NOT exist:** the common case. No collision menu;
proceed to the standard transactional move (today's behavior) plus any git prep.
Confirm the destination parent is writable up front.

Note (inner guard): `move_directory_structure` (`ocman/cli.py:7919`) itself
raises when the destination already exists (`7935`), and both move handlers
already hard-`die` on dest-exists (`11117` project, `11200` session). The C2
collision choice MUST therefore be resolved and the destination cleared/backed-up
BEFORE calling `move_directory_structure` (or before the overlay-copy path), so
the chosen behavior is what happens rather than the existing guard firing. The C2
overlay option (copy over the top) does NOT go through `move_directory_structure`
(which requires an absent dest); it is a separate copy path.

### D. Remote runbook (print-only), pre-filled

After gathering B + C1, print a numbered, copy-paste runbook with real values
substituted (source path, computed bundle path, DST host/path, and the crucial
`--new-project-path`/`--to-project` remap). Structure:
1. (If chosen) local git: the exact `git` commands ocman will run or has run.
2. Export the bundle locally (`ocman session export SPEC --to <bundle>` or the
   project form).
3. Transfer the bundle: `scp <bundle> host:/tmp/`.
4. Transfer the repo, per chosen style:
   - git: push locally (step 1) then on remote `git clone`/`git pull` into
     `host:/path`; OR
   - bulk: `tar -C <src> -cz . | ssh host 'mkdir -p /path && tar -C /path -xz'`.
5. Remote import remapped to the landed path: `ssh host 'ocman session import
   /tmp/<bundle> --new-project-path /path'` (ocman computes and fills `/path`).
6. Verification hints (what to check on the remote) and the guarded local-delete
   step (see E).
Emit the runbook via a `MovePlan.render_runbook()` method (the execution seam).

### E. Delete-after policy

- LOCAL move: source directory is relocated (moved) transactionally as today; no
  separate delete needed.
- REMOTE move: NEVER auto-delete. After printing the runbook, if interactive,
  offer a separate step: "After you have verified the remote import succeeded,
  run `ocman move ... --confirm-remote-delete` (or answer here) to delete the
  local session + repo." This deletion, when invoked, reuses the existing
  `db_delete_sessions_batch` / directory removal with a backup, and requires the
  same typed-yes confirm. Default is to keep local.

### F. Design for later execution (seams, per user note)

Choose abstractions now that do not materially change the print-only behavior but
make a future "actually execute remote" IPD cheap:
- `MovePlan` dataclass holding: source, dest (parsed host/path/is_remote), git
  decisions, transfer style, collision decision, computed bundle path, remap
  target. A single object gathered up front and either rendered (now) or executed
  (later).
- A `TransferStep` list (ordered, each with a human label, a shell command
  string, and an "is_remote/is_network" flag). Print mode joins their labels +
  commands; a future execute mode runs the non-network ones and shells the
  network ones. Keep them pure data now.
- Isolate git calls behind a tiny `git_state(path)` / `run_git(path, args)` helper
  so tests can mock them and a future feature can reuse them.

### G. Command safety (printed and executed)

The runbook interpolates real values (source dir, `host:/path`, bundle path,
remap path) into shell command strings, and git actions are RUN locally. Both are
attack/footgun surfaces (a `worktree`/`directory`/DST containing spaces or shell
metacharacters).

- **Printed commands:** every interpolated value MUST be shell-quoted
  (`shlex.quote`) so a copy-pasted runbook is correct and safe even for paths with
  spaces, quotes, `$`, `;`, or `&`. The printed command is data; it must never be
  a place a crafted path can inject extra shell words.
- **Executed git:** git commands ocman runs MUST use `subprocess` LIST form
  (argv), never `shell=True` and never string interpolation into a shell. Pass the
  repo via `git -C <path> ...` with `<path>` as a discrete argv element.
- **No secrets in output:** the runbook and any logging must not echo tokens,
  credentials, or remote auth material; SSH/git auth is the user's environment.
- Tests MUST include a source path and a DST with spaces and a shell
  metacharacter, asserting the printed commands are correctly quoted and that no
  executed git call uses a shell.

### H. Non-goals (explicit)

- ocman performing ssh/scp/rsync or remote git for a REMOTE move (print only).
- Guessing a git remote/upstream that is not configured.
- Automatic deletion of a local repo/session after a remote move.
- Submodule / LFS / bare-repo special handling (call out as unsupported in the
  runbook; do not silently mishandle).
- Cross-version schema negotiation with the remote ocman (the runbook assumes a
  compatible ocman on the far side; note it).

---

## Tests

- `_parse_move_dest`: `host:/path`, `user@host:/p`, `host:relative` -> remote;
  `/local/path`, `./rel`, `~/x`, `C:\\proj`, `C:/proj` -> local; empty/degenerate
  inputs handled. Assert the Windows-drive readings resolve LOCAL per the rule in
  Resolved decisions.
- Command safety: a source path and a DST containing a space and a shell
  metacharacter produce printed commands whose interpolated values are
  `shlex.quote`-escaped; assert no executed git call uses `shell=True` (spy the
  subprocess call and confirm argv list form).
- `move-dest-backup-*`: the C2 backup options create a directory named
  `move-dest-backup-<timestamp>` under the backups root (NOT `opencode-db-cleanup-*`).
- `--confirm-remote-delete`: the flag path performs the same guarded, typed-yes
  local delete as the inline interactive offer, and is a no-op safe to re-run.
- `git_state`: mock subprocess to simulate clean+in-sync, clean+ahead,
  clean+behind, clean+ahead+behind, no-upstream, dirty (each file-type mix), and
  not-a-git-repo. Assert the correct menu options are offered for each.
- Up-front ordering: assert NO bundle/backup/move/print happens before the final
  confirm (e.g. spy that export/backup are called only after confirm; a "quit"
  answer at any menu leaves the DB and filesystem untouched).
- Local DST exists: each C2 option (backup+remove+move, remove+move, backup+dirty
  overlay, metadata-only, quit) does exactly what it says; backups land under the
  backups dir; rollback on failure restores state (extend today's move rollback
  tests).
- Local DST absent: unchanged transactional move still works (characterization).
- Remote runbook: `render_runbook` emits export + scp + (git|tar) + remote import
  with the correct pre-filled `--new-project-path`; asserts ocman made NO network
  call (no ssh/scp/tar subprocess) in print mode.
- Delete-after: remote flow never deletes local unless the explicit guarded
  confirm path is taken; local move relocates as today.
- Git prep failure aborts BEFORE any move/export (fail before point of no return).

---

## Docs

- README + help: document `ocman move SPEC to host:/path` (prints a runbook),
  the up-front git-state and dest-collision menus, the `--confirm-remote-delete`
  flag, that remote never runs network I/O, and the never-auto-delete-on-remote
  policy.
- ARCHITECTURE: record the `MovePlan` / `TransferStep` seam, the new `git_state`
  helper (first git integration), the printed-command quoting / executed-git
  list-form safety rule (Section G), and that remote transfer is print-only by
  design (execution deferred to a future IPD).
- CHANGELOG under Unreleased.

---

## Execution gate (read before implementing)

- **Open questions:** all resolved (see below). No unresolved decision blocks execution.
- **Scope fence:** implement only Sections A-H. Explicitly OUT: ocman running
  ssh/scp/rsync/remote-git (print-only), guessing a git remote, auto-deleting
  local after a remote move, submodule/LFS/bare-repo handling, remote schema
  negotiation. Do not expand scope without a new plan.
- **Honesty (hard MUST):** when reporting tests, paste the ACTUAL pytest runner
  output (`PYTHONPATH=. <venv>/bin/pytest -q`). Never claim a pass you did not run.
- **Commit discipline:** commit ONLY the files you changed, path-scoped
  (`git commit -m msg -- <paths>`); never `git add -A`/`-a`, never push, never tag.
- **Lifecycle:** on completion, set `Status: EXECUTED (<date>)` and `git mv` this
  plan from `pending/` to `executed/`.

## Resolved decisions (plan-review 2026-07-12, maintainer-confirmed)

- **C2 directory-backup location/naming:** back up an existing local DST into the
  backups root (`~/.local/share/opencode/backups/`) under a DISTINCT prefix
  `move-dest-backup-<timestamp>` (do NOT reuse the `opencode-db-cleanup-*` prefix;
  a directory backup is not a DB-family backup). Timestamp via
  `get_startup_timestamp_local()` for consistency.
- **Guarded remote local-delete surface (E):** expose it BOTH as the interactive
  inline offer after the runbook (the normal path) AND as a re-invocable flag
  `ocman move SPEC to DST --confirm-remote-delete` so the delete can be resumed in
  a later invocation once the user has verified the remote import. Both routes go
  through the same typed-yes confirm and reuse `db_delete_sessions_batch` + backup.
- **`_parse_move_dest` Windows/`host:` rule:** classify as REMOTE only when the
  string matches `^[^/\\:]+(@[^/\\:]+)?:.+` where the char after `:` is NOT a
  path-separator that would indicate a Windows drive; concretely, treat
  `host:/path`, `user@host:/path`, and `host:relative` as remote, but treat a
  single-letter scheme followed by `:\` or `:/` (e.g. `C:\proj`, `C:/proj`) as a
  LOCAL Windows path. Require and test both readings.

## Open Questions

- None remaining; all resolved above.

## Workflow history
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED; PR-001 (FIXED), PR-002 (FIXED), PR-003 (FIXED, dest-backup naming), PR-004 (FIXED, remote-delete surface), PR-005 (FIXED, parse rule), PR-006 (FIXED, execution gate added).
- 2026-07-13 execute (its_direct/pt3-claude-opus-4.8): implemented Sections A-H; 292 passed, 2 skipped; docs updated; moved to executed/.
