# Workflow: getting-started (guided tour and router)

Give a newcomer a guided, in-agent tour of this toolkit: what it is, the mental model,
and - most importantly - which workflow fits what they are trying to do right now, and how
to run it in their specific tool. This is the in-agent complement to the README on-ramp.

It ORIENTS and ROUTES. It is read-only and explanatory by default, and only runs another
workflow when the user says so. Safe to run any time.

## Do not duplicate the catalog or the README

This is a guide, not a second source of truth. For the full list of capabilities and the
installed version, point the user at `/list-workflows` (which reads the manifest). Do not
re-enumerate every workflow here or restate the README; route to the right one and hand
off. Keep the tour short and adaptive.

## Step 1: Detect context (tailor the tour)

Quietly check the repo so the tour fits the situation:

- Is the toolkit freshly installed, or already in use (any run records under
  `workflow-artifacts/`, any IPDs under `.agents/plans/`)?
- Has `setup-repo` likely been run (secret-scanning config, CI, `.gitignore`, the plan
  lifecycle dirs present)?
- What kind of repo is this (language/build, app vs. library, has tests/CI)?
- Which tool is the user in (affects how commands are run - see Step 4)?

Use this to bias the recommendation: a fresh, unset-up repo usually points to `setup-repo`
first; an established repo points to review/assess/ship workflows.

## Step 2: Explain the mental model (briefly)

In a few sentences, not a lecture:

- The spine: **discover (`spec`) -> build -> review -> ship (`release-notes`) -> operate
  (`incident`)**, with **`migrate`** for high-risk changes.
- Three modes of "review": **fix-in-place** (`release-review`), **propose-a-plan**
  (`assess <concern>`, `assess-all`), and **plan-time** (`plan-review`, before you build).
- **Coaching** (`advise <persona>`) is a conversation, not a report.
- **Guided/meta** workflows change files with your confirmation (`setup-repo`, `scaffold`);
  `verify` produces evidence; `list-workflows` shows everything.
- Where things land: assessment/plan proposals as IPDs in `.agents/plans/pending/`; durable
  run records under `workflow-artifacts/<workflow>/<RUN_ID>/`.

## Step 3: Ask the goal and route

Ask what they are trying to do, and route (offer to run the chosen workflow, with consent):

- "Set this repo up / make it conformant" -> `setup-repo`
- "Understand what this toolkit can do" -> `list-workflows`
- "Check one specific thing (security, tests, docs, ...)" -> `assess <concern>`
- "Get the whole picture across all concerns" -> `assess-all`
- "Review a plan before I build it" -> `plan-review`
- "Do a broad review and fix issues before shipping" -> `release-review`
- "Prove the checks actually pass" -> `verify`
- "Turn a fuzzy idea into a spec" -> `spec`; then `advise spec-editor` to harden it
- "Get expert questions on my design/plan" -> `advise <persona>`
- "Plan a risky migration" -> `migrate`
- "Write release notes / bump the version" -> `release-notes`
- "Do a post-mortem" -> `incident`
- "Add a new workflow/lens/persona to the toolkit" -> `scaffold`

If the goal is unclear, ask a clarifying question rather than guessing. If several fit,
recommend the best first step and explain why.

## Step 4: Show how to run it in THIS tool

- **OpenCode / Claude Code:** native slash command, e.g. `/setup-repo`, `/assess security`,
  `/advise skeptic`. Arguments are supported.
- **Codex, Cursor, Antigravity, VS Code Copilot, any other agent:** no repo-file
  slash-command mechanism - use the universal fallback: "Read and execute
  `.agents/workflows/<body path>`" (the body path is in `index.md` / `/list-workflows`).

Confirm which tool the user is in and give the exact invocation for the workflow you
routed to.

## Step 5: Point to depth

For more: `/list-workflows` (the live catalog + version), the `README.md` (on-ramp), and
`DECISIONS.md` (why the toolkit is the way it is).

## Guardrails

- Read-only and explanatory; run another workflow only with explicit consent.
- Orient and route; do not duplicate `/list-workflows` or the README.
- Adapt to the detected context and the stated goal - do not just recite a fixed script.
