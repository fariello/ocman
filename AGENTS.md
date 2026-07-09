# AGENTS

<!-- AGENT-WORKFLOWS:BEGIN -->
## Agent workflows

This repository includes reusable agent workflows under `.agents/workflows/`. They are invoked on demand and are NOT always-loaded context. See `.agents/workflows/index.md` for the list and how to run each (native `/commands` in OpenCode/Claude Code, or "read and execute <body path>" in any other agent).
<!-- AGENT-WORKFLOWS:END -->

## Plan / IPD lifecycle

Implementation plans and IPDs live under `.agents/plans/` and follow a two-stage lifecycle by directory:

- `.agents/plans/pending/` holds plans that are proposed but not yet executed. New plans go here. Give each a `Status:` line (e.g. `Status: PROPOSED (not yet executed)`) so its state is explicit.
- `.agents/plans/executed/` holds plans that have been carried out. Move a plan here (`git mv`) once its work is done.

Do not leave plans in the `.agents/plans/` root; a plan there is a location/status mismatch. Name plans `YYYYMMDD-<slug>-ipd.md`. Release-review workflows treat any in-scope plan still in `pending/` (or otherwise marked not-executed) as a loud warning, so keep a plan's directory and its `Status:` line in agreement.

## Prose conventions

No em dashes in authored prose (docs, comments, docstrings, CLI/help/error text, commit messages). Use a period, comma, colon, or parentheses instead. Two exceptions: a lone `—` used as a table "not available" glyph, and required-verbatim or quoted strings (e.g. the Apache `NOTICE` attribution). This is advisory, not a CI gate.
