# Implementation Plan

## Run

- Run ID:
- Created:
- Based on sections completed:

## Scope summary

Describe the implementation scope selected from the audit findings.

## Explicit non-goals

List changes that should not be made in this run.

## Fix Bar

This plan applies the Fix Bar (`fix-decision-policy.md`): fix every finding by
default; defer only when the Remediation Risk of the fix itself is Medium-High or
higher (complexity / usability / security / functionality). Severity is for
reporting, not for deciding.

## Change batches

| Batch ID | Source finding IDs | Description | Files likely to change | Remediation Risk | Public behavior change | Required validation | Commit plan | Status |
|---|---|---|---|---|---|---|---|---|

## Mandatory `LIVE`/High data-integrity findings

Every `LIVE` or High live-surface/memory finding MUST be fixed in this run or
explicitly escalated to the user - never silently deferred to `TODO.md`.

| Finding ID | Title | Fix-in-run / escalate | Testable seam added | Regression test |
|---|---|---|---|---|
|  |  |  |  |  |

## Self-documenting and guiding-principles fixes

| Action ID | Source finding IDs | `U`/`GP` | Description (prefer in-product over docs) | Risk | Status |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## TODO / backlog dispositions in this run

| TODO ID | Item | Classification | Action this run (fix / reclassify / escalate) |
|---|---|---|---|
|  |  |  |  |

## Deferred findings

Deferral requires Medium-High or higher Remediation Risk; name the axis. Effort,
time, and cost are not valid reasons.

| Finding ID | Remediation Risk | Axis at risk (complexity/usability/security/functionality) | Reason deferred | Safe partial fix done? | Recommended next step |
|---|---|---|---|---|---|

## Blocked findings

| Finding ID | Blocker | What would unblock it |
|---|---|---|

## Wont-do findings

| Finding ID | Reason | Notes |
|---|---|---|

## Deprecated-code decisions

| Candidate ID | Decision | Evidence | Action |
|---|---|---|---|

## Schema validation decisions

| Schema ID | Decision | Rationale | Action |
|---|---|---|---|
|  |  |  |  |

## CI decisions

| CI ID | Decision | Rationale | Action |
|---|---|---|---|

## Validation plan

List commands and checks to run before and after each implementation batch.

## Commit plan

List planned local commits and the action IDs each commit should include.
