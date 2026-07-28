# IPD: reliable log-correlated session attribution for `ocman lr --long` (reusable helper)

- Date: 2026-07-28
- Concern: capability + UI/UX (CLI). `ocman list running`/`lr --long` today shows a Session
  column derived from a best-guess (`_attribute_session`, cli.py:8369): an argv `-s <id>` hint
  (may be stale) or, lacking that, ALL of the cwd's sessions (one-to-many, not the actually-active
  one). For a running opencode there is a MORE reliable signal: correlate the process to its
  `opencode.log` `run=<uuid>` by start-time, then read that run's latest `session.id=ses_...` line
  (the session it is actually working in), and join the DB for the title. The maintainer wants
  `lr --long` to surface the reliable session id AND title, and wants a REUSABLE helper so other
  ocman code can ask "which session is PID X actually in?" (verified working method prototyped in
  a local `find_sessions.py` scratch script supplied by the maintainer).
- Scope: `ocman/cli.py` (new reusable `_active_session_for_process(...)` helper + a small
  `run=<uuid>` correlation reader; `_attribute_session` gains a reliable-first path used by
  `detect_running_instances`; `_sess_str` renders id + title; `-l` short alias for `--long` on the
  `running` subparser), `tests/test_ocman.py`, `README.md`, `CHANGELOG.md`, `DECISIONS.md`. No DB
  schema change, no new dependency, no signalling change. `--json` output is intentionally NOT
  changed (see Design decisions and Non-goals).
- Status: reviewed (not yet executed; awaiting human approval)
- Target version: rides the current in-flight line (final promotion decided at release-review).
- Approval: plan-review complete 2026-07-28; awaiting maintainer approval
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-28 (its_direct/pt3-claude-opus-4.8-1m-us): maintainer asked to add the session id and
  name to `ocman lr`, using the reliable log-correlation method from
  a local `find_sessions.py` scratch prototype, exposed as a reusable helper, and to document the
  known switch-without-interaction caveat. Initial design decisions resolved interactively (see
  Design decisions), including: reliable session shown in the `--long` column (not the default
  columns), `--json` left unchanged (staleness risk), and a `-l` short alias for `--long`.
- 2026-07-28 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): three architecture decisions
  resolved with the maintainer: (1) run the scan LAZILY at the `--long` render site, not inside
  `_attribute_session` (PR-001); (2) UNIQUE-match-or-degrade for run correlation (PR-002); (3) a
  BACKWARD-CHUNKED bounded log read from the oldest process start (>=150 KB steps; maintainer set
   the 150 KB minimum) (PR-003). Line anchors refreshed after the TTY IPD executed (PR-004);
  prose-cleanup scoped to user-facing files (PR-005).
- 2026-07-28 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PR-001..PR-005 all FIXED (lazy render-site scan, unique-match-or-degrade, backward-chunked
  >=150 KB read, refreshed anchors, prose scope). Readiness: GO - PENDING HUMAN APPROVAL.

## Evidence
- Prototype method (the maintainer's local `find_sessions.py` scratch script): (1) `get_pid_start_secs(pid)` reads
  `/proc/<pid>/stat` field 22 (starttime, clock ticks) + boot time from `/proc/uptime`; (2)
  `get_worker_run_id_for_pid` greps `opencode.log` for `creating instance ... directory=<cwd>` /
  `bootstrapping directory=<cwd>` lines and picks the `run=<uuid>` whose `timestamp=` is closest to
  the process start (within a 30s window); (3) `get_session_from_log_for_run_id` greps
  `run=<uuid>` lines for `session.id=ses_...` and takes the LAST one; (4) joins the DB `session`
  table for the title.
- Real log confirms the format (this host): `timestamp=2026-07-08T03:22:40.687Z level=INFO
  run=5e7faa1f message="creating instance" directory=<CWD>`, `... message=bootstrapping
  directory=<CWD>`, and `... message=loop session.id=ses_XXXX step=0`. The log on this host is
  ~73 MB (`<data_dir>/log/opencode.log`).
- ocman already resolves the log location: `discover_storage_locations()["log_dir"]`
  (cli.py:14298) = `<data_dir>/log`, honoring `$XDG_DATA_HOME` / redirected HOME. The active log
  file is `opencode.log` under that dir. Use this, NOT a hardcoded `~/.local/share/...` path (P7).
- ocman already parses `/proc/<pid>/stat` robustly for process STATE in `_pid_is_gone`
  (cli.py:12484-12491): it finds the closing `)` of `comm` with `rfind(b")")` and indexes AFTER it,
  which is the correct way to reach the space-delimited fields when `comm` may contain spaces/parens.
  The reusable helper MUST reach starttime (field 22, i.e. the 22nd whitespace token of the tail
  AFTER the last `)`) the same robust way, NOT the prototype's naive `split()[21]` on the whole line.
- Current attribution + rendering: `_attribute_session(p)` (cli.py:8369) returns
  `{id|ids, provenance, ...}`; `detect_running_instances` attaches it as `it["session"]`
  (cli.py:8364); `_sess_str(s)` (cli.py:8398) renders one honest line and is shared by THREE
  callers: the `kill` chooser (cli.py:12850), the `kill` preview (cli.py:12878), and the
  `lr --long` Session column (cli.py:13031). RS-07 back-compat therefore protects all three.
  `db_find_session(sid)` (cli.py:10112) returns `(id, directory, project_id)` but NOT the title;
  the title lives in `session.title` (see `db_list_sessions_under_dir` cli.py:4309 which selects
  title).
- `lr` rendering: the Session column header is appended only under `--long` (cli.py:12984), and its
  cell is `_sess_str(it["session"])` at cli.py:13031 (the reliable value is computed here per RS-06).
- `running` subparser: `--long` is `dest="running_long"` with NO short form (cli.py:6660);
  normalized at cli.py:7122; dispatched into `cli_list_running(long_output=...)` at cli.py:16503-16507.
  A repo-wide scan shows `-l` is not used by any subparser, so it is free.
- Own-user posture: `os.stat(f"/proc/{pid}").st_uid == os.getuid()` is the established own-user
  check (cli.py:12512, 8342-8347). `/proc/<pid>/stat` and `/proc/<pid>/cwd` reads must tolerate
  `PermissionError`/`OSError` (other users, races) and degrade, never raise.

## Design decisions (RESOLVED with maintainer 2026-07-28)
- Where the reliable session shows: RESOLVED = the EXISTING `--long` Session column, replacing the
  best-guess with the reliable log-correlated id + title WHEN available, else falling back to the
  current guess. Rationale: the log correlation reads a large file (~73 MB) and `/proc` per
  instance; keeping it behind `--long` avoids paying that cost on every plain `lr`. Default columns
  are UNCHANGED.
- `--json` output: RESOLVED = UNCHANGED (do NOT add reliable id/title to JSON). Rationale
  (maintainer): the active session can change at any instant, so embedding a point-in-time
  "active session" in a machine snapshot invites acting on stale/incorrect data. `--json` keeps
  emitting the existing `_attribute_session` dict (argv/cwd guess with provenance), whose provenance
  labels already signal it is a guess. The reliable id+title is a human, at-a-glance affordance.
- Fallback when the log is unavailable / no confident match: RESOLVED = fall back to the current
  argv/cwd guess, with provenance. The helper returns a reliable result labeled provenance
  `"log-active"` when found; otherwise the caller keeps the existing guess (`"launched-with ..."`,
  `"directory (one-to-many)"`, or `"unknown"`). `lr` NEVER fails because the log is missing.
- `-l` short alias: RESOLVED = ADD `-l` as a short alias for `--long` on the `running` subparser
  (`-l` is unused repo-wide). No other command's `--long`/short flags are touched.
- Known caveat (documented, not fixed): if a user switches sessions in the TUI via `/sessions` but
  has NOT yet taken any action in the new session, opencode has not yet logged a `session.id` line
  for the new session under that `run=`, so the log-correlated result reports the PREVIOUS session
  until the first interaction. This is judged a vanishingly small window; it is DOCUMENTED in
  `--help`, README, and DECISIONS rather than engineered around. The `"log-active"` provenance
  wording makes clear it is "the last session this process logged activity in."
- Where the scan runs: RESOLVED (plan-review 2026-07-28, maintainer) = LAZILY at the `--long`
  render site in `cli_list_running`, NOT inside `_attribute_session`. `_attribute_session` is called
  unconditionally by `detect_running_instances` for every instance on every `lr` (incl. default and
  `--json`), so embedding the scan there would run it everywhere and contradict the "cost stays
  behind `--long`" decision. `_attribute_session`, the default table, and `--json` are unchanged.
- Ambiguity / log rotation: RESOLVED (plan-review 2026-07-28, maintainer) = UNIQUE-MATCH-OR-DEGRADE.
  Only label a session `"log-active"` when exactly ONE run matches `directory=<cwd>` within the
  start-time window; if the match is ambiguous (2+ runs) or the startup line is not in the read
  window (rotated/truncated), return `None` and fall back to the existing best-guess. A confident
  wrong id is worse than none.
- Bounded log read: RESOLVED (plan-review 2026-07-28, maintainer) = BACKWARD-CHUNKED SEARCH. Do not
  read the whole ~73 MB log. Take the OLDEST running-opencode start time, read the last >=150 KB of
  the log, and if that chunk has not yet reached back to that oldest start timestamp, seek back
  another >=150 KB and repeat until the oldest start is covered (or the file head / a sane max is
  reached, degrading any process not covered). One accumulated pass builds the correlation and the
  per-run latest-session maps; handle partial lines at chunk boundaries.

## Requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| RS-01 | Reusable helper: PID -> active session id | Add module-scope `_active_session_for_process(pid: int, cwd: str, *, verbosity: int = 0) -> str | None` returning the `ses_...` id the process most recently logged activity in, or `None`. Steps: own-user/`/proc` guarded start-time read (RS-02), correlate to a UNIQUE `run=<uuid>` (RS-03), then latest `session.id` for that run (RS-04). Pure read-only; swallows `OSError`/`PermissionError` and returns `None` on any failure or ambiguity (never raises). This is THE reusable single-PID entry point other ocman code calls. To let the `--long` render avoid re-reading the log once per row, ALSO provide a batch form (e.g. `_active_sessions_for_processes(procs)` returning `{pid: ses_id|None}`) that performs the RS-04 bounded read ONCE across all PIDs; the single-PID helper may delegate to it with a one-element list. | prototype find_sessions.py:49-82; own-uid cli.py:12512 |
| RS-02 | Robust process start-time read | `_proc_start_epoch(pid) -> float | None`: read `/proc/uptime` (boot epoch = `time.time() - uptime`) and `/proc/<pid>/stat`; parse field 22 (starttime, in clock ticks) via the SAME `rfind(b")")`-then-index-the-tail technique already used in `_pid_is_gone` (comm may contain spaces/parens), divide by `os.sysconf("SC_CLK_TCK")` (fallback 100). Return `boot_epoch + starttime/hz` or `None` on any error. Do NOT use the prototype's fragile `split()[21]`. | _pid_is_gone parse cli.py:12484-12491; prototype fragility find_sessions.py:35 |
| RS-03 | Correlate PID to `run=<uuid>` (unique-match-or-degrade) | From the parsed log window (RS-04), find `creating instance`/`bootstrapping` lines containing `directory=<cwd>` and parse each line's `timestamp=<iso>` and `run=<uuid>`. Select the run whose timestamp is closest to the process `start_epoch` within a 30s window. RESOLVED (plan-review 2026-07-28): require a UNIQUE match; if two or more runs match `directory=<cwd>` within the window (e.g. two opencode started in the same dir within ~30s), or if NO startup line is found (e.g. the line rotated/truncated out of the read window), return `None` so the caller DEGRADES to the existing best-guess. A wrong-but-confident id is worse than none. | prototype find_sessions.py:49-72; log_dir cli.py:14298 |
| RS-04 | Bounded backward-chunked log read + run -> latest session id | Read the log at `discover_storage_locations()["log_dir"]/opencode.log` with a BOUNDED BACKWARD-CHUNKED search (RESOLVED with maintainer 2026-07-28), NOT a full 73 MB pass and NOT a per-instance re-grep: compute the OLDEST `start_epoch` across the instances being rendered; read the last >=150 KB of the file (chunk step configurable, minimum 150 KB); if the earliest `timestamp=` seen in that chunk is still NEWER than the oldest process start (i.e. the window has not yet reached back to that process's startup line), seek back another >=150 KB and read again, repeating until the window covers the oldest start (or the file head is reached, or a sane max total is hit -> then degrade for any process not yet covered). Over the accumulated window, build (a) the `directory=<cwd>` -> candidate runs map (RS-03) and (b) the per-`run` LATEST `session.id=ses_...` map in ONE pass. `_latest_session_for_run(run_id)` returns the last `session.id` for that run from the map (chronologically last = the session it is currently working in), or `None`. Handle a partial line at a chunk boundary (discard the first partial line of a mid-file chunk). | prototype find_sessions.py:74-82; maintainer chunked-search decision 2026-07-28 |
| RS-05 | Title lookup by session id | Add/extend a DB lookup returning the title for a `ses_...`. Prefer a small `db_session_title(sid) -> str | None` (single `SELECT title FROM session WHERE id=?`), reusing `_get_sqlite()` + `OPENCODE_DB_PATH` and the corruption-tolerant pattern of `db_find_session` (cli.py:10112). Do NOT overload `db_find_session`'s return tuple (keep its callers stable). | db_find_session cli.py:10112; title column cli.py:4309 |
| RS-06 | Reliable session resolved LAZILY at the `--long` render site (NOT inside `_attribute_session`) | RESOLVED (plan-review 2026-07-28): do NOT put the log scan inside `_attribute_session` (it is called unconditionally by `detect_running_instances` at cli.py:8364 for every instance on every `lr`, including default and `--json`, which would defeat RS-09). Instead, `_attribute_session` is UNCHANGED. In `cli_list_running`, ONLY when `long_output` is set, compute the reliable session per rendered instance: call `_active_session_for_process(it["pid"], it.get("cwd") or "")` (batched via the single RS-04 read for all rows); when it yields an id, build a session dict `{"id": sid, "title": db_session_title(sid), "provenance": "log-active", ...}` and render THAT in the Session column; otherwise render the existing `it["session"]` best-guess. The whole reliable path is guarded so any failure falls back to `it["session"]`. | detect attaches guess cli.py:8364; --long render site cli.py:13031; header append cli.py:12984 |
| RS-07 | `_sess_str` renders id + title | Extend `_sess_str(s)` so a dict with `id` AND `title` renders `ses_... "Title" (provenance)`; the id-only and `ids`/`count` and `unknown` shapes render exactly as today (back-compat for `kill` preview). Title is quoted and truncated to a sane width (e.g. 40 chars) to keep the row readable. | _sess_str cli.py:8398-8410 |
| RS-08 | `-l` short alias for `--long` | On the `running` subparser add `-l` to the existing `--long` option (`sp.add_argument("-l", "--long", dest="running_long", ...)`); no normalization/dispatch change needed (same dest). Update the help text. | subparser cli.py:6660; free `-l` confirmed repo-wide |
| RS-09 | `--json` unchanged; cost stays behind `--long` | Because the reliable correlation lives at the `--long` render site (RS-06) and NOT in `_attribute_session`/`detect_running_instances`, the log scan runs ONLY for `lr --long`/`lr -l` (or a direct call to the reusable helper). The default `lr` and `lr --json` never trigger it and are byte-for-byte unchanged; `--json` emits the existing `_attribute_session` guess dict (no `title`/`log-active`). | json emit cli.py:12963-12966; long-only column cli.py:12984,13031 |
| RS-10 | Docs + caveat (P3/P8) | README `list running`/`lr` row: document that `--long`/`-l` now shows the reliable log-correlated active session id + title (with the switch-without-interaction caveat) and that `--json` keeps the best-guess. `--help` for `--long`/`-l` updated. `CHANGELOG.md` `[Unreleased]` "Added"/"Changed" entry. `DECISIONS.md` entry recording the log-correlation method, the `--json`-unchanged decision, and the documented caveat. | README.md list-running row; CHANGELOG `[Unreleased]`; DECISIONS.md |

## Non-goals
- No change to `--json` (the active session is mutable; a machine snapshot must not imply a stable
  1:1). The best-guess dict with provenance stays.
- No reliable-session cost on the default (non-`--long`) `lr` or on `--json`.
- No engineering around the switch-without-interaction caveat (documented only).
- No new dependency; no log indexing/caching layer (single bounded read per `--long` invocation is
  sufficient; revisit only if profiling shows a real problem).
- No change to `kill`'s selection or preview semantics beyond `_sess_str` now optionally showing a
  title (the id-only/unknown shapes it already produces are unchanged).
- No cross-user session attribution (own-user only; other users' `/proc`/log are not readable).
- No Windows/macOS support for the log/`/proc` correlation (degrades to the existing guess; `lr`
  itself is already Linux-focused).

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output).
- New tests (use a tmp log file + monkeypatched `discover_storage_locations`/`OPENCODE_DB_PATH`;
  monkeypatch `/proc` reads or the helper seams; capsys; no real processes required):
  - RS-02: `_proc_start_epoch` parses a synthetic `/proc/<pid>/stat` whose `comm` CONTAINS spaces
    and parentheses (e.g. `1234 (open code) S ...`) and still returns the correct starttime; returns
    `None` on a missing/garbage stat.
  - RS-03 unique match: one `creating instance ... directory=<cwd>` line within 30s of the start is
    chosen; a start >30s from any line yields `None`; TWO runs matching the same `directory=<cwd>`
    within the window yields `None` (ambiguous -> degrade, not a confident wrong pick).
  - RS-04 latest session: a run with several `session.id=ses_A`/`ses_B` lines returns the LAST
    (`ses_B`); a run with none yields `None`.
  - RS-04 bounded chunked read: with a synthetic log larger than one 150 KB chunk whose oldest
    needed startup line sits in an EARLIER chunk, the backward-chunked search seeks back and still
    finds it; assert it does NOT read the entire file when the needed data is in the last chunk
    (e.g. bytes-read/seek accounting), and that a mid-chunk partial first line is discarded
    correctly. Assert the log is read ONCE for N instances (single accumulated pass), not
    re-grepped per instance.
  - RS-05: `db_session_title` returns the title for a seeded session and `None` for an unknown id
    and for a missing DB (corruption-tolerant).
  - RS-06 (render-site): with `long_output=True` and the helper monkeypatched to resolve a
    `ses_...`, the `--long` Session column shows `ses_... "Title" (log-active)`; with the helper
    returning `None` (log absent/ambiguous), the column shows the EXISTING `it["session"]`
    best-guess unchanged. `_attribute_session` itself is unchanged (no `log-active` path added to it).
  - RS-07: `_sess_str` renders `ses_... "Title" (log-active)` for the id+title shape; still renders
    the id-only, `ids`/`count`, and `unknown` shapes byte-for-byte as today (guards the `kill`
    preview and existing `lr --long` snapshot tests).
  - RS-08: the parser accepts both `lr -l` and `lr --long` and sets `running_long=True`; `-l`
    reaches `cli_list_running(long_output=True)`.
  - RS-09: `lr` (no `--long`) and `lr --json` do NOT trigger the log scan (assert the log-reading
    seam / helper is not called), and `--json` output is unchanged (existing guess dict, no
    `title`/`log-active`). Only `lr --long`/`lr -l` invokes the helper.
  - RS-10 (docs): light check/read that README, CHANGELOG `[Unreleased]`, and DECISIONS mention the
    reliable session, the `--json`-unchanged decision, and the caveat (no runtime test; note in the
    execution record).
- Manual (Linux, real opencode running): `ocman lr -l` shows the reliable `ses_... "Title"
  (log-active)` for a live instance; paste the (redacted) output in the execution record.
- No em/en dash in the USER-FACING material changed by this plan (README, `--help`/CLI text,
  CHANGELOG, DECISIONS). The prose convention is scoped to end-user-facing output, not to this IPD
  itself (maintainer clarification 2026-07-28).

## Gate / execution contract (MUST, per AGENTS.md)
Work the `## Detailed Implementation Checklist (TODO)` below top to bottom (mirror it in a
TodoWrite list while coding); a plan may claim completion only when every execution box AND its
matching `## Verification checklist` row are checked with concrete evidence.
- Open questions: none (the initial design decisions and the three plan-review architecture
  decisions - lazy render-site scan, unique-match-or-degrade, backward-chunked >=150 KB read - are
  all resolved above).
- Scope fence: `ocman/cli.py` (new `_active_session_for_process`, `_proc_start_epoch`,
  `_run_id_for_process`, `_latest_session_for_run`, `db_session_title`; `_attribute_session`
  reliable-first path; `_sess_str` title rendering; `-l` alias), `tests/test_ocman.py`,
  `README.md`, `CHANGELOG.md`, `DECISIONS.md`. Nothing else (no `--json` change, no TUI, no
  `kill`/`reconnect` selection change, no dependency).
- Honesty rule: paste the ACTUAL pytest output; paste the (redacted) real `lr -l` output for the
  manual check or state explicitly it was not run and why.
- Commits: path-scoped (`git commit -m msg -- ocman/cli.py tests/test_ocman.py README.md CHANGELOG.md DECISIONS.md <this ipd>`),
  never `git add -A`/`-a`, never push.
- Lifecycle: on completion + green tests, `git mv` this file pending/ -> executed/ and append an
  Execution record.
- Release: rides the in-flight line; covered by the eventual delta release-review. No tag / no
  release here.

## Detailed Implementation Checklist (TODO)
Execute top to bottom. Every box MUST be checked AND independently verified (see the Verification
checklist) before this plan may claim completion or move to `executed/`. Do NOT check a box on
intent; check it only when the action is actually done.

- [ ] C1 (RS-02) Add `_proc_start_epoch(pid)` using `/proc/uptime` + `/proc/<pid>/stat` field 22 via
  the `rfind(b")")` tail technique and `SC_CLK_TCK`; returns `None` on any error.
- [ ] C2 (RS-03) Add `_run_id_for_process(pid, cwd, start_epoch)` that reads
  `discover_storage_locations()["log_dir"]/opencode.log` and picks the `run=<uuid>` from a
  `creating instance`/`bootstrapping directory=<cwd>` line closest to start within 30s.
- [ ] C3 (RS-04) Add `_latest_session_for_run(run_id)` returning the last `session.id=ses_...` for
  that run; implement RS-03+RS-04 as a SINGLE bounded read of the log (one pass builds the maps),
  not a per-instance re-grep.
- [ ] C4 (RS-01) Add the reusable `_active_session_for_process(pid, cwd, *, verbosity=0)` tying
  C1-C3 together; own-user/`/proc` guarded; returns a `ses_...` id or `None`; never raises.
- [ ] C5 (RS-05) Add `db_session_title(sid)` (single `SELECT title`), corruption-tolerant, reusing
  `_get_sqlite()`/`OPENCODE_DB_PATH`; do NOT change `db_find_session`'s signature.
- [ ] C6 (RS-06) At the `--long` render site in `cli_list_running` (cli.py:13031), compute the
  reliable session per rendered row (batched via the single RS-04 read): on a resolved id build
  `{id,title,provenance:"log-active",...}` and render it; else render the existing `it["session"]`
  guess. Guard so any failure falls back to the guess. Do NOT modify `_attribute_session`.
- [ ] C7 (RS-09) Ensure the log scan is lazy: NOT triggered on the default `lr` or `--json` (only
  for the `--long`/`-l` Session render or a direct helper call). `--json` emits the existing guess dict.
- [ ] C8 (RS-07) Extend `_sess_str` to render `ses_... "Title" (provenance)` for the id+title shape
  (title quoted, truncated ~40 chars); keep id-only / `ids`/`count` / `unknown` shapes identical.
- [ ] C9 (RS-08) Add `-l` as a short alias for `--long` on the `running` subparser (same dest);
  update help text.
- [ ] C10 (RS-10) Docs: README `list running`/`lr` row (reliable session under `--long`/`-l`,
  caveat, `--json` unchanged); `--help`; `CHANGELOG.md` `[Unreleased]`; `DECISIONS.md` entry
  (method, `--json`-unchanged rationale, documented caveat).
- [ ] C11 (tests) Add the RS-02..RS-09 tests from the Validation plan.
- [ ] C12 Run `PYTHONPATH=. pytest -q` and PASTE the ACTUAL runner output into the Execution record.
- [ ] C13 Manual Linux check: `ocman lr -l` against a live opencode shows `ses_... "Title"
  (log-active)`; paste redacted output or state it was not run and why.
- [ ] C14 No em/en dash in the USER-FACING material changed (README, `--help`/CLI text, CHANGELOG,
  DECISIONS); run `aw sanitize --agent` over changed tracked files (clean). The prose convention is
  scoped to user-facing output, not this IPD.

## Verification checklist (cross-check; concrete evidence per item)
Each row maps 1:1 to the execution checklist and is satisfied ONLY by the concrete evidence named.
Do not mark this plan complete until every row has its evidence pasted or cited in the Execution
record.

- [ ] V1 (C1/RS-02) Paste the RS-02 test result: a `comm`-with-spaces `/proc` stat parses to the
  correct starttime; garbage/missing -> `None`. Cite `_proc_start_epoch` by `cli.py:<line>`.
- [ ] V2 (C2/RS-03) Paste the RS-03 test: closest-within-30s UNIQUE run chosen; >30s -> `None`;
  TWO runs matching the same `directory=<cwd>` in-window -> `None` (ambiguous -> degrade).
- [ ] V3 (C3/RS-04) Paste the RS-04 tests: last `session.id` returned; run with none -> `None`; the
  backward-chunked (>=150 KB step) search finds a startup line in an earlier chunk WITHOUT reading
  the whole file (seek/bytes accounting) and discards mid-chunk partial lines; AND the log is read
  ONCE for N instances (single accumulated pass).
- [ ] V4 (C4/RS-01) Cite `_active_session_for_process` by `cli.py:<line>`; paste a test showing it
  returns `None` (not an exception) when the log/`/proc` are unavailable.
- [ ] V5 (C5/RS-05) Paste the `db_session_title` test (seeded title, unknown id, missing DB) and
  confirm `db_find_session`'s signature/callers are unchanged (grep).
- [ ] V6 (C6/RS-06) Paste the render-site test: with `long_output=True` and the helper resolving an
  id, the `--long` Session column shows `ses_... "Title" (log-active)`; with the helper returning
  `None`, it shows the existing `it["session"]` guess; and grep-confirm `_attribute_session` is
  unchanged (no `log-active` path added to it).
- [ ] V7 (C7/RS-09) Paste the test proving the helper/log-reading seam is NOT called for plain `lr`
  and `lr --json`, and that `--json` output has no `title`/`log-active` (byte-compare to today's shape).
- [ ] V8 (C8/RS-07) Paste the `_sess_str` test: id+title shape renders `ses_... "Title" (log-active)`;
  id-only / `ids`/`count` / `unknown` render identical to today (guards `kill` + existing snapshots).
- [ ] V9 (C9/RS-08) Paste the parser test: both `lr -l` and `lr --long` set `running_long=True` and
  reach `cli_list_running(long_output=True)`.
- [ ] V10 (C10/RS-10) Quote the edited README row, CHANGELOG `[Unreleased]` entry, and DECISIONS
  entry showing the reliable session, the caveat, and the `--json`-unchanged decision; confirm
  `--help` updated.
- [ ] V11 (C12) Paste the FULL `pytest -q` summary line; new tests included and green, no masking skips.
- [ ] V12 (C13) Paste the redacted real `lr -l` output showing `ses_... "Title" (log-active)`, or an
  explicit statement it was not run and why.
- [ ] V13 (C14) Paste `aw sanitize --agent` (clean) for changed tracked files; confirm no em/en dash added.

## Deferred / open
- None. (JSON exposure, caveat engineering, log caching/indexing, cross-user, and Windows/macOS
  correlation are explicit non-goals for this IPD.)
