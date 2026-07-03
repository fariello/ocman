# 04 Documentation, Specifications, and Examples

## Context contract

- **Read:** `00-run-protocol.md`, `fix-decision-policy.md`, this file, `01-repository-inventory.md`, Sections 1-3 findings, the project's docs/README/help. Lead personas: complete novice, UI/UX.
- **Produce:** `D`/`A`/`U`/`KD`/`TODO` findings (with Remediation Risk); durable-knowledge assessment; updates to registers, `persona-review.md`, `todo-reconciliation.md`; per-phase report `section-summaries/04-docs-specs-examples.md`.
- **Done when:** the Exit gate at the bottom of this file is satisfied.

## Purpose

Review documentation, specifications, examples, README content, help text, and navigation for accuracy, completeness, consistency, and usefulness. Documentation and specifications must reflect actual current behavior, not hoped-for or planned behavior.

This section is an audit pass. Documentation fixes happen in Section 7.

## Standing constraints for this section

- Preserve public behavior unless a change is clearly justified.
- Do not make speculative changes.
- Do not create broad refactors or formatting churn.
- Use run-specific unique IDs for every finding and action.
- Update the finding and action registers before leaving this section.
- Use TodoWrite if available, but treat `workflow-artifacts/release-review/<RUN_ID>/` as authoritative.
- Mark non-applicable checks explicitly rather than forcing findings.
- Prefer meaningful fixes, not checklist compliance.


## Required inputs

Read the repository inventory, findings from Sections 1 through 3, README, docs, API/CLI/schema/configuration/architecture/deployment/operational docs, examples, changelog, release notes, and help text if available.

## Allowed actions

Allowed: inspect documentation and examples, run non-destructive examples if safe, compare documented behavior against implementation and tests, record findings and candidate actions.

Not allowed: editing docs/examples, changing public behavior to match docs, or removing docs/examples.

## Review checks

Review README, user guides, API docs, CLI docs, architecture docs, configuration docs, schemas, specifications, operational docs, examples, installation/build instructions, packaging/release notes, known limitations, migration notes, and Markdown navigation bars.

Check for outdated claims, missing setup or usage steps, broken examples, terminology inconsistencies, missing limitations or assumptions, missing configuration/security/privacy/operational notes, implementation/docs/spec mismatches, confusing onboarding areas, undocumented implemented behavior, documented unimplemented behavior, partially implemented behavior not labeled clearly, and docs/examples referencing deprecated or obsolete artifacts.

### Self-documenting / learn-as-you-go bar (mandatory)

Lead this section with the complete-novice persona and the UI/UX persona (see the persona-to-section map in `00-run-protocol.md`); append at least one observation per lead persona to `persona-review.md`, or note "no new finding from persona X". The release goal is that a user can learn the project as they go without reading a manual or taking a course. File `U`-type findings (and, where the project should teach the user in-product rather than in a separate doc, note it for Section 7) for:

- Commands, flags, fields, or options whose names do not reveal their purpose.
- Missing or unhelpful `--help`/usage output, missing first-run guidance, or no obvious "what do I do next".
- Errors that are silent, cryptic, or do not tell the user how to recover.
- Undefined jargon or assumed domain knowledge in the UI, CLI, prompts, or error text.
- Non-obvious required steps and confusing defaults.

Distinguish fixes that belong in the product itself (better help text, clearer errors, better defaults, inline hints - handled in Section 7) from fixes that belong in documentation. Prefer making the product self-explanatory over adding more documentation to compensate for it.

### TODO.md and backlog reconciliation in docs

Reconcile `TODO.md`/`BACKLOG.md`/`ROADMAP.md`/`KNOWN_ISSUES.md` against the documentation: are documented features actually implemented, are known limitations documented, and do TODO items contradict what the docs claim? Feed discrepancies into `todo-reconciliation.md` and file `D`/`TODO` findings.

### Durable project knowledge and cold-start orientation (mandatory; type `KD`)

Per the durable-knowledge objective in `00-run-protocol.md`, assess whether a no-context engineer or LLM could orient from the project's own tracked docs. Cover the four knowledge areas and, where one is missing or inadequate, file a `KD` finding to establish or improve it (creating the doc is normally low Remediation Risk, so it is done by default in Section 7; respect the project's existing convention rather than imposing new filenames):

1. **Intent, goals, objectives, audience, scope/non-goals** - usually the top of `README.md` or an `OVERVIEW.md`.
2. **Philosophy / guiding principles** - `GUIDING_PRINCIPLES.md` or equivalent (establishment owned by Section 5).
3. **Architecture and approach** - `ARCHITECTURE.md`/`DESIGN.md`/`docs/architecture/`: components, how they fit, the approach and why that shape.
4. **Design / architectural decision rationale** - a decisions log (`DECISIONS.md`, an ADR directory, `METHODS/`, or equivalent): significant decisions, the *why*, alternatives considered, and trade-offs.

When authoring or improving these, recover intent from the current conversation as a **guarded secondary source** per `00-run-protocol.md`: code/tests/existing-docs are authoritative for behavior; conversation is evidence for intent and rationale only; verify material claims with the user or record them as assumptions in `05-decisions.md` and mark passages "inferred, needs confirmation"; degrade gracefully if no history exists. This is an audit pass - record `KD` findings here and make the actual edits in Section 7.

If the repository already maintains a decisions log, also confirm that recent changes to behavior, parameters, tooling, data formats, or methodology have corresponding dated entries and that reader-facing docs reflect them; file `D`/`A` findings for gaps.

## Required outputs

Update the registers, decisions, commands, checkpoints, `persona-review.md`, `todo-reconciliation.md`, and deprecation candidates if stale docs/examples reveal obsolete artifacts.

Create the per-phase report `section-summaries/04-docs-specs-examples.md` (what was done, why, what was considered but not done) covering documentation health, specification health, self-documenting / learn-as-you-go assessment, major inaccuracies, missing or weak docs, examples needing correction, accurate docs, required pre-release updates, stale or misleading docs/examples, and recommended updates grouped by priority.

Use `D` for documentation/examples, `A` for artifact sync issues, `U` for self-documenting/learn-as-you-go gaps, `TODO` for backlog/doc discrepancies, and `DEP` for stale/deprecated docs or example candidates.

## TodoWrite guidance

If TodoWrite is available, track documentation/spec/example review at a high level.

## Judgment guidance

Favor accuracy over polish. A short accurate README is better than a long aspirational one. Do not add planned features to docs unless clearly labeled as future work or out of scope.

## Non-applicable guidance

If there are few or no docs, record that fact and assess whether the absence matters for the repository type and release intent.

## Exit gate

Do not proceed to Section 5 until all are true (MUST):

- [ ] Documentation/spec/example accuracy assessed; material gaps and inconsistencies recorded with Remediation Risk.
- [ ] Self-documenting / learn-as-you-go bar applied; `U` findings filed for manual-required tasks.
- [ ] Durable-knowledge (`KD`) assessment done for intent/architecture/decision-rationale docs (respecting existing convention); gaps filed.
- [ ] Doc-vs-backlog discrepancies reconciled into `todo-reconciliation.md`.
- [ ] One observation per lead persona appended to `persona-review.md`.
- [ ] Per-phase report written; checkpoint recorded and committed.
