# IPD: Assess documentation - align README/ARCHITECTURE with actual behavior

- Date: 2026-07-05
- Concern: documentation
- Scope: whole project's written docs (`README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `AGENTS.md`); verified against `ocman.py`, `ocman_tui/`, `pyproject.toml`. Excludes `.agents/workflows/` and `workflow-artifacts/` per review-scope rules.
- Status: PENDING (awaiting human approval; not executed)
- Author: its_direct/pt3-claude-opus-4.8-1m-us (via /assess docs)

## Goal

Make `ocman`'s user-facing documentation accurate to what the software does **today**, per the documentation lens's first principle (accuracy before completeness; honest over impressive). The most consequential defect is a config-template line in the README that documents a **key that does not exist** with a **wrong default value** — a user copying it gets a silently dead setting. Secondary gaps: the Argument Reference table omits ~14 real flags, and ARCHITECTURE's "recognized commands" statement is incomplete. Fixing these lets a novice go from README to correct config and correct command discovery without reading the source.

## Project conventions discovered (Step 0)

- Guiding principles: no `GUIDING_PRINCIPLES.md`; principles are stated in `ARCHITECTURE.md` ("Design principles": intuitive/self-documenting, configurable-over-hardcoded, KISS, **honest documentation**). Universal fallback otherwise.
- Pending-plans location/format used: `.agents/plans/pending/` with `YYYYMMDD-<slug>.md` naming (existing repo convention); terminal dir `.agents/plans/executed/`.
- Contributor/spec-sync contract: `AGENTS.md` (points to `.agents/workflows/`); no separate CONTRIBUTING. `CHANGELOG.md` is the change log of record and has an active `[Unreleased]` section.
- Stack / relevant context: single-file stdlib CLI `ocman.py` (~8695 lines) + Textual TUI package `ocman_tui/`; packaged as `ocman` (console script `ocman = "ocman:main"`), Python >=3.10, `__version__ = "1.0.4"` with unreleased changes pending.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for whether to act now. Persona = which reviewer perspective surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| D1 | High | Low | Novice / operator | README config template | README documents config key `default_model = "uri/its_direct/pt1-qwen3-32b-us"`, but the real key is `default_compaction_model` and its real default is `""`. A user copying the template sets a **non-existent key** (silently ignored) and believes a default model is configured when it is not. Both name and value are wrong. | `README.md:227` vs `ocman.py:264` (`"default_compaction_model": ""`), template `ocman.py:226`, `--create-config` prompt `ocman.py:7290`, TUI `ocman_tui/app.py:1597,1628` |
| D2 | Medium | Low | Operator / novice | README Argument Reference | The Argument Reference table is incomplete: it omits real, user-facing flags `-lp/--list-projects`, `-ls/--list-sessions`, `-P/--project`, `-A/--all-sessions`, `-D/--details`, `-H/--head`, `-T/--tail`, `-V/--version`, and the recovery input/output flags `-ir/--input-restart`, `-it/--input-transcript`, `-oc/--output-compact`, plus `--show-compaction-prompt` and `--show-logs`. All exist in argparse. A reader relying on the table cannot discover session-browsing or version flags. | `README.md:162-205`; defined at `ocman.py:4213,4230,4219,4236,4242,4248,4256,4361,4168,4180,4192,4341,4395` |
| D3 | Low | Low | Novice | ARCHITECTURE recognized commands | ARCHITECTURE.md states "The positional command accepts `info`, `help`, `ui`, and `gui`." True for the argparse positional, but incomplete as a statement of recognized commands: `preprocess_argv` also rewrites `disk`/`du`, `delete project [name]`, `list projects`, `list sessions [in [project] X]`, and `show logs`. Reader may think only 4 commands exist. | `ARCHITECTURE.md:20`; `preprocess_argv` at `ocman.py:3948-4033` (esp. 3965,3985,3991,3999,4003,4008) |
| D4 | Low | Low | Operator | README preprocessing list | README's "Command Preprocessing" list documents `list projects`, `list sessions`, `list sessions in [project]`, `show logs` but omits the `disk`/`du` alias and `delete project` natural-language forms that also exist. | `README.md:121-126` vs `ocman.py:3965,3991` |
| D5 | Low | Low | Novice | ARCHITECTURE package layout | ARCHITECTURE lists `ocman_tui/` with `app.py`, `core.py`, `widgets/` but omits the `css/` subdirectory that also ships. Minor completeness gap. | `ARCHITECTURE.md:21-23` vs `ocman_tui/css/` on disk |
| D6 | Low | Low | Maintainer | Stale identifier note | The TUI app class is `OrsessionApp` (a stale pre-rename name); ARCHITECTURE.md:22 states this accurately, so the doc is not wrong. Flag only so the doc reference is not "corrected" to a name that does not exist. No doc change required beyond leaving it as-is (or an optional one-word parenthetical). Renaming the class is a **code** change, out of scope for a docs assessment. | `ARCHITECTURE.md:22`; class at `ocman_tui/app.py:762` |

Verified-accurate claims (no action): `.ocbox` `export_version: 2.0` (`ocman.py:5728`); Python 3.10+ (`pyproject.toml:11`); default retention days 5 (`ocman.py:266`, `--days` default 4297); `ocman disk`/`--by-project` (`ocman.py:3991,4374`); TUI dir `ocman_tui/`, entry point `ocman = ocman:main` (`pyproject.toml`); `__version__` 1.0.4 with `[Unreleased]` present; `info`/`disk` per-project session-diff-only caveat matches code.

## Proposed changes (ordered, validatable)

Fix by default; each item is safe, well-scoped, and verifiable. Doc-only edits (no code/behavior change) unless noted.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | D1 | In the README "Default Layout Template" TOML block, rename `default_model` → `default_compaction_model` and set its value/comment to the real default `""` (empty = prompt/select at compaction time). Match the wording of the in-code template comment (`ocman.py:224-226`). | `README.md:226-227` | Low (usability) | Diff the README template keys against `DEFAULT_CONFIG` (`ocman.py:260-272`): every documented key must exist and match its default. `--create-config` output should match the README template. |
| 2 | D2 | Add the missing rows to the Argument Reference table: `-lp/--list-projects`, `-ls/--list-sessions`, `-A/--all-sessions`, `-P/--project`, `-D/--details`, `-H/--head N`, `-T/--tail N`, `-V/--version`, `-ir/--input-restart`, `-it/--input-transcript`, `-oc/--output-compact`, `--show-compaction-prompt`, `--show-logs`. Keep descriptions one line each, matching argparse help text. Do NOT document the SUPPRESSED/deprecated `-m/--use-model`. | `README.md:162-205` | Low | Cross-check the table against every non-suppressed `add_argument` in `ocman.py:4076-4483`; each should appear exactly once. |
| 3 | D3, D4 | ARCHITECTURE.md:20: after listing the argparse positionals, add one sentence noting `preprocess_argv` also rewrites natural-language commands (`disk`/`du`, `delete project`, `list projects/sessions`, `show logs`) to flags. README:121-126: add `ocman disk` / `du` and `delete project` to the preprocessing bullet list. | `ARCHITECTURE.md:20`, `README.md:121-126` | Low | The documented natural-language commands should each map to a branch in `preprocess_argv` (`ocman.py:3948-4033`). |
| 4 | D5 | ARCHITECTURE.md:21-23: add `css/` to the `ocman_tui/` layout description (one clause). | `ARCHITECTURE.md:21-23` | Low | `ocman_tui/css/` exists on disk. |
| 5 | D1-D4 | Add a `### Documentation` entry under CHANGELOG `[Unreleased]` recording the README config-key correction and argument-reference completion (they are user-visible doc fixes). | `CHANGELOG.md:3+` | Low | Entry present under `[Unreleased]`. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| D6 | Medium-High | Complexity / functionality | Renaming `OrsessionApp`/`orsession` identifiers is a **code** change touching the public TUI export (`ocman_tui/__init__.py`), event-handler name `on_orsession_app_refresh_sidebar`, temp-dir prefix, and tests — outside a docs assessment and risks behavior/compat regressions. The doc is already accurate as written. | Optional future `/assess architecture` or a dedicated rename IPD if the stale name is deemed worth removing. |

## Scope check

- Over-scope (untraceable to a need; propose removal/deferral): none proposed. Explicitly NOT rewriting docs for style, NOT expanding prose, NOT adding new sections — accuracy fixes only (documentation lens: concise+accurate beats long+aspirational).
- Under-scope (needed capability missing; propose adding): the Argument Reference omission (D2) is the main under-documentation; Step 2 adds it. No other missing-doc capability identified — install/configure/run/troubleshoot/backup/restore/limitations are all present and accurate.

## Required tests / validation

Docs-only; no automated test gates. Validation is a manual consistency check the executor must perform and record:

1. **Config parity:** every key in the README template block exists in `DEFAULT_CONFIG` (`ocman.py:260-272`) with a matching default; run `ocman --create-config` to a temp path and confirm the generated file's keys match the README block. (No new key introduced — no config-schema test change needed.)
2. **Flag parity:** every row in the Argument Reference table corresponds to a non-suppressed `add_argument`, and no non-suppressed user-facing flag is missing.
3. **Command parity:** each natural-language command named in the docs maps to a `preprocess_argv` branch.
4. **Regression:** `PYTHONPATH=. pytest` still passes (expected unchanged: 126 passed, 2 skipped) — confirms the doc edits touched no code. If a config-schema test enumerates documented keys, ensure it still passes.

## Spec / documentation sync

This IPD **is** the documentation sync. It changes no user-visible product behavior — only corrects docs to match existing behavior — so a CHANGELOG `### Documentation` note (Step 5) is the only cross-artifact update required.

## Open questions

1. **README config value for `default_compaction_model`:** show it as empty (`default_compaction_model = ""`) to mirror the real default, or show a commented example value so users see the expected format? Assumption (recommended): show `""` as the real default with the in-code comment ("empty = selected/prompted at compaction time"); do not ship a real model string, since that was part of the original defect.
2. **Argument Reference table size (D2):** add all 13 missing flags, or only the high-value session-browsing + `--version` set and leave the low-level `-ir/-it/-oc` recovery I/O flags to `--help`? Assumption (recommended): add all of them for a single source of truth; they are all real and cheap to list.
3. **D6 stale name:** leave `OrsessionApp` mention exactly as-is (recommended), or add a one-word "(legacy name)" parenthetical? No functional impact either way.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes, run the validation, and add the CHANGELOG note.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/` per the project's lifecycle convention.
