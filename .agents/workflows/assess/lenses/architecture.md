# Lens: Architecture and extensibility

Focus the assessment on the structural soundness of the system: how it is decomposed,
how parts depend on each other, and how well it can evolve - without over-engineering.

## Lead personas

Systems and software architect (primary), software engineer, and the stakeholder on
whether the structure supports future goals.

## Rubric

- **Decomposition & cohesion:** clear modules/components with single responsibilities;
  related things together, unrelated things apart.
- **Coupling & dependencies:** loose coupling; dependency direction is sane (no
  cycles, no high-level depending on low-level details); clear interfaces/seams.
- **Abstraction quality:** abstractions earn their keep; not leaky; not premature.
  Solve the general case where the project's purpose implies it - without speculative
  generality.
- **Extensibility:** can likely future needs (new entity types, providers, tenants,
  formats) be met by extension rather than rewrite? Are the right seams present?
- **Configurability over hardcoding:** business rules/thresholds/routing in config or
  data, not scattered constants - where the domain warrants it.
- **State & data flow:** where state lives; single source of truth; avoidable shared
  mutable state; clear data flow. (Cross-reference data-modeling lens.)
- **Boundaries:** internal vs. public surface; what is encapsulated; stable contracts.
- **Consistency:** consistent patterns across the codebase; one way to do a thing.
- **KISS / anti-bloat (Complexity axis):** flag accidental complexity, unnecessary
  layers, and unjustified dependencies AS WELL AS missing seams. Both over- and
  under-engineering are findings.

## IPD emphasis

Architecture changes can be high Remediation Risk (broad blast radius), so be
especially disciplined: propose the smallest structural change that addresses a real,
evidenced problem, prefer staged/refactor-with-tests paths, and route large redesigns
to open questions with a sketch rather than proposing a big-bang rewrite. Name the
invariants any refactor must preserve and route them to characterization tests.
