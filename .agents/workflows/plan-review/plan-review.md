# Plan Review (pre-execution plan / IPD reviewer)
Treat this file as the controlling instruction for reviewing a proposed plan
before implementation, then improving that plan in place.

Review planning documents only. Do not change code, tests, runtime
configuration, infrastructure, or production data. Editing a plan is not
executing it.

This workflow shares these sibling policies:
- `../release-review/fix-decision-policy.md`
- `../release-review/00-run-protocol.md`

This portable single-file variant is SERIAL BY DESIGN: it does not auto-fan-out into parallel audit
lanes (a lone portable file spawning subagents is awkward and not universally available). For a
multi-plan batch that should review plans in parallel, use `../plan-review-long/plan-review-long.md`,
which auto-engages the read-only audit-lane convention (`../release-review/00-run-protocol.md`) when the
scope ledger has 2 or more eligible plans. The two variants are otherwise kept in deliberate parity.

If either is absent, apply these rules from memory:
- Fix findings by default.
- Defer only when the fix itself has Medium-High or High Remediation Risk on
  complexity, usability, security, or functionality.
- Severity is for reporting only.
- Effort, time, cost, and tokens never justify deferral.
- Review through QA/QC, testing/regression, UI/UX, architect, software
  engineer, power user, novice, and stakeholder views.
- Apply security as a mandatory cross-cutting lens.

---
## Memory kernel
Re-read this before each step and before the final report:
1. Review plans only.
2. Verify claims from repository evidence.
3. Fix by default. Severity never decides.
4. Resolve open questions interactively when possible.
5. Never guess a human decision.
6. Preserve valid plan content and required structure.
7. Make at most two local commits. Never push.
8. The reviewed/not-reviewed enumeration is the literal final output.
9. A gate or interactive question MUST NOT assert or imply the verdict it precedes (readiness, approval, GO); it states what was found and asks what to do. The verdict is formed only from the reviewed work's evidence.

---
## Step 0: Scope and project contract
Complete this before judging or editing a plan.

### 0.1 Build the review-scope ledger
List every plan explicitly requested or selected by the project workflow.

Classify each as:
- `ELIGIBLE` - review it.
- `NOT REVIEWED` - skip it, with the exact reason.

Use project eligibility and status rules when present. Otherwise review an
explicitly requested plan unless it is missing, unreadable, malformed beyond
review, or not a planning document.

A file referenced only as evidence is not in scope unless explicitly added.

The final enumeration MUST contain every ledger item and no incidental file.

### 0.2 Discover controlling instructions
Read the applicable repository and directory-scoped instructions, guiding
principles, contributor rules, plan lifecycle, specification obligations, plan
templates, and the target plan.

Do not assume filenames.

If instructions conflict, use the project's precedence rules. If none resolve
the conflict, record an open question. Do not silently choose.

### 0.3 Discover the plan contract and implementation context
Determine:
- Plan location, structure, front matter, status lifecycle, approval rules,
  traceability, workflow history, and commit rules.
- Project type, languages, frameworks, production runtime and data store,
  deployment model, integrations, security model, and test stack.
- Domain invariants from specifications, principles, ADRs, accepted plans,
  code, tests, constraints, and authoritative conversation context.

Apply the rubric to the real production target.

If the plan changes behavior, policy, workflow, API, authorization, state, or
domain rules, require specification and documentation synchronization.

If no project principles exist, use these fallbacks and record that choice:
- Intuitive and self-documenting.
- General-case and configurable.
- KISS.
- Honest documentation.

---
## Step 1: Evidence and pre-review snapshot
For each eligible plan:
1. Read the whole plan.
2. List material files, requirements, issues, ADRs, APIs, schemas, tests, and
   behaviors it relies on.
3. Open the referenced evidence.
4. Verify material claims with `path:line` evidence.
5. Record missing, stale, contradictory, or inaccessible evidence.
6. Do not infer unsupported implementation details.

If missing evidence prevents reliable review, file a finding or open question.

### Pre-review commit
Before editing:
1. Inspect repository status.
2. Isolate the eligible plan files.
3. If any target plan is untracked or modified, commit those plan files
   verbatim as:

   `plan: pre-review snapshot of <scope>`

4. If all target plans are committed and unchanged, skip the snapshot.

Never stage unrelated files. Never amend, reset, rebase, discard user changes,
or push.

If Git is unavailable or a commit fails, continue only when safe and record the
reason. Do not bypass hooks or safety controls unless project rules permit it.

---
## Step 2: Review and revise
### 2.1 Apply all required views
Review against:
- The engineering rubric below.
- Project principles.
- Domain invariants.
- Plan goals and acceptance criteria.
- The eight personas.
- The security lens.

### 2.2 Record findings
Record each distinct actionable issue. Combine duplicate symptoms under one
root cause. Do not invent findings.

Classify each finding with:
- **Severity:** `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`.
- **Scope:** `IN-SCOPE`, `OVER-SCOPE`, or `UNDER-SCOPE`.
- **Area:** rubric or project rule.
- **Evidence:** `path:line`.
- **Remediation Risk:** complexity, usability, security, functionality, and
  overall.
- **Decision:** `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.

### 2.3 Remediation Risk and Fix Bar
Overall Remediation Risk is the highest applicable axis rating.

- **Low:** Local, understood, easy to verify, unlikely to harm behavior.
- **Medium:** Bounded uncertainty with a clear verification path.
- **Medium-High:** Material chance of significant complexity, usability harm,
  security weakness, or functional regression.
- **High:** Likely major harm, a foundational unresolved decision, or no safe
  fix from available evidence.

Fix every finding unless overall Remediation Risk is Medium-High or High.

Every deferral MUST state:
- Axis or axes.
- Why the risk reaches the threshold.
- Required decision or evidence.
- Consequence of leaving it unresolved.

Effort, time, cost, and tokens are never valid deferral reasons.

For over-scope, the default fix is removal or explicit deferral from the plan.
That is normally Low risk.

### 2.4 Revise the plan in place
Make surgical edits:
- Preserve valid content and required structure.
- Replace ambiguity instead of appending duplicate prose.
- Add missing guardrails, sequencing, acceptance criteria, tests, validation,
  specification updates, and traceability.
- Remove unsupported or gold-plated scope.
- Keep the plan concise and executable.
- Do not weaken valid requirements.

When a finding spans plans, fix it in the owning plan and cross-reference it
from dependent plans.

If the approach is fundamentally unsound and cannot be repaired with bounded
edits, mark `REPLAN`, explain why, and describe the minimum shape of a sound
replacement. Do not invent decisions that require the human.

---
## Step 3: Resolve open questions
Complete this before the final report.

### 3.1 Build the question set
Collect and deduplicate:
- Pre-existing open questions.
- Questions created by findings.
- Instruction conflicts.
- Decisions needed to repair or replan.

Resolve questions from authoritative evidence first. Cite the source. Do not
ask the human what the repository already answers.

Mark which questions block correctness, security, scope, architecture, or GO.

### 3.2 Ask interactively
In an interactive run, ask one to three related questions per prompt.

For each question provide:
1. **Decision needed**
2. **Context**
3. **Why it matters**
4. **Options**
5. **Trade-offs**
6. **Recommendation**

Use plain language. Define acronyms and identifiers. Ask and wait before the
final report. Do not guess or bury the recommendation.

After each answer:
1. Record it in the owning plan.
2. Resolve or rewrite the open question.
3. Apply resulting edits.
4. Re-check affected rubric areas.
5. Continue until no resolvable question remains.

### 3.3 Non-interactive exception
A run is non-interactive only when the environment explicitly has no human
interaction channel. A delayed reply is not non-interactive.

In a genuinely non-interactive or interrupted run:
- Leave questions explicitly `OPEN`.
- State the required decision.
- Use verdict `REVIEWED - OPEN QUESTIONS`.
- Recommend `NO-GO`.

---
## Step 4: Finalize state and commit
For each reviewed plan confirm:
- Every finding is `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.
- Every deferral meets the Fix Bar.
- Resolved decisions are written into the plan.
- Required specification and documentation work is included.
- Tests and validation map to affected invariants.
- The plan does not claim execution.
- The plan's gate carries an execution contract (resolved open questions, a scope fence,
  the hard-MUST "paste the actual runner output" honesty rule, path-scoped commit and
  never-push, and the lifecycle move). If any element is missing, ADD it as an in-place
  revision and record it as a finding.

If the project uses `Status`, set it to `reviewed` unless its contract requires
another review-complete value.

`reviewed` means the review occurred. It does not mean approved, GO, ready to
execute, or executed. Only the human or project approval process may approve.

Append or update:

```markdown
## Workflow history
- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>
```

Use the real agent/model name, or `unknown`.

### Hardened-result commit
After revisions and interactive decisions:
1. Commit only reviewed plan files and any required review record.
2. Use:

   `plan-review: harden <scope> (revisions applied)`

3. Never push.

Report a skipped, failed, or inapplicable commit exactly.

---
## Engineering rubric
For each item, verify the plan addresses it or justifies `Not applicable`.

### A. Correctness and data integrity
- Dependent writes are atomic; retries and handlers are idempotent.
- Concurrency, uniqueness, ordering, and partial-failure risks are handled.
- Production data-store syntax, types, constraints, and migrations are valid.
- Public data, audit, and serialized formats preserve required history and
  compatibility when relevant.

### B. Security and privacy
- Identity is verified; authorization is default-deny and resource-scoped.
- Secrets are not hardcoded; trust-boundary inputs are validated.
- Queries, commands, files, uploads, and outbound calls are safe when present.
- Sensitive data collection, logging, exposure, retention, and errors are
  minimized.
- Privileged bypasses and abuse controls are justified when relevant.

### C. Architecture and operability
- The design uses existing canonical mechanisms and avoids duplicate paths.
- New dependencies, services, abstractions, and async work are justified.
- State, caching, time, retries, failure handling, observability, rollout, and
  recovery are explicit when relevant.
- The plan provisions for real needs, not hypothetical scale.

### D. Anti-regression and domain invariants
- Name each affected invariant and map it to a test.
- Preserve intended correct behavior unless an approved change fixes it.
- Add characterization coverage for risky refactors.
- Do not freeze accidental behavior that project policy says to replace.
- Treat unexplained behavior changes as blockers.

### E. Testing and verification
Require concrete tests for applicable happy, validation, authorization,
constraint, failure, rollback, retry, concurrency, integration, accessibility,
and compatibility paths.

Use production-equivalent dependencies where differences matter.

State exact validation commands, environments, and expected evidence.

### F. KISS, principles, and UX
- Prefer the smallest correct design and reuse existing mechanisms.
- Variation should be data or configuration when appropriate.
- Map the plan to each project principle with verifiable outcomes.
- Minimize user effort and define loading, empty, error, success, and recovery
  states when user-facing.
- Include keyboard, semantic, focus, naming, contrast, and assistive feedback
  when accessibility applies.
- Prevent silent failure.

### G. Plan executability
Verify the plan states:
- Problem, driver, goals, non-goals, scope, and exclusions.
- Acceptance criteria and ordered implementation steps.
- Target components and existing mechanisms to reuse.
- Dependencies, sequencing, and data/API/workflow effects.
- Security, privacy, migration, documentation, and specification effects.
- Validation, rollout or recovery when relevant.
- Assumptions, open questions, ownership, and follow-up work.
- An execution contract in the gate: resolved open questions, a scope fence, the hard-MUST
  honesty rule (paste the actual runner output), path-scoped commit and never-push, and the
  lifecycle move.

Another qualified agent or developer must be able to execute the plan without
inventing missing architecture.

---
## Severity and scope
Severity is for reporting only:
- **BLOCKER:** likely data loss, breach, normal-path failure, silent invariant
  violation, or core-principle violation.
- **HIGH:** material reliability, security, accessibility, maintainability, or
  required-coverage gap.
- **MEDIUM:** real gap on a non-critical path or uncommon condition.
- **LOW:** polish or small clarity improvement.

LOW and MEDIUM findings are fixed by default too.

Scope:
- **IN-SCOPE:** flaw in proposed work.
- **OVER-SCOPE:** not traceable to a driver or requirement.
- **UNDER-SCOPE:** required capability, guardrail, test, migration, or
  documentation is missing.

---
## Verdict and readiness
Verdict describes review outcome. Readiness is separate.

Use one verdict:
- **`APPROVE`** - no revisions needed, no open questions, valid deferrals only.
- **`APPROVE WITH REVISIONS APPLIED`** - findings fixed, no open questions,
  valid deferrals only.
- **`REVIEWED - OPEN QUESTIONS`** - review completed but decisions remain.
- **`REJECT - NEEDS REPLAN`** - approach is unsound and not repairable with
  bounded edits.

Readiness (human approval is a SEPARATE step from the review verdict; a reviewed,
clean plan is `GO - PENDING HUMAN APPROVAL`, never a bare `NO-GO`; reserve `NO-GO`
for genuine not-ready conditions):
- **GO:** verdict is `APPROVE` or `APPROVE WITH REVISIONS APPLIED`, all questions
  are resolved, no unfixed BLOCKER or HIGH remains, AND the human has approved
  (`Status: approved`). Cleared to proceed.
- **GO - PENDING HUMAN APPROVAL:** same clean bar as GO (right verdict, no open
  questions, no unfixed BLOCKER/HIGH) but the human sign-off has not happened yet.
  This is the positive, correct readiness for a plan that passed review and only
  awaits approval. It is NOT a failure state.
- **NO-GO:** genuine not-ready: any open question, any unfixed BLOCKER/HIGH, or a
  `REVIEWED - OPEN QUESTIONS` / `REJECT - NEEDS REPLAN` verdict. NOT used merely
  because a clean plan lacks a signature.

A plan may be `Status: reviewed` and be `GO - PENDING HUMAN APPROVAL` (passed,
awaiting sign-off); it is only `NO-GO` when a genuine not-ready condition remains.

---
## Required final report
Do not issue the final report until the question loop is complete, unless the
run is genuinely non-interactive or interrupted.

Use this exact order. Cite evidence as `path:line`. Use one row per finding.

```markdown
## Plan Review - <plan name(s)>
Verdict: <APPROVE | APPROVE WITH REVISIONS APPLIED | REVIEWED - OPEN QUESTIONS | REJECT - NEEDS REPLAN>

### Review scope
ELIGIBLE:
- <plan file>

NOT REVIEWED:
- <plan file>: <reason>

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | <level> | <scope> | <ref> | <path:line> | <finding> | C:<rating>; U:<rating>; S:<rating>; F:<rating>; Overall:<rating> | <FIXED|DEFERRED|OPEN|REPLAN> | <resolution or next step> |

### Edits applied
- `<plan file>` - `<section>`: <edit>

### Deferred and open
- `<finding ID>` - `<DEFERRED | OPEN>`:
  - Reason: <reason>
  - Remediation Risk: <Medium-High | High>
  - Axis: <complexity | usability | security | functionality>
  - Required decision or evidence: <need>
  - Consequence if unresolved: <impact>

### Commit result
- Pre-review snapshot: <hash | skipped unchanged | not applicable | failed: reason>
- Hardened result: <hash | not applicable | failed: reason>
- Push: not performed

### Plans reviewed and not reviewed
REVIEWED:
- `<plan file>`: <GO | GO - PENDING HUMAN APPROVAL | NO-GO> - <reason>.
  Verdict: <verdict>.
  Open questions: all resolved interactively | <N open, blocks GO>.
  Required next step: <approval | decision | replan | other>.

NOT REVIEWED:
- `<plan file>`: <exact reason>.
```

The `### Plans reviewed and not reviewed` section MUST be the literal final
output.

Enumerate every file from the Step 0 ledger. Print nothing after it.
