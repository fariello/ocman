# Decisions and assumptions - assess functionality (TUI parity)

## Concern / scope

- Concern: functionality completeness, specifically CLI<->TUI feature parity, with a
  ui-ux lens for how missing features should be surfaced in the Textual UI.
- Scope assessed: the `ocman_tui/` package (app, widgets, modals) measured against the
  current CLI feature set in `ocman/cli.py`. The CLI is the reference and is NOT in scope
  to change.

## Project conventions discovered

- Plans in `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`.
- No em/en dashes in authored text (the em-dash "not available" table glyph is the
  sanctioned exception).
- Path-scoped commits, never push, paste REAL pytest output (AGENTS.md).
- The TUI imports core logic from `ocman/cli.py` via `ocman_tui/core.py`; long ops use a
  worker-thread pattern and a `_shutting_down` guard.

## Key decisions

- Treated this primarily as a functionality/parity concern (features present in the CLI
  but absent in the TUI), applying the functionality lens, with ui-ux considerations for
  placement (tabs vs. cards) and safety (confirm modals, default-on extracts).
- Chose a PHASED plan ordered safety-first: Phase 1 closes the delete-safety gap (the TUI
  is currently more destructive than the CLI), then high-value read-only views
  (doctor/spend/running), then bulk/large-session handling, then breadth.
- Framed each feature as Required / Expected / Nice-to-have. Required + Expected are
  proposed by default; two Nice-to-haves (filter, advanced/remote move + db rebase) are
  deferred on the Complexity axis to avoid gold-plating a rarely-needed TUI path.

## What was intentionally NOT proposed (and why)

- The reclaim snapshot-force path in the TUI: Remediation Risk Med-High on the
  Safety/Complexity axis (can break OpenCode undo/revert). Proposed to expose only the
  safe reclaim modes now, deferring or extra-gating the snapshot path.
- `filter` and advanced/remote/git-aware move and `db rebase` in the TUI: Complexity axis,
  low TUI demand. Left CLI-only pending explicit stakeholder interest (OQ-3/OQ-4).

## Open questions for the user

- OQ-1: implement `history clear` in the TUI or just remove the stub button?
- OQ-2: expose the reclaim snapshot-force path in the TUI, or keep it CLI-only?
- OQ-3: does the TUI need remote/git-aware move, or is local metadata move enough?
- OQ-4: is `filter` wanted in the TUI?
- OQ-5 (release-critical): must ALL phases land before release, or is a subset the gate
  (e.g. Phases 1-3)? This decides the release cut line.
- OQ-6: new top-level tabs per area vs. folding into the Database Admin tab.

## Method note

The gap inventory was produced by a thorough read of `ocman_tui/` (app.py, widgets,
core.py) cross-referenced against `build_parser()` and the feature functions in
`ocman/cli.py`. Findings are cited to file:line. No files were modified during the
assessment.
