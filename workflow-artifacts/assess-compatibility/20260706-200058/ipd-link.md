# IPD link - assess-compatibility run 20260706-200058

- IPD: `.agents/plans/pending/20260706-assess-compatibility-filter-and-naming.md`
- Summary: Compatibility assessment of the 1.1.0 naming work. Verdict needs work. COMP-1 (Medium):
  CLI writes canonical `YYYYMMDD-HHMM-<full_sid>.<kind>.md` but the TUI still writes
  `opencode-recovery-<sid[:8]>-<HHMMSS>.<kind>.md` + `.compact-prompt.md` - the rename widened a
  pre-existing CLI/TUI divergence and TUI output isn't migratable. COMP-2 (Medium): stale
  `.compact-prompt.md` lookup (ocman.py:8907) vs generated `.prompt.md`, works only by fallback.
  COMP-3 (Medium): case-sensitive suffix parse misses macOS `.RESTART.MD` (shared with edge-cases
  EC-5). COMP-4/6 positive (Windows-safe names; legacy forms readable). COMP-5: new config keys need
  safe defaults. Windows reserved-name sanitizer deferred (complexity). Proposes TUI/CLI naming
  unification + lookup fix + shared case-insensitive fix + config defaults + regression tests;
  recommends co-executing with the security + edge-cases IPDs.
