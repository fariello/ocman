# Step 1: Discover, ground, and snapshot

## Purpose

Establish review scope, project rules, evidence, and the pre-review plan state.

## 1. Build the scope ledger

List every requested candidate plan and mark it:

- `ELIGIBLE` - review it.
- `NOT REVIEWED` - skip it and record the exact reason.

Use project eligibility and status rules when they exist. Otherwise review an
explicitly requested plan unless it is missing, unreadable, malformed beyond
review, or not a planning document.

A plan cited only as evidence is not in scope unless explicitly added.

## 2. Discover controlling rules

Read the applicable hierarchy:

1. Repository and nested agent instructions.
2. Guiding principles.
3. Contributor and workflow rules.
4. Plan templates, lifecycle, and status rules.
5. Specification and traceability obligations.
6. Target plans and referenced decisions.

Do not assume filenames. Use project precedence rules. If a conflict remains,
record an open question and do not silently choose.

Discover:

- plan location, format, front matter, status, approval, history, and commits;
- project type, stack, production runtime/data store, deployment, integrations,
  tenancy, security model, and tests;
- domain invariants from authoritative specs, principles, ADRs, code, tests,
  constraints, and confirmed conversation context.

If behavior, policy, workflow, API, authorization, state, or domain rules
change, require specification or documentation synchronization.

If no principles exist, use the fallback principles from the release-review
protocol and record that choice.

## 3. Ground every eligible plan

For each plan:

1. Read it fully.
2. List its material files, requirements, issues, ADRs, APIs, schemas, tests,
   and behavior claims.
3. Open the actual evidence.
4. Verify material claims with `path:line` citations.
5. Record missing, stale, contradictory, or inaccessible evidence.
6. Do not infer unsupported implementation details.

Create a finding when missing evidence prevents a reliable plan. Create an
open question when human input is required.

## 4. Pre-review snapshot

Before editing:

1. Inspect Git status.
2. Select only eligible plan files.
3. If a target plan is untracked or modified, commit it verbatim as:

   `plan: pre-review snapshot of <scope>`

4. Skip when every target plan is committed and unchanged.
5. Never include unrelated files.
6. Never amend, reset, rebase, discard user changes, or push.

If Git is unavailable or a safe commit cannot be made, continue when safe and
record the reason.

## Exit gate

Do not proceed until:

- [ ] Every requested candidate is in the scope ledger.
- [ ] Project rules and precedence are understood or conflicts are open.
- [ ] Plan contract, production context, and domain invariants are recorded.
- [ ] Material plan claims are grounded in repository evidence.
- [ ] Documentation/specification impact is identified.
- [ ] Pre-review snapshot is committed, skipped, or explained.
