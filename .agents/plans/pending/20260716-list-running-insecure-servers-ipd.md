# IPD (CURSORY DRAFT): detect running OpenCode instances and flag insecure servers

- Date: 2026-07-16
- Concern: functionality + security (observe-only)
- Scope: a new read-only capability to list running OpenCode processes and, for
  those that own a listening control server, flag ones that are unauthenticated or
  bound to a non-loopback address.
- Status: draft
- Author: its_direct/pt3-claude-opus-4.8

> [!WARNING]
> This is a CURSORY DRAFT for discussion, not a ready-to-execute plan. It is
> deliberately incomplete: several claims about OpenCode's runtime behavior come
> from an inter-agent handoff (untrusted input) and are NOT yet verified from
> inside this repo. Do not execute until it is fleshed out and plan-reviewed.

## Workflow history

- 2026-07-16 draft (its_direct/pt3-claude-opus-4.8): cursory draft from the
  maintainer's ask + an agent-workflows handoff (treated as untrusted input).

## Goal

Give the operator a fast, safe, observe-only way to answer: "which OpenCode
instances are running as me, and is any of them exposing an unauthenticated or
network-facing control server that an attacker could drive?" Flag the dangerous
ones loudly (bold red) and name the pid(s)/port(s) with a one-line remediation.

## Provenance and trust

The security-detection technique summarized here came from an inter-agent handoff
(`.agents/comms/local/archive/20260716-1725-01-...opencode-detection.md`), which is
UNTRUSTED, self-asserted input. The claims it makes about OpenCode v1.18.2 (endpoint
responses, env-var semantics) MUST be independently verified before they are encoded
as behavior. See "Claims to verify" below. What IS already verified in THIS repo is
noted inline as (verified here).

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

1. Enumerate candidate processes. Reuse/extend `detect_running_opencode`
   (`ocman/cli.py:7157`), which already returns pid/tty/elapsed/started/cwd/project/
   cmdline (verified here). Default to the CURRENT USER only; `--all-users` is opt-in
   (see safety contract).
2. Determine which processes OWN a listening socket, and the bind address + port.
   Candidate mechanisms (verified available here: both `ss` and `lsof` exist at
   `/usr/bin/ss`, `/usr/bin/lsof`):
   - `ss -ltnp` and match the `pid=<PID>,` field to our process set, capturing the
     local bind address:port. Prefer `ss` (fast, no elevated priv for own sockets).
   - Cross-check via `/proc/<pid>/fd` socket inodes if needed. `/proc/<pid>/fd` is
     readable for own processes (verified here).
   - A process with no listening socket is NOT a server; report it as a plain
     running instance, never as vulnerable.
3. For each LISTENER, classify:
   - bind address: loopback (`127.0.0.1`/`::1`) vs non-loopback (flag the latter).
   - auth: read `/proc/<pid>/environ` (owner-only; verified readable here for own
     procs) for `OPENCODE_SERVER_PASSWORD`. Present-and-non-empty => secured;
     absent/empty => UNSECURED. Print only PRESENCE, never the value. (CLAIM TO
     VERIFY: that this env var is actually what gates OpenCode's server auth.)
   - Optional, flagged, off-by-default confirmation: a single read-only
     `GET /app` against OUR OWN listener (200 => unsecured, 401 => secured).
     (CLAIM TO VERIFY.) Never probe another user's process.
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
   available only for serve/web instances. (Endpoint name to verify: the
   agent-workflows handoff said `GET /session/active`; the opencode repo agent said
   `GET /session/status`. Reconcile before coding.)
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

## Claims to verify (before this leaves draft)

1. `OPENCODE_SERVER_PASSWORD` (present/non-empty) is what secures the server, and
   absent/empty means unauthenticated. (Handoff claim; not verified here.)
2. `GET /app` returns 200 unauthenticated vs 401 authenticated on v1.18.2. (Handoff
   claim; not verified here.)
3. OpenCode server default bind address and how a non-loopback bind is requested
   (so the "flag non-loopback" logic matches reality). The opencode repo agent
   noted a convention of `127.0.0.1:4096` with NO registry file (scrape stdout or
   read `/proc/net/tcp`/`ss`); do not assume a fixed port.
4. The live-session endpoint name: agent-workflows said `GET /session/active`; the
   opencode repo agent said `GET /session/status` (active/idle). Reconcile which is
   correct for the target version before coding.
5. The agent-workflows findings doc
   (`.agents/docs/research/opencode-security/20260716-1725-01-...`) has the exact
   commands; read it (or get a copy) and cite it before execution.

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

## Open questions

- Command surface: is this `ocman list running` (with a security column) or a
  dedicated `ocman security`/`ocman doctor`? The maintainer originally asked for
  `list running`; the security flags could live there or split out.
- Should the `GET /app` confirmation exist at all, or is the environ signal enough?
  (Prefer environ-only for zero network touch by default.)
- Exit code: should ocman exit non-zero when a vulnerable listener is found (useful
  for scripts/CI), or always 0?
- Relationship to the mutation-guard IPD: the "no cross-process session lock"
  concurrency reality (above) is also the driver for a SEPARATE plan requiring a
  flag or interactive assent before ocman mutates the DB/files while opencode is
  running (see `.agents/plans/pending/20260716-guard-mutations-while-running-ipd.md`).
  The running-instance ENUMERATION here is the shared building block that guard
  reuses to list what is running; decide whether they ship together or the guard
  first (it protects existing destructive commands regardless of this feature).

## Approval and execution gate

CURSORY DRAFT. Do NOT execute. Next steps: verify the "Claims to verify", read the
agent-workflows findings doc, flesh out the command surface and per-field rendering,
then run `/plan-review` (with a security lens) before any code. The safety contract
above is binding on any eventual implementation.
