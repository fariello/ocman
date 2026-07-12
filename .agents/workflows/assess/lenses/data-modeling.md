# Lens: Object and data-modeling design

Focus the assessment on the quality, structure, and lifecycle of the project's data models, schemas, and object designs. Applies to database schemas, class hierarchies, serialized state, and configuration structures.

## Lead personas

Architect (primary), software engineer, and stakeholder.

## Rubric

- **Canonical models:** compare semantics, not names. Is a new noun actually just a different state, label, role, or configuration of an existing concept? Separate only when there is a real difference in invariants, identity, or lifecycle.
- **Generality ladder:** follow the preferred order of modeling solutions: (1) use a single model with variation represented as data or configuration, (2) use a shared core model with thin specialization, or (3) use a bounded special case accompanied by a written justification. Do not build for hypothetical needs. Do not replace clear domain models with an unbounded metadata system.
- **Configuration discipline:** use configuration only for expected variation such as labels, roles, thresholds, routing, templates, or effective dates. Configuration must be typed, validated, versioned, auditable, and testable. Do not turn configuration into a hidden programming language.
- **Provenance and historical truth:** preserve what was submitted or effective at each point in time. Do not silently rewrite history. Preserve provenance for imported, derived, or user-entered data. Apply versioning or effective-date rules when historical reconstruction is required.

## IPD emphasis

Data and object model changes carry high Remediation Risk due to migrations and broad blast radius. Propose the smallest evidenced change that addresses the problem. Prefer data or configuration changes over structural refactoring.
