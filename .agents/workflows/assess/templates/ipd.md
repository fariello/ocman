# IPD: Assess <concern> - <short title>

- Date: <YYYY-MM-DD>
- Concern: <performance | security | accessibility | ...>
- Scope: <whole project | the $ARGUMENTS narrowing>
- Status: to-review
- Approval: <set when a human approves, e.g. "approved by <name> <date>"; omit until then>
- Author: <agent/model if known>
- Set: <optional; lowercase-kebab id shared by an ordered set of related plans; omit for a lone plan>
- Order: <optional; 1-based position within Set; omit if not in a set>

<!--
Status vocabulary (readiness within the lifecycle; lowercase-kebab; front-matter is the
single source of truth - see DECISIONS D52). Directories carry DISPOSITION; Status carries
READINESS.
  Pre-terminal (file lives in .agents/plans/pending/):
    draft       - a stub or partial plan; NOT ready to review or execute.
    to-review   - complete enough to critique; ready for /plan-review or human review.
    reviewed    - /plan-review done and revisions applied; awaiting human sign-off.
    approved    - human signed off; ready to execute (add the Approval: line).
    auto-approved - ready to execute, cleared by an automated checker (e.g. /verify-execution)
                  rather than a human; used for low-complexity mechanical correctives (D65). NOT
                  human approval; set only by an automated checker.
  Terminal (file lives in the matching directory; Status MIRRORS the dir):
    executed / superseded / not-executed
  Standing: reusable
Longest path: draft -> to-review -> reviewed -> approved -> executed. Terminal
superseded/not-executed are reachable from ANY pre-terminal state (retire with a
"RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>" header + git mv; never delete).

DEFAULT: a normally-drafted IPD is born `to-review` (a complete proposal is review-ready).
Use `draft` ONLY when this is an explicit stub / "capture now, work on it later". `to-review`
gates on APPROACH-COMMITTED, not all-questions-resolved - open questions are expected and are
what /plan-review interrogates.
-->

## Workflow history

<!-- Append one dated line per workflow that touches this plan (never rewrite prior lines):
     - YYYY-MM-DD /<workflow> (<agent/model>): <one-line outcome>
  Status shows the CURRENT state; this section shows the PATH taken. -->
- <YYYY-MM-DD> created (<agent/model>): <how this IPD was produced>

## Goal

What this plan aims to achieve for the concern, and why it matters for this project's
intent, users, and stakeholders.

## Project conventions discovered (Step 0)

- Guiding principles: <path, or universal fallback>
- Pending-plans location/format used: <path>
- Contributor/spec-sync contract: <path or N/A>
- Stack / relevant context: <...>

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for whether to
act now. Persona = which reviewer perspective surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
|    |          |                  |         |      |         |                      |

## Proposed changes (ordered, validatable)

Fix by default; each item should be safe, well-scoped, and verifiable. Note the
Remediation Risk and the validation for each.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
|      |                    |        |       |                  |            |

## Deferred / out of scope (with reason)

Deferral requires Medium-High or higher Remediation Risk; name the axis (complexity /
usability / security / functionality). Effort/time is never a reason. Where possible,
the safe portion is proposed above and only the risky remainder is deferred here.

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
|            |                  |      |        |                        |

## Scope check

- Over-scope (untraceable to a need; propose removal/deferral): <...>
- Under-scope (needed capability missing; propose adding): <...>

## Required tests / validation

How the executed plan will be verified (commands, test cases, manual checks,
acceptance criteria). Include regression protection for any behavior-affecting change.

## Spec / documentation sync

If the plan changes user-visible behavior, what specs/docs/README must be updated.
N/A with reason if not applicable.

## Open questions

Anything needing a human decision before or during execution, and any assumptions
made (marked so they can be confirmed).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it; that sets
   `Status: reviewed`). Update `Status:` as it progresses (`to-review` -> `reviewed` ->
   `approved`), appending a Workflow-history line at each step.
2. On human approval, set `Status: approved` (+ the `Approval:` line), execute the ordered
   changes, run the validation, and sync specs/docs.
3. Only then set the terminal `Status:` and move this IPD from the pending dir to the right
   terminal dir per the
   project's lifecycle convention (canonical: `.agents/plans/pending/` ->
   `.agents/plans/executed/` when implemented+verified; `superseded/` if replaced by a
   better plan or `not-executed/` if deliberately not run - retire with a
   `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` header + `git mv`, never a
   delete; recurring plans live in `.agents/plans/reusable/`; a repo already using `done/`
   keeps `done/`). Plan files are named `YYYYMMDD-HHMM-NN-<slug>.md` (local date+time; `NN`
   per-minute two-digit sequence, `00` reserved for an orchestrator; lowercase-kebab slug).
