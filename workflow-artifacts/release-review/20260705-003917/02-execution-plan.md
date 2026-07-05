# 02 Execution plan

## Project type
Single-user local admin CLI + Textual TUI for the OpenCode ecosystem. Python; CLI is one stdlib-only module
(`ocman.py`, ~8.7k lines); TUI package `ocman_tui/` (textual/rich). Packaged as `ocman` on PyPI (1.0.4 shipped).

## What this run reviews
The delta since `v1.0.4` (34 commits, unreleased). This is a follow-up review; two prior runs shipped 1.0.4.
Focus on the new/changed surfaces rather than re-auditing the whole stable base from scratch, but run all
sections and let each persona surface anything the delta touches.

Delta surfaces to trace:
- Disk-usage reporting: `ocman info` Backups section, `--by-project`/`disk` per-project breakdown.
- Destructive-confirmation seam: `DestructivePreview`/`render_destructive_preview`/`confirm_destructive`;
  adopters = `--clean-backups`, session/project delete, cleanup/orphan prune, `--clear-history`.
- Process-lock detailed report: `check_opencode_process_lock` shared helper.
- Fractional `--days`.
- Compacted→project-prompts recovery copy: `maybe_copy_compacted_to_project`, `_backup_compacted_bu`,
  `project_prompt_copy_name`, `resolve_project_dir`; wired in `main()` after `run_compaction`.

## How the review will run
Serial, single continuous pass (repo is one large module + a TUI pkg; parallel lanes not needed). Per-section
loop per README: read section file, do work, update registers, write per-phase report, checkpoint, commit.

## Validation strategy
Authoritative: `PYTHONPATH=. pytest` (README-documented; baseline expected 126 passed / 2 skipped). Also
`python -m py_compile`, `--help`/`--version` smoke, and targeted manual traces for live surfaces
(destructive confirm, process lock, compacted-copy) since green tests are not proof for those.

## Known carry-in residuals (prior run) to re-check
S2-M1 (monolith size), S3-R1 (bare pytest resolves installed pkg), S6-CI1, DEP2, disk-usage IPD (now
executed), unbounded backups on disk.

## Special foci this run
1. Version discipline: 1.0.4 already on PyPI → MUST bump before re-publish; CHANGELOG `[Unreleased]` must be
   finalized to the chosen version at release.
2. Pending `docs` IPD in `.agents/plans/pending/` → loud WARNING; the doc inaccuracies it found
   (`default_model` dead key, incomplete arg table) are real and in-scope for docs review.
3. Positioning: README should state the ocman-vs-ocgc reclaim value proposition (user intent).

## Stop point
STOP after Section 8 with a Go/No-Go. Do NOT run Section 9 (bump/tag/push/publish) — user bumps & publishes
after sign-off.
