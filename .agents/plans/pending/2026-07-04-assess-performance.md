# IPD: Assess performance - ocman runtime/resource efficiency

- Date: 2026-07-04
- Concern: performance
- Scope: whole project (ocman.py CLI + ocman_tui), emphasis on the export/import,
  move, recovery/compaction, and history hot paths
- Status: PENDING (awaiting human approval; not executed)
- Author: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us

## Goal

Make ocman's most-expensive operations scale gracefully as opencode databases and
session transcripts grow, and make performance claims *measurable*. ocman is a
local single-user maintenance tool, so the bar is "fast enough and predictable for a
large personal DB / large sessions", not high-throughput serving. Optimize only where
there is concrete evidence of cost (complexity argument or measured), avoiding
speculative micro-optimization.

## Project conventions discovered (Step 0)

- Guiding principles: no dedicated file; universal fallback + the principles section in
  `ARCHITECTURE.md` (intuitive/self-documenting, configurable-over-hardcoded, KISS,
  honest docs).
- Pending-plans location/format used: `.agents/plans/pending/` (created this run; none
  existed). IPD named `YYYY-MM-DD-assess-<concern>.md`.
- Contributor/spec-sync contract: `AGENTS.md` (points to workflows index); README is the
  user-facing doc; CHANGELOG tracks releases.
- Stack: Python 3.10+, single-file CLI (`ocman.py`, ~8074 lines) + Textual TUI
  (`ocman_tui`), SQLite (pysqlite3 on Linux, stdlib fallback elsewhere). Validation:
  `PYTHONPATH=. pytest` (59 tests). No benchmarks exist.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for acting now.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| PERF-1 | High | Low | SW eng / architect | import (collision) | Per-diff-file `json.dumps` + full-string `str.replace` looped over every id in `id_map` → O(diffs × ids × len(diff)); re-scans whole JSON per id | ocman.py:5750-5755 |
| PERF-2 | Medium | Medium-High (functionality) | SW eng | recovery/compaction | `load_export_file`/`load_prior_context_files` read whole files into memory; exports can be tens of MB; downstream builds full Turn lists | ocman.py:1642, 3087 |
| PERF-3 | Medium | Low | SW eng | project/session move | `Path().resolve()` (fs syscalls) per session in a Python loop; move-session scans **all** sessions unscoped | ocman.py:5195-5209, 5261-5286 |
| PERF-4 | Low | Low | architect / power user | history sidecar | `runs` list grows unbounded; whole file loaded+rewritten each mutation (cumulative totals already precomputed) | ocman.py:6201-6260 |
| PERF-5 | Low | Low | SW eng | export temp files | Fixed-name temp JSONL per table in `gettempdir()`; concurrent same-session export could collide; leftovers on kill | ocman.py:5497-5518 |
| PERF-6 | Low | Low | SW eng / stakeholder | measurement | No benchmarks/metrics; optimizations are currently unverifiable and regressions undetectable | tests/ (none) |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | PERF-6 | Add an opt-in micro-benchmark (marker e.g. `@pytest.mark.benchmark`, skipped by default) that builds a synthetic large session subtree + diffs and times: (a) import-collision remap, (b) a large export parse, (c) a move on a many-session DB. Establishes a baseline before optimizing. | tests/test_perf.py (new) | Low | `pytest -m benchmark` runs and prints timings; default `pytest` unaffected (still 59 tests) |
| 2 | PERF-1 | Replace the whole-string replace-loop with a single structural remap: walk the parsed diff (dict/list/str) once and substitute exact-match ids via an `id_map` dict lookup (not substring replace). Preserves output; removes the per-id full-string pass. | ocman.py:5748-5758 | Low | Existing `test_import_session_with_collision` still passes; benchmark (step 1) shows lower time on the collision case; add a unit test asserting nested-id remap correctness |
| 3 | PERF-3 | Resolve the two path prefixes once; rewrite `session.directory` by string-prefix comparison without per-row `resolve()`. Scope `db_move_session_metadata`'s scan with `WHERE directory = ? OR directory LIKE ? ESCAPE ...` so only candidate rows are read. Keep exact current rebasing semantics (incl. the "resolve mismatch → skip" behavior, re-expressed without syscalls). | ocman.py:5187-5226, 5261-5287 | Low | `tests/test_move.py` still passes; add a test with a non-candidate session confirming it is untouched and not scanned into the rewrite; benchmark shows fewer stats/rows |
| 4 | PERF-4 | Cap retained detailed `runs` to a configurable `history_max_runs` (default e.g. 500), trimming oldest on save; keep `cumulative` totals intact. Document the key in README + `ocman.toml` template. | ocman.py:6201-6260, DEFAULT_CONFIG, README.md | Low | New test: after N+K runs, only N retained and cumulative unchanged; config precedence test |
| 5 | PERF-5 | Write export temp JSONL into a per-run `tempfile.mkdtemp` dir and `shutil.rmtree` it in a `finally`; removes fixed-name collision + orphan risk. | ocman.py:5497-5518 | Low | `test_bundle_session_data` still passes; add a test asserting no leftover temp files after export and after a simulated mid-export error |
| 6 | PERF-6 | Re-run the step-1 benchmark after steps 2-3 and record before/after numbers in the executing plan's validation notes. | tests/test_perf.py | Low | Before/after timings recorded; no default-suite regression |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| PERF-2 | Medium-High | functionality | A true streaming/incremental parse of exports/turns would restructure the core recovery pipeline (`load_export_file` → `find_turns` → render), risking correctness of a central feature. The limitation is already documented (README, 1.0.3). | Only pursue if the step-1 benchmark or a real user report shows genuine memory/CPU pain; then design a streaming parser behind the same API with golden-file regression tests. |

## Scope check

- **Over-scope (avoid):** Do not introduce a caching layer, async/threaded import, an
  ORM, or a new serialization format — none are traceable to a demonstrated need and all
  add complexity (KISS). Do not micro-optimize `render_transcript` (already uses
  list-join, not string concatenation) or the DB delete/cleanup paths (already chunk at
  999 to respect SQLite variable limits and stream via `fetchmany`).
- **Under-scope (add):** The missing benchmark harness (PERF-6) is a real gap — without
  it, PERF-1/PERF-3 improvements are unverifiable; adding it is proposed above.

## Required tests / validation

- Default suite `PYTHONPATH=. pytest` must remain green (currently 59 tests) and must
  not include the benchmark by default.
- New: benchmark module (opt-in), collision-remap correctness test, move-scope test,
  history-cap test, export-temp-cleanup test.
- For PERF-1 and PERF-3, correctness is preserved (same DB/diff output); the benchmark
  provides the measurable improvement evidence the lens requires.

## Spec / documentation sync

- PERF-4 adds a config key (`history_max_runs`): update README config template and the
  `DEFAULT_CONFIG`/`ocman.toml` docs.
- No user-visible behavior change for PERF-1/2/3/5 (same outputs, faster/leaner); no doc
  change required beyond a CHANGELOG entry when executed.

## Open questions

1. Preferred default for `history_max_runs` (proposed 500) — or keep unbounded and only
   document the growth? (Assumption: a bounded default is friendlier; confirm.)
2. Is import-collision with large subtrees a real usage pattern for you, or rare? This
   affects how much PERF-1 matters in practice (the complexity argument stands regardless).
3. Should the benchmark live in `tests/` (opt-in marker) or a separate `benchmarks/`
   directory? (Assumption: `tests/` with a marker, to reuse fixtures.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes (benchmark first for a baseline), run the
   validation, and sync docs for PERF-4.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
