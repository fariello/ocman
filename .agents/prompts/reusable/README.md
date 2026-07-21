# prompts/reusable/

Prompts meant to be re-run repeatedly (for example a recurring verification runbook), not a terminal
state.

A reusable prompt stays here across runs; its per-run RESULTS are filed under
`.agents/docs/research/<topic>/`. Keep the prompt self-contained so it can be re-run without the
surrounding session context.
