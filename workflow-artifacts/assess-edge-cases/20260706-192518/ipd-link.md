# IPD link - assess-edge-cases (filter + naming + migration) run 20260706-192518

- IPD: `.agents/plans/pending/20260706-assess-edge-cases-filter-and-naming.md`
- Summary: Edge-case assessment of the new 1.1.0 surface (canonical naming helpers, `filter`,
  migration script). Verdict adequate (safe by default). Findings: EC-1 (Medium) same-minute
  minute-precision collision on migration handled safely but confusingly; EC-2 empty-input sent to
  LLM; EC-3 whitespace-only `--scope` accepted; EC-4 unvalidated `kind`; EC-5 case-sensitive
  suffix; EC-6 8-digit-sid date-only ambiguity (theoretical); EC-7 (positive) invalid-date ->
  dt=None safe fallback. Seconds-precision revert deferred (functionality). Proposes low-risk
  guards + regression tests; recommends co-executing with the security IPD (shared cli_filter block).
