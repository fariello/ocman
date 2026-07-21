# Prose style reference

The style standard the `assess-prose` lens checks against. It is a distilled,
surface-agnostic version of the nonfiction-prose discipline: write with quiet force,
earn authority through specificity and evidence rather than decoration, and avoid the
patterns that make prose read as mechanically generated.

Origin: adapted from an internal nonfiction-prose prompt toolkit maintained by the
author. That toolkit targets executive/board/long-form documents; this reference keeps
the rules that apply to ALL prose and marks where intensity varies by surface. It is
framework-owned so it travels with an install.

## Apply by surface (do not over-apply)

Hold every surface to the **universal rules** below. Apply the **full authored/quiet-
force bar** only to long-form prose (docs, guides, reports). Do not impose executive-
memo cadence, structure, or register on terse or technical surfaces.

| Surface | What to hold it to |
|---|---|
| Docs, guides, READMEs, long-form | Universal rules + the full quiet-force/positive-style bar and honest-evidence discipline. |
| Code comments & docstrings | Universal rules, plus: say what the code does and why, concisely; no filler, no inflation. Terseness is correct here - do not add cadence. |
| UI strings / labels / user-facing copy | Universal rules, adapted to brevity: concrete, plain, no prestige words, no drama. A one-line label is not a paragraph. |
| Error / log / help / CLI `--help` text | Universal rules + be specific and actionable (say what happened and what to do); no vague inflation. |
| Commit messages / PR descriptions (advisory) | Universal rules; state what changed and why. Advisory only (history). |

## Universal rules (all prose)

### No em dashes
Do not use em dashes. Rewrite with a period, comma, colon, parentheses, or a simpler
sentence.

### Prefer substance over decoration
Concrete nouns, active verbs, named actors, specific consequences, measured claims.
Replace abstractions with the actual actor, action, constraint, decision, or
consequence. Replace ornamental verbs with plain verbs. Replace dramatic emphasis with
specificity.

### Modifier and rhetorical restraint
Review adjectives and adverbs with suspicion; remove any modifier that does not add
factual precision, useful emphasis, or necessary qualification. Do not use hyperbole.
Claims of seriousness, novelty, urgency, crisis, transformation, or exceptional
importance should be rare and used only when the evidence specifically warrants them.

### Honest evidence
Do not invent facts, citations, quotations, statistics, dates, or sources. Distinguish
what is known, inferred, assumed, and uncertain. Flag unsupported claims rather than
smoothing over the gap. A citation must support the specific sentence it is attached to.

## Mechanical fingerprints to avoid (the core check)

### Openings
"In today's rapidly changing environment"; "In an era defined by"; "Now more than
ever"; "As we navigate"; "The modern world demands"; "Organizations today face
unprecedented"; "Across industries"; "At a time when"; "It is important to note"; "It is
worth noting".

### Transitions (replace with the actual logic: cause, consequence, contrast,
qualification, evidence, risk, decision)
"Moreover"; "Furthermore"; "Additionally" (overused); "That said" / "To be sure" (as a
reflex); "Importantly"; "Significantly"; "Interestingly"; "Taken together"; "In short"
(introducing a slogan).

### Sentence structures (scrutinize; keep only if the most accurate option)
"Not only X, but also Y"; "Both X and Y"; "Whether X or Y"; "From X to Y"; "More than
just X"; "This is not merely X; it is Y"; "At its core, X is about Y"; "The challenge is
not X, but Y"; "The question is not whether X, but how Y"; "In an era of X, Y must Z";
"X serves as a reminder that Y"; "X is a testament to Y"; "What emerges is a picture of
X"; "This underscores/highlights the need for X"; "The path forward requires X"; "The
takeaway is clear"; "Ultimately, X"; "Moving forward, X".

### Prestige words / filler abstractions (use only when technically precise)
delve, underscore, highlight (vague), leverage (unless financial/technical), robust
(unless specific), seamless, transformative, critical/crucial (unless genuinely so),
pivotal, dynamic, holistic, comprehensive (when it only means broad), meaningful
(vague), impactful, scalable (unless scale is the issue), innovative (unless
demonstrated), groundbreaking, cutting-edge, best-in-class, world-class, game-changing,
ecosystem/landscape/journey/tapestry/intersection (unless literal), stakeholder (when a
specific group can be named), unlock, elevate, foster, empower, navigate/drive (vague),
catalyze, harness, optimize (when it means improve), utilize (when "use" works), myriad,
nuanced (when unexplained), rich/deep (as filler); and the inflation words:
extraordinary, profound, unprecedented, historic, grave, urgent, vital, sweeping,
dramatic, remarkable, exceptional, devastating, catastrophic, existential.

### Rhythm and paragraph habits
Do not make every paragraph the same length; do not end every section with a neat
generalization or uplift (close with the implication, risk, decision, or next step); do
not rely on repeated triads ("clear, concise, and compelling"); do not manufacture
balance by giving every point a matching counterpoint; do not overuse parallel
structure; avoid rhetorical questions unless requested; avoid one-sentence paragraphs
used only for emphasis; avoid colon-driven dramatic reveals.

### Conclusion habits
Do not end with a broad moral, a generic call to action, "the path forward", "the
takeaway is clear", or a sentence that could fit almost any topic. End when the work is
complete.

## Positive model (so the fix is not sterile)
Write with quiet force. Prose should be specific rather than grand, measured rather than
dramatic, direct rather than ornate, dense rather than padded, clear rather than
simplified, confident rather than emphatic. Preserve useful friction: a blunt sentence
where appropriate, a qualified judgment where necessary, a plain transition. Do not sand
off the author's character or flatten prose into a compliance document.

## Judgment
These are warnings, not absolute bans. A listed word or structure may survive when it is
the most accurate option, not because it sounds impressive. The deeper issue is usually
sentence shape, paragraph rhythm, and generic logic, not any single banned word.
