# IPD: Assess prose - em-dash normalization (the one systemic defect)

- Date: 2026-07-07
- Concern: prose (quality/style of the writing itself)
- Scope: project prose - `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `TODO.md`, code
  comments/docstrings/strings in `ocman.py` and `ocman_tui/app.py`, `scripts/`, and the
  authored IPDs in `.agents/plans/`. Excludes `.agents/workflows/` and `workflow-artifacts/`
  (framework + run records, out of review scope).
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Mode: assess (default). Interactive line-editing not requested.

## Goal

Bring the project's prose into conformance with the one universal style rule it currently and
systematically violates - no em dashes - without flattening the author's voice. The assessment
found the writing otherwise reads as clear, specific, authored prose with quiet force: no prestige
words, no reflex transitions, no generic openings/closings in the long-form docs. So this is a
narrow, high-signal, low-risk normalization, not a rewrite.

## Project conventions discovered (Step 0)

- Guiding principles: `ARCHITECTURE.md` "Design principles" (intuitive/self-documenting,
  configurable-over-hardcoded, KISS, honest documentation) + universal fallback. The prose
  standard applied is `.agents/workflows/assess/references/prose-style.md`.
- Pending-plans: `.agents/plans/pending/` -> `.agents/plans/executed/` (IPD house format).
- Stack/audience: single-maintainer local CLI/TUI; docs are developer-facing.
- Surface calibration (from the reference): universal rules apply everywhere; the full
  quiet-force bar applies only to long-form (README/ARCHITECTURE/CHANGELOG). Code comments and
  CLI error/help text are held to the universal rules but stay terse.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| PROSE-1 | Low | Low | nonfiction editor | em dashes (systemic) | The em dash (`—`) is used throughout project prose, violating the one hard universal rule. Approx. **54** occurrences: `ocman.py` 23, `CHANGELOG.md` 17, `README.md` 5, `TODO.md` 5, `ARCHITECTURE.md` 4. Most are parenthetical asides or appositives that a comma, colon, parenthesis, or period expresses at least as well. | grep `—`: ocman.py (e.g. 3562, 5205, 7019), README.md (13, 20-21, 96, 308), ARCHITECTURE.md (16, 29, 73, 82), CHANGELOG.md (many), TODO.md (11, 20, 24, 26) |
| PROSE-2 | Low | Medium-High (usability/voice) | nonfiction editor | quoted/required strings | Two em-dash hits must NOT be rewritten: the Apache NOTICE attribution string quoted in `CHANGELOG.md:60`/README (a required verbatim citation) and any user-provided quotations (e.g. `TODO.md:20` quotes the user's own words "super awesome ... "). Rewriting a required/quoted string would falsify it. | CHANGELOG.md:60 (NOTICE text); TODO.md:20 (user quote) |
| PROSE-3 | Low | Low | nonfiction editor | (positive / no action) | Beyond em dashes, the prose is clean: no prestige/inflation words (no leverage/robust/seamless/comprehensive-as-filler), no reflex transitions (moreover/furthermore), no generic openings/closings in README/ARCHITECTURE. The 1.1.0 code and docs authored in this session introduced **zero** em dashes and zero prestige words. Recorded so the pass is not mistaken for incomplete. | grep for prestige/transitions returned no long-form hits; new helper docstrings (ocman.py 3400-3560, 4860-5170) em-dash-free |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | PROSE-2 | First, **exclude the do-not-touch strings**: the Apache NOTICE attribution (CHANGELOG/README) and any quoted user words (TODO.md:20). Mark them so Step 2 skips them. | CHANGELOG.md:60; README (NOTICE line); TODO.md:20 | Low | Manual: those strings are byte-identical after the pass |
| 2 | PROSE-1 | Replace each remaining em dash with the plainest accurate punctuation, chosen per instance (not a blind sed): parenthetical aside -> commas or parentheses; appositive/expansion -> colon; two independent clauses -> period or semicolon. Preserve meaning and any intentional bluntness; do not merge/split sentences beyond what the punctuation change requires. Do it **by surface**: long-form docs (README/ARCHITECTURE/CHANGELOG/TODO) first, then code comments/docstrings/strings in `ocman.py`/`ocman_tui`. | README.md, ARCHITECTURE.md, CHANGELOG.md, TODO.md, ocman.py, ocman_tui/app.py | Low | `grep -rn "—"` over the scoped files returns only the Step-1 exclusions; a human reads the diffs to confirm no meaning changed and no voice flattened |
| 3 | PROSE-1 | Add a lightweight guard so em dashes do not creep back: either a one-line note in `AGENTS.md`/`CONTRIBUTING` ("no em dashes in authored prose") or an optional local check. Keep it advisory (do NOT add a hard CI gate that could block on a legitimately-quoted em dash). | AGENTS.md or CONTRIBUTING | Low | The note exists; no CI hard-fail added |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| PROSE-2 (rewriting the NOTICE/quoted strings) | Medium-High | usability/honesty | The Apache NOTICE attribution is a required verbatim string; altering it breaks the license's attribution requirement. User quotations must stay verbatim to remain honest attributions. These em dashes stay. | none |
| Line-level stylistic rewrites beyond em dashes | Medium-High | usability/voice | The prose is already clean against the other rules; hunting for subjective "improvements" risks flattening the author's voice (the reference explicitly warns against sanding off character). Not proposed. | Interactive mode only, if the author ever wants a line-by-line pass |

## Scope check

- Over-scope: do NOT do a blanket `sed 's/—/-/'` or a wholesale rewrite; that would risk the
  quoted strings and could flatten voice (Complexity/voice axes). Per-instance punctuation choice
  is the correct KISS fix. Do not add a blocking CI check.
- Under-scope: none. Em dashes are the only systemic universal-rule violation; PROSE-3 records
  that the rest of the prose already conforms.

## Required tests / validation

- After Step 2: `grep -rn "—"` across the scoped files returns only the Step-1 exclusions
  (NOTICE string, user quote).
- Human diff review confirms no sentence changed meaning and no blunt/terse line was inflated.
- `PYTHONPATH=. pytest` stays green (comment/string edits must not alter behavior; 172 passed,
  2 skipped baseline). Any test asserting on a specific message string is updated in lockstep.

## Spec / documentation sync

- N/A for behavior. This is a prose normalization; the only doc change is the optional
  no-em-dash note (Step 3). No user-visible behavior changes.

## Open questions

1. **Em-dash replacement default:** confirm the per-instance approach (choose comma/colon/paren/
   period by context) rather than a single mechanical substitution. (Proposed: per-instance.)
2. **Guard (Step 3):** do you want the advisory no-em-dash note in `AGENTS.md`, and/or an optional
   non-blocking local check, or nothing? (Proposed: a one-line note, no CI gate.)
3. **Test-string coupling:** if any test asserts an exact message containing an em dash, update
   the test with the string. (Assessment did not find one, but confirm during execution.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review`, or run this lens in **interactive mode** if you
   want to approve each rewrite).
2. On approval, execute Steps 1-3, validate with the grep + a human diff read, run the suite.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
