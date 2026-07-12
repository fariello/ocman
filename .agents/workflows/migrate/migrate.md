# Workflow: migrate (assess-and-plan a high-risk change)

Plan a migration - framework X to Y, database v1 to v2, a dependency major bump, a layout
or API change - as a staged, reversible plan grounded in the blast radius and the
invariants that must survive. It follows the assess pipeline: it produces an
Implementation Plan Document (IPD), it does NOT execute the migration.

The framework's own legacy-layout migration (see DECISIONS D17/D19, handled by the
installer) is a concrete example of this shape: inventory what exists, define what must
still hold afterward, move in reversible steps, verify at each.

## What it produces (and does not)

- Produces: a dated IPD in the project's pending plans directory (default
  `.agents/plans/pending/`), through the normal IPD -> plan-review -> approve -> execute
  pipeline.
- Does NOT: change code, run the migration, or move the IPD out of pending. Investigating
  and writing the plan (and its run record) is not "executing".

## Protocol

1. **Scope the migration.** From `$ARGUMENTS` and the user: what is migrating from what to
   what, and why now. Restate it and confirm.
2. **Inventory the blast radius.** Find everything the change touches: call sites, schemas,
   configs, serialized data, public contracts, docs, tests, CI, dependents. Be concrete
   and evidence-based (cite files); do not hand-wave "it is used widely".
3. **Name the invariants.** What MUST remain true across the migration: data integrity,
   public behavior/contracts, backward compatibility windows, security properties,
   performance floors. These are the acceptance criteria for the migration.
4. **Design a staged, reversible plan:**
   - **Characterization tests first:** pin current behavior before changing it, so drift is
     detectable (cross-reference assess-testing).
   - **Small, independently shippable stages,** each with a rollback and a verification
     step (cite `verify` / `run_checks.py` for the checks that must pass per stage).
   - **Expand/contract where relevant** (add new alongside old, migrate, then remove) to
     avoid a big-bang cutover.
   - **Data migrations:** dry-run, backup, and reversibility explicitly addressed.
5. **Risk and rollback:** the highest-risk stages, the point of no return (if any, flag it
   loudly), and the rollback for each stage.
6. **Write the IPD** with the structure below and place it in pending/. Set its front-matter
   `Status: to-review` (or `draft` if deliberately a stub) and add a `## Workflow history`
   line (`- <date> /migrate (<agent/model>): assessed migration; emitted IPD`). **Commit**
   the IPD and NEVER push (commit-only). Recommend `plan-review` before execution given the
   risk.

## Migration IPD structure

- **Goal / from -> to and why.**
- **Blast radius** (inventoried, with file references).
- **Invariants that must survive** (the acceptance criteria).
- **Staged plan:** each stage with its change, its verification, and its rollback.
- **Characterization tests** to add before starting.
- **Risks, point-of-no-return, and rollback strategy.**
- **Validation:** the `verify` checks that must pass at each stage and at the end.

## Guardrails

- Plan only; never execute the migration or change code here.
- Reversibility and staging are the point; a big-bang, irreversible plan is a finding
  against itself - flag it and prefer expand/contract.
- Ground the blast radius in the actual repository; cite files. Do not assume.
- High-risk by nature: recommend plan-review, and make the point-of-no-return explicit.
