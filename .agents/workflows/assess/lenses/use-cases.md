# Lens: Use-case and scenario coverage

Focus the assessment on whether the project has considered the full range of
reasonable ways it will actually be used - the real scenarios, users, and contexts -
and handles them. Complements functionality (what capabilities exist) and edge-cases
(boundary inputs) by reasoning at the level of *whole scenarios*.

## Lead personas

Sophisticated power user and complete novice (different usage patterns), stakeholder
(business scenarios), and QA engineer (scenario-based testing).

## Rubric

- **Enumerate the actors and their goals:** every distinct user/operator/integrator
  type and what they are trying to do.
- **Primary scenarios:** the main ways each actor uses the product end to end - are
  they all supported and coherent?
- **Secondary / alternative scenarios:** less common but reasonable paths, recovery
  flows, "what if they do it in a different order".
- **Lifecycle scenarios:** first use, empty/new state, growth over time, migration,
  upgrade, deprecation, offboarding, data import/export.
- **Multi-user / concurrency scenarios:** two users (or runs) acting at once; shared
  state; collaboration.
- **Failure scenarios:** what the user experiences when a dependency, network, or
  input fails (cross-reference reliability and edge-cases).
- **Environment scenarios:** different platforms, scales, configurations, locales,
  permission levels.
- **Misuse / unhappy scenarios:** reasonable wrong turns and how the product responds.

## IPD emphasis

Produce an explicit catalogue of reasonable use cases, mark each as
supported / partial / unsupported / untested, and propose closing the gaps that
matter (with tests that encode the scenario). This lens often *feeds* the
functionality, testing, and edge-cases work; cross-reference rather than duplicate.
Distinguish scenarios the project should support from those legitimately out of scope.
