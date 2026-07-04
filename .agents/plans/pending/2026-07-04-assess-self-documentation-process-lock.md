# IPD: Assess self-documentation - informative "opencode is running" process-lock report

- Date: 2026-07-04
- Concern: self-documentation (learn-as-you-go; "errors that teach")
- Scope: NARROWED (user request) to the running-opencode detection that blocks
  `--delete` / `--delete-project` / `--clean`, and the message it prints.
- Status: PENDING (awaiting human approval; not executed)
- Author: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us

## Goal

When ocman refuses a destructive op because opencode is running, the error should **tell
the user what is running and how to act** — not just print one generic line. The user
wants, per running process: PID, TTY (if any), CWD, and a "when did it start / how long
running" signal, plus an accurate count (a dozen running should show a dozen, not one
warning). Constraint: gathering this must be fast (~≤2s), no deep/recursive analysis.

## Project conventions discovered (Step 0)

- Guiding principles: none dedicated; universal fallback + `ARCHITECTURE.md`. This request
  is squarely the **"errors that teach"** self-documentation bar.
- Pending-plans: `.agents/plans/pending/`; validation `PYTHONPATH=. pytest`.
- Current behavior (verified): all three destructive paths run
  `pgrep -f "opencode --continue"` and, on returncode 0, raise a single fixed message
  ("Active 'opencode --continue' process detected. Please close OpenCode... Use --force").
  Duplicated at `ocman.py:4599-4609` (delete-session), `4847-4856` (delete-project),
  `5847-5856` (cleanup). Windows skips the check (`sys.platform=='win32'`).
- Feasibility probe (Linux): `ps -o pid,tty,etimes,lstart,args` gives PID/TTY/elapsed/start/
  command cheaply; `/proc/<pid>/cwd` (readlink) gives CWD. All fast, no recursion.

## Findings

| ID | Severity | Rem. Risk | Persona | Finding | Evidence |
|----|----------|-----------|---------|---------|----------|
| SD-1 | Medium | Low | novice / UI-UX | Process-lock error is one generic line regardless of count; no PID/CWD/TTY/start info to act on | ocman.py:4605-4609, 4853-4856, 5853-5856 |
| SD-2 | Low | Low | software engineer | Detection logic copy-pasted in 3 sites | ocman.py:4599-4609, 4847-4856, 5847-5856 |
| SD-3 | Medium | Low | QA / power user | `pgrep -f` matches any command line containing the substring (false positives, incl. ocman's own helpers/editors) | ocman.py:4600 |
| SD-4 | Low | Medium-High (functionality) | power user | Per-process opencode **session id** is not reliably derivable from ps/proc | (no stable source) |
| SD-5 | Low | Medium (functionality) | power user | True "last activity" time is not cheaply/reliably available | /proc/<pid>/stat, platform-specific |
| SD-6 | Low | Low | operator | Must stay cross-platform + within ~2s (no deep recursion) | ocman.py:4596 win32 skip |
| SD-7 | Low | Low | novice | Keep/clarify the actionable `--force` + "close these PIDs" guidance | ocman.py:4608 |

## Proposed changes (ordered, validatable)

| Step | Source IDs | Change | Files | Rem. Risk | Validation |
|------|-----------|--------|-------|-----------|------------|
| 1 | SD-2, SD-3, SD-6 | Add one helper `detect_running_opencode() -> list[dict]` returning per-process `{pid, tty, cwd, started, elapsed, cmdline}`. Implement via a single `ps -eo pid,tty,etimes,lstart,args` call (parse output), add CWD from `/proc/<pid>/cwd` on Linux (best-effort readlink), filter to plausible opencode processes (argv contains `opencode` as the program + a `continue`/session arg — not a bare substring match), and exclude the current process and its ancestors. Hard-timeout the `ps` call (e.g. 3s); on any failure degrade to returning PIDs-only or an empty list (never crash the delete flow). No per-process forking beyond the cheap cwd readlink. | ocman.py | Low | Unit test parsing a canned `ps` output into the expected dicts; test the plausible-process filter rejects a substring-only match; test graceful-degrade when `ps` missing |
| 2 | SD-1, SD-7 | Add `format_running_opencode(procs) -> str` producing a readable block: a count header ("N opencode process(es) are running:") then one line per process — `PID <pid>  tty <tty>  up <elapsed>  started <ts>  cwd <cwd>`. Footer: "Close the processes above, or re-run with --force to bypass this safety check." | ocman.py | Low | Unit test: given N proc dicts, output has the count, one line per PID, and the footer |
| 3 | SD-4 (partial) | Best-effort project attribution: for each proc CWD, look up a matching `project.worktree` (prefix match) in the DB and append `-> project <name/id>` when found. Do NOT print a session id (not reliably derivable). Add a one-line note that the mapping is best-effort by CWD. | ocman.py | Low | Test: a proc whose cwd is under a seeded project worktree shows that project; unknown cwd shows no project |
| 4 | SD-1, SD-2, SD-7 | Replace the three duplicated `pgrep` blocks so that when processes are found (and not `--force`), they raise `RecoveryError(format_running_opencode(...))`. Preserve exact current control flow: found + not force -> raise; `--force` -> bypass; none -> proceed. Keep the `RecoveryError` type and the win32 skip. | ocman.py:4595-4612, 4843-4860, 5843-5860 | Low | Existing delete/cleanup tests still pass; add a test that monkeypatches the detector to return 2 procs and asserts the raised message lists both PIDs |
| 5 | docs | Document the richer process-lock output in README (delete/cleanup safety section) + note the best-effort/`--force` behavior. CHANGELOG `[Unreleased]` entry. | README.md, CHANGELOG.md | Low | Docs only |

## Deferred / out of scope (with reason)

| Finding ID | Rem. Risk | Axis | Reason | Recommended later step |
|------------|-----------|------|--------|------------------------|
| SD-4 (per-process **session id**) | Medium-High | functionality | opencode does not expose the running session id via a documented/stable process signal; printing one would be a guess and could mislead a destructive-op decision. Best-effort *project* attribution by CWD is proposed instead (step 3). | If opencode later exposes session id (pidfile/env/socket), add it then. |
| SD-5 (true **last-activity** time) | Medium | functionality | "When it last did something" (CPU/IO) is fuzzy, platform-specific, and not cheaply reliable within the 2s budget. | Report START time + elapsed (exact, cheap) instead; revisit if a reliable cheap signal appears. |

## Scope check

- **Over-scope (avoid):** No new dependency (parse `ps`; use `/proc` on Linux). No psutil.
  No continuous monitoring, no killing processes for the user, no deep `/proc` walking.
- **Under-scope (add):** count + per-process PID/TTY/CWD/start/elapsed (SD-1) and de-duplication
  (SD-2) and false-positive filtering (SD-3) are the core of the request and are proposed.

## Required tests / validation

- `PYTHONPATH=. pytest` stays green + new unit tests: `ps`-output parser, plausible-process
  filter (rejects substring-only false positives; excludes self), formatter (count + per-PID
  lines + footer), CWD->project attribution, and a delete-flow test (monkeypatched detector
  returns 2 procs -> raised message lists both, `--force` bypasses). Tests must not depend on
  a real opencode process — feed canned `ps` output / monkeypatch the detector.

## Spec / documentation sync

- README delete/cleanup safety section describes the richer listing; CHANGELOG `[Unreleased]`.

## Open questions

1. Confirm the fields to show per process: PID, TTY, CWD, started + elapsed, and best-effort
   project (from CWD). Session id and true last-activity are proposed as **deferred** (SD-4/SD-5)
   because they are not reliably/cheaply obtainable — is best-effort project attribution an
   acceptable substitute for "session id"? (Assumption: yes.)
2. Should the plausible-opencode filter be strict (argv0 basename == `opencode`) or lenient
   (any argv token `opencode` + a `continue`/session arg)? (Assumption: match the program name
   `opencode` with a continue/session arg; documented.)
3. macOS has no `/proc`, so CWD there needs `lsof -p <pid>` (an extra call) or is omitted.
   Acceptable to omit CWD on macOS (show PID/TTY/start) to stay within the time budget?
   (Assumption: omit CWD on non-Linux rather than pay `lsof` cost.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered steps and run the validation.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
