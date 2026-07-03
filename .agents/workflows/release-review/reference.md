# Reference

Look-up material consulted on demand. This file is NOT part of the always-read core
(`README.md` + `00-run-protocol.md` + `fix-decision-policy.md`). Read the relevant
part when a section needs it. In the context-assembly ordering (see
`00-run-protocol.md`), this belongs in the decay-tolerant middle of the window, not
at the end.

## Unique ID type codes

Every finding, candidate action, implemented change, deferred item, blocked item,
deprecated-code candidate, CI candidate, decision, release concern, and final
recommendation has a unique run-specific ID using the pattern
`<RUN_ID>-S<section>-<TYPE><number>` (defined in `00-run-protocol.md`).

| Type | Meaning |
|---|---|
| `A` | General action or artifact concern |
| `B` | Bug or correctness issue |
| `S` | Security or privacy issue |
| `E` | Edge case, error handling, cleanup, recovery, or resource issue |
| `T` | Test gap or test concern |
| `D` | Documentation, specification, example, or help-text issue |
| `F` | Feature completeness issue |
| `U` | Usability, developer experience, or operator experience issue |
| `M` | Maintainability issue |
| `R` | Regression, compatibility, migration, or public contract risk |
| `P` | Packaging, build, release artifact, or versioning issue |
| `O` | Operations or deployment issue |
| `CI` | CI or GitHub Actions issue or recommendation |
| `SCH` | Schema, data contract, serialized format, migration, payload, or config validation issue |
| `DEP` | Deprecated, obsolete, stale, or unused code/artifact candidate |
| `TODO` | Item discovered in `TODO.md`/backlog/roadmap or a `TODO`/`FIXME` code marker that bears on this release |
| `GP` | Guiding-principles violation (against the repo's principles doc or the universal fallback principles) |
| `KD` | Knowledge/handoff-documentation gap: missing or inadequate intent, goals, philosophy, architecture, or design-decision rationale needed for cold-start orientation |
| `MEM` | Memory, resource, lifetime, leak, unbounded-growth, or concurrency/state-safety issue |
| `X` | Concrete implemented change |
| `REL` | Final release decision, blocker, or release readiness finding |
| `Q` | Question or ambiguity |
| `DEC` | Decision or judgment call |

`RR` is a field (Remediation Risk: Low / Medium / Medium-High / High) recorded on
every finding and action, not a finding type. Do not use it as a type code in an ID.

## ID examples

```text
20260606-142233-S1-A1
20260606-142233-S2-B1
20260606-142233-S2-S1
20260606-142233-S2-MEM1
20260606-142233-S2-TODO1
20260606-142233-S3-T1
20260606-142233-S4-D1
20260606-142233-S4-KD1
20260606-142233-S5-GP1
20260606-142233-S5-M1
20260606-142233-S6-CI1
20260606-142233-S7-X1
20260606-142233-S8-REL1
20260606-142233-S9-O1
```

## Schema and data-contract types to consider

When the schema-validation rule in `00-run-protocol.md` applies, schemas may include:

1. JSON Schema.
2. OpenAPI or Swagger specifications.
3. GraphQL schemas.
4. XML Schema.
5. Database schemas or migrations.
6. Protocol buffers.
7. Avro, Parquet, or other data serialization contracts.
8. Configuration schemas.
9. Custom file format schemas.
10. Message, event, API payload, import, export, or serialized output contracts.

Check for: schema syntax validity; drift between schemas, implementation, docs,
examples, tests, and generated artifacts; backward compatibility risks for public
schemas and serialized outputs; missing validation for user-provided or external
data; migration or versioning concerns; stale or non-reproducible generated schema
artifacts; and CI opportunities for schema validation.

## CI checks to consider

When assessing CI (see `00-run-protocol.md`), consider linting, formatting checks,
unit tests, type checks, build checks, packaging checks, security or dependency
checks, documentation checks, and matrix testing for supported versions.

Add or update CI only when validation commands are clear, the workflow is low risk,
it does not publish/deploy/release/upload or change remote state, it does not
require unknown secrets, it aligns with the repository language and package manager,
and it materially improves release readiness. If CI is not added, explain why.

## Register statuses (quick reference)

`identified`, `planned`, `completed`, `deferred`, `blocked`, `not_applicable`,
`superseded`, `wont_do`. The authoritative definition of register requirements is in
`00-run-protocol.md`.
