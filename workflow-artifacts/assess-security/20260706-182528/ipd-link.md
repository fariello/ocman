# IPD link - assess-security (filter + migration) run 20260706-182528

- IPD: `.agents/plans/pending/20260706-assess-security-filter-and-migration.md`
- Summary: Security assessment of the new `ocman filter` command and
  `scripts/migrate_recovery_names.py`. Headline: `_safe_destination`'s path-containment is a
  structural no-op (SEC-1, High/Low-risk); plus symlinked-dir escape (SEC-2), unbounded LLM
  egress with no non-interactive confirm (SEC-3), an uncaught decode error (SEC-4), and minor
  TOCTOU/redundant-backup notes (SEC-5/6). All fixes are low Remediation Risk; heavy FD-level
  TOCTOU hardening deferred on the complexity axis. Verdict: needs work.
