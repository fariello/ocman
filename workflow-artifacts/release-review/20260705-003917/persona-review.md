# Persona review

Per-persona notes appended per section (lead personas own each section).

## Section 1 (inventory)
- Stakeholder (8): delta is bug-fix + additive maintenance features; ocman-vs-ocgc reclaim positioning is the
  headline value not yet reflected in README. Noted for S4/S5.
- Software engineer (5): delta concentrated in ocman.py (+~879 lines) across 4 coherent feature areas + a
  shared confirmation seam; monolith continues to grow (carry-in S2-M1).

## Section 2 (quality/security/edge)
- QA/QC (1): traced all new functions; every one is fail-soft/fail-open on error paths (detect_running_opencode
  returns [] on any failure → fails OPEN so a broken detector never blocks; maybe_copy_compacted_to_project
  wraps its whole body in try/except → never breaks recovery). No happy-path-only defects found in the delta.
- Software engineer (5): DB connections in the new functions (_project_for_cwd, _per_project_disk_usage) all
  use try/finally close; parameterized SQL; centralized SESSION_RELATIONAL_TABLES for identifiers. dir_usage
  uses scandir/stat, skips unreadable, no symlink-follow. No MEM leak/unbounded-growth in the delta
  (history_max_runs already caps the one growing buffer). No new finding beyond M1.
- Security-minded architect (4): confirm_destructive does NOT consult force (force bypasses only the process
  lock — matches ARCH-9 invariant, verified). Path containment in maybe_copy_compacted_to_project
  (is_relative_to under pending). No new attack surface. Secrets scan clean.

## Section 3 (tests/regression)
- Testing/regression expert (2): the delta's live surfaces ARE covered — process lock (refuse/force/fail-open/
  filter/self-exclude, 5 tests), destructive preview (3), cli_clean_backups (cancel/dry-run/keep-delete/all-
  deleted, 6), compacted-copy (11). Real gaps are only _per_project_disk_usage and focused confirm_destructive/
  _project_for_cwd tests — all Low.
- QA/QC (1): the corrected restart→compacted behavior has explicit regression tests (naming, .bu increment,
  trigger/skip/disabled/backup/fail-soft). The old test file was renamed, not lost. No brittle/misleading tests
  spotted in the delta.
