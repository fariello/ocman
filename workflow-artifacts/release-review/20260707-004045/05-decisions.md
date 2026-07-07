# 05 Decisions (run 20260707-004045)

- DEC-1: Parallel audit lanes NOT used. Single maintainer, one primary module, and the review
  concentrates on a well-understood 1.1.0 delta just executed this session. Serial is clearer.
- DEC-2: Scope excludes `.agents/workflows/` (framework) and `workflow-artifacts/` (run records)
  per protocol. ocman is the subject, not the framework.
- DEC-3: Conversation context IS available (this session designed + executed the 1.1.0 work), used
  as a guarded secondary source for intent. Behavior verified against code/tests, not chat.
- DEC-4: This run treats the executed IPDs as input but independently re-verifies the shipped code
  (re-opening cli_filter, the naming helpers, egress/collision helpers, the TUI, the migration).
- DEC-5: Pre-existing static-analysis (LSP) noise (pysqlite3.connect, str|None, TUI NoSelection/
  DummySession duck-typing) is not treated as a finding; the runtime suite is green and these are
  known false positives for this stdlib/optional-dep + Textual codebase.
