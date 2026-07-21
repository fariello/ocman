# prompts/pending/

Run-once and research prompts that are queued to run, or being iterated on before running.

Named `YYYYMMDD-HHMM-NN-<slug>.md`. When a prompt has been run and its results filed under
`.agents/docs/research/<topic>/`, move it to `executed/`. If a prompt is dropped instead of run, retire
it to `superseded/` or `not-executed/` - never leave an abandoned prompt here.
