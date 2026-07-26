# IPD: Assess self-documentation - make the CLI teach at first run and signal errors honestly

- Date: 2026-07-25
- Concern: self-documentation (in-product, learn-as-you-go clarity)
- Scope: whole project, `ocman/cli.py` CLI surface (help text, naming, errors, first-run,
  discoverability); verified against the shipped binary and source
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-25 /assess self-documentation (its_direct/pt3-claude-opus-4.8-1m-us): assessed; proposed 9 changes
- 2026-07-25 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-01..PR-04 (added anti-regression clause naming existing picker + db-info tests; confirmed the db-info exit-code change has no TUI caller; pinned the SD-06 verb change to preprocess_argv; named the SD-01 exit-0 proof). SD-06 resolved = verb `focus` with `filter` alias; SD-01 resolved = keep TTY picker, fix piped path. No open questions remain.

## Goal
The ocman CLI already teaches unusually well (near-total `help=` coverage, task-grouped runnable
examples in the top-level help, actionable "no matches" errors with Suggestions, a `help TOPIC`
system, optional config with a graceful no-config fallback, and best-in-class no-project onboarding).
This plan closes the few places where the product does NOT teach or MISLEADS: the no-args first-run
experience (it silently drops into an interactive picker that EOF-crashes and exits 1 in any
non-TTY context, while the help text promises a plain listing), a couple of error signals that
return success, and small help/naming/discoverability polish. Make the product itself teach and
signal correctly rather than relying on external docs.

## Project conventions discovered (Step 0)
- Guiding principles: AGENTS.md (prose: no em/en dashes in authored prose; sanctioned glyph
  exceptions). Universal fallbacks otherwise.
- Plan lifecycle: `.agents/plans/pending/` -> `.agents/plans/executed/`; files
  `YYYYMMDD-HHMM-NN-<slug>.md`; front-matter `Status:` readiness (to-review -> reviewed -> approved).
- Contributor contract: AGENTS.md + CONTRIBUTING.md.
- Stack: Python 3.10+ argparse CLI (`ocman/cli.py`, ~17k lines) + Textual TUI; version 1.3.0.
- Test stack: pytest (`tests/test_ocman.py`, `tests/test_tui.py`); Linux venv at
  `/home/gfariello/venv/p3.14/`; run `PYTHONPATH=. pytest -q`.
- Review-scope exclusion honored: `.agents/workflows/` and `workflow-artifacts/` NOT assessed as
  the product.

## Findings
Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Persona: N=novice,
U=ui/ux, P=power-user.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| SD-01 | HIGH | Low | N,U | First-run / errors | Bare `ocman` (no subcommand) in a project lists sessions then PROMPTS `Select a session number...`; with non-TTY stdin (pipe/CI/capture) that `input()` hits EOF and is caught as `Error: Unexpected error: EOF...`, exiting 1. A novice or any script gets a crash+failure on the most natural first command. Verified: exit 1 with `</dev/null`. | prompt at cli.py:1697; no-args dispatch cli.py:16794; EOF guard cli.py:15609 |
| SD-02 | HIGH | Low | N | Help accuracy | The top-level/`help` text promises `(no args: lists this directory's sessions, or all projects if none)`, but no-args actually launches the interactive picker (SD-01). The product's own help misrepresents its behavior. | cli.py:5634 vs the picker path cli.py:16794 |
| SD-03 | MEDIUM | Low | N,P | Errors / exit signal | `db info` against a missing `--db` prints a soft yellow "Database file not found" and then renders a mostly-empty info screen, exiting 0. The ideal actionable message already exists (`_db_not_found_error`) but is not used here. Exit 0 hides the failure from scripts. | soft warn cli.py:12894; unused ideal error cli.py:1214-1223 |
| SD-04 | MEDIUM | Low | P | Errors / exit signal | `session search` with no matches prints "No sessions match X." and returns, exiting 0, while the target-resolver's "No matches found" exits 1. Inconsistent signalling; a script cannot tell "ran, empty" from "typo". (Empty-search=0 is defensible; the inconsistency + intent should be explicit.) | search cli.py:16345 (no exit) vs resolve cli.py:5277-5290 (exit 1) |
| SD-05 | MEDIUM | Low | N,U | Examples at point of use | Per-command `-h` shows only usage+flags, no examples; the rich examples live only in the top-level help / `help TOPIC`. A user who runs `session recover -h` (the natural learn-in-place move) never sees e.g. `-mi 50` in context. No `epilog=` on subparsers. | subparser build cli.py:6066-6579 (no epilog) |
| SD-06 | MEDIUM | Low | N | Naming | `filter` as a top-level verb reads as "filter a list" but means "re-scope a recovery Markdown doc via the LLM"; the name misleads even though help clarifies. | cli.py:6506 |
| SD-07 | LOW | Low | N | Help text | `db rebase` help ("Bulk rebase path prefixes...") explains the jargon with the same jargon, so it does not teach. | cli.py:6387 |
| SD-08 | LOW | Low | N | Help text | `filter -C/--compact` help is just "Model to use." and `-oc/--output-compact` just "Output path."; `filter --scope` does not say it is effectively required. Terser than the identical recovery options. | cli.py:6509-6514 |
| SD-09 | LOW | Low | N | Discoverability | A few terminal empty-result `die()`s give no next-step: `die("No sessions found.")` and `die("No sessions found for project: ...")`. | cli.py:16183, 16187 |

## Proposed changes (ordered, validatable)
Fix the misleading/hazardous first-run cluster first (SD-01/02), then the error-signal fixes, then
polish. All are Low Remediation Risk (local, verifiable, no data path touched).

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | SD-01 | In the no-args-in-project path, only launch the interactive picker when stdin is a TTY (`sys.stdin.isatty()`). When stdin is NOT a TTY, print the session listing (non-interactive) and exit 0 instead of prompting. No behavior change for a human at a terminal. | ocman/cli.py (no-args dispatch near :16794; picker :1697) | Low | `ocman </dev/null` exits 0 and prints the listing, not an EOF error; interactive `ocman` at a TTY still shows the picker. Add a test: no-args + non-TTY -> exit 0, no "EOF"/"Unexpected error" in output. |
| 2 | SD-02 | Make the help text match the (now TTY-gated) behavior: e.g. "(no args: at a terminal, pick a session to recover; when piped, lists this directory's sessions)". | ocman/cli.py:5634 | Low | `ocman help` line matches step-1 behavior |
| 3 | SD-03 | Route `db info` on a missing DB through the existing `_db_not_found_error()` (raise -> `die` exit 1 with the actionable "Point at a database with --db PATH, or run OpenCode first" wording) instead of the soft yellow warning + empty screen. | ocman/cli.py:12894 (use :1214-1223) | Low | `ocman --db /nope db info` exits 1 with the actionable message; add a test |
| 4 | SD-04 | Keep `session search` empty-result exit 0 (defensible: "ran, no matches"), but make the intent explicit: a one-line code comment at the branch and confirm it prints a next-step hint. Do NOT change the exit code (changing it could break scripts). | ocman/cli.py:16345 | Low | Comment present; behavior unchanged; note in validation that empty-search intentionally exits 0 |
| 5 | SD-05 | Add an `epilog=` with 1-2 runnable examples to the highest-traffic subcommands (`session recover`, `session compact`, `db clean`, `search`, `backup create`), OR a footer line pointing to `ocman help <topic>`. | ocman/cli.py (those subparsers) | Low | `ocman session recover -h` shows at least one example (e.g. `-mi 50`) |
| 6 | SD-06 | RESOLVED with maintainer 2026-07-25: make `focus` the PRIMARY verb (plain: "focus this recovery doc on the topic I describe"), keep `filter` as a still-working alias. Minimal-churn approach: register the subcommand as `focus` (rename the `new_sub("filter", ...)` at cli.py:6506 to `new_sub("focus", ...)`) and add a `filter` -> `focus` rewrite branch in `preprocess_argv` (cli.py:5766; mirror the `lr`/`lp` branches at cli.py:5827-5829). Do NOT register two subparsers. Update the dispatch key (`group == "filter"`) and the top-level help line to `focus`. Confirm the argv rewrite happens BEFORE argparse sees the verb so `ocman filter ...` still works unchanged. | ocman/cli.py:6506 (subparser + its dispatch); cli.py:5766/5827-5829 (alias mechanism) | Low | `ocman focus FILE.md --scope ...` works; `ocman filter ...` still works (aliased); `ocman -h`/`help` lists `focus` |
| 7 | SD-07 | Rewrite `db rebase` help to teach without the jargon: "Bulk-rewrite stored path prefixes (e.g. after moving your home dir); --from OLD --to NEW." | ocman/cli.py:6387 | Low | `ocman db rebase -h` no longer defines "rebase" with "rebase" |
| 8 | SD-08 | Flesh out the `filter` option help: `-C/--compact` -> "Model to re-scope with"; `-oc/--output-compact` -> "Output path for the re-scoped document"; `--scope` -> note it is required unless `--project` is given. | ocman/cli.py:6509-6514 | Low | `ocman filter -h` reads clearly |
| 9 | SD-09 | Append a next-step to the bare empty-result dies: "Run 'ocman list projects' to see what exists." | ocman/cli.py:16183, 16187 | Low | those messages now include a next step |

## Deferred / out of scope (with reason)
- Shell completion (argcomplete / static scripts) was surfaced (a real discoverability win for a
  noun-verb CLI) but is DEFERRED: it adds a new dependency/packaging surface and per-shell install
  docs (Complexity axis, Medium-High for a self-documentation polish plan). Recommended as its own
  small IPD if wanted. This is a scope/complexity deferral, not an effort deferral.
- Broader command re-naming beyond SD-06 (e.g. consolidating reclaim/db clean/clean-orphans verbs)
  is NOT proposed: their help already distinguishes them and `doctor` routes users to the right one;
  renaming stable commands risks breaking users' muscle memory and scripts (usability axis).

## Scope check
- Over-scope: none. SD-06 renames the verb to `focus` but keeps `filter` working as an alias (no
  removal, no broken usage); no gold-plating.
- Under-scope: SD-01 (the first-run EOF crash) is the one genuine capability gap and is proposed as
  step 1. Shell completion is a real gap but deferred with the named axis (not dropped).

## Required tests / validation
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output).
- ANTI-REGRESSION (steps 1 and 3 change behavior; name the affected invariants and their tests):
  BEFORE editing, note the existing tests on these paths and confirm they still pass (or are updated
  intentionally, not accidentally broken): the session picker `test_picker_uses_real_db_stats`
  (tests/test_ocman.py:2408) for step 1; and the db-info tests `test_db_show_info` /
  `test_db_show_info_by_project` / `test_e2e_db_info_runs` (tests/test_ocman.py:425/546/2232) for
  step 3. Step 3 changes the missing-DB path from exit 0 to a raised RecoveryError/exit 1: confirm
  NO caller depends on `db info` returning 0 on a missing DB (verified in review: `ocman_tui/` does
  NOT call `db_show_info`; re-check `doctor`/`reclaim` storage-discovery paths do not route through
  it for the missing-DB case).
- New/updated tests: (a) no-args + non-TTY stdin exits 0 and prints the listing without "EOF"/
  "Unexpected error" (SD-01); (b) `db info` on a missing DB exits 1 with the actionable message
  (SD-03); (c) `ocman focus ...` and the `ocman filter ...` alias both dispatch to the same command (SD-06).
- Manual/`-h` checks (paste ACTUAL output): the SD-01 proof `ocman </dev/null; echo $?` MUST print
  the listing (no "EOF"/"Unexpected error") and `$?` MUST be `0`; `ocman session recover -h` shows
  an example (SD-05); `ocman focus -h` / `ocman db rebase -h` read clearly; `ocman filter -h`
  still resolves to the same command (SD-06 alias).
- Prose: no em/en dashes introduced in any help/error string or comment
  (`grep -nP $'[\u2013\u2014]'` on the changed files yields no NEW matches).

## Spec / documentation sync
Steps 1-2 change user-visible first-run behavior and the help text together (the help is corrected
in the same step, so it cannot drift). Step 6 renames the verb to `focus` (with `filter` kept as an
alias): update README's Top-level verbs table (rename the `filter` row to `focus`, note the `filter`
alias) and add a CHANGELOG `[Unreleased]` entry. Steps 3-9 are otherwise in-product wording; no
further README change required.

## Open questions
- SD-06: RESOLVED with maintainer 2026-07-25 = make `focus` the primary verb, keep `filter` as a
  working alias (both `rescope` and keeping `filter`-only were rejected: `rescope`/`filter` do not
  teach a novice; `focus FILE.md --scope "X"` reads as "narrow this doc to that topic").
- SD-01: RESOLVED with maintainer 2026-07-25 = keep the interactive picker at a TTY; change ONLY
  the non-TTY (piped/CI) path to print the listing and exit 0. (Dropping the picker / printing help
  were rejected to preserve established, tested behavior.)

## Approval and execution gate
This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT
auto-executed.
- Open questions: SD-06 (verb -> `focus`, keep `filter` alias) and SD-01 (keep TTY picker, fix
  piped path) RESOLVED with maintainer 2026-07-25; no open questions remain.
- Scope fence: `ocman/cli.py`, `tests/test_ocman.py`, and (for the `focus` rename + `filter` alias)
  `README.md` and `CHANGELOG.md`. Nothing else.
- Honesty rule (hard MUST): paste the ACTUAL `pytest -q` output and the ACTUAL `-h` / `echo $?`
  output that demonstrates each behavior change.
- Commits: path-scoped (`git commit -- <paths>`), never `git add -A`, never push.
- Prose: no em/en dashes introduced.
- Lifecycle: on green tests + validation, set `Status: executed` and `git mv` this file to
  `.agents/plans/executed/`.
