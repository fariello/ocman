# IPD: Assess self-documentation - informative "opencode is running" process-lock report

- Date: 2026-07-04
- Concern: self-documentation (learn-as-you-go; "errors that teach")
- Scope: NARROWED (user request) to the running-opencode detection that blocks
  `--delete` / `--delete-project` / `--clean`, and the message it prints.
- Status: EXECUTED (2026-07-04; implemented per the plan-reviewed steps)
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
| SD-8 | Medium | Low | QA / architect | **Safety-gate semantics must be preserved (added in plan-review).** The current check *fails open*: the `except Exception: if isinstance(e, RecoveryError): raise; pass` at ocman.py:4610-4613 swallows any non-RecoveryError and lets the destructive op proceed if the check itself errors. The new detector MUST replicate this (a `ps` failure/timeout must not block a delete) and MUST NOT raise its own non-RecoveryError into the caller. | ocman.py:4610-4613, 4858-4861, 5858-5861 |
| SD-9 | Medium | Low | QA / stakeholder | **Filter direction is safety-critical (added in plan-review).** SD-3's plausible-process filter reduces false *positives*, but on a destructive-op **gate** an over-tight filter creates false *negatives* (a real running opencode is missed → op proceeds → potential data loss). The gate decision must err toward inclusion; only the *display* may be conservatively labelled. | ocman.py:4605 (gate on returncode) |
| SD-10 | Low | Low | software engineer | CWD→project match must be path-aware (added in plan-review). Naive string-prefix (`/a/b` vs `/a/bc`) mismatches; use resolved-path containment, consistent with the existing `_rebased_dir` approach. | ocman.py:5159 db_find_project; `_rebased_dir` |

## Proposed changes (ordered, validatable)

| Step | Source IDs | Change | Files | Rem. Risk | Validation |
|------|-----------|--------|-------|-----------|------------|
| 1 | SD-2, SD-3, SD-6 | Add one helper `detect_running_opencode() -> list[dict]` returning per-process `{pid, tty, cwd, started, elapsed, cmdline}`. Implement via a single `ps -eo pid,tty,etimes,lstart,args` call (parse output), add CWD from `/proc/<pid>/cwd` on Linux (best-effort readlink), filter to plausible opencode processes (argv contains `opencode` as the program + a `continue`/session arg — not a bare substring match), and exclude the current process and its ancestors. Hard-timeout the `ps` call (e.g. 3s); on any failure degrade to returning PIDs-only or an empty list (never crash the delete flow). No per-process forking beyond the cheap cwd readlink. | ocman.py | Low | Unit test parsing a canned `ps` output into the expected dicts; test the plausible-process filter rejects a substring-only match; test graceful-degrade when `ps` missing |
| 2 | SD-1, SD-7 | Add `format_running_opencode(procs) -> str` producing a readable block: a count header ("N opencode process(es) are running:") then one line per process — `PID <pid>  tty <tty>  up <elapsed>  started <ts>  cwd <cwd>`. Footer: "Close the processes above, or re-run with --force to bypass this safety check." | ocman.py | Low | Unit test: given N proc dicts, output has the count, one line per PID, and the footer |
| 3 | SD-4 (partial), SD-10 | Best-effort project attribution: for each proc CWD, map to a `project.worktree` using **path-aware containment** (resolve both, then `Path.is_relative_to`/`relative_to` — NOT naive string prefix, to avoid `/a/b` vs `/a/bc` mismatches), consistent with the existing `_rebased_dir` logic. Append `-> project <name/id>` when found. Do NOT print a session id (not reliably derivable). One-line "best-effort by CWD" note. | ocman.py | Low | Test: proc cwd nested under a seeded worktree shows that project; a sibling path like `/a/bc` vs worktree `/a/b` does NOT match; unknown cwd shows no project |
| 4 | SD-1, SD-2, SD-7, SD-8, SD-9 | Replace the three duplicated `pgrep` blocks with the helper. **Preserve the exact gate semantics:** found+!force → raise `RecoveryError(format_running_opencode(...))`; `--force` → bypass; none → proceed; win32 → skip. **Preserve fail-open (SD-8):** the detector must be wrapped so that if enumeration itself errors/times out, the op proceeds (as today) — the detector returns `[]`/PIDs-only on failure and never raises a non-RecoveryError into the caller. **Preserve gate strength (SD-9):** the gate fires whenever a plausible opencode process is found; the plausibility filter must not be so strict that a genuine running instance is missed (err toward inclusion for the gate; conservative labelling only in display). | ocman.py:4595-4613, 4843-4861, 5843-5861 | Low | Existing delete/cleanup tests pass; monkeypatched detector returns 2 procs → message lists both PIDs and op refuses; `--force` bypasses; detector raising an internal error → op still proceeds (fail-open preserved) |
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

- `PYTHONPATH=. pytest` stays green + new unit tests. The detector MUST be testable without
  spawning real `ps` or depending on the OS — inject/monkeypatch the command-runner and feed
  **canned `ps` output** (SD-6/F determinism). Required cases:
  - `ps`-output parser → expected per-process dicts.
  - Plausibility filter: rejects a bare substring-only match (SD-3) and excludes self, **but a
    genuine `opencode ... continue` line IS matched** (SD-9 regression guard — the gate must not
    drop a real instance).
  - Formatter: count header + one line per PID + actionable footer.
  - CWD→project: nested cwd matches; sibling `/a/bc` vs worktree `/a/b` does NOT match (SD-10);
    unknown cwd → no project.
  - **Gate behavior (SD-8):** detector returns 2 procs → destructive op raises and message lists
    both PIDs; `--force` → bypass; **detector raising internally → op still proceeds (fail-open),
    matching current behavior**; timeout → fail-open, no hang.
- Timestamps rendered with the same `datetime.fromtimestamp(...).strftime('%Y-%m-%d %H:%M:%S')`
  convention used elsewhere in `db_show_info` (PR-6 consistency).

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
4. On the filter-direction tension (SD-9): confirm the gate should **err toward inclusion**
   (over-warn rather than risk missing a real running instance on a destructive op). The lenient
   filter (Q2) is consistent with this; strict argv0 matching is NOT recommended for the gate.
   (Assumption: err toward inclusion for the gate.)

## Plan-review provenance (2026-07-04)

Hardened by the `plan-review` workflow (run 20260704-180500) after re-reading the three check
sites (ocman.py:4595-4613, 4843-4861, 5843-5861). Changes applied:

- **Added SD-8 (safety-gate fail-open semantics):** the current check swallows non-RecoveryError
  exceptions and proceeds if the check itself errors. Step 4 now explicitly requires the new
  detector to preserve fail-open (a `ps` failure/timeout must not block a delete) and never raise
  a non-RecoveryError into the caller.
- **Added SD-9 (filter-direction is safety-critical):** on a destructive-op gate, an over-tight
  plausible-process filter risks a false negative (missing a real instance → data loss). Step 4 +
  tests now require the gate to err toward inclusion, with a regression test that a genuine
  `opencode continue` line is still matched.
- **Added SD-10 (path-aware CWD→project match):** step 3 now uses resolved-path containment
  (`is_relative_to`), not naive string prefix, with a sibling-path test.
- **Tightened the test plan:** injectable command-runner (no real `ps`), fail-open + timeout tests,
  and the SD-9 regression guard.
- **PR-6 (consistency):** render timestamps with the existing `db_show_info` convention.

Verdict: APPROVE WITH REVISIONS APPLIED.

## Execution outcome (2026-07-04)

Executed with explicit user approval (open questions answered: full field set incl. best-effort
project; lenient filter erring toward inclusion; **omit CWD on macOS** — Linux `/proc` only, no
`lsof`; one shared helper wired to all 3 sites).

- **Step 1 (helper):** `detect_running_opencode()` runs one `ps -eo pid,tty,etimes,lstart,args`
  (3s timeout), parses rows, keeps those whose command names `opencode` + `continue` (lenient,
  SD-9), excludes ocman's own PID + parent, and reads CWD from `/proc/<pid>/cwd` on Linux only.
  Fails open (returns `[]`) on any error. Plus `_render_running_opencode()` (count header +
  per-process PID/TTY/uptime/started/CWD/→project + `--force` footer) and
  `check_opencode_process_lock(force, verbosity)` (raises `RecoveryError(render)` when found;
  skips on `force`/win32).
- **Step 3 (best-effort project):** `_project_for_cwd()` maps a CWD to a project via path-aware
  containment against DB `project.worktree` (resolve + `is_relative_to`, longest match wins).
  Session id (SD-4) and true last-activity (SD-5) remain **deferred** (not reliably obtainable);
  start time + elapsed and best-effort project are shown instead.
- **Step 4 (migration):** all three duplicated `pgrep` blocks (delete-session, delete-project,
  clean/clean-orphans) replaced with `check_opencode_process_lock(force, verbosity)`. `force`
  still bypasses ONLY the lock; fail-open preserved.
- **Docs:** CHANGELOG entry. (ARCHITECTURE already documents the process-lock at a high level.)
- Tests: gate refuses when detected + !force; `--force` bypasses (ps never runs); detector error
  → fail-open (op proceeds); detector filter keeps genuine `opencode --continue`, excludes self /
  `vim ...opencode...` / `opencode serve`; renderer lists each process + footer.
- Validation: `PYTHONPATH=. pytest` → 115 passed, 2 skipped.

Deferred (unchanged): SD-4 per-process session id (Medium-High / functionality — not reliably
derivable), SD-5 true last-activity (Medium / functionality). macOS CWD intentionally omitted
(would require a per-process `lsof`; too slow for the ~2s budget).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered steps and run the validation.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
