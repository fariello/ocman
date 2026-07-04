# IPD link

- IPD: `.agents/plans/pending/2026-07-04-assess-functionality-disk-usage.md`
- Summary: Functionality IPD (narrowed to disk-usage reporting) proposing a backups-usage
  section in `ocman info` and a `ocman info --by-project` breakdown of exact per-project
  session-diff bytes + row/token counts. Explicitly excludes per-project DB *bytes*
  (unmeasurable from a shared SQLite file; honest-docs). TUI parity deferred.
- Verdict: needs work.
