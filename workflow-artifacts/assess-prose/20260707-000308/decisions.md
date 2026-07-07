# Decisions and assumptions - assess-prose run 20260707-000308

## Concern and scope
- Concern: prose (how the writing reads), assessed against
  `.agents/workflows/assess/references/prose-style.md`.
- Scope: whole-project prose (no path narrowing given). Excluded `.agents/workflows/` and
  `workflow-artifacts/` per the review-scope exclusions.
- Mode: assess (default). Interactive line-editing not requested.

## Project conventions discovered
- Principles: `ARCHITECTURE.md` + universal fallback. Prose standard = the framework reference.
- IPD lifecycle `.agents/plans/pending/` -> `executed/`; run records under
  `workflow-artifacts/assess-<concern>/<RUN_ID>/`.

## Key decisions / assumptions
- **Verdict "adequate," not "needs work":** the prose is already clean against nearly all the
  universal rules. The objective scans found NO prestige/inflation words and NO reflex transitions
  or generic openings/closings in the long-form docs. The single systemic universal-rule
  violation is the em dash (~54 occurrences). That is real but low-severity and low-risk to fix.
- **Did not invent issues.** The lens warns against manufacturing subjective rewrites. Since the
  writing conforms otherwise, the IPD proposes ONLY the em-dash normalization plus two protective
  exclusions, and explicitly records (PROSE-3) that the rest is clean so the pass is not mistaken
  for shallow.
- **Voice preservation is the governing constraint.** Proposed a per-instance punctuation choice
  (comma/colon/paren/period by context), NOT a mechanical `sed`, and deferred all subjective
  line-level rewrites on the usability/voice axis.
- **Two em-dash classes are protected (PROSE-2):** the Apache NOTICE attribution string (required
  verbatim by the license) and quoted user words (TODO.md:20 quotes the user's "super awesome").
  Rewriting either would falsify a required/verbatim string, so they stay. This is an honesty
  constraint, not a style exception.
- **My own 1.1.0-authored prose was checked and is clean:** the new naming/egress/collision/filter
  docstrings and error strings, the CHANGELOG 1.1.0 additions, and TODO.md introduced zero em
  dashes and zero prestige words. The em-dash corpus is pre-existing project text.

## What was intentionally NOT proposed and why (Remediation-Risk axis)
- Rewriting the NOTICE/quoted em-dash strings: usability/honesty (Medium-High) - required verbatim.
- Subjective sentence-level "improvements" beyond em dashes: voice (Medium-High) - the prose is
  already clean; chasing polish risks flattening the author's voice, which the reference calls a
  defect. Available via interactive mode only, on request.
- A blocking CI check for em dashes: complexity/usability - a hard gate could fail on a
  legitimately quoted em dash; proposed an advisory note instead.

## Open questions for the user (also in the IPD)
1. Confirm per-instance em-dash replacement (vs. one mechanical substitution). Proposed: per-instance.
2. Want the advisory no-em-dash note in AGENTS/CONTRIBUTING (and/or a non-blocking local check)?
   Proposed: one-line note, no CI gate.
3. If any test asserts an exact message string containing an em dash, update it in lockstep
   (none found in the scan; confirm during execution).
