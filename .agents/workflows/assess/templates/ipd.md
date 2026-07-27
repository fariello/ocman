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

## Detailed Implementation Checklist (TODO)

The EXECUTION checklist, placed near the top so the executing agent has an up-front, tickable
plan (`- [ ]` -> `- [x]`, updated in place as each item is completed AND verified). It covers
EVERY required action, decision, deliverable, and validation. This is the primary
progress-tracking mechanism for agents without an external todo tool. Group by task; name EXACT
file basenames + function/symbol names (and line anchors when useful); include the LITERAL
verification command and a reminder to paste its real output. A ticked box is a claim, not proof
- the `## Validation and cross-check` checklist near the end is the evidence pass, and the
completion rule in the gate is the hard gate.

- [ ] **Task 1: <short title>**
  - [ ] Edit `<file>` (`<function/symbol>`, ~line `N`): <exact change + any contract/edge case to preserve>.
- [ ] **Task 2: <short title>**
  - [ ] <exact change>.
- [ ] **Tests and regression protection**
  - [ ] Add/update `<test_name>` in `<test_file>` asserting <expected outcome>.
  - [ ] Run `<literal verify command, e.g. python -m pytest -q>` and PASTE the actual output.
- [ ] **Docs / spec sync** (if user-visible behavior changed): <what to update>.
- [ ] **Lifecycle and commit**
  - [ ] Path-scoped commit(s): `git commit -m "<msg>" -- <paths>` (never `git add -A`/`-a`; never push).
  - [ ] Set terminal `Status:` and `git mv` this plan to the right terminal dir.

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

## Validation and cross-check (verify before reporting done)

A SEPARATE end-of-document checklist the executing agent completes as a deliberate
verification pass BEFORE reporting success. Each item maps 1:1 to a
`## Detailed Implementation Checklist (TODO)` item near the top and requires CONCRETE evidence
(command output, `file:line`, artifact path) that the item was actually performed. No item may
be marked complete unless it was actually done AND verified; any incomplete, blocked, skipped,
or unverified work MUST be reported EXPLICITLY here (not silently dropped or ticked). Make these
items specific enough to catch the common failure of claiming completion without having done
every step.

- [ ] For each execution Task above: CONFIRM it was performed; cite the evidence (diff / `file:line` / artifact).
- [ ] Tests: PASTE the actual runner output (not a claim); confirm it matches the expected outcome.
- [ ] Docs / spec sync applied (or explicitly N/A with reason).
- [ ] Lifecycle + path-scoped commit done as specified (never `git add -A`/`-a`; never push).
- [ ] Any item that is incomplete / blocked / skipped / unverified is reported EXPLICITLY above; if so, STOP and report rather than transitioning the plan.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed.

Completion rule: before claiming done or transitioning this plan to `executed/`, EVERY
`- [ ]` item in the top `## Detailed Implementation Checklist (TODO)` MUST be `- [x]` AND its
matching `## Validation and cross-check` item MUST be verified with CONCRETE evidence (tests run
with the actual output pasted; never claim a pass not run). If any item cannot be completed,
STOP and report it explicitly rather than transitioning the plan. A checklist is a mitigation,
not a guarantee (a box can be ticked without the work), so the reviewer step and the
paste-actual-output rule still apply; an agent-asserted `executed` is a CLAIM, not proof.

Prefer SMALL plans (strong guidance, not an inflexible rule): prefer FIVE or fewer major steps;
avoid more than roughly TEN major steps or 12-18 total actionable checklist items in one IPD.
When work exceeds that scale, spans several code regions/files, mixes distinct concerns, or has
independently-executable phases, split it into an ordered `Set:`/`Order:` of small,
independently-executable and independently-verifiable plans instead of one large plan; when the
parts need coordination, add a `00` orchestrator IPD that defines the sequence, dependencies,
whole-Set completion criteria, and cross-IPD validation. State cross-chunk dependencies in each
chunk's execution contract ("requires `Order N` executed first; if its symbols are absent,
STOP"). This is good hygiene for any model and close to REQUIRED when the executing model is a
faster/weaker tier.

Recommended next steps:

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
