# Assessment run report - functionality (copy restart.md into project prompts)

- Date / run ID: 20260704-183123
- Concern: functionality completeness
- Scope: NARROWED to auto-copying `*.restart.md` into `<project>/.agents/prompts/pending/`
- IPD written: .agents/plans/pending/2026-07-04-assess-functionality-restart-to-project-prompts.md
- Verdict: **needs work** (feature absent) — a clear, well-scoped addition; the main design risks are
  choosing the right "project" directory and doing the cross-repo write safely.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| RSP-2 | High | Medium (functionality) | architect / QA | "The project being worked on" is ambiguous (CWD vs --session-dir vs session.directory vs output_dir); wrong pick writes into an unintended repo |
| RSP-1 | Medium | Low | stakeholder | restart.md is not copied into the project's prompts dir today |
| RSP-3 | Medium | Low | QA | `YYYYMMDD` must come from session last-updated (epoch-ms string; may be "unknown") |
| RSP-4 | Medium | Low | software engineer | Requested `.restart.bu.NNN.md` (001+) scheme differs from existing `_backup_if_exists` (.NN.bak) |
| RSP-6 | Medium | Low | security / QA | Cross-repo write must be path-contained, symlink-safe, and fail-soft |

(Full list incl. RSP-5/7/8 in `findings.csv`.)

## Proposed plan (summary)

1. `resolve_project_dir()` (precedence: --session-dir → session DB directory → CWD).
2. `project_prompt_copy_name()` = `YYYYMMDD-<safe session id>.restart.md` (date from last-updated, with
   startup-date fallback when "unknown").
3. `_backup_restart_bu()` implementing the requested `.restart.bu.NNN.md` (001+) scheme (distinct from
   the existing backup helper).
4. `maybe_copy_restart_to_project()` — triggers only when `.agents/plans` OR `.agents/prompts` exists;
   writes to `.agents/prompts/pending/`; path-contained; **fail-soft** (never breaks primary recovery).
5. Call it after the restart file is written in `recover_from_export`.
6. Opt-out: config key `copy_restart_to_project_prompts` (default true) + `--no-project-prompt`.
7. README + CHANGELOG.

## Deferred (with reason)

- Copying transcript/prompt/compacted too: out of scope — the request is restart-only (RSP-8). Not a
  Remediation-Risk deferral; simply not requested.

## Out-of-repo / organizational notes

- This intentionally writes into the *working project's* repo (not ocman's). The plan keeps it opt-outable,
  path-contained, fail-soft, and only active when the project already uses the `.agents` convention.

## Next step

Review the IPD (optionally run `plan-review`) and approve before execution. This workflow did not execute
the plan and changed no application code. Four open questions (esp. Q1 project-dir precedence) want answers.
