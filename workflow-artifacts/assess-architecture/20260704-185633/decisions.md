# Decisions and assumptions - assess-architecture (destructive-confirm helper) 20260704-185633

## Concern / scope
- Concern: architecture and extensibility. Lens: architecture.md.
- Scope: NARROWED by the user to designing a shared destructive-confirmation / preview abstraction.
- Lead personas: architect (primary), software engineer, stakeholder.

## Project conventions discovered
- CLI (`ocman.py`) + Textual TUI; single-maintainer local tool; KISS + consistency principles.
- Plan lifecycle `.agents/plans/pending/` → `done/`. Validation `PYTHONPATH=. pytest`.
- Four duplicated typed-`yes` blocks (4705/4960/6074/7288); inconsistent styles; `--clear-history` (7607)
  has NO confirmation; TUI has separate async modals (app.py:136, 257).
- Out of scope (framework): `.agents/workflows/`, `workflow-artifacts/`.

## Key decisions
- Verdict **needs work**; the fix is a small seam, NOT a framework.
- **The abstraction = 3 pieces in ocman.py:** a `DestructivePreview`/`PreviewItem` dataclass, a **pure**
  `render_destructive_preview()` (color-independent KEEP/DELETE + all-affected warning), and a
  `confirm_destructive()` I/O seam (single typed-`yes` home). No new module/package/dependency.
- **Blast-radius discipline (architecture lens):** characterization tests FIRST; migrate the 4 live ops
  one-at-a-time; land clean-backups as the first adopter; incremental commits, no big-bang.
- **CLI/TUI split (ARCH-4):** share ONLY the pure render/summary; do NOT unify sync `input()` with the async
  Textual modal — deferred (functionality axis).
- **Anti-over-engineering (ARCH-6):** no config-driven/pluggable renderers/i18n — deferred (complexity axis).
- **Sequencing vs clean-backups IPD (ARCH-8):** this IPD supersedes that IPD's bespoke renderer; clean-backups
  becomes the first consumer of the shared helper. Keep the clean-backups IPD as the detailed row spec.

## What was intentionally NOT proposed (and why)
- Unifying CLI+TUI confirmation I/O: different interaction models; over-abstraction risk (deferred).
- A generalized "framework" (plugins/styles/i18n): over-scope for a single-maintainer tool (deferred).
- Changing WHICH items any op deletes or the selection/cutoff logic: out of scope (behavior-preserving refactor).

## Open questions for the user
1. Incremental sequencing (seam + clean-backups first, then migrate others one-at-a-time, then clear-history) OK?
2. `--clear-history`: add typed-`yes` confirm (+ a force/`--yes` bypass)?
3. Confirm CLI+TUI confirm I/O stays separate (share only the render/summary string)?
4. Mark the clean-backups IPD superseded, or keep it as the clean-backups-specific row spec that builds on the helper?
