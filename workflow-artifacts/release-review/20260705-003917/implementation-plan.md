# Implementation plan (Section 7)

Consolidated fix set from Sections 1–6. All items are Low Remediation Risk (fix-by-default). Two deferred
items (S2-M1 monolith split, S5-F1 `--yes` bypass) and one optional (S6-CI1) are NOT in this plan — see the
final report's "not addressed" table.

Target version for this release: **1.0.5** (semver patch; delta is fully backward-compatible). Confirmed by user.

## Batches (each committed separately)

### Batch A — Documentation accuracy (D1, D2, D3, D4, U1)
1. **D1** (High): README config template — rename `default_model` → `default_compaction_model`, value `""`,
   comment matching in-code template. (`README.md:~228`)
2. **D2** (Medium): README Argument Reference — add the missing rows: `-lp/--list-projects`,
   `-ls/--list-sessions`, `-P/--project`, `-A/--all-sessions`, `-D/--details`, `-H/--head`, `-T/--tail`,
   `-V/--version`, `-ir/--input-restart`, `-it/--input-transcript`, `-oc/--output-compact`,
   `--show-compaction-prompt`, `--show-logs`. (Skip suppressed `-m/--use-model`.)
3. **D3** (Low): ARCHITECTURE.md note the `preprocess_argv` natural-language commands (`disk`/`du`,
   `delete project`, `list …`, `show logs`); README preprocessing list add `disk`/`du` + `delete project`.
4. **D4** (Low): ARCHITECTURE.md add `css/` to the `ocman_tui/` layout.
5. **U1** (Medium): README — add a truthful positioning point. **Name ocgc**, phrased as the author's measured
   result: ocgc (OpenCode Garbage Collector, v0.1.0) claims to reclaim storage, but in the author's test the
   DB shrank only 2.9→2.8 GB; ocman's orphan-cleanup dropped the same DB 2.9→1.9 GB — because ocman deletes
   on-disk session-diff files AND runs `VACUUM` to physically shrink the SQLite file, reporting the reclaimed
   bytes. State the numbers as "in my testing", not as an unqualified absolute. (Verified against
   `ocman.py:5031-5047` VACUUM + file deletion.)

### Batch B — In-product self-documentation (U2)
6. **U2** (Low): `ocman.py:7288` `--create-config` prompt — change "Copy restart file …" to "Copy compacted
   file …" to match the corrected behavior. Keep the config KEY `copy_restart_to_project_prompts` (back-compat,
   S5-M2). Update the DEFAULT_CONFIG_TEMPLATE comment already done in the compacted-copy fix; verify wording.

### Batch C — Test coverage (T1)
7. **T1** (Low): add a focused unit test for `_per_project_disk_usage` (temp DB + fake session-diff files →
   assert per-project sessions/messages/tokens/diff_bytes rows). (T2/R1 optional — add T2 briefly if cheap.)

### Batch D — Packaging hygiene (P2)
8. **P2** (Medium): `pyproject.toml` sdist exclude — replace stale `repository-review/` with `.agents/` and
   `workflow-artifacts/` (and keep `opencode.json`/`opencode.jsonc`) so the PyPI sdist doesn't ship ~4MB of
   framework/run-record cruft. Verify with a local `python -m build` sdist listing (no dist artifacts committed).

### Batch E — Release version prep (R2)  [version bump only; NO publish]
9. **R2** (High): bump `ocman.py __version__` 1.0.4 → 1.0.5; `pyproject.toml version` → 1.0.5; finalize
   CHANGELOG `## [Unreleased]` → `## [1.0.5] - 2026-07-05` (and add a `### Documentation` note for D1/D2/U1/U2).
   This is version metadata + changelog only — it does NOT push, tag, or publish (those are Section 9, gated
   on user approval).

## Validation after each batch / at the end
- `PYTHONPATH=. pytest` (expect 126 → 127 with T1, still 0 failures).
- `py_compile`, `--version` (should print 1.0.5 after Batch E), `--help`.
- `python -m build` sdist content check for P2 (no `.agents/`/`workflow-artifacts/`).
- Re-diff README config template keys vs DEFAULT_CONFIG; re-cross-check arg table vs argparse.

## Out of this plan (deferred — see final report table)
- S2-M1 (monolith split): Medium-High complexity/functionality.
- S5-F1 (`--yes` destructive bypass): Medium-High security/usability.
- S6-CI1 (build+secret CI gate): optional, Medium; single-maintainer maintenance cost.
- S3-T2 / S3-R1: optional low-value; add T2 only if trivial, else note.

## Pending-plan reconciliation
`.agents/plans/pending/20260705-assess-documentation.md`: its D1–D4 are executed by Batches A above. After
Section 7 lands, this IPD is closeable (move pending→executed) — but per the pending-plans rule the review
does not silently execute/move it; recommended as a post-review step for the user, noted in the S8 WARNING.
