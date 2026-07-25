# IPD: Assess documentation - README accuracy for the 1.3.0 CLI surface

- Date: 2026-07-25
- Concern: documentation
- Scope: whole project; edits limited to README.md, CHANGELOG.md, and TODO.md; verified against ocman/cli.py
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-25 /assess documentation (its_direct/pt3-claude-opus-4.8-1m-us): assessed; proposed 7 changes
- 2026-07-25 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-01..PR-03 (added execution-contract gate: scope fence, honesty rule, path-scoped/never-push, lifecycle; completed the AD-06 changelog entry to cover both kill IPDs). AD-02 resolved with maintainer.

## Goal
Bring the user-facing docs back into exact agreement with what ocman 1.3.0 actually does. The
README is unusually accurate already; this plan fixes the one genuinely wrong documented behavior
(the `kill` argument no longer matches its synopsis after kill-by-PID shipped), one inaccurate
environment-variable claim, and a handful of small placement/discoverability gaps. Accurate docs
over impressive docs: this is targeted correction, not expansion.

## Project conventions discovered (Step 0)
- Guiding principles: AGENTS.md (prose: no em/en dashes in authored prose; sanctioned glyph
  exceptions noted there). Universal fallbacks otherwise.
- Pending-plans location/format: `.agents/plans/pending/` -> `.agents/plans/executed/`; files
  `YYYYMMDD-HHMM-NN-<slug>.md`; front-matter `Status:` readiness (to-review -> reviewed -> approved).
- Contributor/spec-sync contract: AGENTS.md + CONTRIBUTING.md (docs are user-visible; keep in sync).
- Stack: Python 3.10+ CLI (`ocman/cli.py`) + Textual TUI (`ocman_tui/`); version 1.3.0.
- Review-scope exclusion honored: `.agents/workflows/` and `workflow-artifacts/` were NOT assessed
  as project docs.

## Findings
Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Persona: N = novice,
E = engineer/operator.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| AD-01 | High | Low | E,N | Accuracy | README documents `ocman kill [PATTERN]` only; the shipped command takes `PID\|PATTERN` (a bare all-digits arg is a PID) and shows an enriched confirm preview (PID/Kind/Uptime/Project/Session+provenance, Listener/Auth when a listener exists). The synopsis is now literally wrong. | README.md:444 vs ocman/cli.py:6458-6460, 12446-12453 (PID branch), 12500-12514 (preview) |
| AD-02 | Medium | Low | E | Accuracy | Env-var table claims `OCMAN_CONFIG_PATH` "Overrides the location of ocman.toml". In code it is a hardcoded module constant, never read from the environment (no `os.environ`/`getenv` for it), so setting it in the shell has NO effect. A user following the README silently fails to relocate their config. | README.md:521 vs ocman/cli.py:224 (constant); grep of ocman/ finds no environ read |
| AD-03 | Medium | Low | N,E | Navigation | `ocman spend` is listed inside the `### history (activity ledger)` table, but `spend` is a top-level verb (there is no `ocman history spend`). Misleads discovery. Flags shown are accurate. | README.md:425 (under history table at :419) vs ocman/cli.py:6497; top-level section at README.md:433 |
| AD-04 | Low | Low | E | Reference | `lr`/`running` `--long` flag (adds a best-guess Session column) is not documented among the `lr` options. | README.md:439 vs ocman/cli.py:6533-6534 |
| AD-05 | Low | Low | N | Completeness | `session export` row reads session-only; project export is only reachable via the top-level `ocman export project SPEC`. No pointer connects them. | README.md:357 vs ocman/cli.py:6296-6299, 6482-6484 |
| AD-06 | Low | Low | E | Changelog hygiene | CHANGELOG `[Unreleased]` is empty although post-1.3.0 work (kill-by-PID + enriched kill preview) is in code. | CHANGELOG.md:3 vs ocman/cli.py:6458, 12500-12514 |
| AD-07 | Low | Low | N | Limitations | Platform support is stated per-command (Linux-only kill/reconnect/running/doctor-server-check) but there is no single consolidated "Platforms" statement tying it to the Linux-only `pysqlite3-binary`. | README.md:439-445, 605 vs pyproject.toml:19 |

## Proposed changes (ordered, validatable)
Fix inaccuracies first (AD-01, AD-02), then navigation/reference, then hygiene/polish.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | AD-01 | Change the README `kill` row title to `ocman kill [PID\|PATTERN]` and add one sentence: a bare all-digits argument is a PID (killed directly after an informed confirm); the confirm preview shows PID, Kind, Uptime, Project, and Session (with provenance), plus a Listener/Auth line when that instance serves a control server. | README.md:444 | Low | Re-read row against ocman/cli.py:6458-6460 and the preview at 12500-12514; wording matches shipped behavior |
| 2 | AD-02 | Correct the env-var table: remove the `OCMAN_CONFIG_PATH` row (it is not an env override). See Open question for the alternative (implement the env read) which is OUT OF SCOPE for this docs plan. | README.md:521 | Low | grep ocman/ shows no environ read for it; row no longer claims an override |
| 3 | AD-03 | Move the `ocman spend` row out of the `### history` table into "Top-level verbs and aliases" (or annotate it as a top-level verb, not `history spend`). | README.md:425, 433 | Low | Confirm `spend` registered top-level at ocman/cli.py:6497; no `history spend` in parser |
| 4 | AD-04 | Add `--long` to the `lr` options description ("adds a best-guess, possibly stale Session column"). | README.md:439 | Low | Matches ocman/cli.py:6533-6534 |
| 5 | AD-05 | Add a parenthetical to the `session export` row pointing to `ocman export project SPEC to FILE` for whole-project bundles. | README.md:357 | Low | Matches ocman/cli.py:6482-6484 |
| 6 | AD-06 | Add an `[Unreleased]` `### Added` CHANGELOG entry covering BOTH post-1.3.0 kill changes shipped in code: the enriched `kill` confirm/choose preview (executed IPD `20260724-1057-01`) AND kill-by-PID (executed IPD `20260724-1454-01`). | CHANGELOG.md:3 | Low | Entry references both shipped behaviors and their executed IPDs; Keep-a-Changelog format preserved |
| 7 | AD-07 | Add a short "Platforms" note to Known Limitations: fully supported on Linux; on macOS/Windows the process features (kill/reconnect/list running/doctor server check) degrade or are unavailable, and `pysqlite3-binary` is Linux-only (stdlib sqlite3 elsewhere). | README.md:605 | Low | Matches per-command Linux-only markers + pyproject.toml:19 |
| 8 | AD-02 | Add a TODO.md item (to-consider/reconsider) recording the removed `OCMAN_CONFIG_PATH` env-override: note it was documented but never implemented (only a per-run `--db` override and programmatic rebinding exist), and that adding a real env override would be a small code change with its own tests + load-ordering care. | TODO.md | Low | TODO.md carries the deferred capability with rationale so it is not lost |

## Deferred / out of scope (with reason)
None deferred on Remediation-Risk grounds (all fixes are Low risk). The CODE alternative for AD-02
(make `OCMAN_CONFIG_PATH` an actual env override) is out of scope because this is a documentation
plan and it is a behavior change requiring its own decision and tests (see Open questions); the
docs-side correction (remove the false claim) is proposed above and is sufficient to remove the
inaccuracy.

## Scope check
- Over-scope: none. The plan corrects/annotates existing rows and adds one short note; it does not
  expand the README with aspirational or duplicated content (Complexity axis respected).
- Under-scope: none for documentation. AD-02's optional code path is intentionally excluded and
  called out as an open question rather than silently dropped.

## Required tests / validation
- No code changes, so no unit tests. Validation is re-reading each changed line against the cited
  `ocman/cli.py` evidence and running `ocman kill -h`, `ocman lr -h`, `ocman spend -h` to confirm
  the documented surface matches the parser help.
- Prose check: no em/en dashes introduced (`grep -nP $'[\u2013\u2014]' README.md CHANGELOG.md`
  yields no NEW matches beyond sanctioned glyph exceptions).
- Optional: run `/plan-review` on this IPD before execution.

## Spec / documentation sync
This plan IS the documentation sync. It changes no user-visible runtime behavior; it makes the docs
match already-shipped behavior. If AD-02 is later resolved by implementing the env override
(separate plan), that plan owns adding the row back plus tests.

## Open questions
- AD-02: RESOLVED with maintainer 2026-07-25 = DOCS FIX. Remove the false `OCMAN_CONFIG_PATH`
  env-override row from README (step 2), and ALSO record the env-override as a future
  to-consider/reconsider item in `TODO.md` with a short explanation (step 8), so the dropped
  capability is not lost. Implementing the env override remains a SEPARATE code plan if pursued.

## Gate / execution contract (MUST, per AGENTS.md)
- Open questions: AD-02 (docs-fix vs code env-override) MUST be resolved before executing step 2
  (see Open questions; resolved with maintainer during /plan-review, recorded there).
- Scope fence: `README.md`, `CHANGELOG.md`, and `TODO.md` ONLY. No code, tests, or other files.
  (This is a documentation plan; the AD-02 env-override, if pursued, is a SEPARATE code plan with
  its own scope and tests.)
- Honesty rule (hard MUST): paste the ACTUAL verification output, i.e. the `ocman kill -h`,
  `ocman lr -h`, and `ocman spend -h` help text, alongside the changed README rows, to prove the
  docs match the shipped parser. Do not claim a match you did not run.
- Commits: path-scoped (`git commit -- README.md CHANGELOG.md ...`), never `git add -A`, never push.
- Prose: no em/en dashes introduced (`grep -nP $'[\u2013\u2014]' README.md CHANGELOG.md` yields no
  NEW matches beyond sanctioned glyph exceptions).
- Lifecycle: on completion + validation, set terminal `Status: executed` and `git mv` this file
  from `.agents/plans/pending/` to `.agents/plans/executed/`.

## Approval and execution gate
This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT
auto-executed. Next steps: review (optionally `/plan-review` this file, which sets
`Status: reviewed`); on approval set `Status: approved` (+ `Approval:` line), apply steps 1-7, run
the validation, then set the terminal `Status: executed` and `git mv` this file to
`.agents/plans/executed/`.
