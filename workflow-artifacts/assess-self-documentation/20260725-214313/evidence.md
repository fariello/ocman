# Evidence inspected - assess self-documentation (20260725-214313)

Read-only. No project files modified. Reproducible inputs below.

## Runtime behavior verified (installed `ocman` binary via the p3.14 venv)
- `ocman` (no args, TTY): prints "ocman - OpenCode Manager", the session listing, then a picker.
- `ocman </dev/null` : lists sessions, then "Select a session number, or type q to quit:" then
  "Error: Unexpected error: EOF when reading a line. Re-run with -v..." EXIT 1. (SD-01/SD-02)
- `ocman -h` : rich curated task-grouped help with runnable examples (Browse/Recover/Maintain/...).
- `ocman help` : same curated help + `help TOPIC` system.
- `ocman session show ses_doesnotexist` : "No matches found... Suggestions: Run 'ocman list ...'".
- `ocman db clean --older-than banana --dry-run` : "invalid --older-than value: could not parse
  duration ... (accepted: 2h, 5d, 6w, 6mo, 1y, or '30 days')" EXIT 2 (correct usage code; corrects
  an earlier mis-observation of exit 0).
- `ocman frobnicate` : argparse invalid-choice listing all commands + "run 'ocman help'" EXIT 2.
- `ocman session search zzzznomatch` : "No sessions match ..." EXIT 0. (SD-04)
- `ocman --db /nonexistent/x.db db info` : soft "Database file not found" + info screen, EXIT 0.
  (SD-03)

## Source verified (ocman/cli.py)
- `die()` definition + default exit 1: cli.py:1198-1211.
- EOF/traceback guard -> die exit 1: cli.py:15609.
- Interactive session picker (`input(...)`): cli.py:1678-1697; invoked from the no-args path
  cli.py:16794; no-project onboarding `print_no_project_context_help` cli.py:4856; gate 16695-16697.
- Help promise "(no args: lists this directory's sessions...)": cli.py:5634.
- `db info` soft missing-DB warning: cli.py:12894; ideal actionable `_db_not_found_error`
  (unused there): cli.py:1214-1223.
- `session search` empty (print + return, no exit): cli.py:16345; target-resolver "No matches
  found" + Suggestions + exit 1: cli.py:5277-5290.
- `filter` subparser + terse option help: cli.py:6506, 6509-6514; `db rebase` help: cli.py:6387.
- Bare empty-result dies without next-step: cli.py:16183, 16187.
- Parser build (help= coverage, no epilog on subparsers): cli.py:6066-6579.

## Method / delegation
- A broad help/naming/error/first-run/discoverability audit was delegated to an explore sub-agent
  (full parser enumeration + runtime exit-code checks). The orchestrator then RE-VERIFIED the
  High/Medium claims (SD-01..04) directly against the live binary and source before writing the
  IPD, and corrected one sub-agent-independent mis-observation (invalid --older-than exits 2, not 0).

## Sampling / truncation
- ocman/cli.py is ~17k lines; inspection targeted the parser build (6066-6579), the no-args
  dispatch + picker (1678-1697, 16690-16800), the error/exit helpers (1198-1223, 6684, 7021,
  15606-15609), and the specific message sites cited above rather than a full read.
