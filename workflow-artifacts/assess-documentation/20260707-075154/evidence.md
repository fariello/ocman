# Evidence - assess documentation (20260707-075154)

Reproducible record of what was inspected.

## Documents read in full

- `README.md` (372 lines)
- `ARCHITECTURE.md` (102 lines)
- `AGENTS.md` (11 lines)
- `TODO.md` (28 lines)
- `CITATION.cff` (17 lines)
- `CHANGELOG.md` (lines 1-60 read; head/1.1.0 section verified; total 348 lines)

## Code cross-checks (verifying doc accuracy)

- `ocman.py:195` -> `__version__ = "1.1.0"`; `pyproject.toml:7` -> `version = "1.1.0"`.
- Config: read `ocman.py:213-290` (`DEFAULT_CONFIG_TEMPLATE` + `DEFAULT_CONFIG`);
  compared key-by-key with README "Default Layout Template" (README.md:257-297). Match,
  including `filter_max_bytes` (5242880) and `filter_secret_scan` (conservative).
- CLI flags: parsed every `add_argument` in `ocman.py` via a Python AST walk to get the
  authoritative flag list (short+long, and which are `argparse.SUPPRESS`ed). Compared to
  README Argument Reference table (README.md:190-249).
  - Confirmed present-in-code but absent-from-table: `--clean-backups` (ocman.py:4433).
  - Confirmed correctly-omitted: `-m/--use-model` (SUPPRESS, ocman.py:4479-4483).
  - Confirmed `--format` is an opencode subprocess arg (ocman.py:1376), not a CLI flag.
- Existence checks: `pyproject.toml` `[project.optional-dependencies] dev` (line 21-22),
  `tests/test_perf.py`, `scripts/migrate_recovery_names.py` all present (README claims OK).
- Grep for hardcoded version strings across project docs: only `CITATION.cff:16` carries
  a version (`1.0.6`); README/ARCHITECTURE carry none.

## Commands run

- `ls -la` (repo root); `find` for `*.md`/`*.rst`/`*.txt` excluding framework/artifact dirs.
- `grep -n '__version__'`, `grep -n 'version' pyproject.toml`, `grep -n 'DEFAULT_CONFIG'`.
- AST parse of `ocman.py` add_argument calls (inline `python3 -c`).
- `grep` for `--clean-backups`, `--format`, `--use-model`, `--compact`, `-C`,
  `show-compaction-prompt`, `show-models` in `ocman.py`.
- `grep -rn '1.0.6|1.0.5|1.1.0'` across project docs.
- `ls .agents/plans/pending/` (empty) and `.agents/plans/executed/` (prior doc IPD present).
- `ls workflow-artifacts/assess-documentation/` (prior run 20260705-001342).

## Sampling / truncation notes

- `ocman.py` is ~9182 lines; not read in full. Inspected the config block (213-290), the
  argparse block (~4393-4497), and used AST + targeted grep for the flag inventory, which
  is sufficient for documentation-accuracy verification.
- CHANGELOG read to line 60 (covers the current 1.1.0 + start of 1.0.6 entries); remaining
  history not material to this assessment.
