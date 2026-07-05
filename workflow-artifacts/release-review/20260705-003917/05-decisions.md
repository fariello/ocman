# 05 Decisions & assumptions

## Scope / mode
- DEC: Serial single-pass review (no parallel audit lanes) — repo is one large module + one TUI package; a
  single reviewer keeps synthesis simple. (00-run-protocol allows serial; recorded per rule.)
- DEC: Review focuses on the `v1.0.4..HEAD` delta as a follow-up review (two prior runs shipped 1.0.4), while
  still running every section and re-checking carry-in residuals.
- DEC: Framework (`.agents/workflows/`) and `workflow-artifacts/` are OUT of scope per 00-run-protocol.

## Assumptions (to confirm with user)
- Q (target version): user referred to "1.0.5". The delta is bug fixes + additive, backward-compatible
  features (no breaking change), so semver patch (1.0.5) is defensible; a minor (1.1.0) is also reasonable to
  signal the new features. VERSION CHOICE IS DEFERRED TO THE USER at Section 9 (this run does not bump).
- Q (conversation intent): ocman-vs-ocgc positioning ("ocman actually reclaims ~95%+ of the space ocgc
  leaves behind, in DB and filesystem") is USER-STATED intent from this session. Treated as intent evidence
  for docs; the *reclaim* behavior itself is verified against code (vacuum/orphan-prune/delete paths) before
  any doc claim is committed. Marked "inferred from conversation, confirm before publishing" where used.

## Standing constraints
- No Section 9 this run (no bump/tag/push/publish). User performs release after sign-off.
- No remote push (permission not granted for this run).

## Conflicts
- None between section files and protocol observed yet.
