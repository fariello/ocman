# Section 5: Feature / Usability / Maintainability (+ principles, TODO triage)

## What I did
- Exercised all eight personas over the 1.1.0 delta (notes in persona-review.md).
- Finalized the per-principle adherence verdict (guiding-principles-assessment.md): all four
  ARCHITECTURE design principles HELD, with two Low self-documenting nits.
- Finalized TODO/backlog triage (todo-reconciliation.md): the single `TODO.md` item (`ocman spend`)
  is an explicitly-informal future idea -> out-of-scope-for-release, leave tracked. No in-code
  markers. No must/should-before-release backlog.
- Reviewed maintainability of the delta: shared helpers (`check_egress_guards`,
  `resolve_recovery_collision`, `canonical_recovery_name`/`parse_recovery_name`) reuse existing
  primitives (`_backup_compacted_bu`, `check_opencode_process_lock`); no duplication; KISS held.

## Findings
- **S5-U1 (Low / RR Low):** `--force` now also overrides the `filter`/`--compact` size cap, but its
  `--help` text still mentions only the process-lock bypass. Self-documenting gap. Fix in S7
  (action S5-A1).

## Why
- Section 5 owns principles + TODO triage + the all-persona sweep; usability of the new escape
  hatches (`--force`, `--allow-secrets`) is exactly the self-documenting bar.

## What I considered but did NOT do
- Splitting `--force` into a separate `--max-bytes`/override flag: no - the security IPD
  deliberately reused `--force` (KISS, one idiom); the fix is to document it, not add a flag.
- Acting on `ocman spend`: out of scope (informal future idea, no committed work).
- Establishing new principle/orientation docs: ARCHITECTURE already carries them; no gap.
