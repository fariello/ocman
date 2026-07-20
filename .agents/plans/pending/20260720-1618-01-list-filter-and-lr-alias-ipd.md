# IPD: `lr` alias + optional filter arg on list projects/sessions/running

- Date: 2026-07-20
- Concern: feature (CLI ergonomics: aliases + list filtering)
- Scope: `ocman/cli.py` argv preprocessing (`preprocess_argv`), the three list handlers
  (`list projects`, `list sessions`, `list running`), help text, and tests. No DB schema
  change, no TUI change.
- Status: reviewed (not yet executed; awaiting human approval)
- Target version: 1.3.0 (cut 1.3.0-rc1 first, promote to 1.3.0 after validation)
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-20 created (its_direct/pt3-claude-opus-4.8): from a maintainer request to (1) make
  `lr` an alias for `list running`, and (2) add an optional case-insensitive filter argument to
  `list projects`/`lp`, `list sessions`/`ls`, and `list running`/`lr`. Design settled with the
  maintainer via Q&A (see Design decisions).

## Goal

Two related CLI ergonomics improvements to the `list` family:

1. **`lr` short alias** for `list running` (parity with the existing `lp` = `list projects`
   and `ls` = `list sessions` short aliases).
2. **Optional positional filter** on all three list commands, a case-insensitive substring
   match that narrows the listing:
   - `lp <PATTERN>` / `list projects <PATTERN>`: keep only projects whose **directory OR name**
     contains PATTERN.
   - `ls <PATTERN>` / `list sessions <PATTERN>`: **project-scope precedence** (see below).
   - `lr <PATTERN>` / `list running <PATTERN>`: keep only running instances whose **project/cwd
     OR attributed session info** (session id(s), title, directory) contains PATTERN.

Matching mirrors the existing case-insensitive idiom used across the file:
`pattern.lower() in field.lower()` (e.g. cli.py:4996, 5035, 5122).

## Design decisions (settled with maintainer)

- **Filter is a POSITIONAL** on all three commands (not a flag), per maintainer preference.
- **`lp` fields:** directory + name.
- **`ls` semantics: filter WITH project-scope precedence.** `ls <ARG>`:
  1. **Project-scope precedence (unchanged behavior).** If `<ARG>` resolves to EXACTLY ONE
     project via the SAME rule `resolve_project_spec` uses today (cli.py:4980-5000: exact
     directory match, else ends-with match, else a case-insensitive substring-on-directory
     match that hits EXACTLY ONE project; 0 or >=2 substring matches do NOT resolve), scope to
     that project's sessions, exactly as today.
  2. **Filter fallback (new).** Otherwise (0 or >=2 project matches, i.e. what today produces
     the fatal "No matches found" / `sys.exit(1)` at cli.py:5287), treat `<ARG>` as a
     case-insensitive substring filter over ALL sessions, matching session **title, directory,
     OR project_dir**.
  This preserves every currently-working `ls <project>` invocation (case 1 is byte-for-byte the
  old path) and only changes the case that used to be a hard ERROR (case 2). That is strictly
  additive for real usage.
  - **KNOWN two-mode subtlety (must be documented in help + CHANGELOG):** because a unique
    substring-on-directory match still takes the scope path, `ls <text>` where `<text>` happens
    to uniquely substring-match one project DIRECTORY scopes to that project rather than
    filtering by session title. This is the intended precedence, not a bug; help text must make
    the two modes explicit so a user who wanted a title filter is not surprised. Users who want
    to force the filter can pass a pattern that does not uniquely match a project directory, or
    use the dedicated `search` command for title/content search.
- **`lr` fields:** project/cwd + attributed session (ids, title, directory).
- **Version = 1.3.0** (semver: new functionality = MINOR, not a bug fix = PATCH). RC first.

## Project conventions discovered (Step 0)

- Guiding principles: universal fallback (no GUIDING_PRINCIPLES.md). No em/en dashes in
  authored prose. Plans: `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`.
- Contract: path-scoped commits, never push without approval, paste REAL pytest output.
- Aliases are string-rewrites in `preprocess_argv` (cli.py:5813-5829), NOT argparse `aliases=`.
- Canonical subcommands: `session list` (cli.py:6211), `project list` (cli.py:6305),
  `running` (cli.py:6451). `_normalize` maps to flags `list_sessions`/`list_projects`/
  `show_running` and `out["project"]=g("name")` for session list (cli.py:6656-6663).
- Handlers: `list projects` inline at cli.py:15225 (+ `print_projects` cli.py:4810);
  `list sessions` inline at cli.py:15334 (scope resolution 15258-15331); `list running` =
  `cli_list_running` cli.py:11836 (instances from `detect_running_instances` cli.py:7983,
  session attribution `_attribute_session` cli.py:8039).

## Findings / requirements

| ID | Requirement | Evidence |
|----|-------------|----------|
| LF-01 | `lr` must alias `list running` | cli.py:5813-5829 has `ls`/`lp` but no `lr`; help at 5539-5540/5724 lists only lp/ls |
| LF-02 | `lp [PATTERN]` filters projects by directory+name | handler cli.py:15225; data `db_list_projects` cli.py:4087 |
| LF-03 | `ls [ARG]` = project-scope precedence, else substring filter (title/dir/project) | scope logic cli.py:15258-15331; unmatched currently exits at 5287 |
| LF-04 | `lr [PATTERN]` filters running instances by project/cwd + session info | `cli_list_running` cli.py:11836; instance fields cli.py:7784-7788/8031-8035 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | LF-01 | In `preprocess_argv`, add `lr` short alias: `if rest[0].lower()=="lr": rest=["running", *rest[1:]]` alongside the ls/lp block (cli.py:5814-5817). Keep `list running` working. | cli.py | Low | new test: `preprocess_argv(["lr"])`/`["lr","foo"]` -> `["running", ...]` |
| 2 | LF-01 | Register a positional `pattern` (nargs="?") on the `running` subparser (cli.py:6451-6458) and carry it through `_normalize` (show_running block cli.py:6876-6881, which already maps `running_long` etc.) to a new flag `out["running_filter"]`. Note the existing `--long` flag uses `dest="running_long"` (cli.py:6456); Step 5 must read `running_long`, not `long`. | cli.py | Low | argparse accepts `running foo`; namespace carries `running_filter` |
| 3 | LF-02 | Add positional `pattern` (nargs="?") to `project list` (cli.py:6305) -> `out["projects_filter"]`. In the `list projects` handler (cli.py:15225), when set, keep only projects where `pattern.lower()` is in `directory.lower()` or `name.lower()`. Apply BEFORE `--limit` and in both text + `--json` paths. Empty-result message names the pattern. | cli.py | Low | filter narrows; json reflects filtered set; no match -> clear message |
| 4 | LF-03 | Add positional to `session list` (already has `name` at cli.py:6211): REUSE the existing `name` positional. In the handler, after the existing project-scope resolution (cli.py:15258-15331) FAILS to set `_project_id`/`_dir_scope` from an explicitly-provided `args.project`, do NOT exit: instead set a `_session_filter = args.project` and list all sessions, then keep only those whose title/directory/project_dir contains the pattern (case-insensitive). Preserve exact current behavior when `args.project` DOES resolve to a project. Must avoid the fatal `resolve_and_expand_targets` path for the positional (that path `sys.exit(1)`s at 5287); use a non-fatal project match (mirror the direct `db_list_projects()` scan already used at 15275-15291, or `resolve_targets` and check `.unmatched` without exiting). Apply filter before `--limit`, in text + `--json`. | cli.py | Medium | back-compat: `ls <realproject>` unchanged; `ls <substring>` filters instead of erroring; json reflects filter |
| 5 | LF-04 | In `cli_list_running` (cli.py:11836), when `running_filter` set, keep only instances where the pattern (ci) is in any of: `cwd`, `project`, or the attributed session's `id`/`ids`/`title`/`directory`/`project_id`. **Session-attribution availability (PR-001):** `_attribute_session` runs as part of `detect_running_instances` (cli.py:8031-8035), so the `session` dict is present on every instance regardless of the `--long` RENDER flag; `--long` only controls whether the Session COLUMN is shown, not whether the data exists. Therefore `lr <PATTERN>` can match session fields WITHOUT requiring `--long`. Confirm this at execution by reading `detect_running_instances`; if (contrary to the current reading) session attribution is gated behind `--long`, the filter MUST still force attribution so `lr <PATTERN>` matches session info as required, and this MUST be noted. Apply the filter before rendering; in `--json` too. Empty-result message names the pattern and the total-before-filter. | cli.py | Low | filter narrows by cwd/project AND by session info even without `--long`; json reflects it |
| 6 | LF-01..04 | Update help text: add `lr` next to lp/ls (cli.py:5539-5540, 5724, and the running help 5547/5697); document the optional `[PATTERN]`/filter arg on each of the three commands in their subparser help and the curated overview. | cli.py | Low | `ocman help`/`--help` shows lr + filter usage |
| 7 | all | CHANGELOG `[Unreleased]` -> new `Added` (lr alias; filter arg on lp/ls/lr) + `Changed` (ls positional now falls back to a substring filter instead of erroring on a non-project arg). Bump version to 1.3.0 at release (Section-9-equivalent / on approval). | CHANGELOG.md, pyproject.toml, cli.py:208 | Low | version consistent; changelog honest |

## Deferred / out of scope

- TUI filter parity for these lists: out of scope (the TUI already has its own filter/search
  surfaces; this IPD is CLI-only). Promote to a separate IPD if wanted.
- Regex or glob matching: out of scope; case-insensitive substring only (KISS, matches the
  existing `search`/resolver idiom).
- Filtering `list models` / `lm`: not requested; out of scope.

## Anti-regression / invariants

- `ls` with NO arg, and `ls <arg>` where `<arg>` resolves to a real project, behave EXACTLY as
  today (project scope). Only the previously-fatal "unresolvable arg" case changes (now filters).
- `lp`/`lr` with no arg behave exactly as today.
- `--json`, `--limit`, `--all-sessions`, `--brief`, `--long` semantics unchanged; the filter is
  applied before `--limit` so counts/withheld stay coherent.
- No change to DB queries' correctness; filtering is in-Python over already-fetched rows.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE ACTUAL output.
- New tests: `preprocess_argv` `lr` rewrite; `lp <pattern>` narrows (dir + name); `ls <realproject>`
  unchanged (back-compat) AND `ls <substring>` filters (title/dir/project) instead of exiting;
  `lr <pattern>` narrows by cwd/project and by session info WITHOUT `--long`; `--json` reflects
  the filtered set for each; empty-match messaging.
- **`--json` empty-result contract (PR-004):** when a filter matches nothing, `--json` MUST emit
  a well-formed payload with an EMPTY list and `count: 0` (mirroring the existing empty-list
  JSON shape), and exit 0, NOT print a human error or non-zero exit. This keeps `lp/ls/lr
  <pattern> --json` scriptable. Add a test asserting the empty-but-valid JSON for each command.
  The human (non-JSON) path may still print a friendly "no match for <pattern>" message.
- Cross-platform: use `abs_path` for any seeded absolute paths (Windows). No new skips.

## Spec / documentation sync

- CHANGELOG Added + Changed entries. Help text (`build_help` overview + per-subparser help).
- README command reference: add `lr` and the `[PATTERN]` filter to the list section.

## Open questions

None. Design settled with maintainer; the two finding-driven questions raised in /plan-review
were resolved from repository evidence, not from the human:
- PR-001 (does `lr` session filtering need `--long`?): NO. `_attribute_session` runs
  unconditionally inside `detect_running_instances` (cli.py:8034); `--long` only gates the
  rendered column, so the filter can match session fields without it.
- PR-002 (what does "resolves to a project" mean for `ls` precedence?): the exact
  `resolve_project_spec` rule (cli.py:4980-5000): exact-dir, else ends-with, else UNIQUE
  case-insensitive substring-on-directory; 0 or >=2 substring matches fall through to the
  filter. Documented in Design decisions with the two-mode subtlety flagged for help/CHANGELOG.

## Workflow history

- 2026-07-20 created (its_direct/pt3-claude-opus-4.8): authored from maintainer request.
- 2026-07-20 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED.
  PR-001 (lr session-filter availability, resolved from evidence: no `--long` needed),
  PR-002 (precise `ls` project-scope-precedence definition + documented two-mode subtlety),
  PR-003 (`--long` dest is `running_long`; Step 5 must read it), PR-004 (`--json` empty-match
  must be a well-formed empty payload, exit 0). No open questions; no unfixed BLOCKER/HIGH.
  GO - PENDING HUMAN APPROVAL.

## Approval and execution gate

- Execution checklist (MUST): before coding, create a TodoWrite step-granular checklist tracking
  each of Steps 1-7, the new tests, the full-suite run with pasted output, the README+CHANGELOG
  sync, the version bump to 1.3.0, the path-scoped commit(s), and the Status-executed +
  `git mv` to `executed/`.
- Scope fence: ONLY the list-command surface (preprocess_argv, the three handlers + their
  subparsers, help, README/CHANGELOG, tests). No TUI, no DB schema, no new runtime dependency.
- Honesty rule (hard MUST): paste ACTUAL `pytest -q` output; never claim a pass not run.
- Commits: path-scoped, NEVER push without approval, NEVER tag outside an approved release step.
- Lifecycle: on completion set `Status: executed` and `git mv` this IPD to `executed/`.
- Release: after execution + green CI, cut `1.3.0-rc1` (tag), validate, then promote to `1.3.0`
  via the release-execution discipline (each externally-visible action separately confirmed).

Next: human review (optionally `/plan-review`) sets `Status: approved`; then execute per the above.
