# Workflow: release-notes (version bump + changelog/notes)

Draft the release notes and changelog for a release, and decide the version bump from the
actual changes. This is a repeatable release-DISCIPLINE step, distinct from
`release-review` Section 9 (which EXECUTES a release): this workflow prepares the
human-facing narrative and the version, and stops there.

Guided and interactive. It drafts notes and updates changelog/version files with
confirmation; it does NOT publish, tag, push, or deploy.

## Honesty about scope (read first)

This workflow DRAFTS notes and BUMPS version files. It does not publish to a registry,
create a git tag, push, or deploy - those are release execution (out of scope here; see
`release-review` Section 9 or your own release process). Say so if the user expects
publishing.

## Protocol

1. **Determine the range.** Ask (or infer from `$ARGUMENTS`) the range since the last
   release: the previous tag/version to HEAD. If there is no prior tag, use the full
   history or a user-specified start.
2. **Gather the changes.** Read the commit history and, if present, merged PRs, the
   existing CHANGELOG, and DECISIONS. Group changes into: Added, Changed, Fixed,
   Deprecated, Removed, Security (Keep a Changelog style), plus Breaking changes called out
   prominently.
3. **Decide the version bump.** Follow the repo's existing scheme (detect it: SemVer is
   the default and is what this framework itself uses via git tags; also handle CalVer or
   any other convention already in use). Recommend the bump from the change content
   (breaking -> major; features -> minor; fixes -> patch, for SemVer) and explain why. For
   a tag-driven repo the "bump" is choosing the next tag. If the release is not yet intended
   for a registry/production (a candidate, not the final), recommend a `vX.Y.Z-rc.N`
   pre-release: it sorts before the final `vX.Y.Z` and pip does not install it without
   `--pre`. A bare `vX.Y.Z` means "intended for the registry". Confirm with the user before
   applying.
4. **Draft the notes** in two registers:
   - **CHANGELOG entry:** concise, categorized, for developers.
   - **Release notes:** a short human narrative for users - highlights, breaking changes
     and migration pointers, notable fixes. Follow the project's prose conventions and the
     assess-prose style guide (`assess/references/prose-style.md`): quiet, clear, no
     hype, no em dashes.
5. **Apply, with confirmation:** update the CHANGELOG (and version files - `package.json`,
   `pyproject.toml`, `VERSION`, etc. - per the repo's convention) only after the user
   confirms the bump and the content. Stage the changes; do not commit unless asked, and
   never tag/push/publish.
6. **Report** the chosen version, the files updated, and the drafted notes. Point at the
   actual release/publish step as a separate, user-driven action.

## Guardrails

- Never publish, tag, push, or deploy. Drafting and version bumping only.
- Base the notes on the ACTUAL changes (commits/PRs/CHANGELOG), not an imagined feature
  list. If a change's user impact is unclear, ask rather than embellish.
- Respect the repo's existing changelog format and version scheme; do not impose a new one
  without asking.
- Prose follows the style guide: no marketing tone, no em dashes.

## Reminders

- Distinct from executing a release: prepare notes + version, stop before publish.
- Breaking changes and migration pointers are the highest-value part - make them
  prominent.
- Confirm the version bump before touching files.
