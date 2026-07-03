# Lens: Guiding-principles validation

Focus the assessment on whether the project conforms to its own stated guiding
principles - treating those principles as a binding contract - and propose closing the
gaps. This lens is uniquely tied to *this project's* declared values.

## Lead personas

All eight, mapped to whichever principles they best judge: e.g. the novice/UX personas
for "intuitive/self-documenting" principles, the architect for "general-case/
configurable/KISS", the security persona for security principles, the stakeholder for
"fitness for purpose / handoff".

## Rubric

- **Discover the principles (Step 0):** read `GUIDING_PRINCIPLES.md` or the project's
  equivalent. If none exists, use the universal fallback principles in
  `../release-review/00-run-protocol.md` and record that, AND propose establishing a
  principles document (recover the intended values from docs, the conversation, and
  observable design choices; mark inferred values for confirmation - do not invent).
- **Make each principle checkable:** for every stated principle, define concrete,
  verifiable criteria (e.g. a "self-documenting" principle implies help text, clear
  errors; an "accessible" principle implies WCAG targets; a "configurable" principle
  implies no hardcoded business rules).
- **Assess conformance per principle:** full / partial / violated / not-applicable,
  with evidence from the actual code, UI, docs, and tests.
- **No regression:** ensure nothing recently changed has drifted from a principle.
- **Tensions:** where principles conflict in practice, surface the tension for a
  stakeholder decision rather than silently picking one.

## IPD emphasis

Produce a per-principle conformance table and propose the changes that bring the
project into alignment, prioritized by how core the principle is and how far the
project drifts. Many alignment fixes are low Remediation Risk; propose by default.
Never propose a change that *violates* a stated principle. Where alignment requires a
product/values decision, route it to the stakeholder as an open question. Cross-
reference the concern-specific lenses (accessibility, self-documentation, etc.) rather
than re-deriving their rubrics.
