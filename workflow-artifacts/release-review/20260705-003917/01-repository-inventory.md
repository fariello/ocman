# 01 Repository inventory

## Current project state
`ocman` (OpenCode Manager): single-user, local admin CLI + Textual TUI for the OpenCode ecosystem. Released
1.0.4 on PyPI. This run reviews the unreleased delta of 34 commits on `main` since tag `v1.0.4`.

## Project type & scope
- **CLI:** `ocman.py`, one self-contained stdlib-only module (~8.7k lines). Console script `ocman = ocman:main`.
- **TUI:** `ocman_tui/` package (textual/rich): `__init__.py`, `app.py`, `core.py`, `css/`,
  `widgets/{database,models,sidebar}.py`.
- **Tests:** `tests/` — test_ocman, test_core, test_recovery, test_export_import, test_move,
  test_config_parsing, test_config_backup_restore, test_tui, test_perf (opt-in), test_compacted_project_prompt
  (new), fixtures/.
- **Packaging:** `pyproject.toml` (hatchling; wheel packages `ocman_tui` + force-include `ocman.py`),
  `requires-python >=3.10`, version 1.0.4.
- **CI:** `.github/workflows/ci.yml` (ubuntu/macos/windows × Python 3.10–3.14).
- **Docs:** `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `AGENTS.md`, `LICENSE` (BSD-3-Clause).

## Intended outcome / audience
Users/operators of OpenCode who need to browse, recover, compact, and MAINTAIN their local session DB —
inspect/reclaim disk, clean old sessions, prune orphans, vacuum, backup/restore, move/export/import sessions.
Stakeholder intent (user-stated this session): ocman is a competitor to `ocgc`; its differentiator is that it
*actually reclaims* the disk/DB space sessions occupy (ocgc reportedly leaves ~95% behind). This is intent
evidence for docs positioning; the reclaim behavior is verified against code before any doc claim ships.

## Guiding principles
No `GUIDING_PRINCIPLES.md`. Principles are stated in `ARCHITECTURE.md` → "Design principles":
intuitive/self-documenting, configurable-over-hardcoded, KISS, honest documentation. Treated as the binding
principles doc for this review (supersedes the universal fallback, though they align).

## Backlog / TODO sources
- No `TODO.md`/`BACKLOG.md`/`ROADMAP.md`/`KNOWN_ISSUES.md`.
- In-code `TODO`/`FIXME`/`HACK`/`XXX`: none real. The only `XXXX` hits are placeholder tokens in
  `preprocess_argv` help/parse text (`ocman.py:3948-4002`, "list sessions in XXXX"). Not backlog items.

## Pending agent plans / staged prompts (for Section 8 WARNING)
- **`.agents/plans/pending/20260705-assess-documentation.md`** — Status: PENDING. IN-SCOPE for this release:
  it documents real README/ARCHITECTURE accuracy bugs (dead `default_model` config key → should be
  `default_compaction_model`; incomplete Argument Reference table; understated preprocess_argv commands; TUI
  `css/` undocumented). Classification: **in-scope-and-pending** → its findings should be folded into this
  review's Section 4 docs fixes rather than shipped unaddressed. NOT executed by this review.
- `.agents/plans/executed/` — completed IPDs (out of scope; history).
- `.agents/prompts/` staging — reusable/executed prompt docs; none queued as "run me now" for this release.

## Public contract summary
- CLI flags/subcommands (argparse + `preprocess_argv` natural-language rewrites). Delta adds: `--by-project`,
  `disk`/`du`, `--clean-backups`, `--clear-history`, `--no-project-prompt`, fractional `--days`.
- Config: `ocman.toml` keys in `DEFAULT_CONFIG` (delta adds `history_max_runs`, `copy_restart_to_project_prompts`).
- Data contracts: SQLite `opencode.db`, `.ocbox` bundle (export_version 2.0), backup ZIP, `ocman_history.json`.

## New/changed code surfaces in the delta (audit targets for S2)
`resolve_project_dir`, `project_prompt_copy_name`, `_backup_compacted_bu`, `maybe_copy_compacted_to_project`
(recovery copy); `_project_for_cwd`, `detect_running_opencode`, `_render_running_opencode`,
`check_opencode_process_lock` (process lock); `dir_usage`, `_per_project_disk_usage`, `cli_clean_backups`
(disk usage / backups prune); `PreviewItem`, `DestructivePreview`, `render_destructive_preview`,
`confirm_destructive` (destructive-confirmation seam).

## Recent changes (CHANGELOG [Unreleased])
Disk-usage reporting; `--clear-history` confirm; `--clean-backups` KEEP/DELETE preview; fractional `--days`;
process-lock detailed report; unified destructive confirmations; compacted→project-prompts copy.

## Drift / inconsistencies (IDs assigned in later sections)
- README config template documents `default_model` (nonexistent; real key `default_compaction_model`,
  default `""`) — carried from the pending docs IPD (D1). → Section 4.
- README Argument Reference omits ~13 real flags (D2). → Section 4.
- ARCHITECTURE understates recognized commands; TUI `css/` undocumented (D3/D5). → Section 4.
- Version still 1.0.4 with a large `[Unreleased]` set; MUST bump before re-publish (already on PyPI). → S6.

## Out of scope (recorded per protocol)
`.agents/workflows/` (framework, incl. release-review runbook) and `workflow-artifacts/` (run records) are
present but NOT reviewed as project code/docs. Untracked/ignored and not part of the repo: `orsession/`
(only `__pycache__`), `opencode-recovery/`, `dist/`, `opencode.json`/`opencode.jsonc`.

## Recommended next actions
Proceed to Section 2 (audit the new code surfaces, esp. the live/destructive ones), then Section 4 folds the
pending docs-IPD fixes + ocman-vs-ocgc positioning, Section 6 handles version discipline.
