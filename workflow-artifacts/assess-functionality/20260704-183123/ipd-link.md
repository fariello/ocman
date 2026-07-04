# IPD link

- IPD: `.agents/plans/pending/2026-07-04-assess-functionality-restart-to-project-prompts.md`
- Summary: Functionality IPD to auto-copy a generated `*.restart.md` into the working project's
  `.agents/prompts/pending/YYYYMMDD-<session_id>.restart.md` when that project uses an `.agents/plans` or
  `.agents/prompts` convention, with a `.restart.bu.NNN.md` (001+) backup on collision. Includes safe
  project-dir resolution, fail-soft cross-repo write, path containment, an opt-out, and restart-only scope.
  Key open question: precedence for "the project being worked on".
- Verdict: needs work (feature absent).
