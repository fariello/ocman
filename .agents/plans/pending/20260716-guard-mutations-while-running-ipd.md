# IPD: guard DB/file mutations while OpenCode is running

- Date: 2026-07-16
- Concern: safety / data integrity (concurrency)
- Scope: every ocman operation that mutates the OpenCode DB or its on-disk files
  must, when one or more OpenCode instances are running, refuse by default and
  proceed only with an explicit flag (`--while-running`) or interactive typed
  assent, after LISTING the running instances.
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-16 draft (its_direct/pt3-claude-opus-4.8): created at maintainer request;
  motivated by the opencode repo agent's concurrency findings (no cross-process
  session lock).
- 2026-07-17 firm-up (its_direct/pt3-claude-opus-4.8): reflected that the broad
  enumerator + rich listing already shipped with `list running` (0b9470c); verified
  the exact current lock call sites + coverage gaps; resolved the flag
  (`--while-running` + `--force` alias), fail-closed-on-Linux, and restore-strictness
  decisions with the maintainer; added spec/doc-sync + anti-regression tests;
  promoted draft -> to-review.
- 2026-07-17 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED; PR-001 (FIXED, guard cli_restore not the internal db_restore_rollback_backup rollback helper), PR-002 (FIXED, make broadening-the-gate an explicit deliberate change + no-accidental-narrowing test), PR-003 (FIXED, TUI paths must honor the guard without a raw input() or be explicitly deferred), PR-004 (FIXED, add the three-state signal backward-compatibly). Claims re-verified against cli.py (5 lock sites, detect returns [] on both none/error, unguarded mutators confirmed). Status -> reviewed.

## Goal

Prevent ocman from corrupting or racing OpenCode's state. When ocman is about to
mutate the shared `opencode.db` or session/backup files while OpenCode instances
are running, it must (1) detect and LIST those instances, (2) refuse by default,
and (3) proceed only on explicit consent: a `--while-running`/`--force`-style flag
OR an interactive typed confirmation. This turns an unsafe silent race into a
deliberate, informed choice.

## Why (the concurrency reality)

Source-cited by the opencode repo agent (opencode `dev @ 08fb47373`, ~v1.18.3;
message archived at `.agents/comms/local/archive/20260717-0006-01-...`):

- OpenCode has NO cross-process session-ownership registry or lock. Same-session
  serialization is an in-memory Fiber coordinator (`run-coordinator.ts`),
  process-local and invisible to other processes; the `Flock` primitive is used for
  npm/cache/MCP/plugin, NEVER for sessions.
- TWO instances can adopt the SAME session id against the SAME db concurrently and
  neither detects the other; liveness cannot be determined offline.
- Therefore a session in the DB may be actively in use by a live process with
  NOTHING protecting it. If ocman deletes/moves/compacts/cleans/restores that data
  underneath a live instance, it can corrupt state or lose work.

The shared DB is a single SQLite file (verified here at multi-GB with an active
WAL); OpenCode holds it open continuously. ocman mutating it while OpenCode writes
is exactly the race to prevent.

## Current behavior (verified in this repo, 2026-07-17)

- `check_opencode_process_lock(force, verbosity)` (`ocman/cli.py:7327`) raises
  `RecoveryError` (with a rendered listing) if opencode is running, unless `force`.
  It fails OPEN (proceeds) if it cannot enumerate.
- It is called by exactly 5 mutators (verified: `cli.py:6979, 7544, 7869, 8049,
  10072`) -> `db_delete_session_recursive`, `db_delete_project_recursive`,
  `db_delete_sessions_batch`, `db_run_cleanup`, `db clean-orphans`.
- **A broad enumerator already exists** (shipped with `list running`, commit
  0b9470c): `detect_running_opencode(broad=True, all_users=...)` matches ANY
  `opencode` executable (catches `serve`/`web`/bare TUI, excludes LSP children), and
  `detect_running_instances(...)` + `cli_list_running(...)` provide the rich listing.
  The guard REUSES these; it no longer needs to add its own enumerator.
- Gaps to close:
  1. **The gate still uses the NARROW matcher.** `check_opencode_process_lock` calls
     `detect_running_opencode()` with the default `broad=False` (`opencode`+`continue`
     only), so it MISSES a bare `opencode`, `opencode serve`/`web`, or a TUI without
     `--continue`. The guard must enumerate with `broad=True` so ANY running instance
     gates a mutation.
     ANTI-REGRESSION NOTE: this is a DELIBERATE behavior change to the safety gate
     shared by the 5 already-guarded functions (delete session/project, batch delete,
     cleanup, clean-orphans) -- it makes the gate STRICTLY MORE inclusive (a superset
     of what it caught before). `list running` intentionally kept the default matcher
     narrow (commit 0b9470c); this IPD changes only the GATE's call to pass
     `broad=True`, not the default. Required tests: (a) a `--continue` TUI that tripped
     the gate before STILL trips it (no accidental narrowing); (b) a bare `opencode` /
     `opencode serve` now ALSO trips it; (c) the no-instances path is byte-identical
     to today (existing destructive-op tests unchanged).
  2. **Coverage is inconsistent (VERIFIED).** The lock is NOT called by
     `_execute_move` (session/project move), `extract_and_import_session` /
     `extract_and_import_project`, `backup restore` (`db_restore_rollback_backup`),
     or `db rebase` (`db_rebase_paths`) -- all of which mutate the DB/files and race
     today. `history clear` rewrites only the ledger sidecar (lower risk) -- include
     it for consistency. These must all route through the guard.
  3. **Only two outcomes today** (`--force` or hard refuse). Add the middle path: an
     interactive typed assent after showing the listing.

## Design (resolved with maintainer 2026-07-17)

1. **One enumeration source of truth (reuse).** Use the already-shipped
   `detect_running_opencode(broad=True)` so the guard sees ANY running opencode
   process for the CURRENT USER. No new enumerator. The rich listing reuses
   `detect_running_instances` / the `cli_list_running` renderer; a compact
   pid/user/uptime/cwd listing is sufficient for the gate.
2. **A single guard entry point** `require_safe_to_mutate(action, *, while_running,
   assume_yes, interactive, verbosity)` that every DB/file mutator calls before it
   writes. `check_opencode_process_lock` is REFACTORED to delegate to (or be
   replaced by) this one function so behavior is uniform. Outcomes:
   - No running instances -> proceed silently (today's happy path; UNCHANGED).
   - Running instances + `--while-running` (or its `--force` alias) -> print the
     listing + a bold-red warning, then proceed (informed override, scriptable).
   - Running instances + interactive TTY (no override) -> print the listing, then a
     typed confirm: "N OpenCode instance(s) are running; mutating shared data now can
     corrupt them. Type 'yes' to proceed anyway:". Proceed ONLY on exact `yes`.
   - Running instances + non-interactive + no override -> REFUSE (exit non-zero) with
     the listing and the `--while-running` hint.
   - `-y/--yes` does NOT authorize proceeding while running; it only skips the
     ordinary destructive typed-confirm. The running-instance risk requires the
     explicit `--while-running` (or an interactive `yes` to the running-specific
     prompt). Keep the two prompts/decisions distinct.
3. **Flag vocabulary (DECIDED).** Add `--while-running` as the explicit,
   self-documenting override; keep `--force` as a working ALIAS for back-compat
   (today `--force` bypasses the process-lock, which is exactly this override).
   Document both; `--while-running` is preferred in help/docs.
4. **Reliability policy (DECIDED): fail-CLOSED on Linux, fail-OPEN elsewhere.**
   On Linux, if enumeration itself ERRORS (not "found none" -- an actual failure to
   run `ps`/read `/proc`), REFUSE by default (require `--while-running`) and print
   the reason: we cannot confirm it is safe. On non-Linux (enumeration unavailable),
   proceed but PRINT that the running-instance check was skipped. This is a
   deliberate change from today's fail-open; the no-instances happy path is
   unchanged, so it only adds friction when detection genuinely breaks on Linux.
   Note: `detect_running_opencode` currently swallows errors and returns `[]`
   (indistinguishable from "none running"; verified `cli.py:7247+`); the guard needs
   a THREE-state signal (`some` / `none` / `unknown`) -- add an enumerator variant or
   out-param that reports enumeration failure distinctly, so fail-closed can trigger.
   Do this BACKWARD-COMPATIBLY: the existing callers (the 5 gate sites and
   `list running`) must keep working unchanged, e.g. a new
   `detect_running_opencode_status()` returning `(state, procs)` that the old
   function is expressed in terms of, rather than changing the current return type.
5. **The listing.** Show each running instance: pid, user, uptime, cwd, project
   (best-effort per the attribution rules in the list-running IPD), and session
   hint. Reuse the `list running` rendering; a minimal listing is acceptable.
6. **`backup restore` (DECIDED): same three-outcome guard** as the others (no
   special always-refuse). It overwrites the whole DB family, so its warning text
   should be especially loud, but it keeps the `--while-running`/typed-yes escape.

## Operations that MUST be guarded

Already guarded today (switch them to the new broad enumerator + `--while-running`):
`session delete`, `project delete`, `db_delete_sessions_batch`, `db clean`,
`db clean-orphans`.

NOT guarded today -- must be ADDED (verified 2026-07-17 they do not call the lock):
- `session move` / `project move` (`_execute_move`) -- physical dir move + DB rebase.
- `session import` (`extract_and_import_session` / `extract_and_import_project`) --
  inserts rows + writes diff files.
- `backup restore` -- guard the USER-FACING command `cli_restore`
  (`ocman/cli.py:11681`), which overwrites the whole `opencode.db` family; loudest
  warning. Do NOT guard the internal `db_restore_rollback_backup` helper
  (`cli.py:8293`): it is called by delete/move/import/cleanup ON FAILURE to ROLL
  BACK (`cli.py:8661,9667,10023,8855`), so guarding it would double-guard and could
  wrongly fire during a rollback. (Verified 2026-07-17.)
- `db rebase` (`db_rebase_paths`) -- bulk UPDATE of path prefixes.
- `history clear` -- rewrites the ledger sidecar (lower risk; included for
  consistency).

Every guarded command needs the `--while-running` flag (alias `--force` where it
already exists) threaded from its parser through the normalizer to the guard call,
mirroring how `-y/--yes` was threaded in the assess-functionality work. Read-only
commands (`list`, `search`, `show`, `db info`, `spend`, `history show`,
`list running`) are NOT guarded.

Note on remote `session/project move`: the print-only remote runbook path does NOT
mutate local state until the guarded delete step, so the guard applies to the LOCAL
move/relocate and to the `--confirm-remote-delete` deletion, not to merely printing
a runbook.

TUI paths (`ocman_tui/`): the TUI's delete/move actions call the SAME underlying
`db_delete_*` / move functions, so guarding at those functions covers the TUI too.
BUT the guard's interaction model differs in a TUI (a blocking stdin `input()` typed
prompt is wrong inside a Textual app). Execution MUST verify how the TUI invokes
these mutators and ensure the guard there uses a TUI-appropriate confirm (or the
TUI passes an explicit assent), never a raw `input()`. If the TUI cannot be made to
honor the guard cleanly in this pass, scope the TUI to a follow-up and say so; do
NOT leave a raw `input()` firing under Textual.

## Non-goals

- Implementing a real cross-process session lease (the `Flock`-style lease is a
  possible FUTURE enhancement, noted in the list-running IPD, not this guard).
- Detecting per-session ownership precisely (impossible offline; the guard is
  coarse-grained: "any opencode running" is enough to warn/gate).
- Killing or signaling OpenCode processes (observe-and-gate only; never terminate).

## Tests

- No instances running -> every mutator proceeds with no prompt (ANTI-REGRESSION:
  the existing destructive-op tests must still pass UNCHANGED; the guard's happy
  path must not alter today's behavior when nothing is running).
- Instances running + non-interactive + no override -> mutator refuses, exits
  non-zero, prints the listing (mock `detect_running_opencode(broad=True)`).
- Instances running + `--while-running` (and `--force` alias) -> proceeds after the
  bold-red warning.
- Instances running + interactive + typed `yes` -> proceeds; `no`/EOF -> aborts,
  nothing mutated (assert DB/files untouched).
- `-y/--yes` alone (no `--while-running`) while running + non-interactive -> STILL
  refuses (assert `-y` does not authorize the running-instance override).
- Broad enumeration gates: a bare `opencode` and `opencode serve` gate a mutation
  (not just `--continue`).
- Fail-closed (Linux): when the enumerator reports enumeration FAILURE (not "none"),
  the mutator refuses by default and `--while-running` overrides; fail-open on
  non-Linux prints the skipped-check caveat and proceeds.
- Coverage: each newly-guarded mutator (`_execute_move`, import, `cli_restore`,
  `db rebase`) actually calls the guard -- one test per mutator, plus an AST/registry
  check that no DB/file mutator bypasses `require_safe_to_mutate`.
- `backup restore` (`cli_restore`) shows its louder warning but still honors the
  override; the internal `db_restore_rollback_backup` rollback helper is NOT guarded
  (a rollback under a running instance must still complete).
- No-accidental-narrowing: a `--continue` TUI that tripped the gate pre-change still
  trips it (PR-002 anti-regression).
- TUI path: the TUI's delete/move honors the guard without a raw stdin `input()`
  (or the TUI scope is explicitly deferred; assert whichever was chosen).
- Backward-compat: existing callers of `detect_running_opencode` keep working after
  the three-state signal is added.
- Full suite green: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` (paste
  real output).

## Spec / documentation sync

- README: document that destructive commands refuse while OpenCode is running and
  how to proceed (`--while-running`), and the fail-closed-on-Linux behavior.
- ARCHITECTURE: record the single `require_safe_to_mutate` guard, the three-state
  (`some`/`none`/`unknown`) enumeration signal, and the fail-closed policy.
- CHANGELOG under Unreleased (note `--force` is now an alias of `--while-running`
  for the running-instance override).

## Resolved decisions (maintainer, 2026-07-17)

- **Override flag:** add `--while-running`; keep `--force` as a back-compat alias.
  `-y/--yes` authorizes only the ordinary typed confirm, NOT the running-instance
  override.
- **Reliability:** fail-CLOSED on Linux (enumeration failure -> refuse unless
  `--while-running`); fail-OPEN on non-Linux with a printed skipped-check caveat.
- **`backup restore`:** same three-outcome guard as other mutators (louder warning,
  but keeps the override).
- **Single code path:** `check_opencode_process_lock` is refactored to delegate to
  the one `require_safe_to_mutate` guard so all mutators behave uniformly.

## Open questions (remaining, non-blocking)

- Exact `require_safe_to_mutate` signature / where the three-state enumeration
  signal lives (new function vs out-param on `detect_running_opencode`); settle in
  implementation.

## Approval and execution gate

This IPD is a proposal (`Status: to-review`); NOT approved, NOT executed. It changes
destructive-command behavior, so it must be plan-reviewed (security + ANTI-REGRESSION
lens: the existing destructive-op tests MUST still pass unchanged when nothing is
running) before code. Sequencing: the enumerator/listing it depends on already
shipped with `list running` (commit 0b9470c), so this can proceed independently. On
execution follow the repo contract: implement only the agreed scope, add the tests
above, paste the REAL pytest runner output, commit path-scoped (never push, never
tag), sync docs, and move this IPD to `.agents/plans/executed/`.
