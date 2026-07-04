# 00 Run Protocol

This file defines the global rules for the release review. These rules apply to all sections.

## Authority model

1. `README.md` is the controlling instruction.
2. This file defines shared rules.
3. Section files `01` through `09` define phase-specific tasks (`09` runs only after a GO/CONDITIONAL GO and explicit user approval to release).
3a. `fix-decision-policy.md` is the authoritative fix policy. `reference.md` holds on-demand look-up tables (type codes, ID examples, schema/CI lists) and is not part of the always-read core.
4. `workflow-artifacts/release-review/<RUN_ID>/` is the authoritative run record.
5. TodoWrite, if available, is live progress tracking only.

If a section file appears to conflict with this protocol, follow this protocol and record the conflict in `05-decisions.md`.

## Review scope exclusions (what NOT to review)

The review operates on the **target project**. The framework's own files and its run records are NOT part of the project under review. Unless the user explicitly states that the framework itself is the subject of this review, exclude the following from the audit scope of every section (and every parallel audit lane):

- **This framework's own directory** (wherever it is installed - e.g. `.agents/workflows/release-review/` and the sibling `plan-review/`, or a `release-review/` directory at the repo root) and any agent-tooling wrappers it ships (`.opencode/commands/`, `.claude/commands/`, `.agents/workflows/index.md`). Do not file findings about the runbook, do not assess it for quality/docs/usability, and do not modify it as part of fixing the target project. You are *executing* these instructions, not reviewing or editing them.
- **`workflow-artifacts/`** - the authoritative run records (this run and any prior runs). Do not audit them as if they were project code or docs.

This is an exclusion from *review scope*, not from all action:

1. You still **create, write, and commit** `workflow-artifacts/release-review/<RUN_ID>/` - that is the run's own output, not a review target.
2. You **may read** prior `workflow-artifacts/release-review/<RUN_ID>/` records as input (e.g. to see what an earlier run did), but do not generate findings about them.
3. Do not count these directories when assessing project size, structure, test coverage, documentation, or cold-start orientation. A project's `README`, `ARCHITECTURE`, tests, etc. are the project's own, not the framework's.
4. **Self-modification guard:** never edit the framework's own files during a run. If the runbook itself seems wrong, record it as a `Q`/`DEC` note in `05-decisions.md` for the user; do not change the instructions mid-run.

**Explicit-subject exception:** if the user explicitly asks to review the framework itself (for example, when the target repository *is* the project that maintains this runbook), then the framework directory is in scope as ordinary project code and these exclusions are lifted for it - but `workflow-artifacts/` run records remain excluded regardless.

When in doubt, treat both directories as out of scope and note the assumption in `05-decisions.md`.

## Execution model (read this before starting)

This runbook is large. The following rules keep it executable reliably on any modern coding agent, including faster or smaller models that tend to silently drop low-salience instructions on long runs.

### Obligation tiers: MUST vs SHOULD

Every obligation in this framework is one of two tiers:

- **MUST** - mandatory. Skipping a MUST is a defect in the run. If you cannot complete a MUST, stop and record a blocker; do not proceed past it silently.
- **SHOULD** - expected, and done by default, but it carries *depth* rather than *existence*. Under time, capability, or scope pressure, a SHOULD may be done more briefly, but it must still be attempted and the reduction noted.

When a section uses the words MUST or SHOULD (or "mandatory"), read them in this sense. The MUST set is small on purpose so it is never dropped; the global MUSTs are:

1. Create and maintain the `workflow-artifacts/release-review/<RUN_ID>/` artifacts (registers, decisions, the per-phase report for each section).
2. Apply the Fix Bar to every finding and record Remediation Risk; never silently drop a finding.
3. Fix or explicitly escalate every `LIVE`/High data-integrity finding (never silently defer to `TODO.md`).
4. Write the per-section exit-gate items before leaving a section.
5. Produce the final report per `templates/final-response.md`, and never push/publish/deploy without explicit permission.

Everything else (persona depth, the richness of cold-start `KD` docs, optional CI additions, nice-to-have fixes) is SHOULD: do it well by default, scale depth honestly under pressure, and record what was scaled back.

### Context-assembly ordering (use the model's attention deliberately)

Models attend most to the end of the context window, next-most to the beginning, and least to the middle. Assemble each phase's working context to exploit that:

- **Front (highest attention):** the small MUST set above, the Fix Bar one-line rule, and the current section's context contract (its "read these / produce these / done when").
- **Middle (tolerated decay):** bulky look-up material (`reference.md`) and the prior registers/artifacts you are consulting. These are reference data; they need to be present, not maximally salient.
- **End (highest attention):** the current section file and its exit-gate checklist - the thing you must execute right now.

In practice: when you start a section, (re-)read its section file and exit gate last, so they are freshest, after you have loaded the rules at the front and any reference/registers in between.

### Model-capability expectation

On a high-capability model, perform the full depth of every SHOULD (rich persona reasoning, deep cold-start `KD` docs, thorough architecture rationale). On a fast or small model, the MUST set is still fully required; SHOULD depth is best-effort - do as much as the model can do well, and record in the per-phase report where depth was reduced and why, so a later higher-capability run (or a human) can deepen it. Do not fake depth; an honest "assessed briefly, needs deeper pass" is better than a hollow analysis.

### Phase-isolated execution mode (optional)

Because `workflow-artifacts/release-review/<RUN_ID>/` is the authoritative state, each audit phase can run with its own fresh context instead of one long continuous transcript. This is optional and useful on fast/small models or very large repositories, where a long transcript degrades.

If running phase-isolated:

1. Each phase reads `00-run-protocol.md`, `fix-decision-policy.md`, its own section file, and the prior registers/artifacts it needs from the run directory; it does its work, writes its artifacts and per-phase report, commits, and ends.
2. The run directory carries all state between phases. Do not rely on conversational memory of a prior phase.
3. **Keep Sections 7 and 8 continuous with each other.** Implementation and final review share the same evidence (the changes just made); splitting them loses grounding that registers cannot restore.
4. Because a re-loaded register is a summary, not the lived reading of the code, Section 7 MUST re-open the actual source files cited by High/`LIVE`/`MEM` findings rather than trusting the register text (see `07-implementation.md`).

If running as one continuous pass (the default for "read and execute README.md"), the same ordering and re-grounding rules still apply; you simply keep all phases in one transcript.

## Review mindset: the eight reviewer personas

This review is not a checklist pass. Every audit section (Sections 1 through 6) and the final review (Section 8) must be conducted while deliberately adopting, in turn, each of the following eight expert personas. The goal is breadth of perspective: a finding obvious to one persona is often invisible to another. Do not merely name the personas; actually reason from each viewpoint and let each surface findings the others would miss.

| # | Persona | Looks for |
|---|---|---|
| 1 | **QA / QC engineer** | Defects, broken behavior, incorrect output, flaky paths, things that "work on the happy path only", missing validation, anything that would fail acceptance. |
| 2 | **Testing & regression-testing expert** | Missing/weak tests, untested critical paths, regression exposure, brittle or misleading tests, missing fixtures/golden files, no protection for recently changed behavior. |
| 3 | **UI / UX expert engineer** | Confusing flows, poor defaults, unclear errors, inconsistent terminology, accessibility gaps, friction, anything that needs a manual to understand, anything that violates "learn as you go". |
| 4 | **Systems & software architect** | Abstraction quality, extensibility, separation of concerns, elegant vs. accidental complexity, future-proofing without bloat, the general case vs. hardcoded special cases, coupling, configurability. |
| 5 | **Software engineer** | Code correctness, readability, maintainability, memory/resource handling, error propagation, dead code, dependency hygiene, idiomatic use of the language/framework. |
| 6 | **Sophisticated power user** | Missing advanced capabilities, ergonomics, scriptability/automation, escape hatches, performance at scale, whether the tool respects expert expectations. |
| 7 | **Complete novice / naive user** | First-run confusion, undefined jargon, missing onboarding, unclear next step, anything that assumes domain knowledge the user does not have, anything requiring "reading the manual" or a course. |
| 8 | **Stakeholder** | Whether the project actually achieves its intended goals/outcomes, fitness for purpose, risk to the mission, reputational/compliance/business risk, value delivered vs. promised. |

When recording a finding, note which persona(s) surfaced it when it adds clarity. A finding raised by the novice or stakeholder persona is as legitimate as one from the QA or security perspective.

### How personas map to sections (so the pass is real, not a token gesture)

You do not have to write eight separate persona analyses in every section. Instead, each section has 2-3 **lead personas** that own it; reason primarily from those, and let the others contribute only when they surface something the leads miss. This concentrates the work where each viewpoint pays off and makes it verifiable.

| Section | Lead personas |
|---|---|
| 2 Quality/security/edge cases | QA/QC (1), software engineer (5), and the security-minded lens within architect (4) |
| 3 Tests/regression | Testing & regression expert (2), QA/QC (1) |
| 4 Docs/specs/examples | Complete novice (7), UI/UX (3) |
| 5 Feature/usability/maintainability | All eight, led by novice (7), power user (6), UI/UX (3), architect (4), stakeholder (8) |
| 6 Compatibility/packaging/release | Operator/stakeholder view (8), software engineer (5) |
| 8 Final ship review | All eight; produce the explicit per-persona sign-off |

**Forcing function:** in each of Sections 2 through 6, append at least one concrete observation per lead persona to `persona-review.md` (or explicitly note "no new finding from persona X in this section"). Section 5 exercises all eight at least briefly. Section 8 produces the full eight-persona sign-off. This makes the persona pass checkable without requiring eight redundant analyses in every section.

## Guiding principles adherence

If the repository contains a guiding-principles document (`GUIDING_PRINCIPLES.md`, `PRINCIPLES.md`, `.agents/GUIDING_PRINCIPLES.md`, a "Principles" section in `README.md`/`CONTRIBUTING.md`, or an equivalent named in `AGENTS.md`), treat it as a binding contract for this review:

1. Discover and read it during Section 1; record its location and a summary in `01-repository-inventory.md`.
2. In every audit section, check the project against each stated principle and file findings for violations (type `GP`).
3. In Section 7, prefer fixes that move the project toward its principles; do not implement changes that violate them.
4. In Section 8, include a per-principle adherence assessment.

If no such document exists, fall back to these universal release principles and record that you did so:

- **Intuitive and self-documenting.** A user should be able to "learn as they go" without reading a manual or taking a course. Naming, defaults, help text, error messages, and first-run behavior should teach the user what to do next.
- **Solve for the general case, configurable over hardcoded.** Avoid special-casing and magic constants where configuration or abstraction is the cleaner answer, without adding speculative features.
- **KISS.** Prefer the simplest design that meets the need; avoid bloat and accidental complexity.
- **Honest documentation.** Docs describe what the software actually does today, not what is hoped for.

## Self-documenting / learn-as-you-go bar

A core release goal of this review is that the released project is **as intuitive and self-documenting as reasonably possible**, so users can learn it as they go. Throughout the review, actively hunt for and record (type `U`) anything that forces a user to read external documentation, attend training, or already possess domain knowledge in order to accomplish a basic task: unclear command/flag/field names, silent or cryptic errors, missing `--help`/usage output, missing first-run guidance, undefined jargon in the UI or CLI, non-obvious required steps, and confusing defaults. Where the fix is safe and in scope, implement it in Section 7 (clearer help text, better error messages, sensible defaults, inline hints), not merely document it.

## Durable project knowledge and LLM cold-start orientation

A first-class goal of this review is that **a competent engineer or an LLM with zero prior context can pick up the project and understand it from the project's own tracked documentation** - not from this review's run record. They should be able to learn the project's intent, goals, objectives, philosophy/principles, architecture and approach, and the rationale behind significant design and architectural decisions (including alternatives considered and trade-offs made).

This is distinct from the self-documenting / learn-as-you-go bar: that bar is about *using* the software (help text, errors, defaults). This is about *understanding* the project (why it exists, how it is built, why it is built that way) for maintenance, extension, and handoff.

Treat this as a constructive objective, not merely an audit. Under the Fix Bar, **creating a missing orientation document is normally a low-Remediation-Risk action and is therefore done by default**, not deferred. Use ID type `KD` for knowledge/handoff-documentation findings.

The target knowledge set (adapt names to the project's existing convention):

| Knowledge | Typical home | What it must convey |
|---|---|---|
| Intent, goals, objectives, audience | `README.md` top section or `docs/OVERVIEW.md` | Why the project exists, who it serves, what success looks like, scope and non-goals. |
| Philosophy / guiding principles | `GUIDING_PRINCIPLES.md` (or equivalent) | The values and design philosophy the project commits to. Establish this if absent (see Section 5). |
| Architecture and approach | `ARCHITECTURE.md` / `DESIGN.md` / `docs/architecture/` | How the system is structured, the main components and how they fit, the approach taken and why that shape. |
| Design / architectural decision rationale | `DECISIONS.md`, an ADR directory (`docs/adr/`, `.agents/decisions/`), or equivalent | Significant decisions, the *why*, alternatives considered, and trade-offs. Append-only and dated where practical. |

**Respect the project's existing convention.** If the project already keeps this knowledge somewhere (ADRs, a `docs/` tree, a wiki pointer, a `METHODS/` directory, design docs), detect it and extend/correct that rather than imposing new files. Only introduce a new file when the knowledge has no existing home. Do not duplicate the same rationale in multiple places; link instead.

Discovery happens in Section 1, the substantive assessment and any establishment of missing docs in Sections 4 and 5, creation/updates in Section 7, and the cold-start orientation verdict in Section 8.

### Recovering intent: use the conversation, but as a guarded secondary source

The richest source of a project's *intent and "why"* is often not in the repository at all - it is in the current conversation, where the user explained goals, constraints, the philosophy, and what was tried and rejected. When authoring or improving orientation docs (intent, goals, rationale, alternatives considered, trade-offs), mine the current chat/session history for that intent, especially when these docs are being created for the first time.

Guardrails (these are not optional):

1. **Code, tests, and existing docs are authoritative for behavior.** Conversation is evidence for *intent and rationale only*. If the conversation conflicts with what the code does, the code wins for behavior, and the discrepancy becomes a finding (the chat may describe a goal the code does not yet meet).
2. **Verify material claims before committing them as durable documentation.** Confirm with the user, or record them as explicit assumptions in `05-decisions.md` and mark the doc passage as "inferred, needs confirmation".
3. **Degrade gracefully.** History may be absent (first message, a fresh session, or a non-interactive runner such as another IDE). Do not assume it exists. If there is no usable history, proceed from the repository and the user, and record in `05-decisions.md` that conversation context was unavailable.
4. **Do not commit sensitive or ephemeral content.** Capture durable conclusions (intent, decisions, rationale), never raw transcript, credentials, or off-topic discussion.

### Asking for missing intent (bounded exception to autonomous operation)

If intent or decision rationale is genuinely missing and cannot be recovered from the repo or the conversation, this is one of the few times it is right to pause and ask the user. Capturing the true "why" is high-value and usually irreplaceable later. Ask a small number (roughly 3 to 7) of high-value, specific questions about intent, goals, audience, and the reasoning behind major decisions; record the answers in `05-decisions.md` and reflect them in the orientation docs. If the user does not answer (or the run is non-interactive), do not block the run: write a best-effort draft clearly labeled "inferred, needs confirmation", list the open questions in the final report, and continue. This is the only documentation task for which a brief, bounded pause to ask is preferred over silent inference.

## TODO.md and tracked-backlog reconciliation

Many repositories carry a `TODO.md` (or equivalent: `TODO`, `TODOS.md`, `BACKLOG.md`, `ROADMAP.md`, `KNOWN_ISSUES.md`, `.agents/TODO.md`, issue-tracker exports, or `TODO`/`FIXME`/`HACK`/`XXX` markers in code). These often contain items that should - or might need to - be addressed before a release. This review must not ignore them.

1. **Discover** all such backlog sources in Section 1 and inventory them in `01-repository-inventory.md`.
2. **Triage** every TODO-like item against this release. For each, classify it as:
   - `must-before-release` - a release blocker or a known defect/risk that should not ship.
   - `should-before-release` - worth doing now if safe and in scope.
   - `out-of-scope-for-release` - legitimately deferred; leave it tracked.
   - `stale/obsolete` - already done, no longer relevant, or contradicted by current code (deprecation candidate).
3. **File findings** (type `TODO`) for any `must-` or `should-` items and feed them into Section 7 selection like any other finding.
4. **Update `TODO.md` itself** in Section 7 when items are completed, become obsolete, or change status - keep it honest. Do **not** use `TODO.md` as a dumping ground to silently defer High-severity findings discovered in this review (see Section 7 non-deferral rule).
5. Record the full triage in `todo-reconciliation.md` and summarize it in the Section 8 report.

## Pending agent plans and staged prompts (release blocker signal)

Repositories driven by agent workflows often accumulate **planned-but-not-executed work**: implementation plans / IPDs awaiting approval or execution, and staged prompt files queued to be run. These are distinct from `TODO.md` backlog items - they are concrete, often-approved units of work that were prepared and then left un-actioned. Shipping while such plans sit pending frequently means releasing with known, already-planned work deliberately or accidentally skipped. This review must surface them **loudly**, not silently.

1. **Discover** in Section 1 and inventory in `01-repository-inventory.md`. Common locations (check those that exist, do not invent):
   - `.agents/plans/pending/` (and any sibling `pending/`-style plan staging dir); IPDs anywhere clearly marked pending/awaiting-approval/not-executed by their `Status:` line.
   - `prompts/`, `.agents/prompts/`, or a similar staging directory holding prompt files queued for execution.
   - Plans in a `done/`/executed dir whose `Status:` still says pending, or vice versa (a status/location mismatch).
2. **Do not execute them.** Discovering a pending plan or staged prompt never authorizes running it during the review.
3. **Classify** each pending plan/prompt against this release: is it work that was expected to ship in this release (a blocker signal), legitimately deferred to a later release, or stale/superseded?
4. **Surface loudly.** Any pending plan or staged prompt that is not clearly out-of-scope for this release is a WARNING that must appear prominently in the Section 8 Go/No-Go and summary (see `08-final-ship-review.md`). Pending in-scope plans push the recommendation off a clean GO toward CONDITIONAL GO with the pending items named as prerequisites/decisions.
5. Record the inventory and per-item classification and reflect it in the Section 8 report.

## Where cross-cutting concerns are performed (ownership map)

Several concerns span the whole review. To avoid both omission and pointless repetition, each has a defined owner section for the substantive work; other sections only contribute incremental findings. Do the substantive work once, in the owner section, and reference it elsewhere.

| Cross-cutting concern | Discover | Substantive pass (owner) | Apply / finalize |
|---|---|---|---|
| Guiding principles | Section 1 (locate + summarize) | Section 5 (per-principle adherence) | Section 7 (fix toward), Section 8 (final verdict) |
| TODO.md / backlog triage | Section 1 (inventory sources) | Section 5 (full triage in `todo-reconciliation.md`), with in-code `TODO`/`FIXME` captured in Section 2 | Section 7 (fix + update `TODO.md`), Section 8 (confirm) |
| Pending agent plans / staged prompts | Section 1 (inventory pending IPDs, staged prompts, status/location mismatches) | Section 1 (classify against this release) | Section 8 (loud WARNING in Go/No-Go + summary; blocks a clean GO if in-scope) |
| Self-documenting / learn-as-you-go | - | Sections 4 (docs side) and 5 (behavior side) | Section 7 (fix in-product), Section 8 (assess) |
| Durable project knowledge / cold-start orientation (`KD`) | Section 1 (locate existing convention) | Sections 4 (intent/architecture/decision docs) and 5 (principles, orientation) | Section 7 (create/update by default), Section 8 (cold-start verdict) |
| Eight personas | - | Sections 2-6 lead-persona notes; Section 5 all eight | Section 8 (full sign-off) |
| Memory / live-interaction surface | - | Section 2 | Section 3 (tests), Section 7 (fix), Section 8 (gate) |
| Schema validation | Section 1 (locate) | Section 6 | Section 7 (fix), Section 8 (final check) |
| Deprecated-code | ongoing | recorded in `deprecation-candidates.md` as found | Section 7 (act) |

If a concern is genuinely not applicable, the owner section records that once; downstream sections do not re-litigate it.

## Mandatory per-phase reports

Each section (Sections 1 through 9) must produce a per-phase report saved under:

```text
workflow-artifacts/release-review/<RUN_ID>/section-summaries/<NN>-<short-name>.md
```

Use `templates/per-phase-report.md`. Every per-phase report must explicitly cover three things:

1. **What I did** in this phase (concrete inspections, commands, edits, decisions).
2. **Why** I did it (the reasoning, the risk being mitigated, the principle/persona driving it).
3. **What I considered but did NOT do**, and the explicit reason (out of scope, too risky, no evidence, deferred, needs human decision). This third part is mandatory and is as important as the first two.

These reports are part of the deliverable. They give the user a readable, auditable narrative of the review independent of the CSV registers.

## Commit-between-phases policy

In addition to committing meaningful tracked product changes (see Commit policy below), commit at every section boundary so the run is recoverable and the per-phase narrative is preserved:

1. After completing each section, commit that section's tracked product changes (if any) as a coherent unit referencing the section's action IDs.
2. Commit the section's per-phase report and updated registers at the boundary too, since run artifacts are committed deliverables by default. Keep them local only if the user explicitly requested local-only artifacts for this run.
3. Never bundle changes from two different sections into one commit unless they are genuinely one logical change.
4. Record each commit in `07-commits.md` and at the section checkpoint in `08-checkpoints.md`.

## Core behavior

Proceed autonomously through the full review unless invoked through a planning-only command. In planning-only mode, complete Sections 1 through 6, create `implementation-plan.md`, and stop before Section 7 implementation.

Section 9 (release execution: pushing, tagging, publishing, deploying) is performed only after Section 8 produces a GO or CONDITIONAL GO and the user has explicitly approved release execution. Do not run Section 9 automatically.

There are two distinct plan artifacts; do not conflate them. `02-execution-plan.md` is the lightweight plan of *how the review itself will run*, created early in Section 1. `implementation-plan.md` is the consolidated plan of *what fixes to make*, created after Sections 1 through 6 and before Section 7.

In planning-only mode, the agent still completes Sections 1 through 6 in full, including each section's per-phase report, register updates, checkpoints, and commits (run artifacts are committed deliverables). It creates `implementation-plan.md`, then stops before Section 7 implementation and presents the plan. Planning-only mode makes no product-code changes and no Section 7 commits.

Proceed autonomously through the full review. Use judgment. Do not stop for minor uncertainty. Record assumptions and proceed conservatively.

Stop or pause only for a true safety blocker, such as risk of deleting user data, exposing or committing secrets, running ambiguous destructive commands, needing unavailable credentials, being unable to separate this run's changes from pre-existing user changes, or needing to alter public behavior without enough evidence or validation.

Execute one section at a time using the per-section execution loop defined in `README.md`: open and read the full section file at the start of that section (do not rely on memory of a section read earlier), do the work, update registers and artifacts, write the per-phase report, record the checkpoint, commit, then proceed. Do not batch multiple sections before reporting and committing.

## Required run directory

Create:

```text
workflow-artifacts/release-review/<RUN_ID>/
```

Run records live under `workflow-artifacts/<workflow-name>/<RUN_ID>/` - one
timestamped directory per run, namespaced by the workflow that produced it (this
runbook uses `release-review`). The run ID already encodes the timestamp, so there is
no separate date level. Use a timestamp run ID:

```text
YYYYMMDD-HHMMSS
```

The `workflow-artifacts/release-review/<RUN_ID>/` artifacts are committed deliverables of the review, not throwaway local notes. Do NOT add `workflow-artifacts/` to `.gitignore`. If a prior run or a stale package added `workflow-artifacts/` to `.gitignore`, remove that ignore line so the artifacts can be tracked, and record the change. Only keep run artifacts local if the user explicitly asks for that on a given run.

Required artifacts:

| Artifact | Purpose |
|---|---|
| `00-run-metadata.md` | Run ID, timestamp, agent/model if known, repository path, Git metadata, initial status, environment summary. |
| `01-repository-inventory.md` | Project type, structure, languages, frameworks, public contracts, tests, docs, build/release artifacts. |
| `02-execution-plan.md` | Lightweight plan for the full review and audit, updated when material facts change. |
| `03-findings-register.csv` | Durable register of all findings, including addressed and unaddressed findings. |
| `04-action-register.csv` | Durable register of all candidate actions, implemented changes, deferred items, and blockers. |
| `05-decisions.md` | Decisions, assumptions, non-applicable judgments, scope choices, and rationale. |
| `06-commands.md` | Commands run, purpose, result summary, and whether output was clean or had errors. |
| `07-commits.md` | Local commits made, files included, source action IDs, and validation. |
| `08-checkpoints.md` | Section boundary checkpoints and reconciliation notes. |
| `implementation-plan.md` | Consolidated implementation plan created after Sections 1 through 6 and before Section 7 (unnumbered to avoid confusion with Section 9 release execution). |
| `10-validation-results.md` | Tests, builds, linters, type checks, security checks, documentation checks, and manual validation. |
| `11-push-plan.md` | Push/no-push decision, rationale, branch/remotes, and recommended next action. |
| `12-final-response.md` | Final saved report matching the user-facing final response. |
| `deprecation-candidates.md` | Deprecated, obsolete, stale, unused, superseded, or misleading code and artifact candidates. |
| `ci-assessment.md` | CI and GitHub Actions assessment, recommendations, changes made, or reasons no change was made. |
| `schema-validation.md` | Discovered schemas, schema validation commands, sample payload/config/example validation, compatibility risks, and schema drift findings. |
| `final-bug-security-audit.md` | Final post-implementation bug, correctness, security, privacy, and unsafe-change sanity audit before completion. |
| `todo-reconciliation.md` | Triage of every discovered `TODO.md`/backlog/`TODO`-marker item against this release, with per-item classification and disposition. |
| `guiding-principles-assessment.md` | Per-principle adherence assessment against the repository's guiding-principles document, or the universal fallback principles if none exists. |
| `cold-start-orientation.md` | Assessment of whether a no-context engineer or LLM can orient from the project's own docs (intent, philosophy, architecture, decision rationale), intent recovered from conversation, open questions, and the cold-start verdict. |
| `persona-review.md` | Per-persona notes capturing what each of the eight reviewer personas surfaced, including the novice and stakeholder views. |
| `section-summaries/` | Mandatory per-phase reports for Sections 1 through 9, each covering what was done, why, and what was considered but not done. |
| `audit-lanes/` | Optional reports from controlled parallel read-only audit lanes used after Section 1. |

If any artifact is not applicable, create it anyway and mark it as not applicable with rationale.

## Unique ID system

Every finding, candidate action, implemented change, deferred item, blocked item, deprecated-code candidate, CI candidate, decision, release concern, and final recommendation must have a unique run-specific ID.

Use this pattern:

```text
<RUN_ID>-S<section>-<TYPE><number>
```

The full type-code table and worked ID examples are in `reference.md` (consult on demand). `RR` is a field (Remediation Risk: Low / Medium / Medium-High / High) recorded on every finding and action, not a finding type; do not use it as a type code in an ID.

Restarts are new runs with new IDs. A restarted run may reference earlier run IDs but must not reuse them.

## Register requirements

Maintain `03-findings-register.csv` and `04-action-register.csv` throughout the run. Use these statuses: `identified`, `planned`, `completed`, `deferred`, `blocked`, `not_applicable`, `superseded`, and `wont_do`.

Findings must include ID, section, type, severity (impact if left alone), Remediation Risk (Low / Medium / Medium-High / High, per the Fix Bar), title, status, affected area, evidence, impact, recommended action, public behavior change, required artifact updates, source files, validation, and next step.

Actions must include ID, source finding IDs, section, status, description, Remediation Risk, files changed, commit, validation, reason not done (which Remediation-Risk axis, if deferred), and recommended next step.

Under the Fix Bar, severity is for reporting and Remediation Risk is for deciding. Any deferred finding must name the Remediation-Risk axis (complexity, usability, security, or functionality) that justifies deferral.

## TodoWrite protocol

If running in OpenCode and TodoWrite is available, use TodoWrite for live progress visibility. Create one todo per major section and one per implementation batch. Keep todo statuses aligned with the run artifacts. Reconcile TodoWrite against the registers before the final report.

Do not use TodoWrite as the official record. If TodoWrite is unavailable, continue without it and record progress in the run directory.

## Optional controlled parallel audit mode

After Section 1 completes the repository baseline, the main agent may use controlled parallel read-only audit lanes for Sections 2 through 6 when doing so is likely to improve review breadth, reduce missed findings, or manage a large repository more effectively.

Parallel audit mode is optional. Do not force it for small or simple repositories.

Allowed lane scopes include:

1. Code quality, correctness, security, privacy, and edge cases.
2. Tests, fixtures, coverage, and regression protection.
3. Documentation, specifications, examples, and help text.
4. Compatibility, packaging, build, CI, deployment, versioning, and release artifacts.
5. Schemas, data contracts, migrations, examples, fixtures, and serialized outputs.
6. Deprecated, obsolete, stale, unused, duplicated, or superseded code and artifacts.

Rules for parallel audit lanes:

1. The main agent must complete Section 1 before starting parallel lanes.
2. Lanes must be read-only.
3. Lanes must not edit tracked files.
4. Lanes must not update official registers directly.
5. Lanes must not create commits.
6. Lanes must not push to a remote.
7. Lanes must not make final release decisions.
8. Lanes must not assign official run-specific IDs.
9. Lanes should use temporary candidate IDs only.
10. Lanes must produce compact reports under `workflow-artifacts/release-review/<RUN_ID>/audit-lanes/` using `templates/audit-lane-report.md`.
11. The main agent must synthesize all lane reports before creating `implementation-plan.md`.
12. The main agent must deduplicate findings, assign official IDs, decide severity, update registers, and record decisions.
13. Section 7 implementation must remain serial.
14. Section 8 final review must remain serial.
15. Section 9 release execution must remain serial.

If parallel lanes are not used, record that decision in `05-decisions.md` and continue serially.


## Live-interaction-surface and data-integrity rule (shared)

A recurring source of production incidents is **live-interaction surfaces** that hermetic unit tests do not exercise: resume/skip/idempotency logic, multi-process or multi-run coordination (start guards, pidfiles, stop/signal targeting, shared ledgers), work-selection/limit/pagination advancement, spend/cap/budget accounting, external-IO/fetch completeness, and any place where incomplete data drives an automated decision or where a re-run can overwrite completed/verified/paid-for output.

Green tests are NOT evidence these are correct. When such surfaces exist, trace the actual runtime behavior by reading the code paths, not by inferring from passing tests.

A defect on a live-interaction surface that can (a) overwrite or destroy completed/verified/paid-for output or user data, (b) spend real money or quota on work that should have been skipped, (c) make an automated decision on incompletely-retrieved or truncated input, (d) signal/stop/coordinate the wrong process, or (e) prevent forward progress through a backlog, is **at least High severity**, is tagged `LIVE` in the finding title, and the difficulty of writing an automated test for it does **not** lower its severity. Section 7 defines the mandatory non-deferral handling for these findings.

## Memory, resource, and lifetime rule (shared)

Treat memory and resource correctness as first-class (`MEM`). Hunt for leaks and unbounded growth (caches/maps/lists/log buffers that never evict), unclosed files/sockets/handles/db connections, missing cleanup on error paths, use-after-free / use-after-close, double-free / double-close, dangling references, retained large buffers, recursion without bounds, and concurrency/state hazards (races, missing synchronization, non-idempotent retries, TOCTOU). Apply this to whatever the language exposes: manual memory, GC pressure and retention, RAII/ownership, context managers, `defer`/`finally`, and connection pools. A confirmed leak or unbounded-growth path that affects long-running or production use is at least Medium and often High.

## Command logging

For every meaningful command, append to `06-commands.md` the command, purpose, working directory, relevant assumptions, result, short output summary, and follow-up action if any.

Do not paste secrets or excessive logs. Summarize long outputs and save only relevant excerpts when needed.

## Commit policy

Use local commits for meaningful tracked repository changes when safe. The `workflow-artifacts/release-review/<RUN_ID>/` run artifacts are committed deliverables by default: commit them alongside the run so the per-phase reports, registers, plans, and final report become part of the project history. Keep them out of commits only if the user explicitly requests local-only artifacts for that run.

Before any commit, run `git status --short`, confirm the files to commit were changed by this run, avoid committing unrelated pre-existing changes, and run appropriate validation first or state why validation could not be run.

Commit at logical checkpoints: after run setup (including the initialized `workflow-artifacts/release-review/<RUN_ID>/` artifacts), at each section boundary (per-phase report plus that section's product changes), after coherent implementation batches, after test/docs/CI updates when they form a reviewable unit, and after final validation cleanup. Keep run-artifact commits separate from product-code commits when practical so history stays readable.

Use commit messages that reference action IDs. If changes cannot be separated from pre-existing user changes, do not commit. Record the blocker.

## Remote push policy

Do not push to a remote during the review. At the end, create `11-push-plan.md` with branch, local commits, permission status, push recommendation, risks, suggested command if permitted, and no-push rationale if permission is absent. Only push if explicitly permitted by the user.

## The Fix Bar (decision policy for what to address)

`fix-decision-policy.md` is the authoritative, full statement of this policy. Read it. It governs Section 7 selection and overrides any older "favor high-priority only" or "minimize changes" framing. The operative rule, restated here so it is not missed:

> **Fix by default.** FIX the finding unless the *Remediation Risk* of fixing it is Medium-High or higher (the risk that the fix itself harms **complexity, usability, security, or functionality**, now or in the future). When unsure, prefer to fix and note the uncertainty.

Key consequences (full rationale and edge cases in `fix-decision-policy.md`):

- Effort, time, and token/compute cost are NOT reasons to skip a fix.
- **Severity is for reporting; Remediation Risk is for deciding.** A Low/cosmetic finding is fixed by default; a High finding is deferred only if its cure clears the Medium-High risk bar.
- Rate Remediation Risk Low / Medium / Medium-High / High and record it on every finding/action. Any deferral must name the at-risk axis. Never silently drop a finding.
- The `LIVE`/High data-integrity non-deferral rule (Sections 2 and 7) applies regardless.
- The Complexity axis is the guard against scope creep: do not let "it is cheap to add" become gold-plating. Over-scope items are flagged and removed/deferred; under-scope (missing required capability) is added by default.

## Deprecated-code analysis

Throughout the review, identify code, files, commands, examples, tests, configs, docs, workflows, or scripts that appear unused, obsolete, superseded, misleading, or harmful to maintainability. Record candidates in `deprecation-candidates.md`.

Classify each candidate as safe to remove now, safe to mark deprecated now, candidate for future removal, probably still needed, or unknown requiring human review.

Do not delete or deprecate something solely because it is old or not immediately referenced. Look for imports, references, tests, docs, package exports, CLI exposure, build scripts, CI workflows, changelog history, external contract risk, and usage patterns.

## CI and GitHub Actions

Assess whether CI should be added or updated. Record findings in `ci-assessment.md`.

You may add or update CI only when validation commands are clear, the workflow is low risk, it does not publish, deploy, release, upload artifacts, or change remote state, it does not require unknown secrets, it aligns with the repository language and package manager, and it materially improves release readiness. The list of CI checks to consider is in `reference.md`. If CI is not added, explain why.

## Schema validation

Throughout the review, identify and validate schemas and data contracts when applicable. The list of schema/data-contract types and the specific things to check for are in `reference.md` (consult on demand).

Record schema findings in `schema-validation.md` and the finding/action registers.

When repository-native validation commands exist, use them. When examples, fixtures, golden files, sample configs, documented payloads, or test data exist, validate representative samples against the relevant schemas when practical and safe.

Do not introduce new schema tooling unless it is low risk, aligned with the repository, and clearly justified. If validation is not possible, explain why and record the residual risk.

## Validation expectations

Use repository-native commands when available. Prefer commands documented in README, package scripts, Makefiles, task runners, CI files, or contribution docs. Do not invent unsafe commands or install heavy new tooling just to validate unless the repository clearly requires it.

## Non-applicable handling

Some repositories will not have APIs, CLIs, UIs, packaging, deployment, docs, tests, or CI. Do not force findings. Mark non-applicable checks explicitly, explain why, and continue.

## Final report requirements

Save the final report to `workflow-artifacts/release-review/<RUN_ID>/12-final-response.md`, then present the same content to the user.

The final report must follow the exact structure in `templates/final-response.md`, which is the single canonical definition of the report (column shapes included). Do not invent different table columns; use the template's.

It begins with two tables defined in the template:

1. **Completed actions** (columns: Unique ID, Description of what was done, Files changed, Commit, Validation).
2. **Identified but not addressed** (columns: Unique ID, Description of what was not done, Remediation Risk + axis, Reason, Recommended next step).

The second table must include audit findings that were identified but not implemented, not only actions that were started and left incomplete. It must include any `LIVE`/High live-interaction-surface finding that was not fixed, flagged `LIVE - needs user decision`; such a finding must never be silently moved into `TODO.md` in place of being reported here. Under the Fix Bar, any unaddressed item was deferred because the fix's Remediation Risk is Medium-High or higher; the Reason must name the axis, not effort/cost.

After the two tables, include every remaining section listed in `templates/final-response.md` (summary of changes, Fix Bar summary, validations run, CI assessment, schema validation, deprecated-code, final bug/security/memory sanity audit, TODO/backlog reconciliation, pending plans / staged prompts, guiding-principles adherence, eight-persona sign-off, self-documenting/learn-as-you-go assessment, documentation/artifact updates, remaining risks, push/no-push decision, GO/CONDITIONAL GO/NO-GO recommendation, restart recommendation, and Section 9 readiness).

## Restart assessment

At the end, decide whether a new review run should be started. Recommend a restart only when implementation changed enough that earlier audit results may be stale, substantial architecture or behavior was discovered late, validation exposed issues requiring another broad pass, or major CI, packaging, public contract, or security changes were made. Do not restart merely because minor fixes were made.

**Loop guard.** This is a recommendation, not an automatic action: never start a new run yourself. Recommend at most one restart per run, and only with a concrete, enumerated list of what the next run must re-examine and why. If a previous run already recommended a restart and this is that follow-up run, do not recommend a third broad pass; instead enumerate any specific residual items as targeted follow-ups for the user to decide on. The goal is convergence, not perpetual review.

## Safety rules

Do not run destructive commands unless clearly necessary and safe. Do not delete user data, generated artifacts, databases, or untracked files without explicit justification. Do not expose or commit secrets. Do not install unnecessary dependencies. Do not change license terms. Do not alter public APIs without compatibility analysis. Do not modify deployment or release automation to publish externally without explicit permission. Stop and record a blocker if a change cannot be made safely.
