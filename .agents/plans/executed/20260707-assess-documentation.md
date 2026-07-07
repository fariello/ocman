# IPD: Assess documentation - post-1.1.0 doc drift (CITATION version, README arg table)

- Date: 2026-07-07
- Concern: documentation
- Scope: project documentation (README.md, ARCHITECTURE.md, CHANGELOG.md, CITATION.cff, AGENTS.md, TODO.md). Framework dirs (`.agents/workflows/`, `workflow-artifacts/`, installer backups, `.claude/`, `.opencode/`, `node_modules`) excluded per review-scope rules.
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Keep ocman's user-facing documentation accurate and complete after the 1.1.0 release.
The docs are strong overall (README, ARCHITECTURE, CHANGELOG were all refreshed for
1.1.0), but two accuracy/completeness defects remain: the citation metadata still
advertises version 1.0.6, and the README Argument Reference table omits the
`--clean-backups` command that the prose documents and the code implements. Both are
low-risk, high-value fixes for the novice and operator personas: a wrong citation
version is published verbatim by GitHub's "Cite this repository" button, and a missing
table row means a reader scanning the canonical option list cannot find a real command.

## Project conventions discovered (Step 0)

- Guiding principles: `ARCHITECTURE.md` "Design principles" (incl. "Honest documentation:
  docs describe current behavior; the changelog tracks each release"). No separate
  `GUIDING_PRINCIPLES.md`.
- Pending-plans location/format used: `.agents/plans/pending/` (terminal dir
  `.agents/plans/executed/`); filename `YYYYMMDD-<slug>.md`; IPD carries a `Status:` line.
  This matches the executed IPDs already present.
- Contributor/spec-sync contract: `AGENTS.md` (agent-workflows pointer + the "no em dashes
  in authored prose" convention, advisory).
- Stack / relevant context: single-file CLI `ocman.py` (`__version__ = "1.1.0"`), Textual
  TUI under `ocman_tui/`, `pyproject.toml` at version 1.1.0, Apache-2.0. A prior
  documentation assessment ran 2026-07-05 (`.agents/plans/executed/20260705-assess-documentation.md`);
  this run covers drift introduced by the 1.1.0 release since then.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for whether to
act now. Persona = which reviewer perspective surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| DOC-1 | High | Low | Novice / operator (citer) | Accuracy | `CITATION.cff` still declares `version: "1.0.6"` and `date-released: "2026-07-05"`, but the shipped project is 1.1.0 (released 2026-07-07). GitHub's "Cite this repository" button and any CFF consumer will publish the wrong version. The README explicitly points users to this button as the citation source. | `CITATION.cff:16-17`; contrast `ocman.py:195` (`__version__ = "1.1.0"`), `pyproject.toml:7` (`version = "1.1.0"`) |
| DOC-2 | Medium | Low | Operator (scanning the reference) | Completeness | The README Argument Reference table (README.md:190-249) omits `--clean-backups` and does not surface its `--days` pairing there. The command exists in code (`ocman.py:4433`) and is described in the "Pruning Backups" prose section (README.md:313-319), so a reader who scans the canonical option table (the section that lists every other flag, including `--backup-opencode` and `--restore`) will not find it. | `README.md:190-249` (no `--clean-backups` row) vs `ocman.py:4433` and `README.md:313-319` |
| DOC-3 | Low | Low | Operator | Consistency | CHANGELOG heads the release `## [1.1.0] - 2026-07-06`, but the tag `v1.1.0` and GitHub release were published 2026-07-07. Minor date skew in an otherwise accurate, current changelog. | `CHANGELOG.md:5`; git tag `v1.1.0` (2026-07-07) |
| DOC-4 | Low | Low | Operator | Accuracy (minor) | The `filter FILE` table row (README.md:244) describes output as written "next to the source (or `-oc`)" but does not state the resulting filename shape, while the CHANGELOG documents it as `YYYYMMDD-HHMM-<session_id>.<scope>.compacted.md`. A one-clause addition would make the table self-consistent with the changelog. Not wrong, just incomplete. | `README.md:244` vs `CHANGELOG.md:14-15` |

Positive verifications (no action needed): README config "Default Layout Template"
(README.md:257-297) matches `DEFAULT_CONFIG`/`DEFAULT_CONFIG_TEMPLATE` exactly
(`ocman.py:213-290`), including the new `filter_max_bytes`/`filter_secret_scan` keys and
their defaults. Every non-suppressed CLI flag in the Argument Reference table maps to a
real `add_argument` (the deprecated `-m/--use-model` is `argparse.SUPPRESS`ed and correctly
omitted; `--format` is an opencode subprocess arg, not an ocman flag, and correctly absent).
README claims for `[dev]` extra, `tests/test_perf.py`, and `scripts/migrate_recovery_names.py`
all resolve to existing artifacts. ARCHITECTURE.md accurately reflects the 1.1.0 code
(canonical naming, `filter`, egress guards, destructive-preview seam).

## Proposed changes (ordered, validatable)

Fix by default; each item is safe, well-scoped, and verifiable. Order: inaccuracies
before gaps (per lens IPD emphasis).

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | DOC-1 | Bump `version:` to `1.1.0` and `date-released:` to the actual release date (`2026-07-07`) in the citation metadata. | `CITATION.cff:16-17` | Low | `grep 'version:' CITATION.cff` shows `1.1.0`; value equals `ocman.py` `__version__` and `pyproject.toml` version. Optional: validate with a CFF linter if available. |
| 2 | DOC-2 | Add a `--clean-backups` row (and note its `--days N` pairing / fractional days) to the Argument Reference table, placed near the other backup rows (`--backup-opencode`/`--restore`). Keep it one concise line consistent with existing rows; the detailed behavior stays in the "Pruning Backups" section. | `README.md` (table ~line 232-233) | Low | Table contains a `--clean-backups` entry; `grep -n 'clean-backups' README.md` returns both the table and the prose section. |
| 3 | DOC-3 | Correct the 1.1.0 changelog date to the release date (`2026-07-07`) for consistency with the tag, OR (author's call) leave as the authoring date. Trivial one-token edit. | `CHANGELOG.md:5` | Low | `CHANGELOG.md` `[1.1.0]` date matches the `v1.1.0` tag date. |
| 4 | DOC-4 | Extend the `filter FILE` table row with the output filename shape (`...written next to the source (or -oc) as YYYYMMDD-HHMM-<session_id>.<scope>.compacted.md`), matching the changelog. | `README.md:244` | Low | Row mentions the canonical output name; consistent with `CHANGELOG.md:14-15`. |

## Deferred / out of scope (with reason)

None. All findings are Low Remediation Risk documentation edits; nothing warrants
deferral (deferral requires Medium-High+ Remediation Risk, and effort is never a reason).

## Scope check

- Over-scope (untraceable to a need): none proposed. Explicitly avoiding gold-plating:
  not adding version strings to README/ARCHITECTURE prose (they currently carry none,
  which is the correct low-maintenance choice; DOC-1 keeps the single canonical citation
  version in `CITATION.cff` only).
- Under-scope (needed capability missing): DOC-2 is the one genuine gap (a real command
  absent from the canonical option table); proposed for addition.

## Required tests / validation

Documentation-only changes; no code or test changes. Validation is by inspection and grep:

- `grep 'version:' CITATION.cff` -> `1.1.0`; equals `__version__` in `ocman.py:195`.
- `grep -n 'clean-backups' README.md` -> matches in both the Argument Reference table and
  the Pruning Backups section.
- Re-read the changed README rows to confirm formatting matches surrounding table rows
  (pipe alignment, wording style).
- No em dashes introduced (AGENTS.md prose convention).
- Full suite remains green as a sanity check (unaffected): `PYTHONPATH=. pytest`.

## Spec / documentation sync

This IPD *is* the documentation sync. No user-visible product behavior changes, so no
code/spec updates are required. `AGENTS.md` prose convention (no em dashes) applies to
the edited text.

## Open questions

Resolved with the user on 2026-07-07 (interactive):

1. DOC-3: **Yes, align the CHANGELOG 1.1.0 heading date** to the chosen release date.
2. Release date for DOC-1 and DOC-3: **use the git-tag / GitHub release date
   `2026-07-07`** (not the PyPI upload date). So `CITATION.cff` `date-released` becomes
   `2026-07-07` and the CHANGELOG heading becomes `## [1.1.0] - 2026-07-07`.

No open questions remain.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes, run the validation, and sync specs/docs.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`
   per the project's lifecycle convention.
