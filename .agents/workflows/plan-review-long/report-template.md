# Plan Review Final Report Template

Use this exact order. Cite evidence as `path:line`.

```markdown
## Plan Review - <plan name(s)>

Verdict: <APPROVE | APPROVE WITH REVISIONS APPLIED | REVIEWED - OPEN QUESTIONS | REJECT - NEEDS REPLAN>

### Review scope

ELIGIBLE:
- <plan file>

NOT REVIEWED:
- <plan file>: <reason>   # skipped CANDIDATES only; `- (none)` if none were skipped. Never list a plan that was never a candidate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | <BLOCKER|HIGH|MEDIUM|LOW> | <IN-SCOPE|OVER-SCOPE|UNDER-SCOPE> | <rubric/project ref> | <path:line> | <finding> | C:<rating>; U:<rating>; S:<rating>; F:<rating>; Overall:<rating> | <FIXED|DEFERRED|OPEN|REPLAN> | <resolution or next step> |

### Edits applied

- `<plan file>` - `<section>`: <concise edit>

### Deferred and open

- `<finding ID>` - `<DEFERRED | OPEN>`:
  - Reason: <reason>
  - Remediation Risk: <Medium-High | High>
  - Axis: <complexity | usability | security | functionality>
  - Required decision or evidence: <needed>
  - Consequence if unresolved: <impact>

### Commit result

- Pre-review snapshot: <hash | skipped because unchanged | not applicable | failed with reason>
- Hardened result: <hash | not applicable | failed with reason>
- Push: not performed

### Plans reviewed and not reviewed

REVIEWED:
- `<plan file>`: <GO | GO - PENDING HUMAN APPROVAL | NO-GO> - <one-line reason>.
  Verdict: <verdict>.
  Open questions: all resolved interactively | <N open, blocks GO>.
  Required next step: <human approval | decision | replan | other>.

NOT REVIEWED:
- `<plan file>`: <exact reason>.   # skipped CANDIDATES only; `- (none)` if none were skipped. Never enumerate plans that were never candidates (e.g. the executed/ dir).
```

Rules:

- One row per distinct root-cause finding.
- Use only the listed Decision values.
- Include every scope-ledger item. (The ledger holds only candidates - named targets + documented-eligibility additions - so this never means enumerating the whole pending/ or executed/ dir.)
- The `### Plans reviewed and not reviewed` section is the final output.
- Print nothing after it.
