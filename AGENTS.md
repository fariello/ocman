# AGENTS

<!-- AGENT-WORKFLOWS:BEGIN -->
## Agent workflows

This repository includes reusable agent workflows under `.agents/workflows/`. They are invoked on demand and are NOT always-loaded context. See `.agents/workflows/index.md` for the list and how to run each (native `/commands` in OpenCode/Claude Code, or "read and execute <body path>" in any other agent).
<!-- AGENT-WORKFLOWS:END -->

## Prose conventions

No em dashes in authored prose (docs, comments, docstrings, CLI/help/error text, commit messages). Use a period, comma, colon, or parentheses instead. Two exceptions: a lone `—` used as a table "not available" glyph, and required-verbatim or quoted strings (e.g. the Apache `NOTICE` attribution). This is advisory, not a CI gate.
