# Assessment run report - functionality (whole project)

- Date / run ID: 20260715-221446
- Concern: functionality (completeness vs. user/stakeholder needs)
- Scope: whole project (ocman CLI/TUI)
- IPD written: `.agents/plans/pending/20260715-assess-functionality-ipd.md`
- Verdict: adequate for functionality (broad, well-wired surface; real gaps in
  machine-readability, spend reporting, and safety/affordance consistency)

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| F1 | High | Low | Power user, stakeholder | No machine-readable output (`--json`) on any command; ocman consumes JSON but emits none. |
| F2 | High | Medium | Stakeholder | `ocman spend` (per-project/session spend, incl. historical) is a demanded backlog item, absent; `db info --by-project` shows disk only, not cost. |
| F3 | Medium | Low | Novice | `export` help says "project export is not yet supported" but project export IS wired and works (stale/misleading doc). |
| F4 | Medium | Low | Power user | Top-level `move` sugar lacks `--confirm-remote-delete`/`-y`/`--force` that the group forms have (remote guarded-delete unreachable via sugar). |
| F5 | Medium | Low | Novice, QA | `-y/--yes` missing on `project delete`, `db clean`, `db clean-orphans`, `backup clean` (cannot run unattended). |
| F6 | Medium | Low | Novice | `--force` means "bypass process-lock" everywhere except `history clear`, where it means "skip confirm" (dual meaning). |
| F7 | Medium | Low-Medium | Power user, QA | `--dry-run` absent on `move`, `backup restore`, `import`, `history clear` (state-mutating, no preview). |
| F8 | Low | Low | Power user | No `--limit`/pagination on `session list`/`project list`/`history show`; `db info` top-models hardcoded LIMIT 3. |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

1. Fix stale `export` help (project export IS supported) - F3.
2. Add `--confirm-remote-delete`/`-y`/`--force` to top-level `move` sugar - F4.
3. Disambiguate `--force` vs `-y` on `history clear` / converge on `-y` for confirm-skip - F6.
4. Add `-y/--yes` to `project delete`, `db clean`, `db clean-orphans`, `backup clean` - F5.
5. Add `--dry-run` to `move` and `import` (defer restore/history-clear) - F7.
6. Add `--limit N` to list/history + parametrize `db info` top-models - F8.
7. Add `--json` to read/report commands with a documented schema - F1.
8. Implement `ocman spend` per the backlog (per-project default, session detail,
   live vs historical toggle; forked-dedupe stretch deferred) - F2.

## Deferred (with reason)

- F7 restore/history-clear dry-run: Remediation Risk Medium-High on functionality,
  because a faithful `backup restore` preview risks diverging from the real restore
  path and giving false assurance; propose a shared-code preview or a confirm prompt
  in a separate IPD.
- Shell completion: Medium on complexity (new dependency/packaging surface); own IPD.
- `resume`/`open` a session: High on functionality; a scope decision (ocman manages,
  opencode runs). Routed to an open question.
- `ocman spend` forked-spend dedupe: Medium-High on complexity; explicitly optional in
  the backlog; follow-up after the base command.

## Out-of-repo / organizational notes (if any)

- The `ocman spend` data-source decision (live cost columns vs. history ledger vs. both;
  what "historically saved spend" means) and the `resume/open` scope question are
  stakeholder calls, captured as open questions in the IPD, not resolvable from the repo
  alone.

## Next step

Review the IPD (optionally run the `plan-review` workflow on it) and approve before
execution. Approval can be partial (Steps 1-6 are low-risk and independent; 7-8 depend
on the open questions). This workflow does not execute the plan.
