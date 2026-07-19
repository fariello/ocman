# IPD produced by this run

- IPD: `.agents/plans/pending/20260719-0125-01-assess-self-documentation.md`
- Summary: 8 proposed in-product self-documentation fixes (accuracy-first). Fix two error
  strings that advertise removed flags (`--show-models`/`--list-projects`); add a top-level
  catch-all so an unexpected exception prints a clean message (traceback only under `-v`);
  teach the accepted duration formats at the failure site; add recovery hints to
  "Database/Session not found" and bare "Invalid selection" prompts; improve `reclaim`
  discoverability via the `help maintain` topic; and make two jargon-y TUI Storage buttons
  self-explaining. Renaming shipped jargon verbs/flags is deferred (compatibility axis).
