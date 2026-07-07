# Assessment run report - prose (project-wide, assess mode)

- Date / run ID: 20260707-000308
- Concern: prose (quality/style of the writing)
- Scope: project prose (README, ARCHITECTURE, CHANGELOG, TODO, code comments/docstrings/strings
  in ocman.py + ocman_tui, scripts/, authored IPDs). Excludes `.agents/workflows/` and
  `workflow-artifacts/`.
- IPD written: `.agents/plans/pending/20260707-assess-prose.md`
- Verdict: **adequate** for prose (clean, authored, quiet-force writing; one systemic
  universal-rule violation - em dashes - which is low-risk to fix)

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| PROSE-1 | Low | Low | nonfiction editor | Em dashes are used systematically (~54: ocman.py 23, CHANGELOG 17, README 5, TODO 5, ARCHITECTURE 4), violating the one hard universal rule. |
| PROSE-2 | Low | Medium-High (usability/honesty) | nonfiction editor | Two classes of em-dash hit must NOT be rewritten: the required Apache NOTICE attribution string and quoted user words. Rewriting them would falsify a required/verbatim string. |
| PROSE-3 | Low | Low | nonfiction editor | (Positive) Otherwise the prose is clean: no prestige/inflation words, no reflex transitions, no generic openings/closings. The 1.1.0 code + docs authored this session added zero em dashes and zero prestige words. |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

1. Exclude the do-not-touch strings (NOTICE attribution, user quotes).
2. Replace each remaining em dash with the plainest accurate punctuation, per instance, by
   surface (long-form docs first, then code comments/strings). Preserve meaning and voice.
3. Add an advisory no-em-dash note (AGENTS/CONTRIBUTING); no blocking CI gate.

## Deferred (with reason)

- Rewriting the NOTICE/quoted em dashes: Remediation Risk Medium-High on usability/honesty - they
  are required-verbatim or user-quoted strings; altering them breaks attribution/honesty.
- Subjective line-level rewrites beyond em dashes: Medium-High on voice - the prose already
  conforms to the other rules and hunting for "improvements" risks flattening the author's voice
  (the reference explicitly warns against this). Offered only via interactive mode if wanted.

## Out-of-repo / organizational notes

- None.

## Next step

Review the IPD (optionally run `plan-review`, or run this lens in interactive mode to approve each
rewrite) and approve before execution. This workflow does not execute the plan.
