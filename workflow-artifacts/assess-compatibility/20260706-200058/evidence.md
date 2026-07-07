# Evidence - assess-compatibility run 20260706-200058

## Files inspected
- `.github/workflows/ci.yml` (11-23): matrix os = [ubuntu, macos, windows], python = 3.10-3.14.
- `pyproject.toml`: `requires-python = ">=3.10"`.
- `ocman.py`:
  - CLI recovery writer: `base_name` via `canonical_recovery_name` (3688) and the three
    artifact paths (3690-3692: transcript/restart/prompt); return order `[transcript, restart,
    prompt]` (3729-3730).
  - `run_compaction` compacted path (4814); compact-prompt docstring (4752, stale
    ".compact-prompt.md").
  - Compaction prompt-file selection (8906-8909): `endswith(".compact-prompt.md")` with a
    `generated_paths[-1]` fallback.
  - `safe_filename` (2517-2536): allow-list `[A-Za-z0-9._-]`, 80-char cap.
  - `parse_recovery_name` (3431-3475): suffix match (case-sensitive), legacy + canonical parsing.
- `ocman_tui/app.py`:
  - Recovery writers (1266-1286): `opencode-recovery-<sid[:8]>-<timestamp>.transcript/.restart/
    .compact-prompt.md`; compacted (1338): `opencode-<timestamp>-<sid[:8]>.compacted.md`.
  - Timestamp `datetime.now().strftime("%Y%m%d-%H%M%S")` (1247, 1337) - local, seconds.
  - Button labels (839-841) referencing `.transcript.md`/`.restart.md`/`.compact-prompt.md`.

## Commands run
- `git show HEAD~6:ocman.py | grep ...` -> confirmed `.prompt.md` (3692) and the
  `.compact-prompt.md` lookup (8907) both PRE-DATE the 1.1.0 work (COMP-2 is pre-existing).
- `grep` for old-name references across `ocman.py` + `ocman_tui/` -> located the CLI/TUI
  divergence and the stale lookup/docstring.
- Reviewed `recover_from_export` return (`[transcript_path, restart_path, compact_prompt_path]`)
  to confirm the `[-1]` fallback currently lands on the compact-prompt path (COMP-2 works by luck).

## Not exhaustively tested / assumptions
- Did not run the suite on macOS/Windows actually (no access this run); reasoned from CI matrix +
  code (case-sensitivity of `str.endswith`, `safe_filename` allow-list). Proposed tests will prove
  it on the matrix.
- Assumed real session ids are `ses_<base62>` (basis for COMP-4 reserved-name unreachability).
- Did not deeply assess the TUI's non-recovery flows (out of this concern's scope).

## Scope exclusions honored
- Did not assess `.agents/workflows/` or `workflow-artifacts/` as project code.
