# IPD: save_ocman_config must preserve unmanaged config keys (FU-01 corrective)

- Date: 2026-07-19
- Concern: bugs (config data loss)
- Scope: `save_ocman_config` in `ocman/cli.py`; a regression test. No behavior change for
  callers that pass a full config.
- Status: executed
- Approval: approved by maintainer 2026-07-19 (proceed directive)
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-19 created (its_direct/pt3-claude-opus-4.8): corrective IPD for FU-01, the
  config-key-reset bug found while executing the TUI-parity Phase 4.
- 2026-07-19 executed (its_direct/pt3-claude-opus-4.8): `save_ocman_config` now merges over
  the existing config (via `load_ocman_config`) instead of `DEFAULT_CONFIG`; added
  `test_save_ocman_config_preserves_unmanaged_keys` (subset save preserves unmanaged keys;
  reset still resets). Full suite: 403 passed, 2 skipped.

## Goal

Stop silently discarding a user's configured values for keys that a given `save` caller
does not pass. Today `save_ocman_config(config_dict)` merges `config_dict` over
`DEFAULT_CONFIG`, so any key not in `config_dict` is written back at its DEFAULT, not its
current value. The TUI config form only manages a subset of keys, so saving it (which also
happens automatically on tab switch and on unmount) RESETS `chunk_max_interactions`,
`chunk_max_lines`, `reclaim_tmp_min_age_hours`, `reclaim_parts_retention_days`,
`filter_max_bytes`, `filter_secret_scan`, `copy_restart_to_project_prompts`, and
`history_max_runs` to their defaults. A user who tuned any of those via `ocman.toml` loses
their change the next time the TUI saves.

## Project conventions discovered (Step 0)

- Guiding principles: AGENTS.md + universal fallback. No em/en dashes in authored text.
- Plans: `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`.
- Contract: path-scoped commits, never push, paste REAL pytest output.
- Stack: `ocman/cli.py` config layer; `load_ocman_config()` reads the toml over
  `DEFAULT_CONFIG`; `save_ocman_config()` renders `DEFAULT_CONFIG_TEMPLATE` from a merged
  dict. `PATH_KEYS` get `~`-collapsed on save and `expanduser`d on load.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| FU-01 | Medium | Low | PU | config/data-loss | `save_ocman_config` merges a partial `config_dict` over `DEFAULT_CONFIG`, so unmanaged keys are reset to defaults on every partial save (notably every TUI config save). | `ocman/cli.py:385-386` (`merged = dict(DEFAULT_CONFIG); merged.update(config_dict)`); TUI subset at `ocman_tui/app.py:2234-2244` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | FU-01 | In `save_ocman_config`, build the merge base from the EXISTING on-disk config, not from `DEFAULT_CONFIG`: `base = load_ocman_config(config_path)` (which itself falls back to `DEFAULT_CONFIG` for any key absent from the file), then `base.update(config_dict)` and render. Keys the caller does not pass keep their CURRENT value; keys never set anywhere still fall back to defaults (template always fully populated). Update the misleading comment. | `ocman/cli.py` | Low | New test: write a config with a non-default `chunk_max_lines`; call `save_ocman_config` with a subset that omits it; reload and assert `chunk_max_lines` is preserved. Existing config tests still pass. |

## Deferred / out of scope

- Changing what keys the TUI form manages, or adding form fields for chunk/reclaim/filter:
  not needed once the save layer preserves them. Out of scope.

## Scope check

- Over-scope: none. A one-function change plus a test.
- Under-scope: none. Fixing at the `save_ocman_config` layer covers ALL partial-save callers
  (the TUI form, and any future one), which is the correct general-case fix.

## Anti-regression / invariants

- Full-config callers (`reset_tui_config` and `cli_create_config` pass a complete dict; the
  reset path passes `DEFAULT_CONFIG`) are unaffected: merging a full dict over the existing
  config still yields exactly that dict's values, so "reset to defaults" still resets.
- The rendered template stays fully populated (every `DEFAULT_CONFIG_TEMPLATE` placeholder
  present), because `load_ocman_config` returns every key.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE THE ACTUAL runner output.
- New regression test (preserve-unmanaged-key) + a reset-still-resets assertion.

## Spec / documentation sync

None (internal behavior fix; no user-facing surface changes). A one-line CHANGELOG "Fixed"
entry.

## Open questions

None.

## Approval and execution gate

This IPD is a proposal and is NOT auto-executed. Execution contract:

- Open questions: none.
- Execution checklist (MUST): before coding, create a TodoWrite checklist tracking: the
  `save_ocman_config` change, the regression test, the reset-still-resets test, the full
  suite run with pasted output, the CHANGELOG "Fixed" line, the path-scoped commit, and the
  Status-executed + `git mv` to `executed/`.
- Scope fence: ONLY `save_ocman_config` and its test. Do NOT change `load_ocman_config`, the
  template, or the TUI form. No new runtime dependencies.
- Honesty rule (hard MUST): paste the ACTUAL `pytest -q` output; never claim a pass you did
  not run.
- Commits: path-scoped, NEVER push, NEVER tag.
- Lifecycle: on completion set `Status: executed` and `git mv` this IPD to
  `.agents/plans/executed/` (verify no pending/executed duplicate).

Next: human approval sets `Status: approved`; then execute per the above.
