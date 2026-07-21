# Persona Review

Lead-persona notes appended per section (2-6); full eight-persona sign-off in Section 8.

## Section 1 (baseline)
- Stakeholder (8): whole 1.3.0 cycle shipped under assess/plan-review discipline; release posture is disciplined. Version-string-vs-CHANGELOG mismatch (DR01) is the one obvious "are we actually releasing?" gap.
- Software engineer (5): product diff cleanly scoped to cli.py + one TUI widget + packaging + tests; no sprawl.

## Section 2 (quality/security/edge cases)
- QA/QC (1): reconnect/kill happy path + survivor path + multi-instance choose + dry-run all exercised in code; no-arg vs pattern branches both covered. No new defect.
- Software engineer (5): db_rename_session closes the connection in finally on every path (no MEM leak); rename uses bound params (no injection). reconnect os.execvp is the intended point-of-no-return, nothing runs after it. Clean.
- Security architect (4): auth probe never touches non-loopback or user-supplied targets and never reads the password VALUE, only presence; fails to "unknown" not "secure" (no false all-clear). The only security finding is CI-hygiene noise (S01), not a live secret.

## Section 3 (tests/regression)
- Testing/regression expert (2): each S2 LIVE path (signal-wrong-process, survivor-no-exec, PID-reuse, zombie-gone) has a dedicated regression test using real child processes and SIGTERM-ignorers, not just mocks. The batch-delete VACUUM flake and Storage-worker race were fixed with deterministic waits this cycle. No brittle-test or coverage-gap finding.
- QA/QC (1): acceptance paths for all 5 new commands (happy + refuse + dry-run + no-match) are covered; the doctor server check covers all four verdict states plus the never-fail UNKNOWN degrade.

## Section 4 (docs/specs/examples)
- Complete novice (7): README command reference documents all 5 new commands thoroughly, each with safety notes, defaults, and the Linux-only caveat; a novice can learn reconnect/kill/rename from README alone without reading code. Good self-documenting posture. The broken AGENTS.md refs (DR03) only bite a contributor, not an end user.
- UI/UX (3): the new commands' help text and the doctor server-check remediation strings mirror the existing lr guidance (consistent terminology). No jargon/onboarding gap in the user-facing surface. Gaps are in maintainer/cold-start docs (ARCHITECTURE verb list A01, DECISIONS entry KD01), not user docs.

## Section 5 (feature/usability/maintainability) - all eight personas
- QA/QC (1): destructive paths (kill/reconnect) confirm-by-default + dry-run; no accidental-data-loss path. Covered.
- Testing/regression (2): comprehensive coverage confirmed in S3; no gap.
- UI/UX (3): consistent grammar and terminology across new commands; remediation strings reused from lr. Killed/survived feedback is clear. No friction finding.
- Architect (4): general-case solved (shared _instance_matches_pattern; reused detection/DB seams); no speculative bloat; KISS preserved. No M/GP finding.
- Software engineer (5): S2 confirmed clean resource handling and injection safety. Maintainable (reuses seams). No M finding.
- Power user (6): scriptable (--json on filters/doctor/lr; -y/--dry-run/--force escape hatches). reconnect foreground-exec is the expert-friendly behavior. No F finding.
- Novice (7): README teaches all commands; help/errors guide recovery; Linux-only caveat stated up front. No U finding for end users (contributor-facing DR03 aside).
- Stakeholder (8): the 1.3.0 goal (safer, more ergonomic local opencode administration: recover an orphaned session, stop a stray server, rename, spot insecure servers) is delivered and matches the CHANGELOG. Fitness for purpose met.
