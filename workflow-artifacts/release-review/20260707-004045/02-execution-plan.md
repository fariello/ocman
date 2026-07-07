# 02 Execution Plan (how the review runs)

- Single continuous pass (not phase-isolated); serial (no parallel audit lanes: see 05-decisions).
- Focus: the 1.1.0 delta since v1.0.6 (filter, canonical naming, egress guards, collision safety,
  TUI parity, prose). The wider codebase was release-reviewed at 1.0.5 (run 20260705-003917); this
  run concentrates on new/changed surface while still applying each section's lens project-wide at
  a lighter depth.
- Independently re-verify the shipped result rather than trusting the executed-IPD text.
- Sections 1-6 audit; implementation-plan.md; Section 7 fix (expect few, since the delta was just
  assessed + plan-reviewed + executed this session); Section 8 Go/No-Go for 1.1.0; final report.
- Validation command: `PYTHONPATH=. pytest` (repo-native; CI matrix mirrors it).
