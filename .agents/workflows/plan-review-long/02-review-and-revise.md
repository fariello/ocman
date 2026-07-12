# Step 2: Review and revise

## Purpose

Find every real plan defect, apply the Fix Bar, and improve the plan in place.

## Required context

Read `review-rubric.md` in full. Apply:

- the plan's goals and acceptance criteria;
- project instructions and guiding principles;
- domain invariants;
- all eight personas;
- the mandatory security lens;
- the rubric.

## 1. Record findings

Record each distinct actionable finding. Combine duplicate symptoms under one
root cause. Do not invent findings.

Each finding MUST contain:

- Severity: `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`.
- Scope: `IN-SCOPE`, `OVER-SCOPE`, or `UNDER-SCOPE`.
- Area: rubric and project-rule reference.
- Evidence: `path:line`.
- Finding and impact.
- Remediation Risk on complexity, usability, security, functionality, and
  overall.
- Decision: `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.
- Resolution or required next step.

Severity is for reporting only.

## 2. Apply the Fix Bar

Overall Remediation Risk is the highest applicable axis:

- **Low:** local, understood, easy to verify, unlikely to cause harm.
- **Medium:** bounded uncertainty with a clear verification path.
- **Medium-High:** material chance of significant complexity, usability harm,
  security weakness, or functional regression.
- **High:** likely major harm, foundational uncertainty, or no safe fix from
  available evidence.

Fix every Low or Medium risk finding.

A deferral MUST state:

- the Medium-High or High axis;
- why the fix is risky;
- needed decision or evidence;
- consequence of leaving it unresolved.

Effort, time, cost, and tokens are invalid reasons.

For over-scope, remove or explicitly exclude the unsupported work by default.

## 3. Revise in place

Make surgical, well-anchored edits:

- preserve valid content and required structure;
- replace ambiguity rather than appending duplicate prose;
- add missing guardrails, sequencing, acceptance criteria, tests, rollout,
  recovery, specification work, and validation;
- inject the gate execution contract if missing (resolved open questions, a scope
  fence, the hard-MUST honesty rule, path-scoped commit and never-push, lifecycle move);
- remove unsupported or gold-plated scope;
- keep the plan concise and executable;
- do not weaken valid requirements.

For cross-plan findings, fix the owning plan and cross-reference dependent
plans. Do not duplicate requirements.

If the approach is not safely patchable, mark `REPLAN`, explain why, and state
the minimum shape of a sound replacement. Do not invent human product choices.

## Exit gate

Do not proceed until:

- [ ] Every rubric area is addressed or justified not applicable.
- [ ] Every real finding is recorded with evidence and all risk axes.
- [ ] Every Low or Medium risk finding is fixed.
- [ ] Every deferral meets the Fix Bar.
- [ ] Over-scope is removed or explicitly excluded.
- [ ] Revised plans remain concise, coherent, and executable.
- [ ] Replan findings identify the minimum required new direction.
