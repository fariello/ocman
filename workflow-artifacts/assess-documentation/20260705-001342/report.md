# Assessment run report - documentation (whole project)

- Date / run ID: 20260705-001342
- Concern: documentation
- Scope: whole project's written docs (README.md, ARCHITECTURE.md, CHANGELOG.md, AGENTS.md), verified against ocman.py, ocman_tui/, pyproject.toml. Excludes .agents/workflows/ and workflow-artifacts/.
- IPD written: `.agents/plans/pending/20260705-assess-documentation.md`
- Verdict: **needs work** for documentation (one High-severity inaccuracy; the docs are otherwise strong and honest)

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| D1 | High | Low | Novice / operator | README config template documents key `default_model = "uri/..."`; real key is `default_compaction_model` with default `""`. Copying the template sets a dead key. (README:227 vs ocman.py:264) |
| D2 | Medium | Low | Operator / novice | Argument Reference table omits ~13 real flags (`-lp/-ls/-P/-A/-D/-H/-T`, `-V/--version`, `-ir/-it/-oc`, `--show-compaction-prompt`, `--show-logs`). (README:162-205) |
| D3 | Low | Low | Novice | ARCHITECTURE "positional command accepts info/help/ui/gui" is incomplete vs preprocess_argv's natural-language commands. (ARCHITECTURE.md:20) |
| D4 | Low | Low | Operator | README preprocessing list omits `disk`/`du` and `delete project`. (README:121-126) |
| D5 | Low | Low | Novice | ARCHITECTURE ocman_tui/ layout omits the shipped `css/` subdir. (ARCHITECTURE.md:21-23) |
| D6 | Low | Low | Maintainer | Stale `OrsessionApp` name; ARCHITECTURE.md:22 states it accurately, so no doc change needed (code rename deferred). |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

- Step 1 (D1): README template `default_model` → `default_compaction_model`, value `""`, matching in-code comment.
- Step 2 (D2): Add the 13 missing rows to the Argument Reference table (one line each; skip suppressed `-m`).
- Step 3 (D3,D4): ARCHITECTURE + README note the `preprocess_argv` natural-language commands (`disk`/`du`, `delete project`, `list ...`, `show logs`).
- Step 4 (D5): Add `css/` to the ARCHITECTURE layout description.
- Step 5: CHANGELOG `[Unreleased]` `### Documentation` note.

All doc-only, Low Remediation Risk. Validation is manual parity checks (config keys vs DEFAULT_CONFIG, table vs add_argument, commands vs preprocess_argv) + `PYTHONPATH=. pytest` unchanged (126 passed, 2 skipped).

## Deferred (with reason)

- D6 (stale `Orsession`/`orsession` identifier removal): Remediation Risk Medium-High on complexity/functionality — it is a code refactor touching the public TUI export, an event-handler name, temp-dir prefix, and tests, outside a docs assessment; the doc reference is already accurate. (Effort is not the reason.)

## Out-of-repo / organizational notes (if any)

- None.

## Next step

Review the IPD (optionally run the `plan-review` workflow on it) and approve before execution. This workflow does not execute the plan.
