# IPD link

- IPD: `.agents/plans/pending/2026-07-04-assess-self-documentation-process-lock.md`
- Summary: Self-documentation IPD (narrowed to the "opencode is running" process-lock error) proposing a
  single `detect_running_opencode()` helper + formatter that lists each running process (count, PID, TTY, CWD,
  start/elapsed) with false-positive filtering and self-exclusion, replacing the 3 duplicated returncode-only
  `pgrep` checks. Best-effort CWD->project attribution instead of a (unreliable) session id; start+elapsed
  instead of (unreliable) last-activity. Deferred: per-process session id (SD-4, functionality) and true
  last-activity (SD-5, functionality).
- Verdict: needs work.
