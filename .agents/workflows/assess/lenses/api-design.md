# Lens: API and public-contract design

Focus the assessment on the quality of the project's public contracts: library APIs,
CLI interfaces, HTTP/RPC endpoints, events, and serialized formats - whatever other
code or people depend on. High value for libraries and services; scope out if there is
no public surface.

## Lead personas

Architect and sophisticated power user (the integrator/consumer), with the novice on
first-use clarity and the stakeholder on compatibility commitments.

## Rubric

- **Surface clarity & minimalism:** is the public surface intentional and as small as
  it can be? Are internals accidentally exposed?
- **Consistency:** naming, parameter order, return/error conventions, casing, units,
  and patterns consistent across the whole surface.
- **Ergonomics:** easy to use correctly, hard to use wrong; sensible defaults; sane
  required-vs-optional; progressive disclosure for advanced use.
- **Error contract:** predictable, typed/structured errors; clear status codes;
  actionable messages; no leaking internals.
- **Data contracts/schemas:** explicit, validated, documented; inputs validated at the
  boundary; outputs stable.
- **Versioning & compatibility:** is there a versioning strategy? Are breaking changes
  identifiable and avoided/managed? Deprecation path with warnings. (Cross-reference
  compatibility lens.)
- **Pagination/filtering/limits** for collection endpoints; idempotency for mutations;
  rate-limit semantics.
- **Discoverability & docs at the contract:** signatures, schemas, and examples where
  the consumer looks (cross-reference self-documentation).
- **API-first integrability:** capabilities exposed programmatically, not just via UI,
  where the project's purpose implies integration.

## IPD emphasis

Distinguish *additive* improvements (low risk - propose by default) from *breaking*
changes to an already-published contract (Functionality-axis Remediation Risk - propose
a compatible path: add-new/deprecate-old, version, or route to an open question).
Never propose silently breaking a public contract.
