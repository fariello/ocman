# Assessment - functionality (CLI<->TUI parity)

Verdict: needs work for functionality parity. The TUI is a solid interactive front end
for a subset of ocman, but it lags the CLI significantly: most of the recent feature wave
is unreachable from the UI, and one path (delete) is actually MORE dangerous in the TUI
than in the CLI because it lacks the new extract-on-delete safety default.

IPD written: .agents/plans/pending/20260718-1648-01-assess-functionality-tui-parity.md

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| T-01 | High | Medium | PU/QA | extract-on-delete not in TUI; TUI deletes with force=True/confirm=False and writes no recovery files (UI more destructive than CLI). |
| T-02 | High | Medium | STK/PU | doctor (storage checkup) absent from the TUI. |
| T-03 | High | Med-High | STK/PU | reclaim (disk reclamation) absent from the TUI. |
| T-04 | Medium | Medium | PU | spend / spend --historical absent. |
| T-05 | Medium | Medium | PU/STK | list running (running + insecure OpenCode instances) absent. |
| T-06 | Medium | Medium | PU | batch / multi-session actions absent (single-select sidebar). |
| T-14 | Low | Low | NOV | history clear is a dishonest stub ("Planned" button -> FutureTodoModal). |

## Proposed plan (summary)

Phased parity plan (each phase independently executable, testable, committable):
- Phase 1 - safety gap: wire extract-on-delete into TUI deletes; fix/remove the
  history-clear stub.
- Phase 2 - storage checkup & reclaim: read-only doctor view + guarded reclaim actions.
- Phase 3 - reporting: spend (per-project + historical) and running views (read-only).
- Phase 4 - bulk + large sessions: multi-select batch delete/export, db clean
  --older-than + scope + extracts, --chunk in recovery.
- Phase 5 - breadth: project export/import, session/local move, backup clean, content
  search.
- Not proposed (gold-plating guard): filter and advanced/remote move/rebase stay CLI-only
  pending stakeholder demand.

## Deferred (with reason)

- reclaim snapshot-force path (part of T-03): Remediation Risk Med-High on Safety/
  Complexity (can break OpenCode undo/revert). Expose safe reclaim modes now; defer or
  extra-gate the snapshot path.
- filter (T-13), advanced/remote move + db rebase (parts of T-10/T-15): Complexity axis;
  low TUI demand.

Next step: review the IPD (optionally run plan-review), answer the open questions
(especially the release cut line OQ-5 and OQ-1/OQ-2), and approve before execution. This
workflow does not execute the plan.
