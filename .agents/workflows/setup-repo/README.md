# setup-repo

Guided, idempotent, drift-aware repo setup AND conformance check: detect state, classify
each area (conformant/partial/missing/outdated), then ask-before-each-change to install
tools, add secret scanning, establish the plan/IPD lifecycle, and add hygiene files. Run
`/setup-repo`, or from any agent: "read and execute
`.agents/workflows/setup-repo/setup-repo.md`". Safe to re-run; stages changes.

## Subdirectories

- `tools/` - deterministic helpers the wizard orchestrates: `setup_tools.py`
  (detect/install dev tools) and `normalize_plan_names.py` (check/normalize plan
  filenames).
