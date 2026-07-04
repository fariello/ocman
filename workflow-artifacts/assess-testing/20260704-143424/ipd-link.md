# IPD link

- IPD: `.agents/plans/pending/2026-07-04-assess-testing.md`
- Summary: Testing IPD proposing 9 low-risk test additions targeting the untested
  recovery/compaction pipeline (export-parser fixture + `find_turns`, renderers,
  `call_compaction_api` mock, end-to-end recovery, config-parsing helpers, estimators,
  legacy-import round-trip, benchmark docs). TEST-1 forces a fix for a real shipped bug in
  the TUI compaction call (`call_compaction_api` wrong arity + str-treated-as-dict).
  Deferred: coverage gating (Medium-High functionality risk).
- Verdict: needs work.
