# Assessment run report - architecture (shared destructive-confirmation/preview helper)

- Date / run ID: 20260704-185633
- Concern: architecture and extensibility
- Scope: NARROWED to designing a shared destructive-confirmation / preview abstraction
- IPD written: .agents/plans/pending/2026-07-04-assess-architecture-destructive-confirm-helper.md
- Verdict: **needs work** — the codebase has four duplicated, inconsistent destructive-confirmation blocks
  and no preview/outcome abstraction; a small, well-bounded seam fixes both and gives the KEEP/DELETE
  request a home. The main risk is over-generalization, which the plan constrains.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| ARCH-3 | High | Medium | architect / stakeholder | No preview/outcome abstraction — each op hand-rolls its "what's affected" view; KEEP/DELETE + total-loss warning has no home (the driver) |
| ARCH-1 | Medium | Low | architect / SW eng | Four duplicated typed-`yes` confirmation blocks |
| ARCH-2 | Medium | Low | architect / novice | Inconsistent confirmation UX; `--clear-history` has NO confirmation |
| ARCH-4 | Medium | Med-High | architect | CLI/TUI confirmation duplication; unifying sync+async I/O would over-abstract |
| ARCH-7 | Medium | Low | architect / QA | Refactoring 4 live destructive confirmations must preserve exact proceed/cancel behavior |

(Full list incl. ARCH-5/6/8 in `findings.csv`.)

## Proposed plan (summary)

Design a small seam in `ocman.py` (no new package/dependency):
1. Characterization tests pinning current confirm behavior of all four ops (safety net).
2. `DestructivePreview`/`PreviewItem` dataclass + a **pure** `render_destructive_preview()` (color-independent
   KEEP/DELETE, forceful all-affected warning) + a `confirm_destructive()` I/O seam (the single typed-`yes` home).
3. `cli_clean_backups` as the FIRST adopter (realizes the KEEP/DELETE request via the helper).
4. Migrate the other three CLI confirmations one-at-a-time behind their characterization tests.
5. Bring `--clear-history` under the helper (add its missing confirmation).
6. TUI reuses only the PURE render/summary (NOT the confirm I/O — sync vs async).
7. ARCHITECTURE.md/README/CHANGELOG.

## Deferred (with reason)

- Unifying CLI + TUI confirm I/O (ARCH-4): Remediation Risk Medium-High / functionality — sync `input()` vs
  async Textual modal are different interaction models; only the pure render/summary is shared.
- Config-driven/pluggable renderers, i18n (ARCH-6): Medium-High / complexity — over-generalization for a
  single-maintainer tool.

## Out-of-repo / organizational notes

- None. Pure internal refactor + one new seam; no dependency, no remote state.

## Next step

Review the IPD (optionally run `plan-review`) and approve before execution. This workflow did not execute the
plan and changed no application code. This IPD supersedes the bespoke renderer in the pending clean-backups IPD
(clean-backups becomes the first adopter here); sequence them together.
