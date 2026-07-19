# Section 2 - Quality, security, edge cases

## What I did
- Ran the mandatory committed-secrets scan two ways: the heuristic
  `tools/scan_secrets.py` (892 noisy candidates -> saved to secrets-scan.json) and the
  mature scanner `gitleaks` (installed; scanned all 348 commits, honoring the repo's
  .gitleaksignore). gitleaks reported 6 leaks, all `aws-access-token` in
  `tests/test_ocman.py`.
- Triaged the 6: confirmed they are SYNTHETIC test fixtures for ocman's own
  secret-redaction/scanning feature (e.g. "Here is my aws token AKIA... on this line"),
  not live credentials. Captured their fingerprints for a .gitleaksignore baseline.
  Filed S2-S1 (Medium sev / Low remediation risk): the empty .gitleaksignore means the
  secret-scan CI would flag these known false positives; remediation is BASELINE (not
  rotate/purge, since nothing is a real secret).
- Traced the release-relevant LIVE / MEM / security surfaces by reading code (not inferring
  from tests): destructive-op guards (all route through require_safe_to_mutate /
  check_opencode_process_lock / _reclaim_guard_db_writes); the LLM egress guard
  (check_egress_guards: size cap + secret scan; HTTPS-only for the API key); DB connection
  lifetimes (closed in finally; 30 connect / 37 close); and the new main() wrapper
  (re-raises SystemExit first so die()'s exit code propagates, then a clean catch-all).
- Triaged in-code TODO/FIXME markers: the 2 grep hits are false positives (ses_XXXX / [XXXXX]).

## Why
- Secret leakage and destructive/data-integrity surfaces are the highest-harm release
  risks; the runbook mandates a history-inclusive secret scan and reading the actual
  live-interaction/guard code paths rather than trusting green tests.

## What I considered but did NOT do
- Rotate/purge the gitleaks hits: not applicable - they are synthetic fixtures, not real
  secrets. Baseline is the correct action (S2-S1).
- A deep re-audit of every code path: most of the surface was reviewed change-by-change
  this session (each change went assess -> plan-review -> execute with tests); I focused on
  the release-new surfaces and found no new B/MEM/LIVE defect.
- Installing trufflehog: unnecessary - gitleaks (the CI scanner) is installed and
  authoritative here.
