# IPD: `ocman list running` -- list OpenCode instances and flag insecure servers

- Date: 2026-07-16
- Concern: functionality + security (observe-only)
- Scope: a new read-only `ocman list running` that lists running OpenCode processes
  (pid/user/uptime/cwd/project/session/cost) and, for those that own a listening
  control server, flags ones that are unauthenticated or bound to a non-loopback
  address.
- Status: EXECUTED (2026-07-17)
- Approval: approved by maintainer 2026-07-17
- Author: its_direct/pt3-claude-opus-4.8

> [!NOTE]
> The runtime claims this rests on (env auth signal, `GET /app` 200/401,
> `/session/status`, default `127.0.0.1` bind, `--mdns` -> `0.0.0.0`, `ss` pid
> mapping, no registry file) were INDEPENDENTLY VERIFIED live on this host against
> opencode v1.18.3 on 2026-07-17 (observe-only, throwaway server, torn down). See
> "Verified facts". The three command/policy open questions were resolved with the
> maintainer (see "Resolved decisions"). Ready for `/plan-review` (security lens).

## Workflow history

- 2026-07-16 draft (its_direct/pt3-claude-opus-4.8): cursory draft from the
  maintainer's ask + an agent-workflows handoff (treated as untrusted input).
- 2026-07-17 firm-up (its_direct/pt3-claude-opus-4.8): read the agent-workflows
  findings doc; INDEPENDENTLY verified the auth/endpoint/bind claims live on this
  host (v1.18.3, observe-only); reconciled the endpoint conflict to
  `GET /session/status`; resolved the command-surface / fail-loud / probe-default
  decisions with the maintainer; promoted draft -> to-review.
- 2026-07-17 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED; PR-001 (FIXED, broaden the too-narrow enumerator so serve/web listeners are actually detected), PR-002 (FIXED, defensive ss/cmdline parsing + IPv6 + fail-loud fallback), PR-003 (FIXED, --probe target strictly from enumerated loopback bind:port, timeout, never non-loopback/user-supplied), PR-004 (FIXED, tests for broadened enumerator/fail-loud/probe-off/env-key-exactness), PR-005 (FIXED, dropped stale CLAIM-TO-VERIFY markers). Runtime claims independently verified live; security lens applied. Status -> reviewed.
- 2026-07-17 execute (its_direct/pt3-claude-opus-4.8): implemented `ocman list running`. Broadened `detect_running_opencode` with `broad`/`all_users` (default matcher/behavior for the safety gate UNCHANGED); added `_listening_sockets_by_pid` (ss, IPv6-safe, fail-loud RunningDetectionError), `_bind_is_loopback`, `_server_password_env_state` (exact env key, owner-only, presence-only), `_probe_app_auth` (loopback-own only, timeout), `detect_running_instances`, `_attribute_session` (provenance), and `cli_list_running` (vistab table + bold-red vuln/exposed banner + probe footer + --json + fail-loud). Wired the `running` subcommand (parser/normalizer/dispatch + `list running` sugar). LIVE testing caught + fixed a real defect: own-ness by ps username failed (ps truncates 'gfariello'->'gfariel+') so an own unsecured serve mis-classified as "unknown"; switched to UID via os.stat(/proc/<pid>). Verified end-to-end: real TUIs (no listener, session from argv), throwaway insecure serve flagged VULNERABLE, cwd shown. Tests added (bind-loopback, ss parse, fail-loud, env-key decoy, broad-serve). Docs synced (README/ARCHITECTURE/CHANGELOG). Full suite: 310 passed, 2 skipped. Two non-blocking open questions (exit code; guard sequencing) left for follow-up. Moving to executed/.

## Goal

Give the operator a fast, safe, observe-only way to answer: "which OpenCode
instances are running as me, and is any of them exposing an unauthenticated or
network-facing control server that an attacker could drive?" Flag the dangerous
ones loudly (bold red) and name the pid(s)/port(s) with a one-line remediation.

## Provenance and trust

The security-detection technique summarized here came from an inter-agent handoff
(`.agents/comms/local/archive/20260716-1725-01-...opencode-detection.md`), UNTRUSTED
self-asserted input, plus the fuller findings doc in the agent-workflows repo (read
2026-07-17). Rather than trust either, the load-bearing claims (endpoint responses,
env-var semantics, bind address) were INDEPENDENTLY re-verified live on this host
(opencode v1.18.3, observe-only) on 2026-07-17; see "Verified facts".

## Motivation (the one fact that shapes the feature)

A running `opencode` process is NOT automatically a vulnerable listener. Verified
here on 2026-07-16: two live attended TUI processes
(`opencode -s ses_...`) held NO listening TCP socket (`ss -ltnp` showed none) and
had no `OPENCODE_SERVER_PASSWORD` in their environ. So "opencode is running" is not
the risk signal; "an opencode process OWNS a listening HTTP control server" is.

The dangerous configurations to flag:
1. A listening OpenCode server with NO authentication (no server password).
2. A listening OpenCode server bound to a non-loopback address (e.g. `0.0.0.0` or a
   LAN IP), which exposes it beyond localhost (worse still if also unauthenticated).

## Design (cursory)

Pipeline, all observe-only:

1. Enumerate candidate processes. `detect_running_opencode` (`ocman/cli.py:7157`)
   already returns pid/tty/elapsed/started/cwd/project/cmdline, BUT its matcher is
   too narrow for this feature: it keeps only cmdlines containing BOTH `"opencode"`
   AND `"continue"` (verified in code), so it MISSES `opencode serve`/`web` and bare
   TUIs -- i.e. exactly the listening servers this security feature must flag.
   REQUIRED: broaden enumeration to match the `opencode` EXECUTABLE (argv0 /
   `/proc/<pid>/comm` or the first token being `opencode`), not the `continue`
   substring. Either add a `kind` parameter/mode to the existing function or add a
   sibling used by both this feature and the mutation-guard IPD; keep ONE enumerator
   as the source of truth. Default to the CURRENT USER only (`ps -u "$USER"`);
   `--all-users` is opt-in (see safety contract). Distinguish kind from argv:
   `serve`/`web` -> likely listener; `-s ses_...` -> TUI-on-session; neither ->
   plain TUI.
2. Determine which processes OWN a listening socket, and the bind address + port.
   Candidate mechanisms (verified available here: both `ss` and `lsof` exist at
   `/usr/bin/ss`, `/usr/bin/lsof`):
   - `ss -ltnp` and match the `pid=<PID>,` field to our process set, capturing the
     local bind address:port. Prefer `ss` (fast, no elevated priv for own sockets).
   - Cross-check via `/proc/<pid>/fd` socket inodes if needed. `/proc/<pid>/fd` is
     readable for own processes (verified here).
   - A process with no listening socket is NOT a server; report it as a plain
     running instance, never as vulnerable.
   - Defensive parsing: `ss -H` output columns can vary; parse the `pid=<N>` token
     and the local `ADDR:PORT` explicitly (regex), tolerate IPv6 (`::1`, `[::]`),
     and never crash on an unexpected line (skip + note). Read `cmdline` as
     NUL-separated. If `ss` is absent, fall back to the `/proc/<pid>/fd` socket-inode
     join to `/proc/net/tcp` (state `0A` = LISTEN); if neither works, FAIL-LOUD
     (per Resolved decisions), do not report "no listeners".
3. For each LISTENER, classify:
   - bind address: loopback (`127.0.0.1`/`::1`) vs non-loopback (flag the latter).
   - auth: read `/proc/<pid>/environ` (owner-only; verified readable for own procs)
     for the EXACT key `OPENCODE_SERVER_PASSWORD` (NUL-separated entries; match
     `\0OPENCODE_SERVER_PASSWORD=` / line start, not a substring so a var like
     `X_OPENCODE_SERVER_PASSWORD` cannot false-positive). Present-and-non-empty =>
     secured; absent/empty => UNSECURED. Print only PRESENCE, never the value.
     (Verified: ABSENT on unsecured serve, SET on secured; see Verified facts #1.)
   - Optional, flagged, off-by-default confirmation (`--probe`): a single read-only
     `GET /app` against OUR OWN listener (200 => unsecured, 401 => secured; Verified
     facts #2). The target host:port MUST be taken strictly from the enumerated
     own-listener's bind:port (never user-supplied), MUST be a loopback address, and
     MUST use a short timeout. Never probe another user's process, and never a
     non-loopback bind (that could reach another host's interface).
4. Report. A per-instance table (pid, user, kind, listener bind:port, auth, uptime,
   cwd, project, session) plus, when any unsecured or non-loopback listener is
   found, a LOUD bold-red banner naming the offending pid(s)+port(s) and the
   remediation (set `OPENCODE_SERVER_PASSWORD` before launch; do not bind to
   0.0.0.0 / use `--mdns` on shared hosts).

Session/CWD/project attribution is covered in the next section (it is the softer
part of the problem and must be reported honestly, not guessed).

## Session / CWD / project attribution (report signals with provenance)

Grounded in two source-cited findings from the opencode repo agent (against
opencode `dev @ 08fb47373`, ~v1.18.3, archived at
`.agents/comms/local/archive/`), plus live checks here (2026-07-16). Treat the
external claims as verify-on-merit; the line refs are opencode's tree, re-pin
before citing in tests.

The authority order for mapping a running instance to a session/project:

1. **The DB is authoritative for session -> project.** `opencode.db`:
   `session.directory` is the per-session working dir; `session.project_id ->
   project.worktree` is the project root. Use these, NOT the process cwd, to name a
   session's project. (`packages/core/src/session/sql.ts`, `project/sql.ts`.)
2. **argv `-s <id>` / `--session <id>` -> DB lookup is the reliable bridge.** If
   `/proc/<pid>/cmdline` carries the session id (verified here: live TUIs show
   `opencode -s ses_...`), resolve it via `db_find_session` to get the true
   `directory`/`project_id`. Label it "launched-with (may be stale)": a TUI can
   switch sessions after launch, so the argv id can go out of date.
3. **A listening server is the only LIVE-authoritative source.** Query the server's
   session-status endpoint for the active/idle session(s). Most attended TUIs do
   NOT listen (verified here: two live TUIs owned no listening socket), so this is
   available only for serve/web instances. Use `GET /session/status` (verified 200
   on a headless serve here 2026-07-17); do NOT use `GET /session/active` as primary
   (it returned 500 on a headless serve). See Verified facts #4.
4. **cwd is a WEAK hint, not authority.** `/proc/<pid>/cwd` is the process working
   dir, which legitimately differs from the session's project dir.

**`/proc/<pid>/cwd` != project dir, verified cases:**
- **Path/`--project` arg:** `opencode /path` or `--project /path` sets the project
  to the arg; kernel cwd stays the launch dir (`cli/cmd/tui.ts:68,164`).
- **`$PWD` divergence:** a relative project arg resolves against the shell's `$PWD`,
  NOT `getcwd()` (`resolveThreadDirectory`, `tui.ts:66-70`). A stale/exported/
  symlinked `$PWD` (or `env PWD=/foo opencode`) desyncs the resolved project from
  the kernel cwd.
- **Symlinks:** both `Filesystem.resolve` and `/proc/cwd` canonicalize, so neither
  matches the symlinked path the user typed.
- **Adopting a session from the "wrong" dir (biggest):** with `opencode -s <id>`,
  session ops run in the STORED `session.directory`, and the process cwd is your
  launch dir, which INTENTIONALLY will not match the project
  (`server/.../workspace-routing.ts:182`). You cannot infer the project from the
  process tree in this case; use the DB via the session id.
- **Multi-directory server:** a serve process routes each request by
  `x-opencode-directory`; its own cwd is irrelevant to the projects it serves.
- **Self-`chdir` / renamed-or-deleted cwd:** the readlink tracks the live inode
  (shows the new path, or `... (deleted)`), which can mismatch project matching.

**Ctrl-Z / cd / fg does NOT desync cwd** (verified reasoning + opencode note): cwd
is per-process; `SIGTSTP` stops in place, the shell's `cd` changes only the shell,
`fg`/`SIGCONT` resumes the same process. That sequence is safe; the cases above are
the real desync sources.

**Reporting rule:** show each attribution signal with its provenance and confidence
(`session (active)` = authoritative from a listener; `session (launched-with)` =
argv, may be stale; `project (from session DB)` vs `project (from process cwd)` when
they differ, show BOTH rather than silently picking one), and when a cwd maps to
many sessions, say "session(s) for this directory," never a fabricated 1:1.

## Concurrency reality (affects safety, not just display)

There is NO cross-process session-ownership registry or lock in opencode
(source-cited): same-session serialization is an in-memory Fiber coordinator
(`run-coordinator.ts:19,39-47`), process-local and invisible to other processes;
V2 execution is "process-local until clustering"; `event_sequence.owner_id`
(`event/sql.ts:7`) is event-replay/sync ownership, NOT runtime execution (do not
read it as "who is running this session"); the `Flock` primitive
(`util/flock.ts`) is used for npm/cache/MCP/plugin, NEVER for sessions. TWO
instances can adopt the SAME session id against the SAME db concurrently, and
neither detects the other. Liveness cannot be determined offline (no PID/heartbeat
column; `session.time_updated` only tells "recently active", not "running now").

Consequence for ocman: never assume a DB session has a single live owner. This is
the direct rationale for the separate "guard DB/file mutations while opencode is
running" IPD (see cross-reference in Open questions). If ocman ever needs a real
session-liveness lease, reuse opencode's `Flock` pattern (heartbeat + `staleMs` 60s
+ `.breaker`, records pid) rather than inventing one.

## Safety contract (hard constraints; non-negotiable)

- Observe-only. Allowed: process enumeration; `/proc` reads on OUR OWN processes;
  the kernel socket table (`ss`/`lsof`); at most an OPTIONAL, flagged `GET /app`
  against OUR OWN listener.
- NEVER call state-changing endpoints (`POST /session`, `/session/{id}/message`,
  `/session/{id}/shell`). NEVER read another user's `/config` (it can leak their
  provider API key). NEVER print secret values (only presence/absence).
- Default CURRENT USER only. `--all-users` is opt-in; without root we cannot read
  other users' environ, so classify their auth as "unknown (not probed)" from the
  socket table + bind address alone. Do not claim a cross-user instance is secure.
- ocman must not become the risk it warns about: no scanning of remote hosts, no
  port sweeps, only inspection of already-listening local sockets owned by
  enumerated OpenCode processes.

## Verified facts (checked live on this host, 2026-07-17, opencode v1.18.3)

Independently confirmed in THIS repo's environment (observe-only: a throwaway
`opencode serve` on a local port, my own process, torn down after), NOT merely
taken from the peer messages. The agent-workflows findings doc
(`~/VC/agent-workflows/.agents/docs/research/opencode-security/20260716-1725-01-...`,
read 2026-07-17) matched, except the endpoint reconciliation below.

1. **Auth signal (env):** unsecured `opencode serve` (no `OPENCODE_SERVER_PASSWORD`)
   -> environ shows the var ABSENT; secured (`OPENCODE_SERVER_PASSWORD=...`) -> SET.
   Read only for OWN processes (`/proc/<pid>/environ`, mode 0400). Print presence
   only, never the value. VERIFIED (ABSENT+unsecured, SET+secured).
2. **Auth signal (loopback GET):** `GET /app` -> 200 on unsecured, 401 on secured.
   VERIFIED both. Safe, read-only; use only against OWN listeners, optional/flagged.
3. **Bind address:** default hostname is `127.0.0.1` (from `opencode serve --help`);
   `--mdns` "defaults hostname to 0.0.0.0" (per `--help`) -> the network-exposed
   escalation case. Port defaults to 0 (ephemeral, assigned) -> DO NOT assume a
   fixed port; read it from the socket table. VERIFIED (help + observed 127.0.0.1
   bind).
4. **Live-session endpoint - RECONCILED:** use **`GET /session/status`** (returned
   200 on a bare serve). `GET /session/active` returned **500** on a headless serve
   here, so it is NOT the reliable choice; do not use it as the primary. Also
   available: `GET /session` (list; fields id/directory/title/time/projectID),
   `GET /project/current` (200). VERIFIED codes: /session/status 200,
   /session/active 500, /project/current 200 on a headless serve.
5. **Listener->pid mapping:** `ss -tlnpH` prints the owning pid + `ADDR:PORT` for
   OWN sockets (`users:(("opencode",pid=...,fd=...))`); parse pid + bind:port.
   VERIFIED. Cross-user without root: `ss`/`/proc/net/tcp` show the LISTEN entry and
   port but not the pid, and other users' `/proc/<pid>/environ` is Permission-denied
   -> classify their auth "unknown (not probed)".
6. **No registry:** no per-instance lock/port/pid file
   (`~/.local/state/opencode/locks/` empty); attended TUIs own NO listener
   (verified earlier with two live TUIs). Enumerate via `ps`; there is nothing to
   look up.

Remaining verify-on-execute item: re-pin any opencode source line refs cited in
tests/docs to the target version at implementation time.

## Tests (cursory)

- Listener detection: mock `ss` output; assert a pid with a listening socket is
  classified as a server and one without is not.
- Bind classification: `127.0.0.1:PORT` => ok; `0.0.0.0:PORT` / LAN IP => flagged.
- Auth classification: mock `/proc/<pid>/environ` with and without the password var;
  assert secured/unsecured; assert the value is never printed.
- Banner: when an unsecured or non-loopback listener exists, the bold-red banner
  names the pid+port; when only safe/loopback-authed listeners (or no listeners)
  exist, no false alarm.
- Non-Linux / no cwd: degrade gracefully (process-level fields only), no crash.
- `--all-users` without root: other users' auth shows "unknown (not probed)".
- Broadened enumerator (PR-001): a mocked `opencode serve ...` process IS detected
  (not just `--continue` TUIs); a bare `opencode` is detected; a `node
  pyright-langserver` child is NOT listed as an instance.
- Fail-loud (resolved decision): when enumeration/socket inspection is unavailable
  (mock `ss`/`ps` failing, or non-Linux), output explicitly says it could not
  determine instances/listener status, and does NOT print an empty "all clear".
- `--probe` default OFF: no HTTP request is made without `--probe` (assert no
  network call), and the footer telling the user how to enable it is printed; with
  `--probe`, the request targets only the enumerated loopback bind:port (assert it
  never targets a non-loopback or user-supplied host).
- Env-key exactness: a process with `X_OPENCODE_SERVER_PASSWORD` set (decoy) but not
  `OPENCODE_SERVER_PASSWORD` classifies as UNSECURED, not secured.

## Resolved decisions (maintainer, 2026-07-17)

- **Command surface: `ocman list running`** (a single command) that lists running
  instances with pid/user/uptime/cwd/project/session AND a security column
  (kind / listener bind:port / auth), with a bold-red banner when a vulnerable
  listener is found. Security is part of the running view, not a separate command.
  It also shows per-instance cost/session-age where a session is resolvable (the
  original ask); those reuse the session-attribution rules above.
- **Reliability policy: FAIL-LOUD.** If ocman cannot reliably enumerate processes or
  sockets (tooling missing, `/proc` unreadable, non-Linux for the socket/env parts),
  it MUST say so explicitly ("could not fully determine running instances / listener
  status") and MUST NOT print an empty or partial result that reads as "nothing
  running" or "nothing vulnerable". Never imply safety it did not verify.
- **`GET /app` probe: INCLUDED, OFF by default.** Default detection uses the env
  signal only (zero network touch). A `--probe` flag enables the harmless read-only
  `GET /app` confirmation against the CURRENT USER's OWN listeners only. When the
  probe is OFF, print a footer telling the user how to turn it on (`--probe`) and
  the one-line caveat (it makes a local, read-only HTTP request to your own
  servers; never to other users').

## Open questions (remaining)

- Exit code: should ocman exit non-zero when a vulnerable listener is found (useful
  for scripts/CI), or always 0? (Leave for plan-review/implementation.)
- Relationship to the mutation-guard IPD: the "no cross-process session lock"
  concurrency reality (above) also drives a SEPARATE plan requiring a flag or
  interactive assent before ocman mutates the DB/files while opencode is running
  (`.agents/plans/pending/20260716-guard-mutations-while-running-ipd.md`). The
  running-instance ENUMERATION here is the shared building block the guard reuses;
  decide sequencing (the guard can ship first with coarse enumeration; if both are
  approved, share the enumeration/rendering code).

## Approval and execution gate

This IPD is a proposal (`Status: to-review`); it is NOT approved and NOT executed.
The runtime claims are verified and the command/policy decisions are resolved, so it
is ready for `/plan-review` (security lens). The safety contract above is binding on
any implementation. On eventual execution follow the repo contract: implement only
the agreed scope (list running + security column, fail-loud, `--probe` off by
default, observe-only, current-user default), add the tests below, paste the real
pytest runner output, commit path-scoped (never push, never tag), and move this IPD
to `.agents/plans/executed/`. The remaining open questions (exit code; sequencing vs
the mutation-guard IPD) are non-blocking and can be settled in review.
