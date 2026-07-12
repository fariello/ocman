# Step 3: Resolve, finalize, and report

## Purpose

Resolve human decisions, finalize review state, create the hardened commit, and
produce the deterministic final report.

## 1. Resolve open questions

Collect:

- pre-existing unresolved questions;
- questions created by findings;
- unresolved instruction conflicts;
- decisions required for repair or replan.

Resolve questions already answered by authoritative evidence and cite it.
Deduplicate overlapping questions. Mark which block correctness, security,
scope, architecture, or GO readiness.

In an interactive run, ask one to three related questions at a time.

For each question provide:

1. Decision needed.
2. Context.
3. Why it matters.
4. Options.
5. Trade-offs.
6. Recommendation and one-line reason.

Use plain language. Define acronyms and identifiers. Do not guess.

After each answer:

1. Record it in the owning plan.
2. Resolve or rewrite the open question.
3. Apply consequent edits.
4. Re-run affected rubric areas.
5. Ask any newly required dependent question.

Continue until no resolvable question remains.

A run is non-interactive only when no human channel exists. A delayed answer is
not non-interactive.

For a genuinely non-interactive run, leave questions `OPEN`, use verdict
`REVIEWED - OPEN QUESTIONS`, and recommend `NO-GO`.

## 2. Finalize plan state

For each reviewed plan confirm:

- every finding is `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`;
- every deferral meets the Fix Bar;
- resolved decisions are written into the plan;
- required spec and documentation work is included;
- tests and validation cover affected invariants;
- the plan does not claim implementation.

Apply the project's review-complete status. If it uses `Status`, set `reviewed`
unless the contract requires another value.

`reviewed` does not mean approved, GO, ready to execute, or executed.

Append or update:

```markdown
## Workflow history

- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>
```

Use `unknown` when the identifier is unavailable.

## 3. Hardened-result commit

After all edits and decisions:

1. Commit only reviewed plans and any required run record.
2. Use `plan-review: harden <scope> (revisions applied)`.
3. Never include unrelated files.
4. Never push.
5. Report skipped or failed commits exactly.

## 4. Verdict and readiness

Use exactly one verdict:

- `APPROVE` - no revisions needed; no open questions; all deferrals pass.
- `APPROVE WITH REVISIONS APPLIED` - findings fixed; no open questions; all
  deferrals pass.
- `REVIEWED - OPEN QUESTIONS` - review complete, but human decisions remain.
- `REJECT - NEEDS REPLAN` - the approach is unsound and not safely patchable.

Readiness:

- `GO` requires APPROVE or APPROVE WITH REVISIONS APPLIED, no open questions,
  and no unfixed BLOCKER or HIGH.
- Otherwise use `NO-GO`.

A reviewed plan may still be NO-GO.

## 5. Final report

Read `report-template.md` in full and use it exactly.

The final reviewed/not-reviewed enumeration MUST contain every item from the
Step 1 scope ledger and MUST be the literal last output.

## Exit gate

The run is complete only when:

- [ ] All resolvable questions are answered and applied.
- [ ] Each plan's review status and workflow history are updated.
- [ ] Every finding and deferral is reconciled.
- [ ] Verdict and GO/NO-GO are consistent.
- [ ] Hardened commit exists or is explained.
- [ ] Final report follows the template exactly.
- [ ] Nothing follows the reviewed/not-reviewed enumeration.
