# assess

Assess ONE concern deeply and propose an Implementation Plan Document (IPD). Run
`/assess <concern> [scope]` (e.g. `/assess security`, `/assess performance src/`), or from
any agent: "read and execute `.agents/workflows/assess/assess.md`" with the concern. Bare
`/assess` lists the available concerns. See `.agents/workflows/index.md` for the full
catalog.

## Subdirectories

- `lenses/` - per-concern lens files (security, performance, accessibility, ...) that
  focus the shared assess harness on one concern.
- `templates/` - the IPD and run-report templates the workflow emits.
- `tools/` - deterministic helpers used during an assessment (e.g. `scan_secrets.py`).
- `references/` - supporting reference material for specific lenses.
