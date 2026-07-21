# .agents/prompts/

Operational STAGING for prompts, organized by lifecycle state. Prompt files are named
`YYYYMMDD-HHMM-NN-<slug>.md` (the creating machine's local date and time; `NN` is a two-digit
per-minute sequence; `<slug>` is lowercase kebab-case), the same convention as plans.

Recognized prompt kinds (front-matter `Kind:`): run-once / research prompts QUEUED to be executed
(the original staging use), and `Kind: session-handoff` resume prompts produced by `/handoff` (a
prompt for the NEXT session rather than a task to run now). Handoff drafts are written to the
gitignored `local/` lane (below) and promoted only after review.

This is NOT the same as `.agents/docs/prompts/`. The two prompt homes are:

- **`.agents/prompts/`** (here): operational staging. "What prompt is queued to run?" A prompt lands
  in `pending/`, is run, and its lifecycle is tracked by MOVING it between the buckets below. Answer
  the question `ls .agents/prompts/pending/` with a glance.
- **`.agents/docs/prompts/`**: the evergreen, copy-paste prompt LIBRARY (reference material, not stamped
  with a framework version, not a run queue).

## The prompt -> results convention

A staged prompt produces RESULTS. Keep them apart:

- The PROMPT lives here (`.agents/prompts/<bucket>/`).
- Its RESULTS (the durable research/analysis you rely on) are filed under
  `.agents/docs/research/<topic>/` (see `.agents/docs/research/README.md`).

This separation follows the filesystem-encoded-state principle (GUIDING_PRINCIPLES P5, DECISIONS D91):
the prompt's lifecycle is glanceable from its directory; the results are durable, path-cited artifacts.

## The lifecycle

- **`pending/`** - queued to run, or being iterated on.
- **`executed/`** - the prompt has been run and its results filed (terminal; `done/` is an accepted alias).
- **`superseded/`** - replaced by a better/subsequent prompt; kept for the record.
- **`not-executed/`** - deliberately decided against, no replacement.
- **`reusable/`** - prompts meant to be re-run repeatedly (e.g. a recurring verification runbook); not a
  terminal state.

Retire a prompt by prepending a `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>` header and
`git mv`ing it to `superseded/` or `not-executed/`. Never silently delete a prompt; retiring preserves
the record and the reason.

## The `local/` quarantine lane (gitignored) - DECISIONS D94

`.agents/prompts/local/` is a GITIGNORED quarantine lane for raw, sensitive, or work-in-progress
prompts that must NOT be accidentally committed - most importantly `/handoff` session-handoff drafts,
which capture raw session context. It mirrors the inter-agent comms `local/` lane (D81): the directory
you write to IS the privilege level.

- **`local/`** (gitignored): never committed. Write raw/sensitive/WIP prompts here. A nested
  `.agents/prompts/.gitignore` ignores it (a created deliverable; it does not touch the repo root
  `.gitignore`). The installer materializes the dir so it is discoverable, but git does not track it
  empty and its contents can never be committed.
- **The tracked lifecycle buckets** (`pending/`, `executed/`, ...): durable prompts that travel with the
  repo, visible to other agents and humans.

To make a `local/` prompt durable: REVIEW and scrub it (remove secrets, personal/sensitive content;
consider `aw check-local-leaks`), then `git mv .agents/prompts/local/<file> .agents/prompts/pending/<file>`.
Promotion is a deliberate human act, never automatic.
