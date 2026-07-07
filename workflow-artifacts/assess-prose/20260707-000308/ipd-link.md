# IPD link - assess-prose run 20260707-000308

- IPD: `.agents/plans/pending/20260707-assess-prose.md`
- Summary: Project-wide prose assessment. Verdict adequate. The prose is clean against nearly all
  universal rules (no prestige words, no reflex transitions, no generic openings/closings), and
  the 1.1.0 code+docs authored this session added zero em dashes/prestige words. The one systemic
  universal-rule violation is the em dash (~54 across ocman.py/CHANGELOG/README/TODO/ARCHITECTURE).
  Proposes a per-instance, voice-preserving em-dash normalization by surface, excluding the
  required Apache NOTICE attribution and quoted user words, plus an advisory no-em-dash note (no
  CI gate). Subjective line-level rewrites deferred on the voice axis.
