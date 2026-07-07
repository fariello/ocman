# Section 2: Quality, Security, Edge Cases

## What I did
- Ran the committed-secrets scan two ways: the built-in `scan_secrets.py` (1587 candidates, all
  low/medium, 0 high) and **gitleaks** over the working tree + 229 commits of history
  (**"no leaks found"** - authoritative). Triaged the built-in candidates: high-entropy strings =
  opencode session ids; "credit-card" mediums = `2026...` recovery-filename timestamps (false
  positives). No confirmed secret or PII. Saved `secrets-scan.json`.
- Re-read the 1.1.0 new code paths (not inferred from tests): `scan_for_secrets`,
  `check_egress_guards`, `resolve_recovery_collision`, `_safe_destination`, and `cli_filter`.
- Traced the LIVE surface: `resolve_recovery_collision` refuses to overwrite while opencode is
  running, else backs up (never deletes non-interactively) - protects a live session's file
  (S2-LIVE1, positive).
- Verified secret-scan redaction: hits are (kind, line) only; the error never echoes the value
  (S2-S1, positive; test-backed).
- Checked MEM: no leaks/unclosed handles in the new code; the size cap is checked before the
  in-memory secret scan, bounding it.

## Findings
- **S2-E1 (Low / RR Low):** `cli_filter` reads the whole file (`read_text`) before the size cap
  rejects it; the security IPD specified an `st_size` pre-check before reading. Local, user-chosen
  file, so no DoS - efficiency/spec-fidelity gap only. Fix in S7 (action S2-A1).
- **S2-S1, S2-LIVE1:** positive confirmations (no action).

## Why
- The 1.1.0 delta added an external-egress path and file-overwrite behavior; those are exactly the
  security/LIVE surfaces the protocol says to trace by reading code. Secrets in git history are the
  classic miss, so gitleaks over full history was run.

## What I considered but did NOT do
- Treating the 1587 built-in candidates as findings: no - triaged as false positives, corroborated
  by gitleaks 0-leaks. Recording them would be noise.
- Broad MEM audit of the whole 9k-line module: the non-delta code was reviewed at 1.0.5; focused on
  the delta here (recorded in execution plan).
- Installing trufflehog: gitleaks (installed) already gives authoritative history coverage.
- Recommending gitleaks-in-CI as a finding: noted for S6 ci-assessment instead (right owner).
