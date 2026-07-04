# Decisions and assumptions - assess-performance 20260704-135426

## Concern / scope
- Concern: performance (runtime + resource efficiency). Lens: performance.md.
- Scope: whole project. No `$ARGUMENTS` narrowing provided.
- Lead personas: software engineer + architect, with power-user/stakeholder "fast enough
  at scale?" view.

## Project conventions discovered
- No `GUIDING_PRINCIPLES.md`; used universal fallback + the principles in `ARCHITECTURE.md`.
- No pre-existing pending-plans dir → created `.agents/plans/pending/` (recorded).
- Validation command: `PYTHONPATH=. pytest` (59 tests currently green). No benchmarks exist.
- Out of scope (framework): `.agents/workflows/`, `workflow-artifacts/` are not assessed as project.

## Key decisions
- Verdict **adequate** (not "at risk"): the tool already streams exports to disk
  (`fetchmany(1000)`), chunks DB ops at 999, precomputes cumulative history totals, and
  renders transcripts via list-join. The one genuinely algorithmic hot spot is PERF-1.
- Fix-by-default applied: 5 of 6 findings proposed for action now (all Low Remediation
  Risk). PERF-2 deferred solely because the *fix* (streaming rewrite of the core recovery
  pipeline) is Medium-High on the functionality axis — not because of effort.
- Ordered the benchmark (PERF-6) first so PERF-1/PERF-3 gains are measurable, per the
  lens's measurement requirement (avoid speculative optimization).

## What was intentionally NOT proposed (and why)
- Caching layer / async import / ORM / new serialization: over-scope, untraceable to a
  need, Complexity axis (KISS). Not proposed.
- Micro-optimizing `render_transcript`, delete/cleanup chunking, or `fetchmany` export:
  already efficient; no evidence of cost. Not proposed.
- The upstream `opencode export` failure (the DB conflict in the user's traceback): an
  opencode-side issue, not an ocman performance concern. Noted, not proposed.

## Assumptions (to confirm — see IPD open questions)
- `history_max_runs` default of 500 is friendlier than unbounded (assumption).
- Benchmark lives in `tests/` behind a marker (assumption).
- Import-collision-with-large-subtrees frequency unknown; PERF-1's complexity argument
  holds regardless of frequency.

## Open questions for the user
1. `history_max_runs` default (or keep unbounded + document)?
2. How common is large-subtree import-with-collision in real use?
3. Benchmark location (`tests/` marker vs `benchmarks/`)?
