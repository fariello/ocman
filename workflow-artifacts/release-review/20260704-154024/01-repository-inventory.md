# 01 Repository Inventory

## Project state summary
`ocman` (OpenCode Manager), currently versioned **1.0.3** in code but carrying an **`[Unreleased]`**
CHANGELOG with user-facing fixes → a **1.0.4** release is pending. CLI (`ocman.py`, ~8100 lines) + Textual
TUI (`ocman_tui/`). Published on PyPI; v1.0.3 tagged and released.

## Delta since v1.0.3 (the primary review subject)
| Commit | Change | Prior review |
|---|---|---|
| 280cfc8 | TUI worker-callback stability (`_safe_call_from_thread`) | fixed after user bug report |
| 428aaf7 | Performance: structural import id-remap, shared `_rebased_dir` helper, `history_max_runs` cap, per-run export temp dir | assess-performance IPD (executed) |
| 2cfd3d2 | TUI compaction repair (render_compact_prompt/call_compaction_api arity + str-as-dict) + recovery/compaction tests; `save_ocman_config` merge-over-defaults | assess-testing IPD (executed) |
| 4b34802 | disk-usage assess IPD (docs/plan only; **not** yet executed) — pending, not part of release code | assess-functionality |

All product changes went through this session's assess -> plan-review -> execute cycles.

## Project type / public contract (unchanged since prior run)
- Python 3.10+ CLI + TUI. Contract: `ocman` console entry, `.ocbox` bundle (v2.0), backup ZIP, `ocman.toml`.
- New config key this cycle: `history_max_runs` (default 500) — additive, backward-compatible.

## Guiding-principles document
- None dedicated. Universal fallback + the "Design principles" section in `ARCHITECTURE.md` (added in the
  prior run). See `guiding-principles-assessment.md`.

## Backlog / TODO sources
- No `TODO.md`/`BACKLOG.md`/`ROADMAP.md`/`KNOWN_ISSUES.md`. **No** in-code `TODO`/`FIXME`/`HACK`/`XXX`
  markers (verified). Pending IPDs exist under `.agents/plans/pending/` (disk-usage) and `.agents/plans/done/`
  (performance, testing) — these are framework plan artifacts, not a product backlog; noted, not triaged as release blockers.

## Test and validation inventory
- `tests/`: test_ocman, test_export_import, test_move, test_config_backup_restore, test_tui, test_core,
  test_recovery (new), test_config_parsing (new), test_perf (new, opt-in). Command `PYTHONPATH=. pytest`.
- **Current result: 91 passed, 2 skipped** (benchmarks). Up from 66 at v1.0.3.
- CI: `.github/workflows/ci.yml` matrix (ubuntu/macos/windows × py3.10-3.14), tests only.

## Documentation inventory
- README.md (adds Known Limitations, benchmark opt-in, history_max_runs config).
- CHANGELOG.md: `[Unreleased]` section documents all delta changes; **`[1.0.3]` is the last released heading**.
- ARCHITECTURE.md present (cold-start orientation; added prior run).

## Build/packaging
- hatchling; deps textual>=3, rich>=13, pysqlite3-binary (linux). Versions in `pyproject.toml:7` (1.0.3),
  `ocman.py:191` (1.0.3), and `ocman_tui/__init__.py:9` fallback (1.0.3, but runtime single-sources from ocman).

## Drift / inconsistencies (IDs)
- `20260704-154024-S1-A1` **Release version drift:** code/pyproject are 1.0.3 but `[Unreleased]` CHANGELOG has
  user-facing fixes (TUI compaction was broken in 1.0.3). Needs 1.0.4 bump + CHANGELOG heading. (Owner: Section 6/7.)

## Key ambiguities (IDs)
- `20260704-154024-S1-Q1` Is the target release version 1.0.4 (patch — all changes are fixes + one additive
  config key + internal perf)? Assumed yes (semver: no breaking changes). Confirm in final report.

## Deprecation candidates
- Same as prior run: `orsession/` (soft optional import), `agents/`, `prompts/`, "Orsession" naming residue
  (`OrsessionApp`). No new candidates from the delta. See `deprecation-candidates.md`.

## Out-of-scope directories
- `.agents/workflows/` (framework, updated to 20260704-01 — tooling only), `.opencode/`, `.claude/`,
  `workflow-artifacts/`, `.agents/plans/` (framework plan artifacts). Present but NOT reviewed as product.

## Recommended next actions
- Section 2: audit the delta code paths (worker guard, structural remap, `_rebased_dir`, history cap,
  export temp dir, compaction fix) for correctness/MEM/LIVE regressions. Section 6/7: 1.0.4 version bump.
