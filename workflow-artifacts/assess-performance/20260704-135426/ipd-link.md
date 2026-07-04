# IPD link

- IPD: `.agents/plans/pending/2026-07-04-assess-performance.md`
- Summary: Performance IPD proposing 5 low-risk optimizations (add benchmark harness;
  replace O(diffs×ids) import-collision string-replace with a structural id remap; drop
  per-row `resolve()` and scope the move-session scan; cap history `runs`; per-run export
  temp dir) and deferring the export-streaming refactor (Medium-High functionality risk).
- Verdict: adequate; one High-severity algorithmic hot spot (PERF-1).
