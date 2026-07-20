# 02 Execution Plan

(Created after initial Section 1 inspection.)

## Plan (delta re-review of v1.2.0)

Serial pass, Sections 1-8, focused on the 16-commit delta since the prior GO (20260719-140024)
while sanity-checking the whole. Emphasis:
- S2: verify the one product fix (extract_and_import_project rebase via _rebased_dir) for
  correctness, edge cases, LIVE/MEM; sanity-scan the rest.
- S3: verify the new/changed tests are meaningful and not weakened; confirm suite green.
- S4: confirm CHANGELOG + DECISIONS.md + README reflect the delta honestly.
- S5: TODO/principles/cold-start (mostly re-confirm; DECISIONS.md is new).
- S6: packaging (vistab floor), CI (fail-fast restore), schema (n/a delta).
- S7: implement S1-CI1 (fail-fast restore) + any new findings.
- S8: eight-persona sign-off + Go/No-Go for v1.2.0.
- S9: only on GO + explicit approval.
