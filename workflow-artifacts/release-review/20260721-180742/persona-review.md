# Persona Review

Lead-persona notes appended per section (2-6); full eight-persona sign-off in Section 8.

## Section 1 (baseline)
- Stakeholder (8): whole 1.3.0 cycle shipped under assess/plan-review discipline; release posture is disciplined. Version-string-vs-CHANGELOG mismatch (DR01) is the one obvious "are we actually releasing?" gap.
- Software engineer (5): product diff cleanly scoped to cli.py + one TUI widget + packaging + tests; no sprawl.

## Section 2 (quality/security/edge cases)
- QA/QC (1): reconnect/kill happy path + survivor path + multi-instance choose + dry-run all exercised in code; no-arg vs pattern branches both covered. No new defect.
- Software engineer (5): db_rename_session closes the connection in finally on every path (no MEM leak); rename uses bound params (no injection). reconnect os.execvp is the intended point-of-no-return, nothing runs after it. Clean.
- Security architect (4): auth probe never touches non-loopback or user-supplied targets and never reads the password VALUE, only presence; fails to "unknown" not "secure" (no false all-clear). The only security finding is CI-hygiene noise (S01), not a live secret.
