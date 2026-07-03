# Cold-Start Orientation Assessment

Can a no-context engineer or LLM orient from the project's own tracked docs?

| Knowledge area | Verdict | Where | Notes |
|---|---|---|---|
| Intent, goals, audience, scope | **Adequate** | README.md top + Core Capabilities | Clear: opencode session recovery/compaction + DB/config/system maintenance for opencode users. |
| Philosophy / guiding principles | **Thin/missing** | (none) | No principles doc. Design values (stdlib-only CLI, rollback-safety-first, self-documenting CLI) are implicit only. |
| Architecture and approach | **Missing** | (none) | No ARCHITECTURE.md. A fresh engineer must reverse-engineer an 8040-line `ocman.py` + `ocman_tui/` package, the `.ocbox`/backup ZIP formats, and the SESSION_RELATIONAL_TABLES DB model. |
| Design-decision rationale | **Thin** | CHANGELOG (scattered) | Some "why" exists in CHANGELOG (e.g. WSL threads-not-workers, timestamp-unification) but there is no decisions log. |

## KD findings
- **20260703-134213-S4-KD1 (Medium sev, Low rem-risk):** No `ARCHITECTURE.md`. Create a concise one covering:
  the two entry points (CLI `ocman.py` + `ocman_tui`), how the TUI reuses CLI functions via `ocman_tui/core.py`,
  the data contracts (`.ocbox` bundle v2.0, backup ZIP, `ocman.toml`), the DB table model
  (`SESSION_RELATIONAL_TABLES`), and the rollback-safety pattern used across destructive ops. Done by default in S7.
- Principles doc: covered by Section 5 (KD/GP). Given this is a single-maintainer personal tool, a short
  principles section may be folded into ARCHITECTURE.md or README rather than a separate file (KISS).

## Intent recovered from conversation
- The only conversation intent is the user's move-crash bug report, confirming the TUI operations must
  complete cleanly. No broader intent to record beyond the repo. No "inferred, needs confirmation" claims made.

## Open questions for the user
- Q1 canonical repo URL (ocman vs opencode-recover). Q2 PyPI 1.0.3 status.
