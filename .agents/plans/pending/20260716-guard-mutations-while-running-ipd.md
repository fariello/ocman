# IPD (DRAFT): guard DB/file mutations while OpenCode is running

- Date: 2026-07-16
- Concern: safety / data integrity (concurrency)
- Scope: every ocman operation that mutates the OpenCode DB or its on-disk files
  must, when one or more OpenCode instances are running, refuse by default and
  proceed only with an explicit flag or interactive typed assent, after LISTING
  the running instances.
- Status: draft
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-16 draft (its_direct/pt3-claude-opus-4.8): created at maintainer request;
  motivated by the opencode repo agent's concurrency findings (no cross-process
  session lock).

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

## Current behavior (verified in this repo)

- `check_opencode_process_lock(force, verbosity)` (`ocman/cli.py:7250`) ALREADY
  raises `RecoveryError` (with a rendered listing) if opencode is running, unless
  `force`. It fails OPEN (proceeds) if it cannot enumerate.
- Gaps to close:
  1. **Detection is too narrow.** `detect_running_opencode` (`cli.py:7157`) keeps
     only processes whose cmdline contains BOTH `"opencode"` AND `"continue"`. That
     misses a bare `opencode`, `opencode serve`, `opencode web`, or a TUI launched
     without `--continue`. The guard should treat ANY opencode process as
     "running", not just `--continue` ones.
  2. **Coverage is inconsistent.** The lock is called on only some destructive paths
     (delete session/project, cleanup, clean-orphans). Other mutators may not call
     it: verify and cover `session move` / `project move`, `session import`,
     `backup restore`, `db rebase`, `history clear` (ledger file), and the new
     `db_delete_sessions_batch`.
  3. **Only two outcomes today** (`--force` or hard refuse). Add the middle path:
     an interactive typed assent after showing the listing.

## Design (draft)

1. **One enumeration source of truth.** Broaden `detect_running_opencode` (or add a
   sibling) so the guard sees ANY running opencode process for the CURRENT USER
   (match on the executable/argv0 being `opencode`, not the `continue` substring).
   Reuse the richer enumeration from the `list running` IPD if it lands first
   (`.agents/plans/pending/20260716-list-running-insecure-servers-ipd.md`); this
   guard only needs "is anything running + a listing", not listener/vuln analysis.
2. **A single guard entry point** `require_safe_to_mutate(kind, *, assume_yes,
   force, interactive)` that every DB/file mutator calls before it writes:
   - No running instances -> proceed silently (today's happy path).
   - Running instances + `--force`/`--while-running` -> proceed, after printing the
     listing and a bold-red warning (informed override, scriptable).
   - Running instances + `--yes` -> treat as consent ONLY if the project decides
     `-y` should cover this (open question); otherwise still require the explicit
     while-running flag.
   - Running instances + interactive TTY (no flag) -> print the listing, then a
     typed confirm ("N OpenCode instance(s) are running; mutating shared data now
     can corrupt them. Type 'yes' to proceed anyway:"). Proceed only on exact yes.
   - Running instances + non-interactive + no flag -> refuse (exit non-zero) with
     the listing and the flag to re-run.
3. **The listing.** Show each running instance: pid, user, uptime, cwd, project
   (best-effort per the attribution rules in the list-running IPD), and session
   hint. This is the "preferably listing them" requirement. Reuse the rendering
   from the list-running feature; a minimal listing (pid/cwd/started) is acceptable
   if that feature has not shipped.
4. **Consistent flag vocabulary.** Reconcile with existing flags: TODAY `--force`
   means "bypass the process-lock". Options: keep `--force` as the override, OR
   introduce `--while-running` as the explicit, self-documenting override and keep
   `--force` as an alias. Decide in review (see open questions). Whatever is chosen,
   `-y/--yes` (skip typed confirm) and the while-running override must have distinct,
   documented meanings (do not conflate "I answered the prompt" with "I accept the
   running-instance risk").
5. **Fail-closed vs fail-open.** Today detection fails OPEN (proceeds if it cannot
   enumerate). For a safety guard, consider fail-CLOSED on Linux where enumeration
   is reliable (refuse if we cannot be sure), while remaining fail-open on
   platforms where enumeration is unavailable, with a printed caveat. Decide in
   review; default to the safer option for destructive ops.

## Operations that MUST be guarded (verify + cover)

DB or shared-file mutators: `session delete` / `project delete` /
`db_delete_sessions_batch`; `db clean` / `db clean-orphans`; `session move` /
`project move` (DB rebase + file move); `session import` (writes rows + diffs);
`backup restore` (overwrites the DB family); `db rebase`; `history clear` (ledger
file). Read-only commands (`list`, `search`, `show`, `db info`, `spend`, `history
show`, `list running`) are NOT guarded.

## Non-goals

- Implementing a real cross-process session lease (the `Flock`-style lease is a
  possible FUTURE enhancement, noted in the list-running IPD, not this guard).
- Detecting per-session ownership precisely (impossible offline; the guard is
  coarse-grained: "any opencode running" is enough to warn/gate).
- Killing or signaling OpenCode processes (observe-and-gate only; never terminate).

## Tests (draft)

- No instances running -> mutator proceeds with no prompt (characterization: all
  existing destructive tests still pass unchanged when nothing is running).
- Instances running + non-interactive + no flag -> mutator refuses, exits non-zero,
  prints the listing (mock `detect_running_opencode`).
- Instances running + `--while-running`/`--force` -> proceeds after the warning.
- Instances running + interactive + typed "yes" -> proceeds; "no"/EOF -> aborts,
  nothing mutated.
- Broadened detection: a bare `opencode` and `opencode serve` are detected (not
  just `--continue`).
- Each guarded command actually calls the guard (a test per mutator, or an
  AST/registration check that no mutator bypasses it).
- Fail-closed/open behavior per the decided policy.

## Open questions

- Flag name: reuse `--force`, or add `--while-running` (clearer) with `--force` as
  an alias? Does `-y/--yes` alone authorize proceeding while running, or must the
  running-risk override be its own explicit flag? (Lean: separate explicit flag;
  `-y` covers only the ordinary typed confirm.)
- Fail-closed on Linux for destructive ops when enumeration is available?
- Should `backup restore` be even stricter (always refuse while running, no
  override), since it overwrites the whole DB family under a live writer?
- Interaction with `check_opencode_process_lock`'s current hard-raise: this IPD
  REPLACES the two-outcome behavior with the three-outcome guard; ensure a single
  code path so behavior is uniform.

## Approval and execution gate

DRAFT. Do NOT execute. This guard changes destructive-command behavior, so it must
be plan-reviewed (security + anti-regression lens: existing destructive tests must
still pass when nothing is running) before code. Sequencing: it can ship before the
full `list running` feature (it only needs coarse enumeration + a listing); if both
are approved, share the enumeration/rendering code. On execution follow the repo
contract: path-scoped commits, never push, paste real test output, and move this
IPD to `executed/` when done.
