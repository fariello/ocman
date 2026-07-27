# IPD (ORCHESTRATOR): <short title of the coordinated change>

- Date: <YYYY-MM-DD>
- Concern: <the shared concern the child IPDs address>
- Scope: ORCHESTRATOR for the ordered Set `<set-id>`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It does NOT itself change files (each child does its own edits).
- Status: to-review
- Set: <set-id>
- Order: 0
- Author: <agent/model if known>

<!--
Use a `00` orchestrator when a change is too large for one IPD (see the size guidance in
`ipd.md` / the ipd-spec: prefer <=5 steps; avoid >~10 steps or 12-18 items) OR has
independently-executable phases that need coordination. The orchestrator itself makes no
file edits; it sequences and validates the children. `NN=00` is reserved for it; children are
`01+`, sharing this file's timestamp and `Set:` id.
-->

## Workflow history

- <YYYY-MM-DD> created (<agent/model>): why this work is an orchestrated Set rather than one IPD.

## Goal

What the whole Set accomplishes and why it is split; one or two sentences.

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `<...-01-...>.md` | <bounded, single-concern change> | none |
| 02 | `<...-02-...>.md` | <...> | 01 |
| 03 | `<...-03-...>.md` | <...> | 01, 02 |

## Completion criteria (the whole Set is done only when)

- <each child executed + its own two checklists verified with evidence>
- <cross-IPD validation below passes>
- <suite green after each child and at the end; leak-clean; no em/en dashes>

## Cross-IPD validation

- Consistency: <the shared concepts/names/rules match across children; read them together and confirm no contradiction>.
- No duplication/drift: <children supersede/update prior decisions in place rather than forking>.
- Dependency correctness: <each child's declared prereq is real; a child does not use a later child's symbols>.
- Size check: <each child stays within the size guidance>.

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
|      |      |        |           |

## Scope check

- Over-scope: none - this orchestrator only coordinates; the children make the bounded edits.
- Under-scope: <what the Set as a whole MUST deliver, kept consistent by the cross-IPD validation>.

## Required tests / validation

How the whole Set is verified (per-child validation + the cross-IPD checks above). Run the suite after each child and at the end; paste ACTUAL output; leak-clean; no em/en dashes.

## Open questions

<Anything needing a human decision about the sequence/scope of the Set.>

## Detailed Implementation Checklist (TODO)

The orchestrator's "actions" are gating the children and running the cross-IPD checks.

- [ ] **Child 01 executed** and its own checklists verified.
- [ ] **Child 02 executed** (after its deps) and verified.
- [ ] **Child 03 executed** (after its deps) and verified.
- [ ] **Cross-IPD validation run** (consistency / no-drift / dependency correctness / size).
- [ ] **Suite green** after the last child (paste actual output); leak-clean; no em/en dashes.

## Validation and cross-check (verify before reporting the Set complete)

Each item maps to a checklist item above; provide concrete evidence.

- [ ] Each child is in `.agents/plans/executed/` with `Status: executed` and its own Validation checklist verified; cite each.
- [ ] Cross-IPD validation performed: quote the shared rule from each child and confirm they match; confirm dependencies were respected in execution order.
- [ ] Paste the actual final `pytest` summary line; confirm leak-clean and no em/en dashes.
- [ ] Report any child that is incomplete/blocked/unverified EXPLICITLY; do NOT mark the Set complete otherwise.

## Approval and execution gate

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark the orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload.
