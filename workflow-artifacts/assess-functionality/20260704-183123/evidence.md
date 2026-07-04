# Evidence - assess-functionality (restart→project prompts) 20260704-183123

Read-only assessment. No code changed.

## Inspected (code)
- `recover_from_export` (ocman.py:3341-3499): restart file written at 3473-3481 —
  `restart_path = output_restart or (output_dir / f"{base_name}.restart.md")`, base_name
  `opencode-<utc-ts>-<safe_session_id>` (3459-3464); `write_text(restart_path, render_restart_context(...))`.
  Returns `generated_paths`.
- `SessionInfo` build in main (ocman.py:8041-8079): `updated=str(s.get("updated",""))` (epoch-ms string);
  placeholder path sets `updated="unknown"` (4387).
- `_fmt_ts` (3679): parses epoch-ms → date (UTC).
- `_backup_if_exists` (3276-3312): `.NN.bak` (2-digit, 01-99), RENAMES the existing file — different scheme
  and semantics from the requested `.restart.bu.NNN.md` (3-digit from 001, keep new file at canonical name).
- Working-dir resolution in main (8001-8029): `session_dir = args.session_dir` (resolved) → `opencode_cwd`;
  session `directory` available via DB rows; `output_dir = args.out` (default ./opencode-recovery).
- `safe_filename` (2510) already used for the session-id filename component.

## Feasibility
- Copy is a single `shutil.copy2`; trigger is two `Path.is_dir()` checks; backup is a rename loop — all cheap.
- Date derivation reuses existing epoch-ms parsing; session id already filename-safed.

## Commands run
- `date`, `git status --short` (clean), `grep` for restart/backup/updated/session_dir sites, `Read` of the
  recover_from_export write block, `_backup_if_exists`, `_fmt_ts`, and the main() session-dir/SessionInfo code.

## Sampling / truncation notes
- Read the relevant functions in full; did not re-read the whole 8000-line file (targeted inspection).
