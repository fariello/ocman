# Lens: UI/UX usability and intuitiveness

Focus the assessment on whether the product is easy, clear, and pleasant to use.
Distinct from accessibility (disability access) and self-documentation (in-product
learning), though they overlap. Applies to any user surface: GUI, CLI, API
ergonomics, prompts. Scope out cleanly if there is no user surface.

## Lead personas

UI/UX engineer, complete novice, and sophisticated power user (clarity for newcomers
without crippling experts), with the stakeholder view on whether it serves its goal.

## Rubric

- **Flows & task completion:** can a user accomplish core tasks with minimal steps and
  no dead ends? Are common tasks fast and obvious; rare ones discoverable?
- **Information architecture:** logical grouping, navigation, naming that matches the
  user's mental model (not the implementation's).
- **Defaults:** sensible, safe defaults; the common case requires the least work.
- **Feedback & states:** clear loading/empty/success/error states; never silent
  failure; progress for slow operations; confirmation for destructive actions; undo
  where feasible.
- **Consistency:** consistent terminology, layout, controls, and interaction patterns;
  no synonyms for the same concept.
- **Error prevention & recovery:** hard to make mistakes; easy to recover; validation
  is timely and specific.
- **Friction & cognitive load:** unnecessary steps, jargon, modes, or surprises;
  double-submit and accidental-action protection.
- **Power-user ergonomics:** keyboard shortcuts, scriptability, bulk actions,
  escape hatches - without burdening novices.
- **Responsiveness/layout** across realistic viewport/terminal sizes.

## IPD emphasis

Lead with the novice walking through real tasks and note every point of confusion or
friction. Prefer fixes that simplify (Complexity axis: do not add features to paper
over a confusing flow). Many UX fixes (better defaults, clearer labels, a loading
state) are low Remediation Risk; propose them by default. Route changes that need
product/design judgment to open questions.
