# Lens: Compatibility and interoperability

Focus the assessment on whether the project works across the platforms, versions,
environments, and systems it must, and whether it preserves backward compatibility for
its existing users and integrations.

## Lead personas

Software engineer and operator, with the power user/integrator and the stakeholder on
not breaking existing users.

## Rubric

- **Platform/OS/runtime:** supported operating systems, architectures, language/runtime
  versions, browsers - claimed vs. actually working; conditional code paths correct.
- **Dependency version ranges:** are declared ranges actually supported and tested?
  Too-loose (breaks) or too-tight (conflicts) constraints; peer-dependency issues.
- **Backward compatibility:** public APIs, CLI flags/output, config keys, env vars,
  schemas, serialized/on-disk formats, and wire protocols - do changes preserve
  existing callers? Migration paths for unavoidable breaks. (Cross-reference api-design.)
- **Forward/interop:** plays well with the systems it integrates with (data formats,
  encodings, protocols, standards conformance); no assumptions about a single
  environment.
- **Data migration:** schema/format migrations are versioned and reversible; old data
  is readable or migratable.
- **Environment assumptions:** locale, timezone, filesystem case-sensitivity, path
  separators, line endings, encoding, available tools.
- **Configuration compatibility:** sensible behavior across supported configurations;
  no hardcoded environment specifics.
- **Standards conformance** where the project claims to implement a standard/spec.

## IPD emphasis

Verify support claims against evidence (CI matrix, conditional code, tests) rather
than the README's assertion. Treat silent breakage of an existing public
contract/format as High/Blocker and propose a compatible path or explicit, documented
migration. Propose a test matrix for the supported set so compatibility is provable.
