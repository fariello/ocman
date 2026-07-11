# Implementation Plan - Session/project listing UX, global-dir notice, disk reporting

Status: PROPOSED (not yet executed)

Improves the no-project navigation screen, the multi-project `list sessions`
format, and the `disk` / `list projects` per-project reporting, based on a real
session run from `/home/gfariello`. Groups five related UX items (issues #1-#5)
plus an optional WAL-checkpoint capability. No code is changed by this plan;
execute only after review.

Evidence lines are `ocman/cli.py:<line>` verified on 2026-07-11 against the
current package layout (`ocman/cli.py`). Line numbers drift; re-verify before
editing.

---

## Motivation (from a real run in `$HOME = /home/gfariello`)

1. `ocman list sessions` from `/home/gfariello` did NOT print the agreed
   "SHOWING ALL PROJECTS ..." notice.
2. Home-dir sessions are filed under the global (`/`) project but keep their real
   `session.directory`, which is confusing and undocumented in the UI.
3. The multi-project session listing lacks first-active date, cost, and split
   token counts, and the requested layout differs from today's.
4. `opencode.db-wal` (5.23 GB) / `opencode.db-shm` dominate "size on disk" and are
   never explained or reclaimable via ocman.
5. `disk` and `list projects` show a bare project-id hash with no directory, an
   unformatted total cost, and no per-project cost / split tokens.

---

## Root causes (verified)

- **#1 missing notice.** The "SHOWING ALL PROJECTS" footer is printed only in the
  `_no_project_match` else-branch (`ocman/cli.py:11125-11132`, gated by
  `_no_project_match` set at `11089-11098`). But running `list sessions` from
  `/home/gfariello` calls `db_list_sessions_under_dir(cwd)` (`4064-4124`), which
  RETURNS rows (home-dir sessions filed under global `/` keep their real
  `session.directory`), so `_dir_scope = cwd` is set and rendering takes the
  `if _dir_scope:` branch (`11090-11093`) instead. The footer lives on a branch
  this path never reaches.
- **#2 home->global mapping.** cwd->project auto-detect (`11000-11025`) matches a
  project only when a `project.worktree` contains the cwd (`_project_for_cwd`,
  `6947-6987`); `$HOME` matches none, and global's worktree is `/`
  (`_display_worktree` labels `/` or `""` as "global (/)", `4401-4411`). So bare
  `ocman` in `$HOME` correctly shows the projects list, and dir-scoped
  `list sessions` shows home-dir sessions that happen to be filed under global.
- **#4 WAL/SHM.** SQLite WAL-mode sidecars: `-wal` holds un-checkpointed writes
  (real data), `-shm` is the shared-memory index. `disk` already sums them into
  "Size on disk" (`db_show_info`, `9696-9997`). There is NO `wal_checkpoint` in
  the codebase (grep confirmed), so ocman cannot fold the WAL back.
- **#5 disk/projects data.** `_per_project_disk_usage` (`9619-9693`) sums only
  `tokens_input+tokens_output` combined (`9642`) and fetches only project `id`+
  `name` (`9635`), NOT `worktree` (the directory) nor cost/split tokens. Global
  historical metrics come from the deletion sidecar `_load_history` (`9395`), whose
  `cumulative` block (`9398-9407`) has NO `project_id`, so per-project historical
  cost is NOT derivable from existing data.

---

## User Review Required

> [!IMPORTANT]
> Decisions already made with the user (2026-07-11):
> - **#1/#2:** keep the current dir-scoped listing, but add a LOUD, highly visible
>   NOTICE that these sessions map to the global (`/`) project, and how to view the
>   true global project. Do NOT auto-jump into the global project.
> - **#3:** per-session "Historical" cost does NOT exist; drop it per session. Keep
>   "First active" (`time_created`) and "Last active" (`time_updated`).
> - **Rendering:** use `vistab` for genuinely tabular blocks (disk per-project,
>   `list projects`); use f-string width padding for the multi-line per-session
>   stanza (it is not a flat table).
>
> Open decision surfaced below: **#5c per-project Historical cost** is not
> available from current data (see Design E). Confirm the chosen resolution.

---

## Design

### A. Add the global-mapping NOTICE (#1, #2)

**There is ALREADY a note here** (do not duplicate it): the `_dir_scope` branch
prints a DIM line at `ocman/cli.py:11092-11093` -
`"(Some ran under OpenCode's global project, worktree 'global (/)'.)"` - gated by
`any(s["project_dir"] in ("/", "", None) for s in all_sessions)`. The change is to
UPGRADE this existing dim note to the LOUD notice the user asked for (and add the
"how to see the true global project" hint), NOT to add a second line.

Replace the dim note (`11092-11093`) with a loud multi-line notice, e.g.:

```
NOTICE: Sessions run from a home/ad-hoc directory generally map to OpenCode's
        global (/) project. These are shown here by directory. To see the true
        global project: ocman list sessions in /
```

- Detection: REUSE the existing condition at `11092`
  (`s["project_dir"] in ("/", "", None)`), which already keys off the worktree
  (not a hardcoded "/home"). Session dicts carry `project_dir` from
  `db_list_sessions_under_dir` (`4097-4114`).
- Style: use the loud helpers (`color_yellow`/`color_red`/`color_bold`) matching
  the batch-delete warnings, so it is unmissable but not an error. Confirm the
  wording with the user before finalizing (the exact "NOTICE:" text was proposed,
  not yet approved verbatim).
- Keep the rest of the listing output intact (per the decision); only the note
  line changes weight/wording.
- The separate `_no_project_match` footer (`11125-11132`) stays on its own branch
  and is unchanged. Add a code comment at BOTH sites cross-referencing each other
  so a future reader does not "fix" one and miss the other.

### B. New multi-project `list sessions` per-session format (#3)

Replace the per-session render block (`ocman/cli.py:11105-11123`) for the
NO-project-specified case with the user's multi-line stanza. Single-project
listings keep their current compact form unless we confirm otherwise.

Target layout:

```
  <n>. ID: <session id> in <project dir>. Name: <title>
       Msgs: <msgs,8w>  Interactions: <ix,8w>  DB Parts: <parts,8w>
       First active: <first>, Last active: <last>, Cost: <$cost>, Tokens: <in,11w> in / <out,11w> out / <cache,11w> cache
```

Data sourcing (two sources, verified):
- `id, title, project_dir, created, updated, cost, tokens_input, tokens_output,
  tokens_cache_read` come from the session dict (`db_list_sessions` `3941-3959`,
  `db_list_sessions_under_dir` `4097-4114`). All confirmed present.
- **`msgs`, `interactions`, `parts` do NOT come from the session row.** They come
  from `db_get_session_stats()` keyed by session id (called at
  `ocman/cli.py:11104`, read at `11114-11122`). The new stanza MUST keep calling
  `db_get_session_stats()` once and look up `stat = session_stats.get(sid, {})`.
- **Honor `has_interactions`.** The current code (`11118-11122`) OMITS the
  interactions field when `stat.get("has_interactions")` is False (some sessions
  have no interaction data). The new format MUST preserve this: when
  `has_interactions` is False, drop the `Interactions: <ix>` column rather than
  printing `0` (which would be misleading). Route this case to a test.

Formatting:
- Comma/decimal separated with the requested widths (msgs/ix/parts 8-wide, tokens
  11-wide) via f-string padding (e.g. `f"{n:>8,}"`, `f"{n:>11,}"`), using the
  shared `fmt_int` helper (F).
- `First active` = `_fmt_ts(created)`; `Last active` = `_fmt_ts(updated)`.
- Cost = active row cost only, via the shared `fmt_cost` helper (F). NO per-session
  "(Historical: ...)" (does not exist; per decision). `cost`/token fields can be
  `None` in the row (`SELECT` uses no COALESCE); coalesce to 0 before formatting.
- Preserve the subagent `prefix` marker for child rows (`11111`) and the title
  truncation (`11107-11108`) unless the new layout supersedes them; decide
  explicitly.
- Keep the existing note lines (approximate-count disclaimer `11101`,
  subagent-hidden note `11099-11100`) and the trailing "Use 'ocman session show
  ...'" line (`11133`).
- Multi-line records: render with f-string padding, NOT vistab (per the rendering
  decision).

### C. `disk` per-project: show directory + cost + split tokens (#5a, #5c)

Extend `_per_project_disk_usage` (`9619-9693`):
- Fetch `worktree` alongside `id, name` (currently `SELECT id, name FROM project`
  at `9635`), and expose a `directory` field (worktree, labeled via
  `_display_worktree` so `/` -> "global (/)"). The current render uses
  `r["name"] or r["id"]` (`9990`), i.e. the raw project-hash id when unnamed -
  this is exactly the #5a complaint; show `directory` instead of / alongside id.
- Change the per-project SELECT (`9640-9644`, currently only `project_id, id,
  tokens_input+tokens_output`) to also aggregate `SUM(tokens_input)`,
  `SUM(tokens_output)`, `SUM(tokens_cache_read)`, and `SUM(cost)` per session, then
  sum per project in the Python accumulation loop (`9647-9650`). COALESCE nulls to
  0 in SQL (cost/tokens columns are nullable). Keep or replace the combined
  `tokens`; the caller decides which fields it prints.
- Render (per-project block `9980-9996`) with `vistab` (tabular): a header row and
  one row per project. Columns: directory (with id available), sessions, messages,
  diff files/bytes, cost, tokens in/out/cache. Right-align numeric columns via
  `set_cols_align`. Preserve the existing "(no projects / no per-project data)"
  empty case (`9986-9987`).

### D. Formatted totals in the Usage Metrics + `list projects` (#5b, #5c)

- #5b: the "Total Cost:" / "Active" / "Historical" values (`9917-9929`) are
  already thousands-separated for tokens but cost is `${x:.4f}` without thousands.
  Use the shared currency helper (F) so large costs show `$4,231.56` (choose 2 or
  4 decimals; recommend 2 for the summary, keep 4 only where precision matters).
- #5c for `list projects` (`print_projects`, `4419-4433`): add per-project cost
  and split tokens to each project's second/third line. This requires
  `db_list_projects` (`3862-3890`) to also aggregate `SUM(cost)`,
  `SUM(tokens_input/output/cache_read)` per project (extend the SELECT at
  `3872-3880`; the existing `GROUP BY p.id` / `HAVING session_count > 0` already
  supports adding SUM columns - COALESCE nulls to 0). `print_projects` then
  renders the extra line(s). Consider vistab here for column alignment across
  projects.
- **Scope interaction (verified):** `print_projects` is ALSO called by the
  no-project navigation screen `print_no_project_context_help` (`4444`, via
  `main()` `11491-11493`). Adding cost/token lines to `print_projects` will change
  that screen too. Decide: either (a) accept the enriched output on both (likely
  fine, more informative), or (b) add a `show_metrics: bool` flag so the nav
  screen stays compact. Recommend (a) unless the nav screen becomes too tall;
  make the choice explicit and test both call sites.

### E. Per-project Historical cost (#5c) - DECIDED

Per-project historical (deleted) cost/tokens are NOT available: the deletion
sidecar `cumulative` block (`_load_history`, `9398-9407`) has no `project_id`, and
per-run entries are not reliably project-scoped.

**Decision (confirmed by user 2026-07-11):** show per-project **Active**
cost/tokens only, and keep **Historical** as a single GLOBAL line in the Usage
Metrics summary (as today). Simple, honest, no schema/sidecar change. Do NOT
fabricate a per-project historical number from global data.

Not done (would require a separate IPD, no backfill possible): recording
`project_id` in future deletion-metrics runs so per-project historical could
accrue going forward. That is a larger change to `save_deletion_metrics` (`9530`)
and the sidecar schema and is explicitly out of scope here.

### F. Shared formatting helpers (KISS / de-dup)

There is NO currency/thousands helper today; formatting is inline in dozens of
places (thousands `f"{n:,}"` e.g. `9909,9924-9929,9994-9995,11357-11361`; cost
`f"${x:.4f}"` e.g. `9594,9614,9923-9927,11354`). Add small helpers:
- `fmt_int(n, width=0)` -> comma-separated, optional right-pad width.
- `fmt_cost(x, decimals=2)` -> `$` + comma-separated with fixed decimals.
Use them in the new/edited render sites. Do NOT churn unrelated call sites in this
plan (scope control); adopt them incrementally where B/C/D already edit.

### G. WAL checkpoint capability (#4) - optional, gated

Explain WAL/SHM in `disk` output (one clarifying line under "Size on disk", e.g.
"WAL holds un-checkpointed writes; run 'ocman ...' to reclaim"). Optionally add a
`checkpoint` action that runs `PRAGMA wal_checkpoint(TRUNCATE)` to fold the WAL
back and shrink `-wal`:
- MUST refuse (or warn loudly) if OpenCode is running (reuse
  `check_opencode_process_lock`, `7109`/`7337`), since checkpointing under an
  active writer is ineffective (a `TRUNCATE` checkpoint cannot complete while
  another connection holds the WAL) and confusing.
- Issue the PRAGMA on a WRITE connection that ocman opens and closes for this
  action; do not run it on a read-only info connection. `wal_checkpoint(TRUNCATE)`
  only fully truncates when no other connection is using the WAL.
- Read-only `disk` must NOT auto-checkpoint (no surprise mutation on an info
  command). Checkpoint is an explicit, separate action.
- Report before/after `-wal` size so the user sees the reclaim (mirrors the
  delete report vocabulary).
- If out of scope for this plan, split into its own IPD; keep only the
  explanatory line under "Size on disk" here. (Recommend splitting: it is a
  distinct destructive-ish maintenance op, unlike the read-only reporting in A-D.)

---

## Tests

- #1/#2: dir-scoped listing from a dir whose sessions map to global prints the
  NOTICE exactly once; a dir mapping to a real project does NOT print it; the
  `_no_project_match` footer path is unaffected (regression).
- #3: no-project `list sessions` renders the new 3-line stanza with correct
  comma-separated widths, First/Last active, cost, and split tokens; existing note
  lines and the trailing show-hint remain; single-project listing unchanged
  (characterization before edit).
- #3 edge cases: a session with `has_interactions == False` OMITS the
  Interactions column (does not print `0`); a session with NULL cost/tokens
  renders `$0.00` / `0` (coalesced), not a crash or "None".
- #5a: `disk` per-project block shows each project's directory (and id); global
  shows "global (/)".
- #5b: total cost renders comma-separated; token totals unchanged.
- #5c: per-project active cost + split tokens present; historical remains a single
  global line (per decision E); no per-project historical fabricated.
- #4 (if included): `checkpoint` refuses when OpenCode is running; shrinks `-wal`
  when closed (or mock the PRAGMA and assert it is issued with TRUNCATE);
  read-only `disk` never issues a checkpoint.
- Formatting helpers: `fmt_int`/`fmt_cost` unit tests (thousands, width, decimals,
  negative/zero).

---

## Docs

- README + help: document the home/global mapping NOTICE, the new multi-project
  listing format, the enriched `disk`/`list projects` output, and (if included)
  the `checkpoint` action and WAL explanation.
- ARCHITECTURE: note the `fmt_int`/`fmt_cost` helpers and that historical metrics
  are global-only (no per-project attribution).

---

## Non-goals

- Auto-jumping into the global project from `$HOME` (explicitly rejected).
- Backfilling per-project historical cost (impossible from existing data).
- Reworking single-session / single-project listing beyond keeping it intact.
- Mass-refactoring every inline format string to the new helpers.
