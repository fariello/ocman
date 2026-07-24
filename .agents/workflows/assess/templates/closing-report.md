# Closing report: artifacts and next steps (shared convention)

Every workflow that PRODUCES a durable artifact (an IPD, a spec, a post-mortem plus action
IPDs, a run record) MUST end its run by presenting this closing report to the user, so the
user always knows exactly what was written (or that nothing was) and what to do next. This is
the single canonical definition (GUIDING_PRINCIPLES P8, P2 honest reporting, P3
self-documenting); the producing workflows reference it rather than restating it. It lives
here as the anchor producer's shared template; other producers reference it by this path
(`.agents/workflows/assess/templates/closing-report.md`).

The report has two required parts and one branch:

- **Created** - list every artifact the run wrote, one per line, with its repo-relative path
  (the IPD(s), the spec, the post-mortem, the run record). If a producer also writes a run
  record, ALWAYS include a `Run record:` line: the path when written, or
  `Run record: not written (<local-only | skipped | none>)` when not, so it is never silently
  absent.
- **If nothing was created** - state that plainly AND why, naming the reason: assessed and
  found nothing warranting a plan; the user declined the write; or the run was aborted (say at
  which point). Never end a producing run leaving the user unsure whether an artifact exists.
- **Next steps** - the concrete next actions with exact commands (review the artifact,
  `/plan-review <path>`, approve, then execute; or `/advise ...` where relevant). Never just
  "done".

## Worked example: artifact(s) created

```
Created:
  IPD:        .agents/plans/pending/20260722-1430-01-<slug>.md
  Run record: workflow-artifacts/assess-security/20260722-143012/

Next steps:
  1. Review the IPD (optionally run /plan-review on it).
  2. Approve it (set Status: approved), then execute; this workflow does not execute the plan.
```

## Worked example: nothing created

```
Created: none.
Reason:  assessed <concern> across <scope> and found nothing that warrants a plan; the
         current state is adequate. A run record was still written for the audit trail.
  Run record: workflow-artifacts/assess-security/20260722-143012/

Next steps:
  - No action required. Re-run this assessment after relevant changes if you want a fresh check.
```
