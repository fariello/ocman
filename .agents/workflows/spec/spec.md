# Workflow: spec (draft a reviewable specification)

Turn a fuzzy request into a clear, reviewable specification: what we are building, for
whom, why, and how we will know it is done. This is the FRONT of the funnel - it feeds
`plan-review` and then implementation.

Guided and interactive, like `setup-repo`: you ask questions, the user answers, and you
produce the spec document with per-step confirmation. It writes a planning artifact; it
does not write code.

## Division of labor with `/advise spec-editor`

- **`spec` PRODUCES the artifact** (this workflow): it drafts the specification document.
- **`/advise spec-editor` INTERROGATES it** (the advise persona): an interactive session
  that pressure-tests an existing spec for ambiguity and missing criteria.

Natural flow: `spec` to draft, then `/advise spec-editor` to harden it, then `plan-review`
before building. Do not duplicate the spec-editor's interrogation here; draft well, then
hand off.

## Where the spec goes

Detect the project's convention (ask if unclear): a specs/RFC/ADR directory
(`.agents/docs/specs/`, `docs/rfcs/`, `.agents/plans/`), or create `.agents/docs/specs/` if none exists.
Name the file `YYYY-MM-DD-<slug>.md`. Confirm the location with the user before writing.

## Protocol

1. **Understand the request.** Read `$ARGUMENTS` and any referenced material. Restate the
   request in one or two sentences and confirm you have it right before going further.
2. **Interview for the essentials** (ask in small batches, not all at once; when a question
   is a picker/decision, put its full question set - context, question, options - inside the
   interactive prompt itself, per GUIDING_PRINCIPLES P12):
   - The problem and the goal (the job to be done, and for whom).
   - Non-goals and explicit scope boundaries.
   - Users/actors and their key scenarios.
   - Constraints (technical, regulatory, timeline, compatibility).
   - Success criteria that are testable.
3. **Draft the spec** using the structure below. Mark anything you inferred rather than
   were told as "(assumption - confirm)"; collect real unknowns under Open Questions
   rather than guessing.
4. **Review with the user** section by section; revise. Get confirmation before writing
   the file.
5. **Write the file** to the confirmed location, add a `## Workflow history` line
   (`- <date> /spec (<agent/model>): drafted spec`), then **commit** it and NEVER push
   (commit-only).
6. **Closing report.** End by presenting the shared closing report
   (`../assess/templates/closing-report.md`): the artifact CREATED (the spec file path), or -
   if the user declined the write - that none was created and why, plus the next steps:
   `/advise spec-editor <file>` to harden it, then `/plan-review` on the implementation plan
   when one exists.

## Spec structure

- **Title and one-line summary.**
- **Problem / motivation:** what is wrong or missing today, and why it matters.
- **Goals:** the outcomes this must achieve (each testable).
- **Non-goals:** what is explicitly out of scope.
- **Users / actors and scenarios:** who uses this and the key flows.
- **Requirements:** functional and non-functional, each specific and verifiable. Separate
  MUST from SHOULD/NICE-TO-HAVE.
- **Acceptance criteria:** how we will know each goal/requirement is met (the tests that
  would pass).
- **Constraints and dependencies:** what bounds the solution; what it relies on.
- **Risks and open questions:** known unknowns, decisions still needed.
- **Out-of-scope / future:** deliberately deferred ideas.

## Honesty and guardrails

- Specify WHAT and WHY, not the implementation HOW (leave design to the plan/architect).
- Do not invent requirements the goal does not need (no gold-plating); do not paper over
  genuine unknowns - record them as Open Questions.
- Guided writes only: confirm the location and content before creating the file. Never
  write code.

## Reminders

- Draft, then hand off to `/advise spec-editor` and `/plan-review`.
- Testable goals and acceptance criteria are the point; vague specs fail review.
- Mark assumptions explicitly; do not guess to fill a gap.
