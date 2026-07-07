# Cold-start orientation (run 20260707-004045)

Can a no-context engineer/LLM orient from the project's own tracked docs?
- **Intent/goals/audience:** README top section (reclaim opencode DB space; recover/compact
  sessions; local single-user). Clear.
- **Philosophy/principles:** ARCHITECTURE "Design principles" (intuitive/self-documenting,
  configurable-over-hardcoded, KISS, honest docs) + AGENTS.md prose convention.
- **Architecture/approach:** ARCHITECTURE covers entry points, CLI/TUI relationship, the canonical
  recovery-naming scheme + helpers, the destructive-confirm seam, data contracts.
- **Decision rationale:** the executed IPDs under `.agents/plans/executed/` capture the 1.1.0
  design decisions (filter, egress guards, collision safety, TUI parity, naming) with alternatives
  and open-questions resolved. CHANGELOG records the shipped result + the --compact behavior change.

Verdict: **cold-start orientation is adequate.** The 1.1.0 delta is documented in ARCHITECTURE +
CHANGELOG + executed IPDs; no missing orientation doc. (Intent recovered from this session is
consistent with the code; no unconfirmed material assumptions.)
