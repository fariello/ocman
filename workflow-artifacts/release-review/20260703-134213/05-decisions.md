# 05 Decisions and Assumptions

## D1 — Framework directories out of scope
`.agents/workflows/`, `.opencode/`, `.claude/`, and `workflow-artifacts/` are the review framework and
its run records. Per `00-run-protocol.md` they are excluded from the review scope. The subject is `ocman`.

## D2 — No parallel audit lanes
The repository is a single cohesive app. `ocman.py` (large) was already mapped by one explore agent.
Serial single-pass review is sufficient and higher-signal. No parallel lanes used.

## D3 — Pre-existing uncommitted change treated as this run's fix
`ocman_tui/app.py` had an uncommitted diff at run start: the `self.call_from_thread -> self.app.call_from_thread`
fix made earlier in this same chat session (the crash the user reported). The user explicitly approved
treating it as part of this review and committing it (finding S2-B1, action S7-A1). It is a correct fix for a
LIVE-class TUI bug, isolated to those lines, so it is safe to attribute to this run.

## D4 — Guiding principles: fallback used
No guiding-principles document exists. The universal fallback principles apply (see
`guiding-principles-assessment.md`).

## D5 — Conversation as intent source
The only conversation context is the user's bug report about the move crash. It confirms intent: the TUI
move/export/import should complete cleanly. No broader recorded intent beyond the repo itself. Cold-start
orientation docs will be drafted from the repo + README; material claims marked where inferred.

## Assumptions / open questions
- Q1: canonical repo/clone URL (README says `ocman`, remote says `opencode-recover`). Needs user confirmation.
- Q2: whether 1.0.3 is released to PyPI yet. Affects CHANGELOG expectation but not blocking.

## LSP type-checker noise
The type checker flags `pysqlite3.connect` (dynamic binding), `NoSelection` unions, and textual
`push_screen` overloads in app.py. These are pre-existing and mostly false positives from dynamic typing;
not treated as findings except the two potentially-real ones captured as S2-E1 (1319 None-subscript, 1422-1424 unbound).
