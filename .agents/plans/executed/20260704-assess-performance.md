# IPD: Assess performance - ocman runtime/resource efficiency

- Date: 2026-07-04
- Concern: performance
- Scope: whole project (ocman.py CLI + ocman_tui), emphasis on the export/import,
  move, recovery/compaction, and history hot paths
- Status: EXECUTED (approved by user 2026-07-04; implemented — see Execution outcome below)
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
| PERF-1 | High | Low | SW eng / architect | import (collision) | Per-diff-file `json.dumps` + full-string `str.replace` looped over every id in `id_map` → O(diffs × ids × len(diff)); re-scans whole JSON per id. **Also latently incorrect:** substring `str.replace` can corrupt an id that is a substring of another id or that appears inside unrelated text. | ocman.py:5748-5758 (loop 5753-5754) |
| PERF-2 | Medium | Medium-High (functionality) | SW eng | recovery/compaction | `load_export_file`/`load_prior_context_files` read whole files into memory; exports can be tens of MB; downstream builds full Turn lists | ocman.py:1642, 3087 |
| PERF-3 | Medium | Low | SW eng | project/session move + rebase | `Path().resolve()` (fs syscalls) per session in a Python loop; `db_move_session_metadata` **and** `db_rebase_paths` scan **all** sessions unscoped (`SELECT id, directory FROM session`). Three functions share the pattern. | ocman.py:5227-5232 (project move), 5285-5292 (session move), 5363-5368 (rebase) |
| PERF-4 | Low | Low | architect / power user | history sidecar | `runs` list grows unbounded; whole file loaded+rewritten each mutation (cumulative totals already precomputed) | ocman.py:6201-6260 |
| PERF-5 | Low | Low | SW eng | export temp files | Fixed-name temp JSONL per table in `gettempdir()`; concurrent same-session export could collide; leftovers on kill | ocman.py:5504-5519 |
| PERF-6 | Low | Low | SW eng / stakeholder | measurement | No benchmarks/metrics; optimizations are currently unverifiable and regressions undetectable | tests/ (none) |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 0 | PERF-1, PERF-3 | **Characterization tests first (anti-regression).** Before changing any logic, add tests that pin the CURRENT correct output of: (a) import-collision id remap (DB rows + rewritten diff-file contents for a subtree with nested/parent ids), and (b) project-move, session-move, and rebase directory rewriting (incl. the "not under prefix → skipped" and exact-match cases). These are the green-before/green-after baseline for steps 2-3. Name the at-risk invariants: *every occurrence of an old id maps to its remapped id and nothing else is altered*; *a session directory is rebased iff it equals or is nested under the old prefix*. | tests/test_export_import.py, tests/test_move.py | Low | New tests pass against current code (baseline), then remain green after steps 2-3 |
| 1 | PERF-6 | Add an opt-in micro-benchmark (marker e.g. `@pytest.mark.benchmark`, skipped by default) that builds a synthetic large session subtree + diffs and times: (a) import-collision remap, (b) a large export parse, (c) a move/rebase on a many-session DB. Establishes a baseline before optimizing. **Informational only — never a hard pass/fail CI gate** (timings are machine-dependent). | tests/test_perf.py (new) | Low | `pytest -m benchmark` runs and prints timings; default `pytest` unaffected (still 59 tests); benchmark is not added to the default/CI gate |
| 2 | PERF-1 | Replace the whole-string replace-loop with a single structural remap: walk the parsed diff (dict/list/str) once and substitute **exact-match** ids via an `id_map` dict lookup (replace whole string values/keys equal to an old id; do NOT substring-replace). This is both faster and fixes the latent substring-corruption bug — so the step-0 characterization test must assert the *correct* mapping, not bug-for-bug parity; call out any intentional behavior change in the CHANGELOG. | ocman.py:5748-5758 | Low | Step-0 characterization test (corrected expectations) + existing `test_import_session_with_collision` pass; add a test where one id is a substring of another to prove no corruption; benchmark shows lower time |
| 3 | PERF-3 | Apply to **all three** functions (`db_move_project_metadata`, `db_move_session_metadata`, `db_rebase_paths`): resolve the two prefixes once; rewrite `session.directory` by prefix comparison without per-row `resolve()`. Add a SQL **candidate pre-filter** (`WHERE directory = ? OR directory LIKE ? ESCAPE '\'`) to the two unscoped scans, but keep the authoritative match/rebase in Python so semantics are unchanged even if stored paths are non-canonical. Extract the shared rewrite into one helper to avoid three divergent copies (KISS). | ocman.py:5227-5232, 5285-5292, 5363-5368 | Low | Step-0 characterization tests for all three functions stay green; add a test with a **non-canonical** stored directory (trailing slash / `..` / symlink) confirming the pre-filter + Python match still rebases it; benchmark shows fewer stats/rows |
| 4 | PERF-4 | Cap retained detailed `runs` to a configurable `history_max_runs` (default e.g. 500), trimming oldest **on save only** (never mutate on read); keep `cumulative` totals intact. On first save after upgrade an over-cap file is trimmed down. Document the key in README + `ocman.toml` template. | ocman.py:6201-6260, DEFAULT_CONFIG, README.md | Low | New test: after N+K runs, only N retained and cumulative unchanged; loading an over-cap file does not alter it until a save; config precedence test |
| 5 | PERF-5 | Write export temp JSONL into a per-run `tempfile.mkdtemp` dir and `shutil.rmtree` it in a `finally`; removes fixed-name collision + orphan risk. | ocman.py:5504-5519 | Low | `test_bundle_session_data` still passes; add a test asserting no leftover temp files after export and after a simulated mid-export error |
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
- **Under-scope (add):**
  - The missing benchmark harness (PERF-6) is a real gap — without it, PERF-1/PERF-3
    improvements are unverifiable; adding it is proposed above.
  - **`db_rebase_paths` (added in plan-review):** the original draft's PERF-3 covered only
    the two move functions; `db_rebase_paths` (ocman.py:5363-5368) shares the same
    unscoped-scan + per-row `resolve()` pattern and MUST be included, or `--rebase-paths`
    keeps the slow/inconsistent code path. Step 3 now covers all three via one shared helper.
  - **Characterization tests (added in plan-review):** PERF-1 and PERF-3 touch
    correctness-adjacent logic (id remap, path rebase); step 0 now pins current behavior
    before the change so refactors are provably safe.

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
4. PERF-1 is also a latent **correctness** fix (substring `str.replace` can corrupt ids).
   Confirm the intended behavior is exact-id remapping (assumed yes); the characterization
   test will encode the corrected expectation and it will be noted in the CHANGELOG.

## Plan-review provenance (2026-07-04)

This IPD was hardened by the `plan-review` workflow (run 20260704-140000). Changes applied:
corrected `file:line` anchors (PERF-3, PERF-5) against the actual source; expanded PERF-3
to include `db_rebase_paths` (previously omitted) via a shared helper; added a step-0
characterization-test requirement for PERF-1/PERF-3 (anti-regression); flagged PERF-1's
latent substring-`replace` correctness bug and required the test to assert the corrected
mapping; clarified the PERF-3 SQL scan is a candidate pre-filter with the authoritative
match kept in Python (safe on non-canonical stored paths); marked the benchmark as
informational-only (never a CI gate); specified PERF-4 trims on save only (never on read).
Verdict: APPROVE WITH REVISIONS APPLIED.

## Execution outcome (2026-07-04)

Executed with explicit user approval. All steps completed; PERF-2 remained deferred as
planned. One in-flight scope adjustment was confirmed with the user:

- **PERF-3:** the SQL `LIKE` candidate pre-filter was **dropped** (not implemented)
  because it cannot safely reproduce the current `Path.resolve()`-based matching for
  non-canonical stored paths (PR-5 tension). Implemented the behavior-preserving part:
  a shared `_rebased_dir` helper across all three functions, resolving prefixes once.
  The per-row `resolve()` is retained (it is the correctness mechanism). This deferral
  is Medium-High Remediation Risk on the **functionality** axis.

Results:
- **PERF-1:** `_remap_ids_in_json` structural remap replaces the substring-replace loop.
  Measured ~**26× faster** per diff (6.73 ms → 0.26 ms, 300-session id_map) and fixes a
  latent correctness bug (substring corruption of unrelated tokens). Regression test
  `test_import_session_collision_remaps_ids_in_diffs_no_substring_corruption` added
  (fails on old code, passes now).
- **PERF-3:** shared `_rebased_dir` helper; `test_move.py` green + new non-canonical-path
  characterization test.
- **PERF-4:** `history_max_runs` (default 500), trim-on-save only; two tests added.
- **PERF-5:** per-run `mkdtemp` export staging dir + `rmtree`; leftover-temp test added.
- **PERF-6:** `tests/test_perf.py` opt-in benchmarks (`OCMAN_BENCHMARK=1`), never a CI gate.
- Bonus latent fix: `save_ocman_config` now merges over defaults (partial-config saves
  can't break when new keys are added — surfaced by the TUI config-tab test).

Validation: `PYTHONPATH=. pytest` → 64 passed, 2 skipped. Docs synced (README config
template, CHANGELOG). Commit: see git history (feat/perf + test commits).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes (benchmark first for a baseline), run the
   validation, and sync docs for PERF-4.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
