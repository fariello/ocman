# IPD: Assess <concern> - <short title>

- Date: <YYYY-MM-DD>
- Concern: <performance | security | accessibility | ...>
- Scope: <whole project | the $ARGUMENTS narrowing>
- Status: PENDING (awaiting human approval; not executed)
- Author: <agent/model if known>

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

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes, run the validation, and sync specs/docs.
3. Only then move this IPD from the pending dir to the right terminal dir per the
   project's lifecycle convention (canonical: `.agents/plans/pending/` ->
   `.agents/plans/executed/` when implemented+verified; `superseded/` if replaced by a
   better plan or `not-executed/` if deliberately not run - retire with a
   `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` header + `git mv`, never a
   delete; recurring plans live in `.agents/plans/reusable/`; a repo already using `done/`
   keeps `done/`). Plan files are named `YYYYMMDD-HHMM-NN-<slug>.md` (UTC date+time; `NN`
   per-minute two-digit sequence, `00` reserved for an orchestrator; lowercase-kebab slug).
