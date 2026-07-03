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

## Section 3
## Section 4
## Section 5
## Section 6
## Section 8 (final eight-persona sign-off)
