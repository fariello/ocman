# Execution plan (the review itself)

Serial pass (no parallel lanes; see 05-decisions.md). Sections in order:

1. Current state / inventory / pre-flight gate. (done)
2. Quality/security/edge cases: read the recent-change surface + core error/DB paths;
   security lens on the LLM egress, the `--db`/path handling, reclaim/delete guards.
3. Tests/regression: run the full suite (paste output), assess coverage of the new features.
4. Docs/specs/examples: README/ARCHITECTURE/CHANGELOG accuracy vs. current behavior; help
   text; cold-start orientation.
5. Feature/usability/maintainability + guiding-principles adherence + full TODO triage +
   eight-persona pass.
6. Compatibility/packaging/release: wheel build, entry point, deps, CI; version-bump +
   CHANGELOG-cut plan.
7. Implementation: apply the version bump (1.1.0 -> 1.2.0) + CHANGELOG cut; any other
   low-risk fixes surfaced. Re-run the suite.
8. Final ship review: eight-persona sign-off, cold-start verdict, GO/NO-GO. Stop for the
   human GO.
9. Release execution: ONLY after GO + explicit approval (push, tag, publish, verify CI).

Expectation: given the tree is clean, tests pass, and all recent work was already
reviewed this session, the audit should surface few new findings; the substantive Section 7
action is the version bump + CHANGELOG cut.
