# 02 Execution Plan (how this review runs)

## Nature of this run
Follow-up release review focused on the **delta since v1.0.3** and cutting **1.0.4**. Not a from-scratch
audit — the prior run (20260703-134213) covered the full baseline; this run re-grounds on the changed code
and the release-hygiene delta. Serial single pass, no parallel lanes (small cohesive delta).

## Approach
- Section 2: re-open and audit the delta code paths (worker guard `_safe_call_from_thread`; structural
  `_remap_ids_in_json`; shared `_rebased_dir`; `history_max_runs` trim; per-run export temp dir; compaction
  fix; `save_ocman_config` merge). MEM/LIVE lens on move/delete/import/compaction.
- Sections 3-6: confirm tests cover the delta, docs are honest (CHANGELOG `[Unreleased]`), principles/cold-start
  intact, packaging/version correct.
- Section 7: primarily the 1.0.4 version bump + CHANGELOG heading (S1-A1); other fixes only if the audit finds them.
- Validation: `PYTHONPATH=. pytest` (91 pass baseline). Local commits; NO push (no permission).

## Non-goals
- No re-litigation of prior-run findings already fixed. No execution of the pending disk-usage IPD (separate
  approval). No changes to out-of-scope framework dirs.
