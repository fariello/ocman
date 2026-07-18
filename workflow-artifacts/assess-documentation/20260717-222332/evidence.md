# Evidence - assess documentation

## Docs inspected
- README.md (full read; command-reference tables, install section, config template,
  quickstart, session-header prose, env mentions).
- ARCHITECTURE.md (entry points, verb list, KISS principle, session-header + reclaim
  subsections).
- CHANGELOG.md ([Unreleased] section).
- pyproject.toml (dependencies, requires-python, console-script entry).

## Code inspected (ocman/cli.py) for cross-checking claims
- `import vistab` at cli.py:90 (proves the CLI is not stdlib-only / not zero-dep).
- argparse surface: `_add_recovery_opts` (cli.py:6019), compact opts add
  (cli.py:6186-6193), session list/show/import/delete (cli.py:6150-6216), project
  list/delete (cli.py:6238-6246), reclaim flags (cli.py:6392-6411), top-level verbs
  spend/running/doctor/reclaim (cli.py:6354,6382,6389,6392).
- `DEFAULT_CONFIG` (cli.py:307-325) and `DEFAULT_CONFIG_TEMPLATE` (cli.py:224-305);
  string-quoting in `save_ocman_config` (cli.py:394-395).
- env reads: NO_COLOR/FORCE_COLOR/TERM (cli.py:137-143), OPENCODE_DB (cli.py:12568),
  XDG_DATA_HOME (cli.py:12580), OPENCODE_CONFIG_DIR (cli.py:12586).

## Commands run (verification)
- `ls ocman.py` -> "No such file or directory" (confirms D-02).
- `sed -n '90p' ocman/cli.py` -> `import vistab` (confirms D-01/D-04).
- `sed -n '/dependencies = [/,/]/p' pyproject.toml` -> textual, rich, vistab,
  pysqlite3-binary (confirms D-01).
- `PYTHONPATH=. .../python -c "import ocman; ocman.main()" session recover --show-secrets`
  -> "error: unrecognized arguments: --show-secrets" (confirms D-03).
- `PYTHONPATH=. .../python -c "import ocman; ocman.main()" doctor` (run earlier this
  session) -> confirms doctor/reclaim exist and work.

## Method
- An explore subagent performed the systematic doc-vs-code diff across the 7 audit areas
  (command/flag coverage, recent features, config keys, getting-started, env vars,
  stale claims, CHANGELOG). Its highest-severity findings were then independently
  re-verified against the code by the coordinator (the command runs above) before being
  written into the IPD, per the assess workflow's "verify, do not infer" rule.

## Sampling / limits
- README/ARCHITECTURE line numbers cited in findings are as-of this run; docs shift, so
  the IPD instructs the executing agent to re-locate them. The exhaustive per-command
  flag diff relied on the argparse grep + `--help`; not every one of the ~30 subcommands
  was help-dumped individually, but every finding cites a concrete code line.
