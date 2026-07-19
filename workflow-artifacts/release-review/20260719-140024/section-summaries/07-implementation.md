# Section 7 - Implementation

## What I did
- A1 (S1-REL1): bumped the version 1.1.0 -> 1.2.0 in pyproject.toml and ocman/cli.py
  (`__version__`), and cut the CHANGELOG (`[Unreleased]` -> `## [1.2.0] - 2026-07-19`,
  keeping a fresh empty `[Unreleased]`).
- A2 (S2-S1): added the 6 confirmed-false-positive gitleaks fingerprints (synthetic
  AWS-key-shaped test fixtures) to `.gitleaksignore`, with a comment explaining they are not
  live secrets.
- A3 (S1-REL1): rebuilt the wheel as `ocman-1.2.0-py3-none-any.whl` (local, non-publishing).
- Re-validated: `ocman -V` -> 1.2.0; `gitleaks detect` -> no leaks; full suite 407 passed,
  2 skipped.
- Committed the product changes as 2554395 (kept separate from the run-artifact commits).

## Why
- These are the two findings from the audit (version bump + secret-scan baseline), both Low
  remediation risk and non-behavioral; fixing by default per the Fix Bar. The version bump
  is the substantive release-prep step; the gitleaks baseline keeps the secret-scan CI green
  after push.

## What I considered but did NOT do
- Any behavioral change: none - the audit found no B/MEM/LIVE/GP/KD/SCH defect to fix.
- Deferring anything: nothing cleared the Medium-High deferral bar; both actions were done.
- Publishing/tagging/pushing: prohibited until Section 9 after an explicit GO.
- Choosing a different version (2.0.0/1.1.1): 1.2.0 is correct (additive, no breaking
  changes, > the published 1.1.0). Assumed pending the maintainer's confirmation at the GO.
