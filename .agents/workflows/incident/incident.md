# Workflow: incident (blameless post-mortem)

Conduct a structured, blameless post-mortem for a production incident: build the timeline,
assess impact, identify contributing factors (systemic, not personal), capture what went
right and wrong, and emit concrete follow-up actions as IPDs. This is the REACTIVE
complement to the preventive reliability / logging-audit / intrusion-detection lenses.

Guided and interactive. It writes a post-mortem document and emits action IPDs; it does
not change code.

## Honesty about scope (read first)

This workflow is REPO-SCOPED. The authoritative incident data - monitoring, SIEM, on-call
timelines, dashboards, customer reports - lives with the operator, not the repository.
This workflow structures the post-mortem and reasons from the code, config, and any
evidence the user provides. It must clearly mark what is known-from-evidence vs.
reconstructed-or-assumed, and it must not fabricate a timeline or a root cause it cannot
support. Ask the user for the operational facts; do not invent them.

## Blameless discipline

Focus on systems and contributing factors, never on individual blame. Phrase findings as
"the system allowed X" / "the process lacked Y", not "person Z erred". The goal is to make
the same failure harder next time, not to assign fault.

## Where it goes

Write the post-mortem to the project's convention (ask if unclear): `docs/incidents/`,
`docs/postmortems/`, or create `docs/incidents/`. Name it
`YYYY-MM-DD-<incident-slug>.md`. Emit follow-up action IPDs into the project's pending
plans directory (default `.agents/plans/pending/`), one per action, dated and named. These
run through the normal IPD -> plan-review -> approve -> execute pipeline.

## Protocol

1. **Gather the facts.** From `$ARGUMENTS` and the user: what happened, when detected, how
   detected, who/what was affected, current status. Ask for timestamps, logs, alerts, and
   any operator data. Mark each fact as evidenced or reported.
2. **Build the timeline:** detection -> escalation -> diagnosis -> mitigation ->
   resolution, with times. Note gaps where data is missing rather than filling them in.
3. **Assess impact:** who/what was affected, for how long, severity, data integrity, and
   any customer/financial/compliance dimension the user reports.
4. **Contributing factors (systemic):** the chain of conditions that let it happen - code
   defects, missing tests/alerts, config, process gaps, unclear ownership. Prefer "why did
   the system permit this" over a single "root cause".
5. **What went right / wrong:** honest assessment of detection, response, and communication.
6. **Follow-up actions:** concrete, owned, prioritized. Emit each as an IPD into pending/,
   cross-referenced from the post-mortem. Tie preventive actions to the relevant assess
   lens where useful (e.g. add tests -> assess-testing; add alerting -> logging-audit).
7. **Write and confirm:** review the post-mortem with the user; write it on confirmation;
   list the emitted action IPDs.

## Post-mortem structure

- **Summary:** one paragraph - what, impact, resolution.
- **Timeline** (with evidenced/reported markers).
- **Impact.**
- **Contributing factors** (systemic).
- **What went well / what did not.**
- **Follow-up actions** (each linked to its IPD).
- **Appendix:** evidence considered and its limits.

## Guardrails

- Repo-scoped and honest about it; never fabricate operational data or a root cause.
- Blameless; systems and processes, not people.
- Guided writes; confirm before writing the post-mortem and before creating action IPDs.
- Emits plans (IPDs) for action; it does not execute them.
