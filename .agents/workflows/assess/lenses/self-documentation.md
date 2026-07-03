# Lens: Self-documentation (learn-as-you-go)

Focus the assessment on whether a naive, non-expert user can learn the product *while
using it*, without reading external docs or taking a course. This is the in-product
clarity bar (distinct from repo documentation, which is the `documentation` lens).
Applies to libraries, CLIs, APIs, and UIs.

## Lead personas

Complete novice (primary) and UI/UX engineer, with the power user checking that
discoverability does not get in the experts' way.

## Rubric

- **Naming:** do command/flag/function/field/option names reveal their purpose without
  a lookup? Avoid jargon and abbreviations the user would not know.
- **Help & usage:** is there `--help`/usage output, signatures with types, docstrings,
  hover/tooltips, or inline hints at the point of use? Is it accurate and sufficient?
- **First-run / onboarding:** does the product tell a new user what to do next? Is the
  first useful action obvious from the product itself?
- **Errors that teach:** are errors specific, and do they say how to recover or what
  valid input looks like - not just "invalid input" or a stack trace?
- **Discoverability:** can a user find capabilities by exploring (help, autocomplete,
  menus, examples) rather than needing prior knowledge?
- **Examples at the point of use:** worked examples in help/docstrings/empty states.
- **Sensible defaults that demonstrate intent**, so the user learns by doing.
- **Assumed domain knowledge:** anything that silently requires expertise the target
  user lacks is a finding.

## IPD emphasis

For every place a user would have to ask, guess, or look something up, propose making
the *product* teach them (clearer name, better help text, an actionable error, an
inline hint, a better default) rather than adding external documentation to compensate.
These fixes are almost always low Remediation Risk and high value; propose by default.
