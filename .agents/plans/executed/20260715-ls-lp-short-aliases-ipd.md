# Implementation Plan - `ls` / `lp` short aliases

Status: EXECUTED (2026-07-15)

Add short command aliases `ocman ls` and `ocman lp` for `ocman list sessions [NAME]`
and `ocman list projects`.

Note on lifecycle: this IPD is RETROACTIVE. The change was implemented directly
(commit `97bbffe`) as a trivial, self-contained CLI-alias addition, then this plan
was written to keep the tracked plan record consistent with the rest of the repo.
It documents exactly what shipped.

---

## Motivation

`ocman list sessions` and `ocman list projects` are the two most frequently typed
commands. Short aliases (`ls`, `lp`) reduce typing for a daily-use tool. The names
mirror the muscle memory of shell `ls` and are easy to remember (`lp` = list
projects).

## Current behavior (pre-change, verified)

- `preprocess_argv` (`ocman/cli.py`) already layers natural-language sugar over the
  subcommand grammar, including word-order aliases `list projects` -> `project list`
  and `list sessions [NAME]` -> `session list [NAME]`, and peels leading global
  options (`--db`, `-v`, etc.) so rewrites still fire when globals precede the verb.
- No single-token short aliases existed.

## Design

- In `preprocess_argv`, BEFORE the existing word-order block, add a rewrite:
  - `ls [NAME ...]` -> `session list [NAME ...]`
  - `lp [ARGS ...]` -> `project list [ARGS ...]`
- Map directly to the canonical `session list` / `project list` forms (not via the
  `list projects` sugar) so there is one hop and passthrough args are preserved.
- Leading global options are already peeled before this point, so `ocman --db X ls`
  works unchanged.
- Case-insensitive match on the first post-globals token only; anything else passes
  through untouched.

## Non-goals

- Aliases for other verbs (show, recover, compact, etc.).
- A general user-configurable alias system.
- Changing the canonical `list`/`session list`/`project list` grammar.

## Tests

- `test_preprocess_ls_lp_short_aliases` (`tests/test_ocman.py`): asserts
  `ls` -> `session list`, `lp` -> `project list`, `ls NAME` carries the arg,
  leading globals are preserved (`--db X ls`), and passthrough args survive
  (`lp --foo`).

## Docs

- In-app help: browse-examples rows and the aliases table note `ls`/`lp`; the
  `preprocess_argv` docstring lists the rewrite.
- README: word-order alias section and the aliases table show the short forms.
- CHANGELOG: Unreleased / Added.

## Validation (as executed)

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` -> 293 passed, 2 skipped.
- Direct dispatch check: `ls` -> `list_sessions=True`, `lp` -> `list_projects=True`,
  `ls myproj` carries the project arg; real `lp` invocation rendered the projects
  list.

## Workflow history
- 2026-07-15 execute (its_direct/pt3-claude-opus-4.8): implemented in commit
  `97bbffe`; retroactive IPD recorded. 293 passed, 2 skipped.
