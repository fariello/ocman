# Evidence - assess-prose run 20260707-000308

## Standard applied
- `.agents/workflows/assess/references/prose-style.md` (universal rules + mechanical
  fingerprints + surface table). Read in full.

## Files inspected
- Long-form: `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `TODO.md`.
- Code prose: comments/docstrings/strings in `ocman.py`, `ocman_tui/app.py`,
  `scripts/migrate_recovery_names.py`.
- Authored IPDs in `.agents/plans/` (this session's work).

## Commands run (objective scans)
- Em dashes: `grep -rc "—"` over the scoped files ->
  ocman.py 23, CHANGELOG.md 17, README.md 5, TODO.md 5, ARCHITECTURE.md 4, ocman_tui/app.py 0
  (~54 total in project prose).
- Located each em dash: `grep -n "—" <file>` per file.
- Verified my 1.1.0 additions are em-dash-free: `sed -n '3400,3560p;4860,5170p' ocman.py | grep "—"`
  returned nothing; the 1.1.0 CHANGELOG region had only the (pre-existing, quoted) NOTICE line.
- Prestige/inflation + reflex transitions in long-form:
  `grep -niE "leverage|robust|seamless|transformative|crucial|...|moreover|furthermore|it is worth noting|in today's"`
  over README.md/ARCHITECTURE.md -> NO hits.
- Confirmed `TODO.md:20` "Super awesome" is a quoted user phrase (honest attribution), not authored inflation.

## Findings basis
- PROSE-1: the em-dash counts above.
- PROSE-2: CHANGELOG.md:60 is the Apache NOTICE attribution (required verbatim); TODO.md:20 is a
  user quotation.
- PROSE-3 (positive): the prestige/transition scans returned nothing in long-form; new-code
  docstrings are em-dash-free.

## Not exhaustively done / assumptions
- Did not enumerate every em-dash line in the report (the IPD leads with the systemic pattern +
  counts + representative locations, per the lens's "lead with systemic patterns" guidance).
- Subjective sentence-rhythm/voice judgments were deliberately NOT hunted (voice-preservation
  constraint); only objective universal-rule checks drove findings.
- Scope exclusions honored: did not assess `.agents/workflows/` or `workflow-artifacts/`.
