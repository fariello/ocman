# Assessment run report - performance (whole project)

- Date / run ID: 20260704-135426
- Concern: performance
- Scope: whole project (ocman.py CLI + ocman_tui); emphasis on export/import, move,
  recovery/compaction, history hot paths
- IPD written: .agents/plans/pending/2026-07-04-assess-performance.md
- Verdict: **adequate** for performance, with one **High**-severity algorithmic hot spot
  (import-collision remap) worth fixing and a missing benchmark harness to make perf
  claims measurable.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| PERF-1 | High | Low | SW eng / architect | Import-collision diff remap is O(diffs × ids × len(diff)) via json.dumps + full-string replace per id (ocman.py:5750-5755) |
| PERF-2 | Medium | Medium-High (functionality) | SW eng | Whole-file reads of exports/context into memory; scales with transcript size (ocman.py:1642, 3087) |
| PERF-3 | Medium | Low | SW eng | Per-session `Path().resolve()` syscalls in move loops; move-session scans all sessions unscoped (ocman.py:5195-5209, 5261-5286) |
| PERF-4 | Low | Low | architect | Unbounded history `runs` list; whole-file load+rewrite per mutation (ocman.py:6201-6260) |
| PERF-6 | Low | Low | SW eng / stakeholder | No benchmarks; optimizations unverifiable, regressions undetectable |

(Full list incl. PERF-5 in `findings.csv`.)

## Proposed plan (summary)

1. Add an opt-in benchmark harness (baseline) — PERF-6.
2. Replace import-collision string-replace loop with a single structural id remap — PERF-1.
3. Remove per-row `resolve()` and scope the move-session scan with a `WHERE` prefix — PERF-3.
4. Cap retained history `runs` (configurable) while keeping cumulative totals — PERF-4.
5. Use a per-run temp dir for export JSONL to avoid name collision/orphans — PERF-5.
6. Re-run the benchmark; record before/after — PERF-6.

## Deferred (with reason)

- PERF-2 (whole-file export/context reads): Remediation Risk **Medium-High** on
  **functionality** — a streaming parse would restructure the core recovery pipeline and
  risk correctness of a central feature. Already documented as a limitation (README,
  1.0.3). Pursue only if the benchmark or a real report shows genuine pain. (Effort is
  not the reason; correctness risk is.)

## Out-of-repo / organizational notes

- The export traceback that originally motivated attention (an `opencode export` failure)
  is an upstream opencode DB conflict, not an ocman performance issue; out of scope here.

## Next step

Review the IPD (optionally run `plan-review` on it) and approve before execution. This
workflow does not execute the plan.
