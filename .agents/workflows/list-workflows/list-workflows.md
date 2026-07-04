# Workflow: list-workflows (toolkit discovery)

Answer, in-agent, "what can this toolkit do, and which version is installed here?"
without the user reading `index.md` by hand. This is the companion to the parameterized
`/assess <concern>` command: it is how you discover the available concern values.

This workflow only READS and REPORTS. It never changes files, never writes an IPD, and
never runs another workflow. It is safe to run any time.

## Inputs

`$ARGUMENTS`, if present, is an optional filter:

- A group name (`core`, `assess`, `advise`) lists just that group.
- A concern or command name (`security`, `plan-review`, `assess`) shows just that item,
  expanded (its full description and how to run it in every tool).
- Empty: list everything, grouped.

Match case-insensitively; accept the same aliases the assess harness does (e.g. `a11y`
-> accessibility, `perf` -> performance). On an unknown value, show the closest matches
and then fall through to the full listing.

## Single source of truth

Read `.agents/workflows/index.md` and use ONLY what is declared there:

- The version: the `<!-- WORKFLOWS-VERSION: ... -->` header line (and/or
  `.agents/workflows/VERSION`).
- The capabilities: the manifest table between `<!-- WORKFLOWS-MANIFEST:BEGIN -->` and
  `<!-- WORKFLOWS-MANIFEST:END -->`. Each row is `command | body | lens | description`.

Do NOT hand-maintain or invent a second list. If a capability is not in the manifest, it
does not exist; if the manifest and this description ever disagree, the manifest wins.
This keeps the listing from drifting as the toolkit grows.

## How to classify the manifest rows

1. **The `assess` row** is the parameterized assessment command (`/assess <concern>`).
2. **The `assess-<concern>` rows are the concern CATALOG, not separate commands.** They
   define the valid `<concern>` values for `/assess`. List them as concerns under the
   `assess` command, grouped by area (correctness, security/privacy, compliance, UX/docs,
   product/design, delivery/quality) if you can infer the area from the description;
   otherwise list them alphabetically. Never present them as their own slash commands.
3. **`advise-<persona>` rows are the persona CATALOG for `/advise <persona>`**, not
   separate commands. They define the valid `<persona>` values. List them as personas
   under the `advise` command, each with its one-line charter. Never present them as their
   own slash commands.
4. **Every other row is its own standalone command** (e.g. `release-review`,
   `release-review-plan`, `plan-review`, `setup-repo`, `scaffold`, `list-workflows`).

## What to output

Start with one line stating the installed version (from the header/`VERSION`). If a
`VERSION` file is absent, say the installed version is unknown (older install) and
suggest re-running the installer.

Then, unless a filter narrowed it:

1. **Core workflows** - a table of the standalone commands with their one-line
   description and whether they change code.
2. **Assessments** - `/assess <concern>`; then the concern catalog grouped by area, each
   with its one-line focus. Note that a bare `/assess` lists concerns and asks.
3. **Advise personas** - `/advise <persona>`; then the persona catalog (the
   `advise-<persona>` rows), each with its one-line charter. Note that a bare `/advise`
   lists personas and asks. If no `advise-*` rows exist, omit this group.

For each command, show how to run it PER TOOL, concisely:

- **OpenCode / Claude Code:** the native `/<command>` (with `<concern>`/args where
  relevant), e.g. `/assess security`, `/release-review`.
- **Any other agent (Codex, Cursor, Antigravity, Copilot, ...):** the universal fallback
  - "Read and execute `<body path>`" using the row's body path (for `/assess`, name the
  concern so the harness resolves the lens).

Keep it scannable: grouped, with run instructions, not a raw dump of the table.

## Filtered output

If `$ARGUMENTS` named a single item, show only that item, fully expanded: its
description, its body path, and the per-tool run instructions. If it named a group, show
only that group's entries.

## Reminders

- Read-only. Do not modify any file or run any other workflow.
- The manifest is the single source of truth; do not add capabilities that are not in it.
- Report the version honestly, including "unknown" when there is no `VERSION` file.
