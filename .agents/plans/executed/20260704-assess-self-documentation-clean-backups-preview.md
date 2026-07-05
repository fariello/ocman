# IPD: Assess self-documentation - clean-backups KEEP/DELETE preview + all-deleted warning

- Date: 2026-07-04
- Concern: self-documentation ("errors/prompts that teach") + UI/UX
- Scope: NARROWED (user request) to the `ocman --clean-backups` confirmation output.
- Status: EXECUTED (2026-07-04; realized as the first adopter of the shared destructive-confirm seam)
- Author: OpenCode / its_direct/pt3-claude-opus-4.8-1m-us

## Goal

Before confirming a destructive backup purge, show the user the full picture: list **all**
backups, tagging each red **DELETE** (past the cutoff) or green **KEEP** (retained), so the
outcome is visible. If the purge would remove **every** backup, say so forcefully (no
rollback safety would remain). Distinction must survive without color.

## Project conventions discovered (Step 0)

- Guiding principles: none dedicated; universal fallback + `ARCHITECTURE.md` (self-documenting,
  honest docs, KISS). This is the "prompts/errors that teach" + destructive-op-safety bar.
- Pending-plans: `.agents/plans/pending/`; validation `PYTHONPATH=. pytest`.
- Target: `cli_clean_backups(days, dry_run, verbosity)` at **ocman.py:7224-7331**. It scans
  `default_backup_dir` for items named `opencode-backup-*` / `rollback-before-restore-*` /
  `opencode-db-cleanup-*`, collects only those with `st_mtime < cutoff` into `backups_to_delete`,
  prints just those, then prompts. Color helpers exist: `color_red`/`color_green`/`color_bold`/
  `color_yellow` (ocman.py:147-166). Size rendering: `human_size_local`.
- Domain invariant (safety): this is a **destructive** command; the change must make the outcome
  MORE visible and MUST NOT weaken the existing typed-`yes` confirmation or the dry-run behavior.

## Findings

| ID | Severity | Rem. Risk | Persona | Finding | Evidence |
|----|----------|-----------|---------|---------|----------|
| CB-1 | Medium | Low | novice / UI-UX | Only doomed backups are listed; user can't see what survives | ocman.py:7237-7278 |
| CB-2 | High | Low | stakeholder / QA | No forceful warning when the purge removes ALL backups (100% of rollback safety) | ocman.py:7280-7288 |
| CB-3 | Medium | Low | QA | "older than N days" header + "Created:" (actually st_mtime) can mislead | ocman.py:7263, 7277 |
| CB-4 | Low | Low | software engineer | Keep-set is not collected (needed to show KEEP rows) | ocman.py:7239-7256 |
| CB-5 | Low | Low | UI-UX | Column alignment breaks when ANSI color tags are added (padding counts escape bytes) | ocman.py:7278 |
| CB-6 | Low | Medium (complexity) | power user | Listing ALL backups could bury DELETE rows at scale | behavioral |
| CB-7 | Low | Low | QA | Dry-run should show the same annotated view + warning | ocman.py:7283-7285 |
| CB-8 | Low | Low | accessibility | Must not rely on color alone (color-blind / no-color terminals) | new output |
| CB-9 | Low | Low | novice / UI-UX | No column headers; the reader must infer that the fields are name/size/date. Add a header row: `Backup`, `Size`, `Created`/`Modified`, `Action`. | ocman.py:7263-7278 (no header printed) |
| CB-10 | Low | Low | UI-UX | Size column is left-aligned (`{human_size_local(size):<10}`), so numbers don't line up by magnitude (e.g. `56.00 KB` vs `4.43 GB`). Right-align the Size column. | ocman.py:7278 |

## Proposed changes (ordered, validatable)

> **Sequencing (plan-review):** the sibling architecture IPD
> (`20260704-assess-architecture-destructive-confirm-helper.md`) is the source of truth for the
> **shared renderer** `render_destructive_preview()` (column headers, right-aligned Size, color-independent
> DELETE/KEEP `Action`, all-affected warning) and the `confirm_destructive()` seam. If that IPD lands first
> (recommended), this plan's steps 2/4/5 are realized by **building the `DestructivePreview` and calling the
> shared helper** rather than re-implementing the table — steps 2/3/5 below then describe the clean-backups
> *inputs* (which items are DELETE vs KEEP, the `Backup`/`Size`/`Modified`/`Action` labels) to that helper.
> The header + right-align (CB-9/CB-10) live in the shared renderer so all destructive commands match. If
> this plan is executed standalone instead, implement the table inline per the steps below.

| Step | Source IDs | Change | Files | Rem. Risk | Validation |
|------|-----------|--------|-------|-----------|------------|
| 1 | CB-4 | In the single scan pass, collect **both** `to_delete` and `to_keep` lists of `(item, mtime, size)`. Compute size once per item here (reuse the existing `dir_usage()` helper at ocman.py:6210 for directory backups — the executed disk-usage feature already added it — rather than a fresh `os.walk`), reused for both display and the reclaim total. | ocman.py:7239-7256, 6210 | Low | Unit test: given a temp backup dir with mixed mtimes, the two lists partition correctly at the cutoff |
| 2 | CB-1, CB-8, CB-5, CB-9, CB-10 | Render an annotated table of **all** backups with **column headers** `Backup`, `Size`, `Created`/`Modified` (per CB-3), `Action` (CB-9) and a separator rule. Each row: name (left-aligned), **size right-aligned** in its column (CB-10), date, and an `Action` cell with the literal word `DELETE` (red) or `KEEP` (green). Compute each column's width from the plain-text content, then **pad plain text before applying color** so alignment holds with color on/off (CB-5); the DELETE/KEEP words carry meaning, color is enhancement only (CB-8). Sort DELETE rows first (oldest→newest), then KEEP rows. | ocman.py:7262-7281 | Low | Test (color forced off): a header row with `Backup`/`Size`/`Action` is present; the Size column is right-aligned (values share a right edge); a DELETE row per doomed item and a KEEP row per retained item |
| 3 | CB-6 | Always list DELETE rows in full. For KEEP rows, list them in full up to a threshold (e.g. 20); beyond that, print the first few then `… and N more kept` — unless `-v`, which lists all. Keeps the actionable DELETE signal from being buried. | ocman.py (render) | Low | Test: with > threshold keeps, output summarizes; with `-v`, all keeps shown |
| 4 | CB-2 | After the table, compute `kept = len(to_keep)`. If `kept == 0` and `len(to_delete) >= 1`, print a prominent red block: `WARNING: this will delete ALL <N> backups — NO rollback backups will remain.` Otherwise print the normal `N to delete, M kept` summary + reclaim size. | ocman.py:7280-7281 | Low | Test: all-old set → ALL-backups warning present; partial set → warning absent, "M kept" shown |
| 5 | CB-3 | Header/summary: keep the day count but also show the concrete cutoff timestamp (already computed as `cutoff_time`) e.g. `Deleting backups modified before <cutoff ts> (older than <days> days)`. Relabel the per-row `Created:` → `Modified:` (it is `st_mtime`). | ocman.py:7263, 7277 | Low | Test: header shows cutoff ts; row label is "Modified" |
| 6 | CB-7 | Ensure dry-run renders the identical annotated table + ALL-backups warning, then stops before the prompt/delete (as today). No behavior change to the typed-`yes` confirmation on the real path. | ocman.py:7283-7295 | Low | Existing behavior preserved; dry-run test shows table+warning, deletes nothing |
| 7 | docs | README (backup section) notes the KEEP/DELETE preview and the all-backups warning. CHANGELOG `[Unreleased]`. | README.md, CHANGELOG.md | Low | Docs only |

## Deferred / out of scope (with reason)

| Finding ID | Rem. Risk | Axis | Reason | Recommended later step |
|------------|-----------|------|--------|------------------------|
| (age-based `--clean` session purge preview) | — | scope | The request is specifically about `--clean-backups`; applying the same KEEP/DELETE treatment to the session `--clean` prompt is a separate (though analogous) change | Consider a follow-up for `db_run_cleanup`'s confirmation if wanted |

## Scope check

- **Over-scope (avoid):** No new dependency; no interactive per-item selection; do not change which
  items are deleted or the cutoff math; do not touch the session `--clean` prompt (separate command).
- **Under-scope (add):** the KEEP/DELETE full view (CB-1), the ALL-backups warning (CB-2), and
  color-independent labels (CB-8) are the core of the request and are proposed.

## Required tests / validation

- `PYTHONPATH=. pytest` stays green + new unit tests (seed a temp backup dir with fixed mtimes/sizes;
  monkeypatch `default_backup_dir` and `input`): partition correctness (step 1); annotated table shows
  a **header row** (`Backup`/`Size`/`Modified`/`Action`, CB-9), the **Size column right-aligned** (values
  share a right edge, CB-10), DELETE per doomed + KEEP per retained with correct labels and alignment when
  color is forced off (steps 2/5); ALL-backups warning present iff kept==0 (step 4); KEEP summarization past
  threshold and full under `-v` (step 3); dry-run shows table+warning and deletes nothing (step 6).
  Reuse/extend the existing `test_clean_backups` fixture.
- Determinism: force NO_COLOR (or call the color helpers' no-color path) in assertions so tests match
  plain text, independent of terminal.

## Spec / documentation sync

- README backup/restore section: document the KEEP/DELETE preview and the ALL-backups warning.
- CHANGELOG `[Unreleased]` entry (Changed/Added).

## Open questions

1. KEEP-summarization threshold (proposed 20) and `-v`-shows-all — acceptable? Or always list every KEEP
   row regardless of count? (Assumption: summarize beyond 20, full under `-v`.)
2. Sort order: DELETE rows first (oldest→newest) then KEEP rows, or one combined chronological list with
   inline tags? (Assumption: DELETE-first grouping, since DELETE is the actionable set.)
3. Should the same KEEP/DELETE treatment also apply to the session age-based `--clean` confirmation
   (`db_run_cleanup`)? (Assumption: out of scope for this change; separate follow-up.)

## Execution outcome (2026-07-04)

Executed as the **first adopter** of the shared destructive-confirmation seam (built in
`20260704-assess-architecture-destructive-confirm-helper.md`). All steps done:

- Step 1 (CB-4): scan collects both `to_delete` and `to_keep`; directory sizes via the existing
  `dir_usage()` helper. Step 2 (CB-1/5/8/9/10): renders a headered table (`Backups`/`Size`/
  `Modified`/`Action`) with **right-aligned Size** and color-independent `DELETE`/`KEEP` words.
  Step 3 (CB-6): KEEP rows summarized beyond 20, full under `-v`. Step 4 (CB-2): forceful
  "delete ALL N backups" warning when nothing is kept. Step 5 (CB-3): header names the concrete
  cutoff timestamp; per-row label is `Modified`. Step 6 (CB-7): dry-run shows the same table and
  deletes nothing; typed-`yes` confirmation preserved via `confirm_destructive`. Step 7: README +
  CHANGELOG.
- Tests: characterization (cancel/dry-run) + KEEP/DELETE preview, all-deleted warning, right-align.
- Verified live on the real backups dir (22 delete / 5 keep, 7.23 GB, right-aligned, cutoff header).
- Validation: `PYTHONPATH=. pytest` → 107 passed, 2 skipped.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT
auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute the ordered steps and run the validation.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
