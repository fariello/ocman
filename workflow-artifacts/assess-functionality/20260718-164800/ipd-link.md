# IPD produced by this run

- IPD: `.agents/plans/pending/20260718-1648-01-assess-functionality-tui-parity.md`
- Summary: a phased plan to bring the Textual TUI to feature parity with the CLI. Phase 1
  closes the delete-safety gap (extract-on-delete + history-clear stub); Phase 2 adds a
  read-only doctor view and guarded reclaim; Phase 3 adds spend and running views; Phase 4
  adds multi-select batch actions, db clean --older-than/scope/extracts, and --chunk;
  Phase 5 adds project bundles, local move, backup clean, and content search. filter and
  advanced/remote move/rebase are deferred (gold-plating guard). Open questions include the
  release cut line (which phases gate release).
