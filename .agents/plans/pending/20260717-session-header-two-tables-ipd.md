# IPD: unified two-table "session header" for all session listings

- Date: 2026-07-17
- Concern: usability / consistency (session-list rendering)
- Scope: introduce ONE shared renderer for a per-session "header" (an identity line
  plus two vistab tables) and route every session-listing surface through it, grouping
  by project when more than one project is shown. Add a `--compact` opt-out that keeps
  the old terse one-line-per-session form.
- Status: to-review
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
  the default; `--compact` restores the old one-liner. (3) Duration is derived
  (`updated - created`); the "Finish" column is labeled "Last active" (honest: there is
  no true finish marker).

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
- `--compact` renders the prior terse one-line-per-session form instead. CRITICAL: the
  compact form is ALSO produced by the SAME single function (a `compact=True` branch of
  `render_session_header`), so BOTH the full two-table block AND the compact one-liner
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
- Ordering: preserve the current `time_updated DESC` order WITHIN a project; group
  boundaries follow first appearance. (Do NOT globally re-sort in a way that breaks the
  existing index-to-session mapping used by numeric specs; verify the numbering source.)

### D-4 Route every session-listing surface through it

- `ocman session list` / `ls` / `list sessions` / `sessions` (the inline block at
  `cli.py:12783-12924`): replace BOTH the single- and multi-project print loops with
  `render_session_list(...)`. Keep all existing headers/footers/NOTICES and the
  `--json` branch unchanged.
- `ocman search` (`cli.py:12979-12995`): render each hit's session via
  `render_session_header(row, stats, index=idx)`, then keep the match `where`/snippet
  lines beneath it (search-specific context is additive, not a different session form).
- Interactive pickers (`display_sessions` `cli.py:1545`, ambiguity picker
  `cli.py:5131/5176`): these operate on `SessionInfo`, not `db_list_sessions` dicts, and
  are SELECTION prompts. Decision (D-4a, resolved): route them through the SAME
  renderer by adapting `SessionInfo` -> the row dict shape (a small adapter), so the
  header is identical; the picker keeps its trailing "enter a number" prompt. If stats
  are not readily available in a picker path, pass `stats=None` (renderer shows zeros /
  "n/a") rather than diverging the format.
- `--compact` flag: add to the session-list + search commands (and honor in the shared
  renderer). Threaded through the normalizer like other recovery/list flags.

### D-5 CLI surface

- Add `--compact` (store_true) to `session list` and `search` (and `sessions`/`ls`
  inherit via the same subparser). Normalizer sets `out["compact_list"] = ...`;
  handlers pass it to the renderer. (Name it `compact_list` internally to avoid clashing
  with the `compact` recovery flag / `session compact` verb.)

## Test plan

Unit (pure, no DB):
- `_fmt_duration`: 0-day, multi-day, `updated < created` -> '-', missing/None -> '-',
  unparseable -> '-'. No em dash in output.
- `render_session_header`: contains "Session ID: <id>" and "Name: <title>"; includes
  both table headers; `index=None` omits the "N." prefix, `index=3` includes "3."; a
  subagent row (`parent_id` set) shows the `⤷ ` prefix; `compact=True` returns the
  one-line form (assert it does NOT contain the table headers).
- single-source-of-truth: assert both forms come from `render_session_header` only.
  Grep-style test (or a call-graph assertion) that no other function builds a per-session
  identity/stats string; every surface (list, search, pickers) calls the shared renderer
  for BOTH the full and the `--compact` output, so the two forms are byte-identical
  regardless of which command produced them.
- `render_session_list`: multi-project input prints one `Project:` line per distinct
  project (in first-appearance order); single-project prints exactly one; global
  enumeration is continuous across groups (indices 1..N, not per-project resets) so a
  numeric `recover <N>` still maps correctly.
- `has_interactions=False` -> Table 2 Interactions cell renders "n/a", not "0".

Integration / characterization:
- `ocman session list` on a seeded multi-project DB: output contains the `Project:`
  group headers and, for a known session, both tables with the right values; `--json`
  output is unchanged (byte-for-byte vs before).
- `--compact` reproduces the prior one-line-per-session shape (characterize against the
  current format so the opt-out is a faithful fallback).
- `ocman search` hit renders the shared header + its snippet lines.
- vistab version guard: a test asserts the renderer works on the pinned vistab (import
  + render a sample), so CI catches a version regression.

Run: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and paste real output.

## Docs

- README: update the `session list` / `search` descriptions and the "Recovery"/listing
  examples to show the grouped two-table output and `--compact`; note Duration is
  derived and "Last active" == last-updated (not a completion marker).
- ARCHITECTURE: a short subsection on the single `render_session_header` /
  `render_session_list` seam and that all CLI session listings funnel through it (TUI
  excluded).
- CHANGELOG: Added/Changed entry.

## Risks and non-goals

- Risk: numeric-spec mapping. The global 1..N enumeration is what `recover <N>` relies
  on; grouping MUST NOT renumber per-project. Mitigated by the continuous-enumeration
  test.
- Risk: verbosity for large projects. Mitigated by `--compact`.
- Risk: adopting `set_cols_dtype`/`F2` would raise the vistab floor to 1.2.1. Avoided by
  keeping the existing "format-to-string + pass strings" idiom; only bump the pin if a
  dtype code is actually used.
- Non-goal: the TUI (`ocman_tui/`) rendering (unchanged).
- Non-goal: adding a real "session finished" timestamp to the schema; "Last active" is
  the honest label for last-updated.
- Non-goal: changing `--json` output shape.

## Open questions

- O-1 (decide at execution, non-blocking): in a single-project `session list`, print the
  `Project:` group header once at the top, or omit it entirely? Leaning: print once (one
  line, keeps the format identical to the multi-project case).

## Execution contract (gate)

An executing agent MUST:
- Resolve O-1 at execution (print-once leaning) and record it in the Workflow history;
  invent no other scope. TUI stays untouched. `--json` shape stays unchanged.
- Scope fence: the inline `list_sessions` block, the `search` block, the two pickers,
  the new shared renderer + `_fmt_duration`, the `--compact` flag wiring, their tests,
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
