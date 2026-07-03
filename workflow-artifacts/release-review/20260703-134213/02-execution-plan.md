# 02 Execution Plan (how the review runs)

## Project type
Python CLI + Textual TUI, single-user local tool for opencode SQLite session management.
Public contract: `ocman` CLI, `.ocbox` bundle, backup ZIP, `ocman.toml`.

## Review approach
- Serial, single continuous pass (no parallel audit lanes — repo is one cohesive app; the large `ocman.py`
  was mapped via one explore agent already). Recorded in `05-decisions.md`.
- Sections 1-6 audit; Section 7 implement safe fixes under the Fix Bar; Section 8 final ship review.
- Validation command: `PYTHONPATH=. pytest`. Also `python -c "import ast; ast.parse(...)"` for syntax and
  `python -c "import ocman"` for import sanity.
- Local commits at section boundaries; NO push (no permission).

## Focus areas (from Section 1)
1. Security: Zip-Slip in restore (High).
2. LIVE/data-integrity: TUI move/export/import worker crash (High) — already fixed; move/import DB transactions.
3. MEM: connection leak on export error path; large-file reads.
4. Docs drift: CHANGELOG 1.0.3, version single-source, README clone URL.
5. Cold-start knowledge: no ARCHITECTURE/DECISIONS docs.

## Non-goals
- No refactor of the 8040-line ocman.py structure. No streaming rewrite of export loader (risk).
- No push/publish/deploy. No changes to out-of-scope `.agents/`, `.opencode/`, `.claude/`, `workflow-artifacts/`.
