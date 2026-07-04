# Lens: Prose quality and style (all prose in the project)

Focus the assessment on the **quality and style of the prose itself** - wherever words
are written for a human to read: repository docs, code comments and docstrings,
user-facing UI strings, error/log/help and CLI `--help` text, and (advisory) commit
messages and PR descriptions. The question is not "are the docs accurate/complete"
(that is the `documentation` lens) or "can a novice learn the product" (that is
`self-documentation`); it is "does the writing read as clear, precise, authored prose
with quiet force, free of the patterns that make writing feel generic or mechanically
generated."

## Lead personas

An exacting nonfiction editor (primary) and the software engineer (for comments/
docstrings/technical accuracy of the wording), with the complete-novice and UI/UX
views for user-facing copy.

## The standard

Assess against `../assess/references/prose-style.md` (the framework's distilled prose
style guide, adapted from the maintainer's nonfiction-prose toolkit). That reference
defines the universal rules (no em dashes, substance over decoration, modifier and
rhetorical restraint, honest evidence), the mechanical fingerprints to avoid (openings,
transitions, sentence structures, prestige words, rhythm and conclusion habits), the
positive "quiet force" model, and - importantly - how intensity varies by surface. Read
it and apply it; do not re-derive the banned lists here.

## Apply by surface (do not over-apply)

Per the reference's surface table: hold every surface to the universal rules, but apply
the full authored/quiet-force bar only to long-form prose. A code comment or a one-line
tooltip should be terse and plain; do NOT rewrite it into executive-memo cadence. The
most common real defects are: em dashes; inflated modifiers and prestige words;
generic openings and reflex transitions; section endings that reach for uplift instead
of the implication; and unsupported or overstated claims.

## Rubric

- **Mechanical fingerprints:** scan for the openings, transitions, sentence structures,
  prestige/filler words, and rhythm/conclusion habits in the reference. Flag by pattern,
  with location and the suggested plainer rewrite.
- **Em dashes:** flag every em dash (fast, objective, high-signal); propose a period/
  comma/colon/parenthetical/simpler-sentence rewrite.
- **Modifier and hyperbole discipline:** flag inflated modifiers and hyperbole not
  warranted by the evidence.
- **Honesty:** flag prose that overstates certainty, implies unsupported facts, or reads
  as aspirational rather than describing what is true today (cross-reference the
  `documentation` lens for doc-accuracy specifics).
- **Voice preservation (a constraint, not a target):** do NOT propose changes that
  flatten the author's voice, remove useful bluntness, or make prose more symmetrical/
  ornate/uniform. Preserve intentional plainness and useful friction. Sanding off
  character is a defect, not an improvement.
- **Surface fit:** flag prose whose register is wrong for its surface (a comment written
  like a memo; a UI string written like a paragraph).

## Two modes (the author chooses; default is assess)

Prose edits are voice-bearing and often numerous, so this lens supports two modes.
Infer the mode from `$ARGUMENTS` (e.g. an `interactive` flag) or ask if unclear.

- **Assess mode (default; consistent with the other assess-* lenses):** produce an IPD
  and run record. Because a repo-wide prose pass can surface hundreds of small nits,
  the IPD should lead with **systemic patterns** ("em dashes in N files"; "leverage/
  robust overused"; "three README sections end in generic uplift") and the
  highest-value specific rewrites, not an exhaustive line-by-line list. Group by
  surface and by pattern. Fix-by-default under the Fix Bar; the main deferral axis here
  is usability/voice (a "fix" that flattens voice carries real Remediation Risk).
- **Interactive mode (opt-in, author-in-the-loop):** walk the author through changes
  conversationally - show a passage, propose a revision, let them accept, edit, or skip
  - preserving voice at each step (this is where the toolkit's "read it yourself, remove
  any sentence you would not stand behind" discipline actually happens). Work
  surface-by-surface or file-by-file. Still record a run record of what was changed;
  in interactive mode you MAY apply accepted edits directly (with the user confirming
  each), which is the one assess lens that edits prose in place, by explicit consent.

## IPD emphasis

Lead with the objective, systemic wins (em dashes, prestige-word overuse, generic
openings/closings) - they are low Remediation Risk and high signal. Treat subjective
line-level rewrites as suggestions the author confirms, not mandates. Never propose a
change whose only effect is to make the prose more uniform. Cross-reference
`documentation` (accuracy/completeness) and `self-documentation` (in-product
learnability) rather than duplicating them; this lens owns *how the words read*, not
whether the docs are correct or the product is learnable.
