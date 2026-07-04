# Evidence - assess-self-documentation (process-lock) 20260704-175217

Read-only assessment. No code changed.

## Inspected (code)
- The three process-lock checks: `ocman.py:4595-4612` (delete-session), `4843-4860` (delete-project),
  `5843-5860` (cleanup). All run `subprocess.run(["pgrep","-f","opencode --continue"], ...)` and, on
  returncode 0, `raise RecoveryError("Active 'opencode --continue' process detected. Please close OpenCode...
  Use --force ...")` — identical text, returncode-only (no count, no per-process detail).
- Windows skip: `if not force and sys.platform != "win32":` (4596).
- `--force` flag: `ocman.py:4206-4208`.

## Feasibility probes (Linux, this host)
- `ps -eo pid,tty,etimes,lstart,args` → PID, controlling TTY, elapsed seconds, start timestamp, full command.
- `/proc/<pid>/cwd` readlink → working directory (fast, per-process, no recursion).
- Confirmed `pgrep -f "opencode --continue"` **false-positive risk**: it matched this assessment's own shell
  probe command (which merely contained the string), demonstrating SD-3.
- No opencode was genuinely running during the probe; the only match was the probe itself → reinforces the
  need for a plausible-process filter + self-exclusion.

## Not reliably obtainable (grounds the deferrals)
- Per-process opencode **session id**: not present in `ps` args or a documented env/pidfile signal → SD-4.
- True **last-activity** time: `/proc/<pid>/stat` CPU times exist but interpreting them as "last did something"
  is fuzzy and Linux-only → SD-5. Start time + elapsed are the cheap, exact substitute.

## Commands run
- `date`, `git status --short` (clean), `grep` for the pgrep sites, `ps`/`pgrep -af`/`readlink /proc/<pid>/cwd`
  feasibility probes, `uname -s`, `command -v ps`.

## Sampling / truncation notes
- Read the three check blocks in full; did not re-read the whole 8000-line file (targeted, needle inspection).
