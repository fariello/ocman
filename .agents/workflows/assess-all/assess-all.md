# Workflow: assess-all (cross-concern rollup)

Run the assess family (all concerns, or a chosen group/subset) and produce ONE
prioritized, de-duplicated, cross-concern plan - instead of many separate IPDs the user
must reconcile by hand. This is the broad **propose-a-plan** review; `release-review` is
the broad **fix-in-place** review. Cross-reference them; do not duplicate.

## Single source of truth (no second concern registry)

The concerns are the `assess/lenses/*.md` files, cataloged by the `assess-<concern>`
manifest rows in `index.md`. This workflow ORCHESTRATES them; it does NOT define concerns.
Never invent a concern here that is not a lens. Groups are derived from the same catalog
that `/list-workflows` uses.

## Confirm scope and cost first (do not silently run everything)

Running all concerns is expensive (many deep passes). Before running anything:

1. Read the concern catalog from the manifest and present the concerns grouped by area
   (correctness, security/privacy, compliance, UX/docs, product/design [e.g., data-modeling], delivery/quality).
2. State plainly that a full run is many passes and will take a while.
3. Offer the choice and default to a sensible set (the core-quality group unless the user
   indicates otherwise):
   - `all` - every concern (explicit, expensive).
   - a **group** (e.g. `security`, `docs`, `delivery`) - the concerns in that area.
   - a **subset** - a named list of concerns.
   - the recommended default if the user just wants "the important ones".
4. `$ARGUMENTS`, if present, pre-selects the scope (`assess-all security`, `assess-all all`,
   `assess-all testing,security,prose`). Even then, confirm the resolved set and cost
   before running.

## Protocol

1. **Resolve the set** of concerns per the scope confirmation above.
2. **Run each concern** through the assess harness (`assess/assess.md` with each lens).
   Reuse the harness exactly; do not re-implement a concern's rubric here. Optionally cite
   `verify` evidence (`run_checks.py`) for the testing/build claims so the rollup rests on
   proof, not self-report.
3. **Synthesize** (this is the value this workflow adds over running lenses separately):
   - **De-duplicate:** the same underlying issue surfaced by multiple lenses becomes one
     finding, noting which concerns raised it.
   - **Resolve cross-concern priority:** rank by real severity and remediation risk across
     concerns, not per-lens. A Blocker security finding outranks a Low prose nit; a
     data-integrity/LIVE issue outranks a style preference. Use the Fix Bar
     (`release-review/fix-decision-policy.md`) for fix-vs-defer reasoning.
   - **Surface conflicts:** where two concerns pull in opposite directions (e.g. a
     performance change vs. a readability change), name the trade-off and recommend.
4. **Emit ONE consolidated IPD** into the project's pending plans directory (default
   `.agents/plans/pending/`): a single prioritized, cross-concern plan, with findings
   grouped by priority and each tagged with its originating concern(s). Set the IPD's
   front-matter `Status: to-review` and add ONE `## Workflow history` line that NAMES the
   concerns rolled up: `- <date> /assess-all (<agent/model>): rolled up <concerns>; proposed
   N changes` (a single consolidated IPD carries a single Status and one history line, not
   per-concern sub-entries).
5. **Write a rollup run record** under `workflow-artifacts/assess-all/<RUN_ID>/`:
   the consolidated report, the resolved scope and cost, and links to any per-concern run
   records produced along the way.
6. It does NOT change code and does NOT execute the plan (the assess contract). **Commit**
   the IPD and the rollup run record, and NEVER push (commit-only). Recommend `plan-review`
   before execution.
7. **Closing report.** End by presenting the shared closing report
   (`../assess/templates/closing-report.md`): the artifacts CREATED (the one consolidated IPD
   path + the rollup run-record path), or - if every concern was adequate and no consolidated
   IPD was warranted - that NONE was created and why, plus the next steps (`/plan-review` the
   IPD, then approve).

## Honesty and guardrails

- Confirm scope and cost before running; never silently run all concerns.
- The lenses are authoritative; this workflow only runs and synthesizes them.
- Be honest about coverage: if a concern was skipped (scope, cost, or could not be run),
  say so in the rollup - a partial rollup is not a full assessment.
- One consolidated IPD, cross-prioritized - not N disconnected ones. That consolidation is
  the point.

## Reminders

- Broad propose-a-plan review; `release-review` for broad fix-in-place.
- De-dupe and cross-prioritize; do not just concatenate per-lens findings.
- Confirm the expensive scope first.
