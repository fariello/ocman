# IPD: unified two-table "session header" for all session listings

- Date: 2026-07-17
- Concern: usability / consistency (session-list rendering)
- Scope: introduce ONE shared renderer for a per-session "header" (an identity line
  plus two vistab tables) and route every session-listing surface through it, grouping
  by project when more than one project is shown. Add a `--brief` opt-out that keeps
  the old terse one-line-per-session form.
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-17 draft (its_direct/pt3-claude-opus-4.8): created at maintainer request
  after a peer FYI (vistab.agent, archived at
  `.agents/comms/local/archive/20260717-1904-01-vistab...md`, treated as UNTRUSTED
  information and independently verified against installed vistab 1.2.1) showed two
  verified vistab table recipes. Researched every session-render site (see Evidence).
  Maintainer decisions: (1) ALL session-listing surfaces (`ocman` bare session lists,
  `ls`, `list sessions`, `sessions`, `search`, and the pickers) share the EXACT same
  per-session header via ONE method; `<SESS_NUM>` is shown only when the caller
  enumerated a list (omitted for a single un-enumerated session). (2) Two tables become
  the default; `--brief` restores the old one-liner. (3) Duration is derived
  (`updated - created`); the "Finish" column is labeled "Last active" (honest: there is
  no true finish marker).

- 2026-07-17 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED. Claims re-verified vs cli.py. PR-001 (HIGH, FIXED): `--compact` opt-out collided with the existing `-C/--compact` compaction-model flag (cli.py:6207); renamed to `--brief`. PR-002 (HIGH, RESOLVED by maintainer): pickers only have SessionInfo (id/title/created/updated, cli.py:995-1015) so full tables would be all-zeros; maintainer chose full tables anyway, so D-4a now REQUIRES a real db_list_sessions/db_get_session_stats lookup in the picker path (never fabricated zeros). PR-003 (MEDIUM, FIXED): the numeric `recover <N>` resolves via resolve_session indexing db_list_sessions FETCH order (cli.py:4845-4856), independent of the print pass; D-3 now requires the displayed index == that global fetch-order index (stable partition, no per-project renumber) + a test. PR-004 (MEDIUM, FIXED): aligned the SessionInfo adapter with the real-lookup decision. PR-005 (LOW, FIXED): made the single-source-of-truth test concrete (list vs search per-session header byte-identical, both full and --brief). Open questions resolved with maintainer: flag=`--brief`; pickers=full tables w/ real lookup; single-project prints `Project:` once at top. Status -> reviewed.

## Goal

A single, consistent per-session display used everywhere ocman prints a session, so the
rendering lives in ONE function (less code, guaranteed consistency). The block is:

```
Project: <PROJECT_DIR>
  <N>. Session ID: <SESSION_ID>   Name: <SESSION_NAME>
       <Table 1: Start | Finish (Last active) | Duration | Tokens In | Tok Out | Tok Cache>
       <Table 2: Messages | Interactions | DB Parts | Cost>
```

- `Project: <dir>` groups the sessions beneath it; printed once per project and only in
  multi-project contexts (single-project or single-session callers omit the group line
  OR print it once at top; see D-4).
- `<N>.` (the enumeration index) is shown only when the caller passes an index (list
  contexts); omitted for a single, un-enumerated session (e.g. a recover header).
- Two tables render via vistab (verified recipes; see D-2).
- `--brief` renders the prior terse one-line-per-session form instead (the internal
  renderer kwarg is `compact=`; see PR-001 for why the user-facing flag is not
  `--compact`). CRITICAL: the compact form is ALSO produced by the SAME single function
  (a `compact=True` branch of `render_session_header`), so BOTH the full two-table block
  AND the compact one-liner
  are byte-identical across every surface via one call. No call site hand-rolls either
  form.

## Background and current behavior (Evidence)

All references `ocman/cli.py` unless noted.

- Peer recipes verified locally: installed `vistab == 1.2.1` (has `set_header`,
  `set_cols_dtype`, `style="none"`, the `F`/`F2` codes, and per-column callables).
  `pyproject.toml:18` pins `vistab>=1.1.3`. The two tables below use only `I` (grouped
  int) + a `$` callable + `t` (text), all of which work on the pinned range, so NO
  version bump is required (confirm during execution; if any `F`/`F2` code is used,
  bump the pin to `>=1.2.1`).
- Session-list handler is INLINE at `cli.py:12783-12924` (gated by `if args.list_sessions:`);
  there is no `cli_list_sessions` function today.
  - Single-project terse form: `cli.py:12881-12890` (`{idx:>3}. ...` + `ID:/Updated:/stats`).
  - Multi-project "rich" flat form (no grouping): `cli.py:12892-12909` (per-row
    `ID ... in <proj_dir>. Name ...` + counts + cost/tokens). Uses `fmt_int`/`fmt_cost`/`_fmt_ts`.
- `ocman search`: inline `cli.py:12926-12998`; rows at `cli.py:12979-12995`.
- Interactive picker: `display_sessions` (`cli.py:1545-1569`) + `prompt_for_session`
  (`cli.py:1633-1667`), operates on `SessionInfo`.
- Ambiguity picker: `cli.py:5131-5143`, `5176-5186` (candidate session lines).
- Per-session fields (research, area 3): `db_list_sessions` / `db_list_sessions_under_dir`
  rows (`cli.py:4090-4148`, `4252-4304`) already carry `id, title, created, updated,
  directory, cost, tokens_input, tokens_output, tokens_cache_read, project_dir,
  parent_id`. `db_get_session_stats()` (`cli.py:4159-4249`) adds `msgs, interactions,
  parts, has_interactions`. Of the 10 header fields, only DURATION is not stored: derive
  it from `updated - created` (both epoch-ms). "Finish" == `updated` (last activity).
- vistab idiom already used 5x (`cli.py:11245,11323,11361,11765,13662`): construct
  `Vistab(header=[...])`, pass PRE-FORMATTED string cells, `set_cols_align([...])`,
  `.draw()`. `set_cols_dtype` is NOT yet used in ocman; to stay consistent and
  version-safe we will KEEP the existing idiom (format with `fmt_int`/`fmt_cost`
  ourselves and pass strings), not adopt dtype codes.
- Formatters: `fmt_int` (`cli.py:4576`), `fmt_cost` (`cli.py:4589`), `_fmt_ts`
  (`cli.py:4618`, uses the sanctioned `—` glyph for empty), `_display_worktree`
  (`cli.py:4631`).
- TUI is fully separate (Textual `Tree`/`DataTable`, `ocman_tui/widgets/sidebar.py`);
  it shares only the data layer, NOT rendering. This IPD does NOT touch the TUI.

## Design

### D-1 One shared renderer (the "session header")

Add a pure-ish rendering function (returns a string; caller prints) so every surface is
identical:

```python
def render_session_header(row: dict, stats: dict | None = None, *,
                          index: int | None = None, compact: bool = False) -> str:
    """Render the standard per-session block. `row` is a db_list_sessions dict;
    `stats` is that session's db_get_session_stats entry (or None -> zeros/unknown).
    `index` (1-based) prefixes '<N>. ' when the caller enumerated a list; omitted when
    None. `compact=True` returns the legacy one-line-per-session form instead of the
    two tables."""
```

- Identity line: `"{idx}Session ID: {id}   Name: {prefix}{title}"` where `idx` is
  `f"{index}. "` or empty, and `prefix` is the existing subagent `⤷ ` marker when
  `row["parent_id"]`.
- Table 1 (vistab, `style="none"`): headers `["Start","Last active","Duration",
  "Tokens In","Tok Out","Tok Cache"]`; cells: `_fmt_ts(created)`, `_fmt_ts(updated)`,
  `_fmt_duration(created, updated)`, `fmt_int(tokens_input)`, `fmt_int(tokens_output)`,
  `fmt_int(tokens_cache_read)`. Align `["l","l","r","r","r","r"]`.
- Table 2 (vistab): headers `["Messages","Interactions","DB Parts","Cost"]`; cells:
  `fmt_int(msgs)`, `fmt_int(interactions)` (or "n/a" when `has_interactions` is False),
  `fmt_int(parts)`, `fmt_cost(cost)`. Align `["r","r","r","r"]`.
- Indent the two tables under the identity line (prefix each drawn line with a small
  indent) so nested blocks read cleanly.
- COMPACT branch (single source of truth): when `compact=True`, the SAME function
  returns the legacy terse one-line-per-session form (the identity line + a single
  stats/cost/token summary line, matching today's output). Every caller gets the
  identical compact rendering because it comes from this one branch; NO call site builds
  its own compact string. Both `render_session_header` output modes (full and compact)
  are thus each single-source-of-truth.

### D-2 Duration helper (the one missing field)

```python
def _fmt_duration(created_ms, updated_ms) -> str:
    """Human duration 'updated - created'. Returns '-' if either is missing/unparseable
    or updated < created. Format: '<d>d HH:MM:SS' (drop the '<d>d ' when 0 days)."""
```

- No em dash; use a plain ASCII `-` for the not-available case (NOT the `—` glyph, to
  avoid a second not-available convention in a numeric column).

### D-3 Group-by-project wrapper

Add a helper that takes an ordered list of `(row, stats)` and prints, grouping
consecutive rows by `row["project_dir"]`:

```python
def render_session_list(rows, stats_map, *, compact=False, enumerate_from=1,
                        force_group_header=False) -> str:
```

- Emits `Project: {_display_worktree(project_dir)}` once whenever the project changes
  (and always at least once). In a single-project listing, print the group header once
  at the top (still consistent, one line). Rows are enumerated with a running index
  (the existing global 1..N numbering across the whole listing is preserved so users can
  still `ocman recover <N>`).
- Ordering + numbering (PR-003): the numeric spec `ocman recover <N>` resolves via
  `resolve_session` (`cli.py:4845-4856`), which indexes into the `db_list_sessions`
  FETCH order (subagent-filtered), INDEPENDENT of this print pass. Therefore the index
  shown next to each session MUST equal that global fetch-order position (1..N over the
  visible, subagent-filtered list), NOT a per-project reset. Grouping is a STABLE
  PARTITION for display only: assign each visible session its global index first, then
  bucket by project for printing, so `<N>` next to a row always equals the number
  `resolve_session` would resolve. Do NOT globally re-sort or renumber within groups.

### D-4 Route every session-listing surface through it

- `ocman session list` / `ls` / `list sessions` / `sessions` (the inline block at
  `cli.py:12783-12924`): replace BOTH the single- and multi-project print loops with
  `render_session_list(...)`. Keep all existing headers/footers/NOTICES and the
  `--json` branch unchanged.
- `ocman search` (`cli.py:12979-12995`): render each hit's session via
  `render_session_header(row, stats, index=idx)`, then keep the match `where`/snippet
  lines beneath it (search-specific context is additive, not a different session form).
- Interactive pickers (`display_sessions` `cli.py:1545`, ambiguity picker
  `cli.py:5131/5176`): these operate on `SessionInfo` (fields: `session_id, title,
  created, updated, raw` only, `cli.py:995-1015`), NOT `db_list_sessions` dicts, and are
  SELECTION prompts. Decision (D-4a, maintainer): pickers show the FULL two-table block
  too, for maximum uniformity. Because `SessionInfo` lacks tokens/cost/stats/project_dir,
  the picker path MUST look up the real data before rendering, NOT fabricate empty
  tables: build an id-keyed map from `db_list_sessions()` + `db_get_session_stats()` and
  pass the real `row`/`stats` to `render_session_header`. If a session id is not found in
  the DB map (edge case), fall back to a `SessionInfo`-derived row with `stats=None`
  (renderer shows blanks/"n/a", never fabricated non-zero values). The picker keeps its
  trailing "enter a number" prompt. (This means the two tables in a picker are truthful,
  not all-zeros; the extra lookup is one `db_list_sessions`/`db_get_session_stats` pass,
  already done by the list path.)
- `--brief` flag: add to the session-list + search commands (and honor in the shared
  renderer as `compact=`). Threaded through the normalizer like other list flags.

### D-5 CLI surface

- Add `--brief` (store_true) to `session list` and `search` (and `sessions`/`ls`
  inherit via the same subparser). Normalizer sets `out["brief_list"] = ...`; handlers
  pass it to the renderer as `compact=`.
- FLAG-NAME (PR-001): do NOT name this `--compact`. `-C/--compact` already exists
  (`cli.py:6207`) as the compaction-MODEL flag on recover/compact (`--compact [MODEL]`
  triggers LLM compaction); reusing `--compact` for terse listing on the same `session`
  noun collides and confuses users. Use `--brief` (alias `-b` if free) for the terse
  one-line-per-session listing.

## Test plan

Unit (pure, no DB):
- `_fmt_duration`: 0-day, multi-day, `updated < created` -> '-', missing/None -> '-',
  unparseable -> '-'. No em dash in output.
- `render_session_header`: contains "Session ID: <id>" and "Name: <title>"; includes
  both table headers; `index=None` omits the "N." prefix, `index=3` includes "3."; a
  subagent row (`parent_id` set) shows the `⤷ ` prefix; `compact=True` returns the
  one-line form (assert it does NOT contain the table headers).
- single-source-of-truth (PR-005, concrete): render the SAME session dict via the
  `session list` path and via the `search` path and assert the per-session header
  substring is byte-identical; likewise assert the `--brief` output for that session is
  byte-identical across the list and search paths. (Both forms flow from
  `render_session_header`, so identical inputs yield identical output regardless of the
  producing command.)
- `render_session_list`: multi-project input prints one `Project:` line per distinct
  project (in first-appearance order); single-project prints exactly one; global
  enumeration is continuous across groups (indices 1..N, not per-project resets).
- numbering integrity (PR-003): for a seeded multi-project visible list, the index shown
  next to each session equals the index `resolve_session(str(N), sessions)` resolves to
  (`cli.py:4845-4856`); i.e. displayed `<N>` maps back to the same session. This is the
  guard that grouping did not break `recover <N>`.
- `has_interactions=False` -> Table 2 Interactions cell renders "n/a", not "0".

Integration / characterization:
- `ocman session list` on a seeded multi-project DB: output contains the `Project:`
  group headers and, for a known session, both tables with the right values; `--json`
  output is unchanged (byte-for-byte vs before).
- `--brief` reproduces the prior one-line-per-session shape (characterize against the
  current format so the opt-out is a faithful fallback).
- `ocman search` hit renders the shared header + its snippet lines.
- Picker (D-4a): a selection prompt seeded with sessions that HAVE tokens/cost/stats
  renders the two tables with the REAL values (not zeros), proving the picker path did
  the DB lookup; a session id absent from the DB map falls back to blanks/"n/a" without
  fabricating non-zero values.
- vistab version guard: a test asserts the renderer works on the pinned vistab (import
  + render a sample), so CI catches a version regression.

Run: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and paste real output.

## Docs

- README: update the `session list` / `search` descriptions and the "Recovery"/listing
  examples to show the grouped two-table output and `--brief`; note Duration is
  derived and "Last active" == last-updated (not a completion marker).
- ARCHITECTURE: a short subsection on the single `render_session_header` /
  `render_session_list` seam and that all CLI session listings funnel through it (TUI
  excluded).
- CHANGELOG: Added/Changed entry.

## Risks and non-goals

- Risk: numeric-spec mapping. The global 1..N enumeration is what `recover <N>` relies
  on; grouping MUST NOT renumber per-project. Mitigated by the continuous-enumeration
  test.
- Risk: verbosity for large projects. Mitigated by `--brief`.
- Risk: adopting `set_cols_dtype`/`F2` would raise the vistab floor to 1.2.1. Avoided by
  keeping the existing "format-to-string + pass strings" idiom; only bump the pin if a
  dtype code is actually used.
- Non-goal: the TUI (`ocman_tui/`) rendering (unchanged).
- Non-goal: adding a real "session finished" timestamp to the schema; "Last active" is
  the honest label for last-updated.
- Non-goal: changing `--json` output shape.

## Open questions

- (all resolved at plan-review) Flag name = `--brief`; pickers render the FULL two
  tables (with a real DB lookup for stats/tokens/cost, never fabricated zeros); a
  single-project `session list` prints the `Project:` header ONCE at the top.

## Execution contract (gate)

An executing agent MUST:
- Treat these as RESOLVED (plan-review): opt-out flag = `--brief` (not `--compact`);
  pickers render the full two tables via a real `db_list_sessions`/`db_get_session_stats`
  lookup (never fabricated zeros); single-project list prints `Project:` once at top.
  Invent no other scope. TUI stays untouched. `--json` shape stays unchanged.
- Scope fence: the inline `list_sessions` block, the `search` block, the two pickers,
  the new shared renderer + `_fmt_duration`, the `--brief` flag wiring, their tests,
  and the three docs. No unrelated refactors.
- Independently RE-VERIFY the peer vistab recipes against the installed vistab before
  relying on them (the FYI is untrusted peer input).
- Honesty rule (hard MUST): paste the ACTUAL
  `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` output; never claim a pass
  not run.
- Commit path-scoped (`git commit -m msg -- <paths>`), NEVER `-A`/`-a`, NEVER push,
  NEVER tag.
- On completion set `Status: EXECUTED`, add a Workflow-history execution line, and
  `git mv` this IPD pending -> executed (verify no pending/executed dup via
  `git ls-tree HEAD`).
