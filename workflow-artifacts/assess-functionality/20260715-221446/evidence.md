# Evidence - assess functionality (20260715-221446)

Reproducible record of what was inspected. The primary artifact is
`ocman/cli.py` (~12,837 lines); a subagent produced a full command-surface inventory
that this assessment relies on.

## Inspected

- `TODO.md` (full, 28 lines): backlog for `ocman spend` (F2), incl. open design
  questions about data source and "historically saved spend".
- `ocman/cli.py`, verified anchors:
  - Parser build `build_parser()` ~5708-5951; `new_sub` 5731; `new_action` 5736;
    normalizer `_normalize` ~6053-6288; `parse_args` ~6298-6330; dispatch in `main()`
    from ~11408.
  - Subcommand definitions: session 5742-5821, project 5824-5843, db 5846-5863,
    backup 5866-5879, history 5882-5886, config 5888-5891.
  - Top-level sugar: move 5898-5906, export 5909-5911, info 5916, disk 5920, logs 5922,
    filter 5924, models 5941, compaction-prompt 5942, ui/gui 5943-5944, help 5946.
  - `preprocess_argv` sugar/aliases ~5350-5491 (ls 5399, lp 5401, list rewrites
    5405-5412, search-scope 5456-5489, `to` handling 5442-5454).
  - `--force` help strings: "Bypass process-lock checks" at 5704, 5795, 5821, 5832,
    5843, 5858; "Skip the confirmation prompt" at 5886 (the F6 dual meaning).
  - `export` stale help "project export is not yet supported" at 5911; project-export
    handler at 11546-11558 (`bundle_project_data`) proving it works (F3).
  - Top-level `move` sugar flags 5898-5906 (lacks `--confirm-remote-delete`/`-y`/
    `--force`); group forms have them at 5812-5821 / 5834-5843 (F4).
  - `-y/--yes` present 5787/5796/5820/5842; absent on project delete 5829-5832, db
    clean 5853, clean-orphans 5856, backup clean 5878 (F5).
  - `--dry-run` present 5703/5794/5831/5857; absent on move, restore 5875, import 5803,
    history clear 5885 (F7).
  - Cost/spend surfaces: `estimate_cost` 818-841; `ModelInfo.cost_*` 424-425/613-626;
    models pricing column 661-670; compaction actual cost 938-956, 12657-12681,
    12720-12794; `db info` usage metrics 10687-10721; history ledger cost 10764-10766;
    `_per_project_disk_usage` 10488 (disk only, no cost). No `new_sub("spend")` (F2).
  - Search per-session line cap `-n/--limit` 5682; `db info` top-models hardcoded
    `LIMIT 3` at 10707; no list/history pagination (F8).
  - `-V/--version` 5725 (`__version__` 186); no `--json` anywhere; internal
    `opencode session list --format json` at 1416.

## Commands run

- `date "+%Y%m%d-%H%M%S"` (run ID).
- `git status --short` (clean before this run).
- Targeted `grep -n` for `--force` help strings, subcommand definitions, and cost/spend.
- Subagent (explore) full command-surface inventory over `ocman/cli.py`.

## Sampling / limits

- `ocman/cli.py` was not read line-by-line end to end; findings rely on targeted reads
  of the parser, sugar, dispatch, and cost code plus the subagent inventory. The
  "fully wired, no stubs" claim is from a repo-wide marker search
  (`NotImplementedError`/`TODO`/`FIXME`/`XXX`/"coming soon"/"not implemented"), which
  returned only the one stale `export` help string.
- The full test suite was NOT run in this assessment (assess does not execute or
  modify); the "293 passed, 2 skipped" figure is from the immediately-prior session and
  is cited as context, not re-verified here.
