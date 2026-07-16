# Plan Review (long / modular orchestrator)

Treat this file as the controlling instruction for reviewing and improving a
proposed implementation plan before code is written. This is the multi-file
("long") variant of `plan-review`: an orchestrator that loads one step at a
time to reduce directive drift. The single-file `../plan-review/plan-review.md`
is the equivalent portable version; the two are kept in deliberate parity.

## Memory kernel

These rules apply in every step:

1. Edit planning documents only. Do not implement code or configuration.
2. Verify material claims against repository evidence. Do not guess.
3. Fix findings by default. Severity does not decide whether to fix.
4. Defer only when the fix itself has Medium-High or High Remediation Risk on
   complexity, usability, security, or functionality.
5. Effort, time, cost, and tokens never justify deferral.
6. Resolve open questions with the human whenever interaction is available.
7. Never push or include unrelated files in a commit.
8. The reviewed/not-reviewed enumeration is the final output.
9. A gate or interactive question MUST NOT assert or imply the verdict it precedes (readiness, approval, GO); it states what was found and asks what to do. The verdict is formed only from the reviewed work's evidence.

Use `../release-review/fix-decision-policy.md` for the Fix Bar and
`../release-review/00-run-protocol.md` for the eight personas. Security is a
mandatory cross-cutting lens.

If those sibling files are absent, apply the same rules from memory.

## Boundary

Review and revise plans only. Do not change code, tests, runtime configuration,
infrastructure, production data, or deployment state.

## Execution rule

Execute the steps below in order. At the start of each step:

1. Re-read this Memory kernel.
2. Read the named step file in full.
3. Read any referenced rubric or template only when that step requires it.
4. Read the active step's exit gate last.
5. Complete the exit gate before proceeding.

Do not load all step files at once unless the environment forces you to.
Do not work from memory of a step read earlier.

## Parallel review of multi-plan batches (auto-engaged; TRIAL)

When the scope ledger (built in step 1) contains 2 OR MORE ELIGIBLE plans, the per-plan
review/verify phase AUTO-ENGAGES read-only audit lanes per the canonical convention in
`../release-review/00-run-protocol.md` ("Auto-parallel read-only audit lanes"): one lane reviews
each eligible plan in isolation (read it, verify every `path:line` claim against source, apply the
rubric + personas + security lens) and RETURNS a findings report plus proposed edits as suggestions.
Lanes are read-only: they do not edit plan files, resolve open questions, commit, or assign final
IDs. The coordinator (you) then works SERIALLY: synthesize the lane reports, run a CROSS-PLAN
conflict/overlap pass (lanes cannot see each other), resolve open questions interactively with the
human, apply all in-place edits, and make all path-scoped commits. With a single eligible plan, review
serially as usual (fan-out is pure overhead). A `--no-parallel` instruction forces serial. This is a
TRIAL. The single-file portable `../plan-review/plan-review.md` stays serial by design (see its note).

## Steps

1. Read and execute `01-discover-and-snapshot.md`.
2. Read and execute `02-review-and-revise.md`.
3. Read and execute `03-resolve-and-finalize.md`.

## Global stop conditions

Stop and record a blocker if:

- required evidence cannot be accessed and the plan cannot be reviewed safely;
- user changes cannot be separated from proposed commits;
- a required destructive or state-changing action would be needed;
- instruction conflicts cannot be resolved without human judgment;
- the plan's fundamental approach is unsound and needs replan.

Do not treat ordinary uncertainty as a stop condition. Record it and proceed
conservatively when safe.

## Completion

The run is complete only when:

- every scope-ledger item is accounted for;
- every finding has a decision;
- every deferral passes the Fix Bar;
- every resolvable question is resolved and written into the plan;
- plan status and workflow history are updated;
- commits are made or explained;
- the final report uses `report-template.md` exactly; and
- no output follows its final reviewed/not-reviewed enumeration.
