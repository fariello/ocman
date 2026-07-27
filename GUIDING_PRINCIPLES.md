# Guiding Principles

These are the principles that shape ocman as a product. They are inferred from the codebase, tests,
and decisions log, and are meant to describe how ocman actually behaves today (not an aspirational
wish list). Where a point is an intention rather than an invariant it is marked "(intent)".

Note on scope: ocman vendors a shared agent-workflow toolkit under `.agents/` (from the
`agent-workflows` project). That toolkit has its OWN, separately numbered "Guiding Principles"
document about how AI agents should work in this repo (fix-by-default, self-contained questions,
externalized state, and so on). References of the form "GUIDING_PRINCIPLES P5 / P12" in `AGENTS.md`
and `.agents/**` point at THAT framework document, not at this file. This file is about the ocman
tool itself.

## P1. Safety first for destructive actions

ocman deletes sessions, projects, and database rows, and it signals live processes. Every
destructive path confirms by default (`-y` to skip, `--dry-run` to preview), keeps a restorable
backup where it can, and refuses or defers rather than risk corrupting a live OpenCode database.
Signalling is own-user only with a PID-reuse guard (see `DECISIONS.md`).

## P2. No silent data loss

Nothing destructive happens without the user seeing it. Deferred actions are re-resolved,
re-previewed, and re-confirmed before they run; a declined item is kept, a vanished target is
skipped and reported, and an auto-drain that would delete without asking is deliberately NOT
provided.

## P3. Self-documenting; learn as you go

A user should be able to learn ocman from ocman: discoverable `--help` with examples, clear command
and flag names (for example `filter` was renamed to `focus`), actionable error messages that say how
to recover, and next-step hints on empty results. Prefer making the tool explain itself over writing
a separate manual.

## P4. Legible, bracketed output

Human output uses consistent bracketed status tags (`[NOTIC]`, `[ERROR]`, and so on) and honest
summaries (bytes reclaimed, rows deleted). Machine output (`--json`) stays clean and free of the
human decorations.

## P5. Externalize state; do not trust memory

Durable state lives on the filesystem in inspectable formats: the SQLite database, the
`ocman_history.json` ledger, and the `ocman_pending.json` manifest. These are schema-versioned where
a format can evolve, written atomically, corruption-tolerant on read, and glanceable from their
location. ocman does not rely on in-process memory for anything that must survive a run.

## P6. KISS, and guard against scope creep

Solve the real case simply. New capabilities are scoped to what is needed and no more: the
pending-actions feature covers the delete-family only, and extending it to rename/move/rebase or
adding auto-drain was deliberately deferred on the complexity and functionality axes rather than
built speculatively.

## P7. Config over hardcoding; respect the user's layout

Paths and retention come from `ocman.toml` and CLI arguments (Defaults < config file < CLI), not
baked-in assumptions, so a user can point ocman at a non-default OpenCode layout without editing
code. (intent) The one deliberate exception is the config-file location itself, which is currently a
module constant; a real environment override is tracked in `TODO.md`.

## P8. Single source of truth; keep docs honest

Behavior is defined once in code; `README.md`, `--help`, `ARCHITECTURE.md`, `DECISIONS.md`, and
`CHANGELOG.md` describe what actually ships. When behavior changes, its docs and its decision entry
change with it.

## P9. Cross-platform where it is safe, loud where it is not

ocman runs on Linux, macOS, and Windows for the portable operations. Where a capability depends on
Linux-only process and socket enumeration (kill, reconnect, running-instance detection), ocman says
so and fails loud rather than giving a false "nothing running".
