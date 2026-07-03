# 06 Commands

| # | Command | Purpose | Result |
|---|---|---|---|
| 1 | `git rev-parse/status/remote/log` | Establish git baseline | main @ e6c5943; 1 modified file (app.py); remote opencode-recover |
| 2 | `python -c "import ast; ast.parse(app.py)"` | Syntax check after app.py fix | OK |
| 3 | `PYTHONPATH=. python -m pytest -q` | Run full test suite | 56 passed in ~12s |
| 4 | `wc -l` on sources | Size inventory | ocman.py mapped via explore agent; TUI ~2300 lines total |
| 5 | grep run_worker/call_from_thread | Trace TUI threading surface | Confirmed modals used self.call_from_thread (bug); App-class usages correct |
| 6 | grep class boundaries in app.py | Confirm which call_from_thread are in App vs Screen | App spans 761->EOF; 1119+/1448+/1559 are App (correct); modals 535-724 were the bug |

Working directory: /home/gfariello/VC/ocman for all. No secrets in output.

## Section 7
| # | Command | Purpose | Result |
|---|---|---|---|
| 7 | pytest (targeted) | Validate T1/T2 new tests | both pass |
| 8 | `PYTHONPATH=. pytest` | Full suite after all fixes | 58 passed |
| 9 | `import ocman_tui` | Verify single-sourced version | 1.0.3 |
Files re-opened before fixing (protocol): ocman.py:6770-6929, ocman.py:5440-5505, app.py:1376-1429.
