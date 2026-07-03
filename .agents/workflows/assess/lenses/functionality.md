# Lens: Functionality completeness

Focus the assessment on whether the project provides the functionality its users and
stakeholders would reasonably want or need to achieve its purpose - and whether
implemented functionality actually works end to end.

## Lead personas

Stakeholder (does it achieve the goal?), sophisticated power user (is anything
expected missing?), complete novice (can they do the basic job?), and the QA engineer
(does the claimed functionality actually work?).

## Rubric

- **Intent vs. delivery:** restate the project's purpose (Step 0) and map core
  user/stakeholder goals to implemented capabilities. Where is there a gap?
- **Incomplete workflows:** features that are started but not finishable; happy-path
  only; missing the obvious next step a user needs.
- **Documented-but-missing / present-but-undocumented:** reconcile claims, docs, and
  reality.
- **Table-stakes capabilities** for this project type that users will assume exist
  (e.g. search, export, undo, pagination, bulk ops, config) and that are absent.
- **Integration completeness:** does it actually connect to the systems it claims to?
- **Backlog signal:** `TODO`/roadmap items that represent required-but-missing
  functionality (cross-reference any backlog).
- **Over-scope check:** functionality not traceable to a real need (propose
  deferral/removal) - guard against gold-plating while filling real gaps.

## IPD emphasis

This lens is judgment- and stakeholder-heavy: distinguish *required* gaps (block the
purpose), *expected* gaps (users will assume it), and *nice-to-have*. Propose required
and clearly-expected functionality by default; route genuinely product-level scope
decisions to open questions for the stakeholder. Pair with the use-cases lens to
ground "what users need" in concrete scenarios.
