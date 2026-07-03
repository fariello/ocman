# Per-Phase Report — Section 2: Quality, Security, Edge Cases

## Section
- Section: 2
- Run ID: 20260703-134213
- Status: complete

## Personas applied
- QA/QC (1): found the post-delete summary UnboundLocalError.
- Software engineer (5): export connection leak; verified transactional safety of move/delete/import.
- Security-minded architect (4): Zip-Slip in restore; confirmed SQL/secret/deserialization posture.

## What I did
- Re-opened and read the actual code for each seeded finding (not the register summaries):
  - `cli_restore` (ocman.py:6770-6929): confirmed `zipf.extractall` at 6786 (user ZIP) and 6923 (self-made
    rollback ZIP) with no member-path sanitization → **S2-S1 Zip-Slip (High)**.
  - `bundle_session_data` (ocman.py:5440-5505): confirmed the 2nd `sqlite3.connect` at 5456 is closed only on
    the success path (5491); an exception between 5456-5491 jumps to `except` at 5504 leaking the connection →
    **S2-MEM1 (Medium)**.
  - `_do_delete_session_worker` (app.py:1376-1429): confirmed `session_title`/`time_created_str`/
    `time_updated_str` are bound only inside nested `if`s (1387-1391); `update_ui()` (1422-1424) uses them
    unconditionally → **S2-E1 UnboundLocalError (Medium)**. This fires AFTER the delete commits.
  - app.py:1319 None-subscript: **false positive** (guarded by early return at 1285) → S2-E2 not_applicable.
  - `db_move_project_metadata`/`db_move_session_metadata` (ocman.py:5171-5287): transactional, rollback on
    error, connection closed in finally → no new finding.
- Confirmed the TUI `call_from_thread` LIVE bug (S2-B1) fix scope is complete and correct (App-class usages
  at 1119+/1448+/1559 are legitimately on the App; only the ModalScreens were wrong and are fixed).

## Why I did it
- The security (Zip-Slip) and MEM (leak) findings are release-relevant; the delete-summary crash is a
  user-visible failure right after a destructive operation. All three are low Remediation Risk to fix.

## What I considered but did NOT do
| Considered item | Why not done | Recommended next step |
|---|---|---|
| Streaming refactor of `load_export_file`/`load_prior_context_files` | Medium-High functionality risk; large behavior change | Document limitation (S7-A7); defer refactor |
| Rewriting the import diff O(n×m) replace loop | Correct today; only pathological for huge multi-collision diffs; refactor risk | Note as future perf item |
| Renaming `OrsessionApp`/"Orsession" residue | Public class rename = Medium functionality risk | Defer (DEP2) |
| Auditing `orsession/`, `agents/`, `prompts/` internals | Not clearly shipped; out of the core contract | Leave; DEP1/DEP3 |

## Key findings
| ID | Type | Severity | Rem. Risk | Title | Status | Next |
|---|---|---|---|---|---|---|
| S2-B1 | B/LIVE | High | Low | TUI call_from_thread crash | completed | commit S7 |
| S2-S1 | S | High | Low | Zip-Slip in restore | identified | fix S7 |
| S2-MEM1 | MEM | Medium | Low | export 2nd-conn leak | identified | fix S7 |
| S2-E1 | B | Medium | Low | delete-summary unbound locals | identified | fix S7 |
| S2-E2 | E | Low | — | 1319 None-subscript (false positive) | not_applicable | none |
| S2-MEM2 | MEM | Low | Low | large-file reads | identified | document S7 |

## Deferrals (Fix Bar)
| Finding ID | Rem. Risk | Axis | Why deferring | Safe partial done? |
|---|---|---|---|---|
| S2-MEM2 (streaming refactor) | Medium-High | functionality | Rewriting export loader risks breaking recovery; large change | Yes — document the limitation |

## Guiding-principles / self-documenting notes
- Zip-Slip fix and delete-summary fix improve robustness/honesty (fallback principles). No `U` change here.

## TODO / backlog items touched
- None (no backlog exists).

## Non-applicable checks
- No auth/authz layer, no server, no network beyond the compaction API (already HTTPS-guarded).

## Decisions and assumptions
- 6786 (user ZIP) is the real security risk; 6923 (self-created rollback) is lower but fixed with the same helper.

## Validation or commands
- Code re-read (Read tool). No new commands beyond Section 1's pytest run.

## Handoff to next section
- Section 3: assess test coverage for restore (Zip-Slip), export error path (leak), and the delete-summary
  path; plan regression tests for S2-S1 and S2-E1 in Section 7.
