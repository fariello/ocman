# Persona Review

Per-persona observations accumulated across sections. Seeded in Section 1.

## Section 1 (inventory) — seed observations
- **Stakeholder (8):** Project delivers its stated goal (opencode session management) and ships on PyPI. CHANGELOG
  drift (no 1.0.3) slightly undermines trust in release hygiene.
- **Software engineer (5):** Monolithic `ocman.py` but well-sectioned; DB access uses manual try/finally
  consistently. One error-path connection leak found (S2-MEM1).
- **Novice (7):** README quickstart is strong; TUI has discoverable tabs. Will verify --help output in S4/S5.

(Sections 2-6 append their lead-persona observations below.)

## Section 2 (quality/security/edge/MEM/LIVE)
- **QA/QC (1):** Traced the delete-summary path — confirmed a real UnboundLocalError (S2-E1) when session
  metadata isn't fetched before showing the post-delete summary. Happy-path tests miss it.
- **Software engineer (5):** Export's second SQLite connection (ocman.py:5456) isn't in try/finally → leaks on
  error path (S2-MEM1). Move/delete/import DB ops are otherwise correctly transactional with rollback+finally-close.
- **Security-minded architect (4):** `zipf.extractall` on a user-supplied restore ZIP (ocman.py:6786) is a
  Zip-Slip vector (S2-S1, High). SQL uses parameterized values + hardcoded/allowlisted identifiers (safe).
  No pickle/eval/exec. API keys HTTPS-guarded and never printed. Import path traversal already defended.
- No new finding from power-user/novice/stakeholder specific to Section 2 beyond those carried forward.

## Section 3 (tests/regression)
- **Testing/regression expert (2):** Restore has happy-path + rollback tests but no Zip-Slip regression (T-1);
  import has strong SQLi + traversal rejection tests. Delete-summary metadata-absent path untested (T-2).
- **QA/QC (1):** 56 tests pass; move/export/import/backup/restore/cleanup all have coverage. Coverage is
  behavior-focused, not just quantity. Gaps map exactly to the two fixes this run will make.
- Note: `test_restore_rollback_safety` asserts error message `match="Restoration failed and rolled back"` —
  preserve that contract when editing restore.

## Section 4 (docs/specs/examples)
- **Complete novice (7):** README quickstart + argument reference + config template are strong; `ocman --help`
  has short forms and worked examples. A novice can get going without a manual. Good self-documenting bar.
- **UI/UX (3):** CHANGELOG drift (no 1.0.3) and two minor doc inaccuracies (clone URL S1-A2, rollback filename
  S4-U1) slightly erode trust. Architecture/decision docs missing for maintainers (S4-KD1).

## Section 5
## Section 6
## Section 8 (final eight-persona sign-off)
