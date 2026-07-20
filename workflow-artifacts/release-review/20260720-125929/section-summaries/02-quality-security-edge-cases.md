# Section 2 - Quality, Security, Edge Cases (per-phase report)

## What I did

- Isolated the exact product-code delta since the prior GO (`git diff 2554395..HEAD --
  ocman/ pyproject.toml`): it is ONLY (a) the macOS firmlink import-rebase fix in
  `extract_and_import_project` (route through `_rebased_dir`, lexical fallback retained) and
  (b) the `vistab>=1.1.3` -> `>=1.3.0` dependency floor.
- Read `_rebased_dir` (`cli.py:9749`) and the fix site (`cli.py:10751-10778`) and reasoned
  through correctness and edge cases (equal-prefix, nested, unrelated, unresolvable dirs).
- Traced MEM/resource handling in `extract_and_import_project`: context-managed `zipfile`,
  `conn.close()` in `finally`, transaction with `commit`/`rollback`, pre-mutation rollback
  backup. The fix adds no new resource acquisition.
- Ran the mandatory committed-secrets scan two ways: gitleaks (authoritative, 372 commits)
  and the built-in `scan_secrets.py`. Saved output to `secrets-scan.json`.
- Filed S2-B1 (delta fix correct) and S2-S1 (secret candidates are known synthetic fixtures).

## Why

- A re-review's correctness risk is concentrated in what changed. The delta is tiny and I
  verified it directly rather than re-auditing the whole 16.4k-line module (already reviewed
  at the prior GO).
- The secret scan is a MUST every run; git history can hide secrets even when the tree is clean.

## Findings

- S2-B1 (B, Medium sev / Low RR, completed): macOS firmlink rebase fix is correct; the
  fallback never rebases an unrelated dir, so no behavior regression. No data-loss/overwrite
  path (import already makes a rollback backup + runs in a transaction). No MEM/LIVE regression.
- S2-S1 (S, Low / Low, not_applicable): 22 built-in "high" secret candidates are the synthetic
  `AKIA1234567890123456` / `ghp_12345678901234567890` fixtures inside
  `test_scan_and_redact_secrets` (and history), already baselined in `.gitleaksignore`;
  gitleaks reports no leaks. Confirmed false positives.

## What I considered but did NOT do

- **Full cold re-audit of the entire codebase:** not done. The prior GO reviewed v1.2.0; the
  loop-guard/convergence principle scopes this run to the delta plus sanity. The unchanged
  code carries the prior run's assessment.
- **Purging the synthetic fixtures from git history:** not done and not warranted. They are
  fabricated test data, not real secrets; history rewrite is a disruptive operator action with
  no security benefit here.
- **New edge-case tests for the rebase beyond the added regression test:** the OS-agnostic
  regression test (mutation-checked) already covers the canonicalization case; Section 3 confirms.
