# Persona Review

## Section 1 (inventory) — seed
- Stakeholder (8): v1.0.3 shipped with TUI compaction broken; cutting 1.0.4 with the fix is the key outcome.
- Software engineer (5): delta is well-tested (91 tests) and went through plan-review; low residual risk.
- Testing expert (2): new recovery/compaction + config-parsing test suites materially raise confidence.

## Section 2 (quality/security/edge/MEM/LIVE — delta audit)
- **QA/QC (1):** Re-read the delta paths (worker guard, compaction fix, history trim). The compaction fix
  is correct and test-covered; no new happy-path-only defect found in the delta.
- **Software engineer (5):** `_safe_call_from_thread` guard is sound (shutdown flag + RuntimeError catch);
  minor broad-catch note (S2-M1, defer — narrowing is fragile). Structural remap, `_rebased_dir`, history
  trim (on-save only), per-run export temp dir all preserve behavior and were validated by tests.
- **Security-minded architect (4):** Ran the mandatory committed-secrets scan (built-in + gitleaks).
  **gitleaks: no leaks in 156 commits.** Built-in 1582 hits are entropy/ID/timestamp false positives — the
  domain is session IDs/hashes (S2-S1). No SQLi/path/deserialization regression in the delta; import/restore
  guards (from prior run) unchanged.
- MEM/LIVE: delta introduced no new leak/data-integrity surface; the export temp-dir change *improved* resource
  hygiene. No new `LIVE`/High finding.

## Section 3 (tests/regression)
- **Testing/regression expert (2):** Delta is well-covered — new recovery/compaction + config-parsing suites,
  plus regression tests for every prior High/LIVE finding (compaction, worker guard, zip-slip, delete-summary,
  history cap, legacy import, non-canonical move). 91 passed under the documented invocation.
- **QA/QC (1):** Caught a real evidence subtlety (S3-R1): bare `pytest` can test an *installed* copy; the
  documented `PYTHONPATH=. pytest` and CI (editable install) are correct. Not a code defect.

## Section 4 (docs/specs)
- **Novice (7):** README delta additions (Known Limitations, benchmark opt-in, `history_max_runs`) are clear
  and present. No new manual-required task introduced.
- **UI/UX (3):** CHANGELOG `[Unreleased]` honestly describes the delta; the one gap is the version heading (S1-A1).

## Section 5 (feature/usability/maintainability — all eight, delta lens)
- **Stakeholder (8):** The delta delivers real value — TUI compaction now works (was broken in 1.0.3), perf
  improved, backups history bounded. Fit for a 1.0.4 patch.
- **Power user (6):** New `history_max_runs` config is a welcome control; no capability regressions.
- **Architect (4):** Delta reduced duplication (shared `_rebased_dir`) and simplified the remap — net KISS-positive.
- **Software engineer (5):** Maintainability improved; only minor S2-M1 (broad catch) deferred.
- No new feature gap for this release. (The disk-usage capability the user asked about is a separate,
  planning-approved IPD — not a 1.0.4 blocker.)

## Section 6 (compatibility/packaging/release)
- **Operator (8):** `pip install ocman` + `ocman ui`; first-run `--create-config` works; new `history_max_runs`
  is optional/defaulted. 1.0.4 is a clean patch — no migration, no breaking change. Backups still grow (the
  user's 7.3 GB) but that visibility feature is a separate IPD, not a 1.0.4 gap.
- **Software engineer (5):** Version bump needed in 3 places (ocman.py, pyproject, ocman_tui fallback);
  single-sourcing means the fallback is belt-and-suspenders. CI is correctly configured (editable + PYTHONPATH).

## Section 8 (final eight-persona sign-off)
