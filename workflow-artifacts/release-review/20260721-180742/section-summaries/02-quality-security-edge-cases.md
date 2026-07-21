# Section 2 - Quality, Security, Edge Cases

## What I did
- Traced the highest-risk new surfaces in the 1.3.0 delta by READING the code paths (not
  inferring from green tests), per the mandatory LIVE/MEM review:
  - Process signalling (`_reuse_guard_ok`, `_kill_pid_gracefully`, `_pid_is_gone`,
    `cli_reconnect`, `cli_kill`, `_kill_targets`, `_instance_matches_pattern`).
  - Server-auth security check (`_server_password_env_state`, `_probe_app_auth`,
    `_bind_is_loopback`, `detect_running_instances`).
  - Session rename DB path (`db_rename_session`).
- Ran the committed-secrets scan two ways: the built-in `scan_secrets.py` (953 heuristic hits,
  overwhelmingly low false positives, e.g. README docs of OPENCODE_SERVER_PASSWORD) AND the
  repo's authoritative scanner `gitleaks` over full history (3 hits).
- Triaged the 3 gitleaks hits: ALL in the PRIOR run's artifacts
  (`workflow-artifacts/release-review/20260720-125929/`), all the same synthetic AWS test-fixture
  strings already baselined for `tests/test_ocman.py`, echoed into that run's findings register
  and report text. Not live secrets (nothing to rotate). Confirmed `secret-scan.yml` CI is
  currently green (the action's default scan range does not hit them), so CI is not broken.

## Why
- The 1.3.0 cycle's defining risk is process signalling (reconnect/kill can stop the wrong
  process) and an auth-state probe that must never leak a password. These are exactly the
  live-interaction and security surfaces that green unit tests do not prove correct, so I read
  the runtime paths directly.
- The secrets scan is a mandatory MUST; gitleaks is the repo's authoritative scanner.

## Findings
- **S2-LIVE01** (not_applicable / traced-clear): signalling surface is correctly guarded
  (own-user via /proc st_uid + still-opencode re-check before EACH signal; zombie-aware gone
  check; require_opencode up front; survivor stops no-exec; one confirm; dry-run zero side
  effects; TOCTOU window narrow and documented). No defect.
- **S2-S02** (not_applicable / traced-clear): auth check reads password STATE only, owner-only
  /proc, probes only own loopback listeners, read-only GET /app, fails to "unknown". No leak.
- **S2-B01** (not_applicable / traced-clear): rename is atomic, injection-safe (bound param),
  closes the connection in finally. No defect / no MEM leak.
- **S2-S01** (identified, Low sev / Low RR): 3 non-baselined gitleaks hits in the PRIOR run's
  artifacts (synthetic fixtures). Fix = add 3 fingerprints to `.gitleaksignore` in Section 7.

## What I considered but did NOT do
- Did NOT fix S2-S01 here (audit-then-fix; Section 7 owns the edit).
- Did NOT treat the 953 built-in-scanner hits as findings: they are documented heuristic false
  positives (env-var docs, redacted fixture mentions); gitleaks is authoritative.
- Did NOT re-audit v1.2.0-and-earlier code broadly: this is a promotion review of the 1.3.0
  delta, and the prior release-review (20260720-125929) already audited the pre-1.3.0 surface.
- Did NOT open a MEM finding: the only new long-lived resource is the rename DB connection,
  which is closed in finally; reconnect/kill are short-lived one-shot commands.
- No in-code TODO/FIXME markers exist to triage (Section 1 confirmed 0).
