# Lens: Repository documentation

Focus the assessment on the project's written documentation: README, guides, API/CLI
reference, configuration, operational/runbook docs, examples, changelog, and
contributor docs. Distinct from self-documentation (in-product clarity) and from
cold-start knowledge (intent/architecture/decisions, covered under guiding-principles
and release-review's KD objective).

## Lead personas

Complete novice and the software engineer/operator who must use or maintain the
project from the docs.

## Rubric

- **Accuracy:** does every doc describe what the software actually does *today*? Verify
  claims against the code; flag outdated/aspirational content. Honest docs over
  impressive docs.
- **Completeness:** install, configure, run, common tasks, troubleshooting; public
  API/CLI surface documented; configuration and env vars documented with defaults.
- **Getting started:** can a new user go from zero to a first success following the
  README alone? Are prerequisites and steps correct and ordered?
- **Examples:** present, correct, runnable, and representative of real use.
- **Reference quality:** parameters, return values, errors, edge cases, units.
- **Operational docs:** deployment, monitoring, backup/restore, runbooks where the
  project type warrants.
- **Consistency & navigation:** terminology consistent with the product; findable
  structure; working links; changelog/release notes current.
- **Limitations & assumptions:** known limitations, supported versions/platforms, and
  security/privacy notes stated.

## IPD emphasis

Prefer fixing inaccuracies (highest harm) before filling gaps. Where the right fix is
to make the *product* self-explanatory instead of documenting around a rough edge,
note it and cross-reference the self-documentation lens. Doc fixes are low Remediation
Risk; propose by default, but avoid bloat (Complexity axis): concise and accurate
beats long and aspirational.
