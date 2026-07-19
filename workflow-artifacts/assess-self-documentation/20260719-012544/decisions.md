# Decisions and assumptions - assess self-documentation

## Concern / scope

- Concern: self-documentation (learn-as-you-go / in-product clarity). Resolved from the
  argument `self-docs` to the `self-documentation` lens.
- Scope: whole product's IN-PRODUCT self-documentation - the CLI (`ocman/cli.py`: help
  system, error messages, flag/command naming, first-run) and the TUI (`ocman_tui/`: labels,
  empty states, hints). Repo docs (README/ARCHITECTURE) are explicitly OUT of scope (the
  `documentation` lens, already assessed and executed separately this cycle).

## Project conventions discovered

- Plans in `.agents/plans/pending/` -> `executed/`; `YYYYMMDD-HHMM-NN-<slug>.md`; Status
  born `to-review`.
- No em/en dashes in authored text (sanctioned exception: the em-dash "not available" table
  glyph in code).
- Path-scoped commits, never push, paste REAL pytest output (AGENTS.md).
- Error seam: `die(message, exit_code)` and `RecoveryError`; `main()` top-level catch at
  `cli.py:16309-16313`.

## Key decisions

- Applied the self-documentation lens (lead: complete novice; plus UI/UX engineer and power
  user). Fix-by-default: every place a user must guess/look up/hit a dead end is proposed as
  a product fix (clearer message, actionable error, better label, discoverability), not as
  external docs.
- Verified the two highest-value claims directly against source before proposing:
  (a) `--show-models`/`--list-projects` are NOT registered as args (stale in error strings);
  (b) `main()` catches only KeyboardInterrupt + RecoveryError (traceback can leak).
- Ordered the IPD accuracy-first (SD-01 dead-end error) then the traceback guard (SD-02),
  then teaching-error/discoverability polish.

## What was intentionally NOT proposed (and why)

- Renaming jargon verbs/flags (`filter`, `rebase`, `-mi/-ml/-ic`, `.ocbox`, "subagent"):
  deferred on the COMPATIBILITY axis (Remediation Risk Medium-High). Renaming a shipped,
  documented CLI surface breaks users' muscle memory and scripts; each already carries a
  clear `help=` string, so the self-doc gain does not justify the compat cost. If ever
  pursued, do it with deprecated aliases in a dedicated compatibility IPD.
- Chaining the no-args screen to `doctor`/`config create`: the no-args "Next steps" screen
  is already strong; folded into SD-07's step only if trivial, else a small optional
  follow-up. Not a Fix-Bar deferral, just a nice-to-have.

## Open questions for the user

- OQ-1 (SD-07): add `reclaim` to `help maintain` only, or also a pointer in the plain
  overview? Leaning: `help maintain` at minimum.
- OQ-2 (SD-02): on an unexpected exception, prefer a clean `die()` message with a `-v` hint
  (proposed), or always show the traceback? Leaning: clean by default, traceback under `-v`.

## Method note

Evidence was gathered by a thorough read of the CLI help system, error/`die`/`RecoveryError`
sites, `build_parser` flag definitions, the no-args/onboarding path, and the TUI widgets'
labels/placeholders/empty states, then the two riskiest claims were re-verified directly.
No files were modified.
