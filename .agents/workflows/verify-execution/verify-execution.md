# Verify Execution (cross-check that an executed plan was actually done)

Treat this file as the controlling instruction for verifying that an EXECUTED implementation
plan (IPD) was actually implemented as written, and for emitting a corrective plan when it was
not. This is how one agent cross-checks another agent's (or a past session's) execution.

It is the post-execution sibling of the reviews: `/plan-review` reviews a plan BEFORE building;
`/release-review` reviews a whole repo before shipping; `/verify-execution` reviews whether a
specific plan's execution MATCHES the plan.

It shares this framework's policies rather than redefining them:

- **Fix Bar** (`../release-review/fix-decision-policy.md`): used only to RATE the gaps it reports.
  This workflow never fixes; it reports and emits a corrective plan.
- **Evidence discipline**: re-open the actual `path:line` and diff; never trust a commit message
  or a walkthrough's claim of success.

If the sibling policy files are absent, apply the same rules from memory.

---

## What this command does and does NOT do

- IT DOES: read an executed plan, its commit(s), and the resulting diff; check each required change
  was actually done; re-run the repo's real validation; write a run record; and, for any gap, EMIT a
  corrective IPD.
- IT DOES NOT: change application code, tests, or configuration; fix the gaps in place; or push. The
  corrective IPD is executed separately, by whichever agent, later.

---

## Concurrency rule (this workflow is often run WHILE another agent is active)

This command is typically run to cross-check work another agent may STILL be doing in the same repo.
Therefore:

- Commit ONLY the file(s) THIS workflow creates (its corrective IPD and its run record), path-scoped:
  `git commit -- <exact-path> ...`. NEVER a bare `git commit`, `git add -A`, or `git commit -a` - the
  other agent may have unrelated files staged, and a bare commit would sweep their in-flight work into
  yours.
- Do NOT stage, amend, revert, `git mv`, or reset any file this workflow did not itself create.
- Do NOT rewrite history while another agent may be active.
- If the working tree or index shows another agent's in-progress changes, that is expected: leave them
  entirely alone.

(Learned the hard way: a bare commit here once swept a concurrently-running agent's staged renames
into the wrong commit, and a detached-HEAD investigation stranded a file.)

---

## Step 0: Identify the target and load its requirements

1. **The target** is an EXECUTED plan (its path is the argument). If it is missing, unreadable, or not
   a plan, stop and say so.
2. **Extract what the plan REQUIRED**, so you have a checklist to verify against:
   - its ordered proposed changes;
   - its required tests / validation and acceptance criteria;
   - its spec/doc-sync obligations;
   - any findings it agreed to fix during `/plan-review` (read the plan-review record / Workflow
     history) - these are part of "what was required".
3. **Discover the project's conventions** you will judge against (do not hardcode): guiding
   principles, the plan lifecycle/status vocabulary, the test/validation commands.

---

## Step 1: Discover the execution evidence

1. Find the commit(s) that executed the plan. Use the argument if given; otherwise derive them from
   `git log` and the plan's `## Workflow history`.
2. Read the ACTUAL diff of those commit(s). Do NOT trust the commit message or any walkthrough's
   claim - read what changed.
3. Note the pre-execution baseline where it matters (e.g. was the test suite already red BEFORE this
   execution?), so you can attribute problems honestly.

---

## Step 2: Check each required change was actually done

For every item from the Step 0 checklist, re-open the evidence at `path:line` in the diff and
classify it:

- **done** - implemented as specified;
- **partial** - started but incomplete;
- **missing** - claimed or expected but not present in the diff (a common false-completion signature:
  status set to `executed` and a walkthrough claiming success, but the code/tests unchanged);
- **diverged** - done differently than the plan said (verify it is still correct);
- **over-scope** - done but NOT in the plan (unrequested work; the Fix Bar default for over-scope is
  removal or a separate reviewed plan). Judge over-scope by COMPLEXITY/risk, not raw size.

Record each with `path:line` evidence and a Severity + Remediation Risk (for the corrective IPD).

---

## Step 3: Re-run the repo's real validation

1. Run the project's actual validation by reusing `/verify` (discover and run the repo's own
   test/lint/build/type-check commands; capture real exit codes). If `/verify` is unavailable, run the
   validation the plan itself specified.
2. **Attribute honestly:** distinguish failures INTRODUCED by this execution from a pre-existing red
   baseline. Never blame the execution for failures it did not cause; never excuse failures it did.
3. A red result that this execution introduced or left (when the plan required green) is a gap.

---

## Step 4: Verdict, run record, and (if needed) a corrective IPD

### Verdict

State exactly one:

- **MATCHES** - every required change done, validation passes (or the only red is a pre-existing
  baseline the plan did not own), no gaps.
- **DIVERGES** - the work differs from the plan (over-scope, diverged implementation, or a
  behavior-affecting change the plan did not authorize).
- **INCOMPLETE** - required changes are missing or partial, or the plan was marked executed while its
  own validation does not pass (false completion).

Then a **GO / NO-GO** on the real question: "should this plan be considered truly executed as
approved?" GO only when MATCHES and validation is genuinely green.

### Run record (ALWAYS)

Write a brief record to `workflow-artifacts/verify-execution/<RUN_ID>/` (RUN_ID = local
`YYYYMMDD-HHMMSS`): the plan reviewed, the execution commit(s), the per-required-change results, the
validation result (with baseline attribution), and the verdict. This is durable provenance even on a
clean MATCHES.

### Corrective IPD (only when there are gaps)

If MATCHES with green validation and no gaps, emit NO corrective IPD - say so. Otherwise write ONE
corrective IPD into `.agents/plans/pending/`, named
`YYYYMMDD-HHMM-NN-fix-<original-slug>-<short>.md`, that:

- states exactly what was missed / diverged / left red and what must be done to close it;
- cross-references the original plan and the execution commit(s);
- carries findings with Severity + Remediation Risk; NEVER fixes in place.

**Status of the corrective IPD (D65):** born `auto-approved` (ready to run without human review) when
the correction is fully specified, has zero open questions, corrects already-reviewed work, and is
LOW-COMPLEXITY/low-risk - judged by COMPLEXITY, not file count (a large mechanical `foo`->`bar` sweep
can auto-approve; a small risky refactor of critical logic cannot). Add an `Approval:` line
`auto-approved by /verify-execution <date>; not human-reviewed` and a Workflow-history line with the
rationale. Otherwise born `to-review`. Err toward `to-review` ONLY on genuine complexity uncertainty
(do not be super-cautious for its own sake - this corrects an already-hyper-cautious reviewed plan).
`auto-approved` is set by THIS checker, never by an executor fast-tracking its own work; and an
`auto-approved` plan still must pass its stated validation before being marked `executed` (D64).

---

## Required report format

```
## Verify Execution - <plan name>
Verdict: <MATCHES | DIVERGES | INCOMPLETE>
Readiness: <GO | NO-GO> - <one-line reason>

### Execution evidence
- Commit(s): <hashes>
- Baseline: <e.g. suite was green | 2 pre-existing failures>

### Required-change check
| Item | Result (done/partial/missing/diverged/over-scope) | Evidence (path:line) | Severity | Remediation Risk |
|------|---------------------------------------------------|----------------------|----------|------------------|

### Validation
- <command> -> <result>; attribution: <introduced by this execution | pre-existing>

### Run record
- workflow-artifacts/verify-execution/<RUN_ID>/

### Corrective IPD
- <path to emitted corrective IPD + its status (auto-approved | to-review)> | none (clean MATCHES)
```

Be rigorous and specific; cite `path:line`; do not invent gaps where there are none, and do not
find fault where the execution was faithful. The verdict + readiness is the point: say plainly
whether the plan was truly executed.
