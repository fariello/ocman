# Decisions and assumptions - assess documentation

- Concern/scope: documentation, whole project. The invocation argument `docs` is the
  concern itself (documentation lens), so it did not further narrow scope; the whole
  project's written docs were assessed.
- Project conventions discovered: plans in `.agents/plans/pending/` named
  `YYYYMMDD-HHMM-NN-<slug>.md`; Status lifecycle draft->to-review->reviewed->approved->
  executed; no em/en dashes in authored Markdown (the `—` glyph is the sole sanctioned
  exception); path-scoped commits, never push (AGENTS.md). Universal guiding-principles
  fallback applies (intuitive/self-documenting, general-case/configurable, KISS, honest
  docs).
- Lens applied: documentation. Lead personas: complete novice (following the README) and
  the engineer/operator maintaining from the docs. Accuracy prioritized over
  completeness per the lens's IPD emphasis.

## Key decisions

- Verified the highest-severity claims against code directly rather than trusting the
  audit: confirmed there is no `ocman.py`, `vistab` is a hard top-level import
  (`cli.py:90`), pyproject lists 4 core deps, and `session recover --show-secrets`
  errors "unrecognized arguments." All corroborated the audit.
- Ordered the proposed changes accuracy-first (D-01..D-04 false claims), then config/env
  coverage, then CLI-table coverage, then polish (D-10/D-11) - matching the lens.
- D-10 (built-in `help all` omits new commands) is an in-PRODUCT self-documentation gap,
  not a written-doc defect. The plan only aligns the README wording and cross-references
  the self-documentation lens; it does NOT propose changing the help generator (that
  would be a separate assess/self-documentation IPD). Recorded as OQ-1.

## Intentionally NOT proposed (and why)

- No new documentation files, tutorial, or docs site: that is gold-plating (Complexity
  axis) and untraceable to a stated need; the fix is to correct/complete existing docs.
- No change to the `help all` generator: out of the documentation lens's scope (product
  self-documentation), surfaced as a cross-reference/open question instead.
- Nothing was deferred on Remediation-Risk grounds: every finding is a low-risk doc
  correction, so all are proposed for action.

## Open questions for the user

- OQ-1: soften the README `help all` claim (this plan's approach) vs. a follow-up to make
  `help all` actually list every command. Leaning: soften now; spin a self-documentation
  IPD if wanted. Non-blocking.
- OQ-2: is a release imminent that should convert CHANGELOG `[Unreleased]` to a version
  heading? Assumed NO (leave `[Unreleased]`).
