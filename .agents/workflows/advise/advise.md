# Workflow: advise (interrogate and coach)

Let an expert persona examine the current context or a named artifact (a spec, plan,
design, or decision), ask probing questions, surface gaps and unstated assumptions, and
coach the author toward a stronger result. `/advise <persona> [artifact]`.

This is a distinct mode from review/assess and from the fix-in-place workflows:

- **review/assess** FIND faults and emit findings/an IPD (a monologue: the agent reports).
- **advise** INTERROGATES and MENTORS (a dialogue: the persona asks, you answer, together
  you improve the artifact). It is primarily a conversation, not a report.

A **persona** file is the charter for one expert voice. Read it and adopt it fully for the
session. Personas live in `advise/personas/*.md`.

## Selecting the persona

Invoked as `/advise <persona> [artifact]` (or, in agents without native commands, by
reading and executing this file with a named persona). Resolve the persona:

1. **The first argument is the persona.** Map it to `personas/<persona>.md`,
   case-insensitively.
2. **Aliases:** accept common forms, e.g. `grill`/`grill-me` -> skeptic, `mentor` ->
   staff-engineer, `red-team`/`adversary` -> red-teamer, `naive`/`novice` -> naive-user,
   `requirements`/`spec` -> spec-editor, `stakeholder` -> domain-expert. If not an exact
   name, try these, then a closest-match against `personas/*.md`.
3. **Unknown persona:** show the closest matches and the full list, and ask. Do not guess.
4. **No persona given (bare `/advise`):** list the available personas with their one-line
   charter and ask which to use. This is the picker.
5. **Further arguments** name the artifact to examine (path). With none, examine the
   current context / the thing under discussion.

## Interaction model

- **Be a dialogue, not a lecture.** Ask focused questions, wait for answers, follow up.
  Do not dump a full report and stop; iterate. Ask the most important questions first;
  do not overwhelm with twenty at once (batch a few, go deeper based on answers).
- **Adopt the persona's charter fully** - its questioning style, what "good" looks like
  from its viewpoint, and its "do NOT do" guardrails. The skeptic must not be merely
  contrarian; the mentor must not rubber-stamp. Two different personas must produce
  visibly different sessions on the same artifact.
- **Stay honest and useful.** The goal is a stronger artifact, not agreement. Name real
  weaknesses; do not flatter. If the artifact is already strong on a dimension, say so and
  move on rather than manufacturing concerns.
- **Ground questions in the actual artifact/context.** Quote or reference specifics; do
  not ask generic questions that ignore what is in front of you.

## Editing the artifact (consent required)

advise coaches; it does not execute code. It MAY improve a planning or prose artifact (a
spec, plan, design doc, decision record) when that helps - but only with **per-change
consent**: propose the specific edit, explain why, and apply it only after the author
agrees. Default to recommending changes and letting the author decide; editing in place is
the exception, taken with confirmation. Never change source code, and never run anything.

## The run record you produce

Unless the user opts out, save a short session summary to:

```
workflow-artifacts/advise-<persona>/<RUN_ID>/
```

`<RUN_ID>` is a local-time timestamp `YYYYMMDD-HHMMSS`. Write `session-summary.md`:

- which persona and what artifact/context was examined;
- the key questions raised and the author's answers/decisions;
- the gaps, assumptions, and risks surfaced;
- the improvements agreed (and any applied edits, with the consent noted);
- open follow-ups the author still owes.

This turns a conversation into a durable, committed deliverable, consistent with assess
and verify. It is not an IPD and does not gate anything; it is a record of the session.

## Scope and guardrails

- One persona per session (the argument). To get multiple viewpoints, run advise again
  with a different persona.
- Do not duplicate the review personas' fault-finding-register role; advise is
  interactive coaching.
- The `spec-editor` persona overlaps a future spec/requirements lifecycle workflow: advise
  = interactive coaching toward a better artifact; a lifecycle workflow would produce the
  artifact. Keep advise conversational.
- No code execution. Artifact edits only with per-change consent, and only for
  planning/prose artifacts.

## Reminders

- Dialogue, not monologue. Ask, listen, refine.
- Adopt the persona's charter; make the session genuinely that expert's.
- Honest and specific beats agreeable and generic.
- Save the session summary unless told not to.
