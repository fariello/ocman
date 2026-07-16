# IPD: Assess functionality - close user-facing capability and consistency gaps

- Date: 2026-07-15
- Concern: functionality (completeness vs. user/stakeholder needs)
- Scope: whole project (ocman CLI/TUI)
- Status: approved
- Approval: approved by maintainer 2026-07-15 (all 8 steps; open questions 1-2 answered below)
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-15 /assess functionality (its_direct/pt3-claude-opus-4.8): assessed; proposed 8 changes.
- 2026-07-15 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED; PR-001 (FIXED, characterization mechanism), PR-002 (FIXED, --force/-y semantics matrix), PR-003 (FIXED, --json schema-first sub-step), PR-005 (FIXED, execution contract in gate); PR-004 (acknowledged, no fix). Findings F1-F8 evidence re-verified against ocman/cli.py.

## Goal

Identify functionality that ocman's users and stakeholders would reasonably expect but
that is missing, incomplete, or inconsistent, and propose concrete, safe additions.
ocman's stated purpose is a complete administration suite for an OpenCode environment
(sessions, database, config): "administer, maintain, and repair." Judged against that
purpose, the command surface is broad and well wired, but there are real gaps in
machine-readability, spend reporting, and safety/affordance consistency that affect
daily usability.

## Project conventions discovered (Step 0)

- Guiding principles: `AGENTS.md` (prose conventions, plan lifecycle, execution
  contract); universal fallback (intuitive/self-documenting, KISS, honest docs) where
  unspecified.
- Pending-plans location/format used: `.agents/plans/pending/` with a two-directory
  lifecycle (`pending/` -> `executed/`); repo names plans `YYYYMMDD-<slug>-ipd.md`
  (this file follows that existing convention rather than the harness `-HHMM-NN-` form).
- Contributor/spec-sync contract: `AGENTS.md` (path-scoped commits, never push, paste
  real test output, no em/en dashes; behavior changes sync README/ARCHITECTURE/CHANGELOG).
- Stack / relevant context: single Python package `ocman/cli.py` (~12.8k lines) plus
  `ocman_tui`; SQLite over the OpenCode DB; argparse git/kubectl-style grammar; pytest
  (293 passed, 2 skipped at time of assessment).

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Persona = which
reviewer perspective surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| F1 | High | Low | Power user, stakeholder | Missing table-stakes | No machine-readable output. No `--json`/`--format` on any command; every command prints human tables only. ocman itself consumes `opencode session list --format json` but exposes nothing scriptable, so users cannot pipe ocman into other tooling. | `ocman/cli.py:1416` (consumes JSON); no `--json` anywhere |
| F2 | High | Medium | Stakeholder, power user | Documented-but-missing capability | `ocman spend` (per-project / per-session spend reporting, incl. historical) is a named backlog item with real demand, absent today. Cost is surfaced only inside `db info`, `models`, and compaction; `db info --by-project` reports disk only, not cost per project. | `TODO.md:5-28`; `db info` usage metrics `ocman/cli.py:10687-10721`; `_per_project_disk_usage` `10488` (no cost) |
| F3 | Medium | Low | Novice, stakeholder | Present-but-undocumented / stale docs | Top-level `export` help says "project export is not yet supported", but project export IS wired and works. Misleads users into not using a real capability. | help text `ocman/cli.py:5911`; project export handler `11546-11558` (`bundle_project_data`) |
| F4 | Medium | Low | Power user | Incomplete workflow (sugar asymmetry) | The top-level `move` sugar lacks `--confirm-remote-delete`, `-y/--yes`, and `--force`, which the group forms (`session move`/`project move`) have. So a remote move via `ocman move ...` cannot do the guarded local cleanup or skip prompts; users must switch to the long form. | sugar `ocman/cli.py:5898-5906` vs group forms `5812-5821`, `5834-5843` |
| F5 | Medium | Low | Novice, QA | Inconsistent safety affordance | `--yes` (skip typed confirm) exists on `session delete`/`compact`/`move` but NOT on `project delete`, `db clean`, `db clean-orphans`, `backup clean`, so those cannot run unattended/scripted without a TTY answer. | `-y` present `5796/5787/5820/5842`; absent `5829-5832`, `5853`, `5856`, `5878` |
| F6 | Medium | Low | Novice | Confusing dual-meaning flag | `--force` means "bypass process-lock checks" on all DB/delete/move ops but means "skip the confirmation prompt" on `history clear`. Same flag name, two behaviors; a user reasoning from one will be surprised by the other. | "Bypass process-lock" `5704/5795/5821/5832/5843/5858` vs "Skip the confirmation prompt" `5886` |
| F7 | Medium | Low-Medium | Power user, QA | Incomplete safety parity | `--dry-run` exists on delete/clean ops but is absent on `move`, `backup restore`, `session import`, and `history clear`, all of which mutate state. Users cannot preview these before committing. | dry-run present `5794/5831/5703/5857`; absent on move (`5812-5843`), restore (`5875`), import (`5803`), history clear (`5885`) |
| F8 | Low | Low | Power user | Missing table-stakes | No list pagination/limit on `session list`, `project list`, `history show` (only `search` has a per-session line cap `-n`); `db info` top-models is hardcoded `LIMIT 3`. Long installations produce unbounded output. | search `-n` `5682`; no limit on list/history; `db info` `LIMIT 3` `10707` |

Not proposed as defects (verified present, for the record): `-V/--version` exists
(`5725`); help is rich (`help [TOPIC]`, `help all`, per-command `-h`); `--db` override
is global; shell completion and a `resume/open` verb are absent but judged out of scope
(see Deferred and Open questions).

## Proposed changes (ordered, validatable)

Fix by default; each item is safe and independently shippable. Order reflects
value/effort and dependency (F3 first as a pure doc fix; consistency fixes next; larger
features last).

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | F3 | Correct the `export` help text to state project export IS supported (auto-detected). | `ocman/cli.py:5911` (+ README if it repeats the claim) | Low | `ocman export --help` shows accurate text; grep shows no "not yet supported"; add/keep a project-export test. |
| 2 | F4 | Add `--confirm-remote-delete`, `-y/--yes`, `--force` to the top-level `move` sugar and thread them into the shared `_execute_move` (already accepts these). | `ocman/cli.py:5898-5906`, normalizer `_apply_move_or_export` | Low | New parse test: `ocman move S to h:/p --confirm-remote-delete -y` sets the flags; dispatches identically to `session move`. |
| 3 | F6 | Disambiguate confirm-skip vs process-lock. Target semantics matrix (make it TRUE everywhere): `-y/--yes` = skip the typed confirmation; `--force` = bypass the process-lock check ONLY. On `history clear`, ADD `-y` as the confirm-skip and keep `--force` as a working back-compat alias that also skips confirm there (history clear has no process lock), documenting `-y` as preferred. Do NOT make `--force` skip confirm on any command that has a process lock. | `ocman/cli.py:5886` (+ help strings for 5704/5795/5821/5832/5843/5858) | Low | Tests assert the matrix: on a process-lock op, `--force` alone does NOT skip the typed confirm (still prompts / declines non-TTY), and `-y` does; on `history clear`, both `-y` and `--force` skip. `--help` text reads consistently. |
| 4 | F5 | Add `-y/--yes` (typed-confirm skip) to `project delete`, `db clean`, `db clean-orphans`, `backup clean`, mapping to the existing `confirm_destructive(assume_yes=...)` seam. `--force` on these stays process-lock-only (per Step 3); adding `-y` must NOT change what `--force` does. | `ocman/cli.py:5829-5832,5853,5856,5878` + handlers | Low | Tests: each command with `-y` proceeds non-interactively; with only `--force` (no `-y`) on a non-TTY it still declines (confirm not skipped); baseline behavior without either flag is unchanged. |
| 5 | F7 | Add `--dry-run` to `session move`/`project move` (report the plan and, for remote, the runbook, without acting) and to `session import` (report what would be imported/remapped). Defer restore/history-clear dry-run (see Deferred). | `ocman/cli.py` move handlers, `extract_and_import_session` | Low-Medium | Tests: `move --dry-run` and `import --dry-run` change nothing on disk/DB and print the intended actions. |
| 6 | F8 | Add `--limit N` (and sensible default cap with a "showing N of M" note) to `session list`, `project list`, `history show`; make `db info` top-models limit a constant/flag. | `ocman/cli.py` list/history/info renderers | Low | Tests: `--limit 2` caps rows and prints the truncation note; default behavior unchanged when under the cap. |
| 7 | F1 | Add `--json` to read/report commands (`session list`, `project list`, `db info`, `search`, `history show`), keeping human output the default. FIRST sub-step: define the per-command JSON schema (top-level object with a `schema_version` int and a command-named array/object; keys mirror the existing dict fields such as `id`, `title`, `project_dir`, `created`/`updated` as epoch-ms integers, `cost` float, `tokens_input/output/cache_read` ints; nulls emitted as JSON `null`, never the "not available" glyph) and get it reviewed before wiring. Then add one small `emit(rows, as_json)` helper reused by all five commands (one path, not five). | `ocman/cli.py` renderers + a shared emit helper | Medium | Tests: `--json` parses (`json.loads`), contains the documented keys and `schema_version`, and renders nulls as `null`; the schema is documented in README; human output byte-for-byte unchanged without the flag (characterization test per Required tests). |
| 8 | F2 | Implement `ocman spend` per its backlog spec: per-project spend table (default), `--sessions`/`ocman spend <project>` detail, live vs live+historical toggle, reusing `estimate_cost`/session cost columns and the history ledger; forked-dedupe is a stretch, out of this IPD's core. | `ocman/cli.py` (new subcommand + query), README, CHANGELOG | Medium | Tests: per-project totals equal SUM(cost) per project; historical toggle includes/excludes ledger cost; `--json` variant if Step 7 landed. Open questions in TODO.md must be resolved first (see below). |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| F7 (restore/history-clear dry-run) | Medium-High | Functionality | `backup restore` relies on an always-created rollback backup and has no confirm today; adding a faithful dry-run means modeling the full restore without side effects, which risks diverging from the real path and giving false assurance. `history clear` dry-run is lower value (ledger-only). | Separate IPD scoping a restore preview that shares the real restore's planning code, or add a confirm prompt instead. |
| (new) shell completion | Medium | Complexity | Real value but adds a dependency/generator and packaging surface; a product/priority call, not a clear gap. | Its own IPD if desired (argparse + argcomplete or a static completion script). |
| (new) `resume`/`open` session | High | Functionality | ocman deliberately recovers/exports transcripts; launching/resuming an OpenCode session is a different responsibility and a scope decision for the maintainer. | Open question below; separate IPD if in scope. |
| F2 forked-spend dedupe | Medium-High | Complexity | Attributing shared/forked tokens once across a fork tree is genuinely hard and the backlog marks it optional ("do not block the core"). | Follow-up once base `ocman spend` ships. |

## Scope check

- Over-scope (untraceable to a need): none proposed; `--json`, `--limit`, and `spend`
  all trace to power-user/stakeholder needs or the explicit backlog. Forked-spend
  dedupe and resume/completion are deliberately deferred, not gold-plated in.
- Under-scope (needed capability missing; proposed to add): machine-readable output
  (F1/Step 7), spend reporting (F2/Step 8), safety-affordance parity (F4-F7).

## Required tests / validation

- Run the full suite after each step: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`
  and paste the real runner output (per AGENTS.md).
- Per-step tests are named in the table above; emphasize characterization: human
  output must be unchanged when the new flags are absent (F1, F6, F8 especially).
- **Characterization mechanism (how "unchanged" is pinned):** before adding a flag to a
  command that already prints, capture the CURRENT default output in a test using the
  existing `capsys`/`temp_db` pattern (see `tests/test_ocman.py::test_db_show_info`,
  `test_list_sessions_approximate_stats`, `test_db_show_info_by_project`) and assert the
  new default run still contains those exact markers. The new flag is exercised in a
  SEPARATE assertion. This turns "unchanged" from a claim into a regression guard. For
  F8, assert the default (no `--limit`) output is byte-for-byte the pre-change output on
  a small fixture.
- For F5/F4, assert both the new-flag path (skips confirm / sets flags) and the
  unchanged non-TTY-declines-safely default. Reuse the `confirm_destructive(assume_yes=...)`
  seam (verified present at `ocman/cli.py:7264`, `7775`, `8330`); `-y` must map to
  `assume_yes`, NOT to `--force` (which stays process-lock only, per F6/Step 3).

## Spec / documentation sync

All steps change user-visible behavior; each must update the README command table and
relevant sections, `ARCHITECTURE.md` where a new seam is added (JSON emitter, `spend`),
and `CHANGELOG.md` under Unreleased. Step 1 is itself a doc fix. Step 8 should also
remove its item from `TODO.md` once shipped.

## Open questions

1. **`--json` schema stability:** RESOLVED (maintainer 2026-07-15): YES, treat JSON
   output as a documented, semi-stable contract with a `schema_version` field; note
   breaking schema changes in CHANGELOG. Step 7 proceeds.
2. **`ocman spend` data source (from TODO.md):** RESOLVED (maintainer 2026-07-15): BOTH
   live session cost columns AND the deletion history ledger
   (`OPENCODE_HISTORY_PATH`), with a flag toggling live-only vs. live+historical.
   "Historically saved spend" = cost of since-deleted sessions/projects recorded in the
   ledger's cumulative totals (not compaction-avoided estimates). Step 8 proceeds.
3. **`resume`/`open` a session:** in scope for ocman at all, or explicitly a non-goal
   (ocman = manage/recover, opencode = run)? Deferred pending this decision.
4. **`--yes` vs `--force` convergence (F6):** acceptable to keep `--force` as a working
   alias on `history clear` for back-compat while steering docs/users to `-y`? Assumed
   yes (no breaking change).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed.

Execution contract (binding on whoever executes):
- **Open questions:** Steps 1-6 have no blocking open questions. Step 7 is gated on
  open question 1 (JSON schema-stability commitment); Step 8 is gated on open question 2
  (`ocman spend` data source). Do NOT execute 7 or 8 until those are answered.
- **Scope fence:** implement only the approved Steps as written. Explicitly OUT (see
  Deferred): `backup restore`/`history clear` dry-run, shell completion, `resume`/`open`,
  and `ocman spend` forked-spend dedupe. Do not expand scope without a new plan.
- **Honesty (hard MUST):** when reporting tests, paste the ACTUAL runner output
  (`PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`). Never claim a pass you did
  not run.
- **Commit discipline:** commit ONLY the files you changed, path-scoped
  (`git commit -m msg -- <paths>`); never `git add -A`/`-a`, never push, never tag.
- **Lifecycle:** each Step is independently shippable; approval and execution may be
  partial. On completing the approved set, set `Status: EXECUTED (<date>)` and `git mv`
  this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`. If only some
  Steps are executed and the rest are dropped, retire per the repo lifecycle (record
  what shipped vs. what was cut).

Recommended next steps:

1. Review this IPD (this `/plan-review` set `Status: reviewed`). Steps are independently
   shippable, so approval can be partial (e.g. approve Steps 1-6 now, hold 7-8 pending
   open questions 1-2).
2. On approval, set `Status: approved` (+ an `Approval:` line), execute the approved
   ordered steps, run the validation, and sync docs.
3. Then set the terminal `Status: EXECUTED` and `git mv` this IPD to
   `.agents/plans/executed/` per the repo lifecycle.
