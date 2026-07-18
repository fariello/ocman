# IPD: Assess documentation - fix README/ARCHITECTURE accuracy after the recent feature wave

- Date: 2026-07-17
- Concern: documentation
- Scope: whole-project written docs (README.md, ARCHITECTURE.md, CHANGELOG.md,
  the generated config template); accuracy-first, verified against `ocman/cli.py`.
- Status: EXECUTED
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-17 /assess documentation (its_direct/pt3-claude-opus-4.8): assessed; proposed 14 changes.
- 2026-07-18 executed. Notes / deltas since the audit:
  - D-01/D-02/D-04 (README zero-dep + `ocman.py` standalone story; ARCHITECTURE `ocman.py`
    and "standard library only"): fixed. README now lists the real deps
    (textual/rich/vistab/pysqlite3-binary) and the `ocman = "ocman:main"` console script;
    ARCHITECTURE points at `ocman/cli.py`.
  - D-03: recovery-options table split into shared vs compaction-only (verified against
    `session recover --help` / `session compact --help`).
  - D-05/D-06: config template fixed (`default_out_dir = "opencode-recovery"`,
    `filter_secret_scan = "conservative"`) and the 4 missing keys added; the README block
    now parses as valid TOML and covers every `DEFAULT_CONFIG` key.
  - D-07: added an "Environment variables" subsection (NO_COLOR, FORCE_COLOR,
    OCMAN_CONFIG_PATH, OPENCODE_DB, XDG_DATA_HOME, OPENCODE_CONFIG_DIR). OCMAN_BENCHMARK is
    a test-only var and intentionally omitted from the user README.
  - D-08: added the missing flags (list `--json`/`--limit`, `session show -D`,
    `session import --dry-run`, reclaim `--tmp-min-age-hours`/`--force`).
  - D-09: ARCHITECTURE verb list now includes spend/running/doctor/reclaim.
  - D-10: softened the `help all` claim (curated, not exhaustive). Note: since the audit,
    commit 704180b already made `help`/`help all` list doctor/spend/running, so this is now
    a wording fix only.
  - D-11 (CHANGELOG): the reclaim/batch-delete CHANGELOG wording was already refined in
    later commits; not re-edited here. Additionally documented two features that shipped
    AFTER this IPD was written: extract-on-delete (`--extracts`/`--no-extracts`/`-o` on
    session/project delete and db clean) and the bare-word `help` == `-h` behavior.

## Goal

Bring ocman's written documentation back into agreement with what the code does today.
A large feature wave shipped recently (doctor/reclaim, chunking, the two-table session
header, list-running, spend, git-aware move, the mutation guard). CHANGELOG kept up, but
README/ARCHITECTURE carry several now-FALSE accuracy claims (the worst: a
"zero-dependency / `ocman.py` standalone script" install story that no longer exists),
plus coverage gaps (undocumented flags, env vars, and config keys). Per the
documentation lens, inaccuracies are the highest harm and are fixed first; gaps second.
Honest, concise docs over impressive ones.

## Project conventions discovered (Step 0)

- Guiding principles: AGENTS.md + the universal fallback (intuitive/self-documenting,
  general-case/configurable, KISS, honest docs). Prose rule: NO em/en dashes in authored
  Markdown (the `—` "not available" table glyph is the only sanctioned exception).
- Pending-plans location/format: `.agents/plans/pending/`, `YYYYMMDD-HHMM-NN-<slug>.md`;
  Status lifecycle draft -> to-review -> reviewed -> approved -> executed; terminal dirs
  `executed/`, `superseded/`, `not-executed/`.
- Contributor/spec-sync contract: AGENTS.md (path-scoped commits, never push, real test
  output). Docs-only change here: no code/tests touched, so no test run required beyond a
  link/consistency check.
- Stack: single-package Python CLI (`ocman/cli.py`) + Textual TUI; console script
  `ocman = "ocman:main"`; deps textual/rich/vistab/pysqlite3-binary.

## Findings

Severity = impact if left alone; Remediation Risk = the Fix-Bar gate. Persona: novice
(new user following the README) or engineer/operator (maintainer using the docs).
All doc line numbers are from the audit; the executing agent MUST re-locate them (docs
shift) rather than trust the exact numbers.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| D-01 | High | Low | novice | Install/accuracy | README claims "Zero external dependencies; requires only Python 3.10+ and the `opencode` CLI." False: `vistab` is hard-imported and textual/rich/vistab/pysqlite3-binary are CORE deps; the CLI cannot run without vistab. | README.md ~126 vs `ocman/cli.py:90` (`import vistab`), `pyproject.toml:15-19` |
| D-02 | High | Low | novice | Install/accuracy | "Standalone Script (Zero-Dependency CLI Mode)" tells the user to `chmod +x ocman.py && ./ocman.py help`. There is NO `ocman.py`; the module is `ocman/cli.py` with console script `ocman`. Following this fails immediately. | README.md ~145-150 vs repo (no `ocman.py`), `pyproject.toml` (`ocman = "ocman:main"`) |
| D-03 | High | Low | engineer | Accuracy | README "Recovery options" table says it applies to `recover` AND `compact` and lists `--show-secrets`, `--expunge-secrets`, `-y/--yes`, `--force`. These exist ONLY on `compact` (verified: `session recover --show-secrets` errors). | README.md ~340,360-362 vs `_add_recovery_opts` `cli.py:6019` (lacks them) + compact adds at `cli.py:6186-6193` |
| D-04 | High | Low | engineer | Accuracy | ARCHITECTURE says the CLI is "standard library only for the CLI path" and repeatedly names `ocman.py`. Both false: `vistab` hard-imported; module is `ocman/cli.py`. Self-contradicts the same doc's vistab-table description. | ARCHITECTURE.md ~16,64,152,250-251 vs `cli.py:90`, `pyproject.toml` |
| D-05 | Medium | Low | engineer | Config/accuracy | README config template shows `filter_secret_scan = conservative` (unquoted -> invalid TOML; generator quotes strings) and `default_out_dir = "./opencode-recovery"` (real default is `opencode-recovery`, no `./`). | README.md ~469,438 vs `cli.py:394-395`, `cli.py:310` |
| D-06 | Medium | Low | engineer | Config coverage | 4 config keys missing from the README config section: `chunk_max_interactions`, `chunk_max_lines`, `reclaim_tmp_min_age_hours`, `reclaim_parts_retention_days`. | README.md ~430-470 vs `DEFAULT_CONFIG` `cli.py:321-324` + template `cli.py:292-304` |
| D-07 | Medium | Low | novice/engineer | Env coverage | No consolidated "Environment variables" section. `OPENCODE_DB`, `XDG_DATA_HOME`, `OPENCODE_CONFIG_DIR` (honored by doctor/reclaim discovery) are undocumented in README; `NO_COLOR`/`FORCE_COLOR` only mentioned in passing. | README (no env section) vs `cli.py:12568,12580,12586,137,139` |
| D-08 | Medium | Low | engineer | CLI coverage | Undocumented flags in README command tables: `reclaim --tmp-min-age-hours` + `--force`; `session show -D/--details`; `session import --dry-run`; `-y/--yes` on session/project delete; `--json`/`--limit` on session/project list. | README.md ~330-337,368-369,411 vs `cli.py:6150-6154,6161,6201,6216,6238-6240,6246,6407-6411` |
| D-09 | Medium | Low | engineer | Accuracy | ARCHITECTURE top-level verb list omits shipped verbs `spend`, `running`, `doctor`, `reclaim`. | ARCHITECTURE.md ~20-21 vs `cli.py:6354,6382,6389,6392` |
| D-10 | Low | Low | novice | Accuracy | README says `ocman help all` "prints the complete command reference (every group, action, and option)", but built-in `help all` output contains no `doctor`/`reclaim`/`spend`/`running`. Either the claim is wrong or `help all` is stale. | README.md ~174,420 vs live `ocman help all` |
| D-11 | Low | Low | engineer | CHANGELOG | reclaim entry omits `--tmp-min-age-hours` and the non-Linux `--force`; batch-delete has no discrete entry (only referenced inside the guard entry). | CHANGELOG.md ~17-28,47 |

## Proposed changes (ordered, validatable)

Ordered accuracy-first (highest harm), then coverage, then polish.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | D-01, D-02, D-04 | Remove the "zero external dependencies" and "standalone `ocman.py`" install story. State the real install: `pip install .` (or the console script `ocman`), Python >= 3.10, and the actual deps (textual, rich, vistab, pysqlite3-binary on Linux); dev extras optional. Fix ARCHITECTURE's `ocman.py` -> `ocman/cli.py` and drop "standard library only for the CLI path" (note it uses vistab). | README.md, ARCHITECTURE.md | Low | grep README/ARCHITECTURE for `ocman.py` and "zero"/"standard library only" -> none remain; deps listed match `pyproject.toml`; `ls ocman.py` no longer referenced |
| 2 | D-03 | In the "Recovery options" table, split which flags apply to `compact` only vs both. Move `--show-secrets`/`--expunge-secrets`/`--allow-secrets`/`--force` (size cap)/`-y` under `compact`; keep the recovery-tuning flags (`-o/-d/-mi/-ml/--chunk/-t/--all-roles/-i*/-o*/-k`) as shared. | README.md | Low | `session recover --help` and `session compact --help` agree with the table; documented recover flags all accepted, documented compact-only flags rejected by recover |
| 3 | D-05 | Fix the README config template: quote `filter_secret_scan = "conservative"`; change `default_out_dir` to `"opencode-recovery"`. | README.md | Low | values match `save_ocman_config` output; a copied template parses as valid TOML |
| 4 | D-06 | Add the 4 missing config keys (`chunk_max_interactions`, `chunk_max_lines`, `reclaim_tmp_min_age_hours`, `reclaim_parts_retention_days`) with their real defaults + one-line descriptions to the README config section, matching `DEFAULT_CONFIG_TEMPLATE` comments. | README.md | Low | every `DEFAULT_CONFIG` key appears in the README config section; defaults match `cli.py` |
| 5 | D-07 | Add a concise "Environment variables" subsection: `NO_COLOR`, `FORCE_COLOR`, `OPENCODE_DB`, `XDG_DATA_HOME`, `OPENCODE_CONFIG_DIR`, `OCMAN_BENCHMARK`, with one line each on effect. | README.md | Low | each honored env var (grep `os.environ.get` / `getenv` in cli.py) is listed |
| 6 | D-08 | Add the missing flags to the README command tables (reclaim `--tmp-min-age-hours`/`--force`; `session show -D`; `session import --dry-run`; delete `-y`; list `--json`/`--limit`). | README.md | Low | each documented flag exists in the matching `--help` |
| 7 | D-09 | Update the ARCHITECTURE top-level verb enumeration to include `spend`, `running`, `doctor`, `reclaim`. | ARCHITECTURE.md | Low | list matches the top-level `new_sub` set in cli.py |
| 8 | D-10 | Resolve the `help all` claim: EITHER soften the README wording (e.g. "curated overview of the main commands") OR (preferred, cross-ref self-documentation lens) note that `help all` is curated and `ocman <cmd> -h` is the exhaustive per-command reference. Do NOT claim exhaustiveness the built-in help does not deliver. | README.md | Low | README wording matches what `ocman help all` actually prints |
| 9 | D-11 | Add `--tmp-min-age-hours`/non-Linux `--force` to the CHANGELOG reclaim entry; add a short batch-delete line (or fold explicitly into the delete description). | CHANGELOG.md | Low | CHANGELOG reclaim entry lists all reclaim flags; batch-delete behavior noted |

## Deferred / out of scope (with reason)

None deferred. Every finding is a low-Remediation-Risk documentation correction; all are
proposed above. (No finding clears the Medium-High bar that would justify deferral.)

## Scope check

- Over-scope: none. This plan is confined to correcting and completing existing docs; it does
  NOT add new doc files, tutorials, or a docs site (that would be gold-plating).
- Under-scope: D-10 hints at an in-PRODUCT gap (built-in `help all` omits new commands).
  That is a self-documentation concern, not a written-doc fix; this plan only aligns the
  README wording and cross-references the self-documentation lens rather than changing
  the help generator. If the maintainer wants `help all` to actually list the new
  commands, that is a separate assess/self-documentation IPD.

## Required tests / validation

Docs-only; no application code/tests change, so no pytest run is required. Validate by:
- `grep -Rn "ocman.py" README.md ARCHITECTURE.md` returns nothing (D-02/D-04).
- `grep -RniE "zero (external )?dependenc|standard library only" README.md ARCHITECTURE.md`
  returns nothing (D-01/D-04).
- For every flag/command added or moved: confirm against
  `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/python -c "import ocman; ocman.main()" <cmd> --help`.
- Every `DEFAULT_CONFIG` key appears in the README config section with the matching default.
- Every env var ocman reads is listed in the new env section.
- No em/en dashes introduced in authored prose (the CHANGELOG attribution line `—` is the
  sole pre-existing sanctioned exception).

## Spec / documentation sync

This plan IS the documentation sync. No user-visible behavior changes; it only makes the
docs match current behavior. No code/spec files change.

## Open questions

- OQ-1 (D-10): prefer softening the README `help all` claim (this plan), or is a
  follow-up wanted to make the built-in `help all` actually list every command? Leaning:
  soften now, spin a self-documentation IPD if desired. Non-blocking.
- OQ-2: is there a release imminent that should turn `[Unreleased]` into a version
  heading? If so, the CHANGELOG edits (Step 9) should land under that version. Assumed
  NO for now (leave `[Unreleased]`).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution and
is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it; that sets `Status: reviewed`).
2. On approval, set `Status: approved` (+ `Approval:` line), apply the ordered doc changes,
   run the validation greps/help-checks above, and confirm no em-dashes were introduced.
3. Then set `Status: executed` and `git mv` this IPD from `pending/` to `executed/`
   (verify no pending/executed duplicate with `git ls-tree HEAD`). Commit path-scoped;
   never push without explicit direction.
