# Plan Review (pre-execution plan / IPD reviewer)

Treat this file as the controlling instruction for reviewing a **proposed plan
before any code is written**, and then **improving that plan in place** so it is
materially safer and more likely to produce a reliable, usable, secure, intuitive,
and principle-aligned outcome.

This is the plan-time sibling of the release review. Where the release review reviews
finished code before shipping, this reviews a written implementation plan before
building. Catching a missing transaction boundary, an authorization gap, or an
over-scoped feature on paper is far cheaper than catching it in code.

It shares this framework's policies rather than redefining them (the release-review
runbook is its sibling directory):

- **Fix decisions are governed by `../release-review/fix-decision-policy.md`** (the
  Fix Bar): fix by default; defer only when the *Remediation Risk* of the fix itself
  is Medium-High or higher (complexity / usability / security / functionality).
  Severity is for reporting, not for deciding. Effort/time/token cost are never a
  reason to defer.
- **Review through the eight personas** defined in
  `../release-review/00-run-protocol.md` (QA/QC, testing/regression, UI/UX, architect,
  software engineer, power user, novice, stakeholder), led here by the architect,
  software-engineer, security, and stakeholder views.

If those files are not present (for example this prompt was copied on its own), apply
the same rules from memory: fix-by-default gated by Remediation Risk, and
multi-perspective review.

---

## What this command does NOT do

You review and revise **planning documents only**. You never change application code,
tests, or configuration from this command. Producing or editing the plan is not
executing it.

---

## Step 0: Discover the project's conventions (do not hardcode)

Before reviewing, discover and read what the project actually uses; do not assume any
particular filenames or stack:

1. **Guiding principles:** `GUIDING_PRINCIPLES.md`, `PRINCIPLES.md`, a "Principles"
   section in `README.md`/`CONTRIBUTING.md`, or whatever `AGENTS.md` names. The plan
   must conform to these. If none exist, use the universal fallback principles in
   `../release-review/00-run-protocol.md` (intuitive/self-documenting,
   general-case/configurable, KISS, honest docs) and record that you did so.
2. **Agent/contributor contract:** `AGENTS.md`, `CONTRIBUTING.md`, or equivalent, for
   required plan sections, spec-sync obligations, and lifecycle rules.
3. **Plan location and format:** where plans live (e.g. `.agents/plans/`, `docs/rfcs/`,
   ADRs, a `PLAN.md`) and the required structure (goal, target files, proposed
   changes, architecture/drivers, validation steps). Review the plan against its own
   contract.
4. **Project type, stack, and production database/runtime**, so the rubric below is
   applied to the real target (e.g. the production DB dialect, not just the test one).
5. **Domain invariants:** the business/correctness truths this project must never
   violate. Discover them from specs, principles, existing code, and the conversation;
   do not assume a fixed domain. These become anti-regression check targets.

If the plan proposes user-visible behavior changes, confirm it also plans to sync the
project's specification/docs (whatever the project uses, e.g. a functional spec or
`README`); if that is missing, add it.

---

## Operating mode (review AND revise)

1. **Review** the target plan(s) against the rubric below. Read the actual referenced
   source files (`file:line`) to verify the plan's claims rather than trusting its
   self-description. (This is the same "re-open the evidence" discipline as
   `release-review` Section 7.)
2. **Record every finding**, however small: bug, gap, ambiguity, missing-but-required
   capability, over-scoped/gold-plated feature, or polish. Assign each a **Severity**
   (for reporting/ordering only) and a **Remediation Risk**, then apply the Fix Bar.
3. **Revise the plan in place, fix by default.** Make surgical, well-anchored edits
   that preserve the plan's existing valid content and its required structure. Add
   guardrails, missing sections, and specificity; do not weaken or delete valid
   content. For over-scoped findings, the "fix" is to recommend removal/deferral
   (itself low Remediation Risk, so do it). When a finding spans multiple plans, fix
   it in the owning plan and cross-reference the others.
4. For any finding you do **not** fix, record it in the plan's Open Questions (or
   equivalent) with the explicit Remediation-Risk justification: which axis
   (complexity / usability / security / functionality) and why it is Medium-High or
   higher. "Too much effort/time" is never a valid reason to defer.
5. **Report back** using the format below: the verdict, the findings table, and the
   exact edits made to each plan, with enough detail for a human to audit. Do not mark
   the plan as executed; reviewing/revising is not executing.

---

## Cross-cutting engineering rubric (applies to every plan)

For each item, verify the plan addresses it **or** explicitly and correctly scopes it
out (and does not regress it). "Not applicable" must be justified, never assumed.
Apply only the items relevant to the project type discovered in Step 0.

### A. Data-layer correctness and integrity

- **Atomicity:** any operation with multiple dependent writes is wrapped in a real
  transaction with rollback. Flag no-op or sequential-callback patterns that can leave
  orphaned partial state.
- **Idempotency and single-response:** request handlers cannot double-respond or
  double-apply; retries are idempotent.
- **Dialect/parameter safety:** parameterization is correct on the *production* data
  store, not just the test one.
- **Migrations:** schema changes are versioned and reversible (expand/contract for
  zero-downtime where relevant); hot/queried columns are indexed.
- **Audit/immutability:** if audit or append-only data is touched, the append is
  concurrency-safe and queried by an indexed key.

### B. Security baseline

- **Authentication:** no trust of unverified input for identity; no defaulting to a
  privileged user; mocks for an MVP step are explicitly gated to non-production.
- **Authorization:** default-deny; route-level and object/row-level checks; tenancy
  scoping so no query crosses tenants; reconsider blanket "admin bypasses everything".
- **Secrets:** none hardcoded; via a secrets manager; fail-fast if absent in prod.
- **Inputs/uploads:** validation at the boundary (reject unknown fields); upload
  type/size/scan hardening; rate limiting that works across a stateless fleet; safe
  error envelopes (no internals/stack traces to clients).

### C. Scalability seams ("architect the seam, provision for today")

- **Stateless tier:** no request-path local state that assumes a single node.
- **Externalized state:** connection pooling; read/write split where read-heavy;
  partition/tenancy key designed in.
- **Async side effects:** notifications, integration sync, scans, report precompute
  moved off the request path onto a durable, retryable, idempotent queue with a
  dead-letter path.
- **Cache correctness:** hot reads cached with explicit invalidation;
  correctness-critical derived status is a strong read and synchronously invalidated,
  so stale data never shows a wrong "OK".
- **No anti-scale constants:** no hardcoded "today"/clock; clock is injectable.

### D. Anti-regression / preserve invariants

- If the plan refactors, moves, or rewrites code that enforces business/correctness
  truth, it must require **characterization/regression tests that pin current correct
  behavior before the change**, green after. Name the at-risk invariants (from Step 0)
  and route each to a test. Treat behavior diffs as blockers unless explicitly
  approved as bug fixes.

### E. Observability and operability

- Structured logs with a correlation ID propagated across request/worker/integration;
  metrics for new paths; meaningful health/readiness; alerts for new failure modes,
  each mapped to a runbook.

### F. Testing, verification, and seeding

- Concrete unit + integration tests for happy path, validation errors, the
  authorization matrix (role x resource, including cross-tenant denial), constraints,
  and failure/rollback paths. Integration tests run against the production-equivalent
  data store to catch dialect drift. Accessibility and, where relevant,
  contract/e2e/load coverage. Test seed/fixtures retain realistic edge-case scenarios.

### G. KISS and cost discipline

- New dependencies, services, or abstraction layers must be justified (why necessary,
  why this one). Prefer the simplest correct design and managed primitives. Flag
  premature complexity AND missing seams. This is the Fix Bar's complexity axis acting
  as the counterweight to fix-by-default.

### H. Guiding-principles and UX conformance

- Verify the plan is checkable against each of the project's stated principles
  (Step 0) and does not regress any. Where principles cover usability/accessibility,
  require concrete, verifiable targets (e.g. contrast ratios, keyboard operability,
  loading/empty/error states, no silent failure), not vague claims.

### I. Domain invariants (project-specific)

- For each domain invariant discovered in Step 0, verify the plan preserves it and
  routes it to a test. Do not silently change a currently-correct domain outcome while
  "fixing" logic.

---

## Severity (reporting and ordering only; does not gate the fix decision)

- **BLOCKER** - will corrupt/lose data, breach security, crash on a normal path,
  silently break an existing rule/invariant, or violate a core principle.
- **HIGH** - materially harms reliability, scalability headroom, accessibility,
  maintainability, or omits a required test/guardrail on an exercised path.
- **MEDIUM** - a real gap or ambiguity on a non-critical path or under unlikely
  conditions.
- **LOW** - polish, wording, nice-to-have.

Because the Fix Bar (not severity) decides whether to act, LOW and MEDIUM findings are
fixed by default too; they are left undone only if their *fix* clears the Medium-High
Remediation-Risk bar.

**Scope axis (always check):** OVER-SCOPE (untraceable to a stated driver/requirement;
default action: recommend removal/deferral) and UNDER-SCOPE (a required capability the
plan omits; default action: add it).

---

## Verdict (state one explicitly)

- `APPROVE` - no findings remain that should have been fixed; any deferrals are
  justified by Medium-High-or-higher Remediation Risk.
- `APPROVE WITH REVISIONS APPLIED` - you found and fixed issues; summarize them.
- `REJECT - NEEDS REPLAN` - the fundamental approach is unsound and cannot be patched
  with edits; explain why and what a sounder approach looks like.

---

## Required report format

```
## Plan Review - <plan name(s)>
Verdict: <APPROVE | APPROVE WITH REVISIONS APPLIED | REJECT - NEEDS REPLAN>

### Findings
| ID | Severity | Scope | Area (rubric ref) | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|-------------------|---------|------------------|----------|------------|

### Edits applied (per plan)
- <file>: <concise description of each edit>

### Deferred / open (with reasons)
- <finding>: deferred - Remediation Risk <Medium-High|High> on
  <complexity|usability|security|functionality> because <reason>.
  (Effort/time is never a reason.)
```

Be rigorous and specific, cite `file:line` evidence, and do not invent issues where
there are none. Default to fixing - even small bugs, nits, and polish - because the
only justification for leaving a finding unaddressed is that the *fix itself* carries
Medium-High-or-higher risk to complexity, usability, security, or functionality.
Never let a finding pass merely because it was effortful, and never let a real
BLOCKER pass because it was inconvenient to fix.
