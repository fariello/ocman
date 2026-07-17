# IPD: chunk large sessions on recover / compact / export

- Date: 2026-07-17
- Concern: usability / scale (large sessions)
- Scope: split a large session into multiple ordered, self-contained parts so the
  recovered transcript/restart Markdown, the compaction LLM input, and the .ocbox
  export stay manageable, instead of only being able to TRUNCATE (drop older turns).
- Status: PROPOSED (not yet executed)
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-17 draft (its_direct/pt3-claude-opus-4.8): created at maintainer request
  from the TODO.md backlog entry. Researched the existing recover/compact/filter/
  export/config subsystems (see Evidence). Maintainer resolved the four open design
  questions: (1) BOTH a `--chunk` flag AND a new choice in the interactive large-
  session prompt; (2) apply to ALL THREE outputs (recovery, compaction, export),
  phased; (3) split on INTERACTION boundaries, never mid-turn; (4) filenames use the
  filter-style stem sub-segment `.part-NNofMM`. Promoted to to-review.

## Goal

When a session is large, let the user split it into N ordered, complete parts rather
than truncating (which discards older turns). Chunking must:

- never split a single turn or interaction across two parts;
- produce round-trip-safe filenames consistent with the existing recovery/filter
  naming conventions;
- be opt-in (a `--chunk` flag) and also offered as a choice in the existing
  interactive "this session is large" prompt;
- cover the recovered transcript/restart Markdown (Phase 1), the compaction LLM
  input with per-chunk API calls and aggregated cost (Phase 2), and the .ocbox
  export (Phase 3);
- leave the existing default (truncate / prompt) behavior unchanged when `--chunk`
  is not requested.

## Background and current behavior (Evidence)

All references are to `ocman/cli.py`.

- Recovery engine: `recover_from_export` (`cli.py:3649`) builds three artifacts
  (transcript, restart, compact prompt) from a turn list. Assembly is per-turn via
  `render_transcript` (`cli.py:2638`), `render_restart_context`, `render_compact_prompt`
  (`cli.py:3291`).
- Large-session handling TODAY = TRUNCATE. Thresholds `LONG_SESSION_LINE_THRESHOLD
  = 2500` and `LONG_SESSION_INTERACTION_THRESHOLD = 100` (`cli.py:201-202`, module
  constants, NOT config). When exceeded and no explicit limit is given,
  `prompt_for_truncation` (`cli.py:2533`) asks N/lines/interactions/both, then
  `apply_truncation` (`cli.py:2476`) keeps the most-recent tail via
  `truncate_turns_by_interactions` (`cli.py:2395`) / `truncate_turns_by_lines`
  (`cli.py:2433`). See the flow at `cli.py:3740-3773`.
  NOTE: the TODO said ">250 interactions"; the real constant is 100. This IPD uses
  the existing constants and does not silently change them.
- Interaction boundary already defined: `count_interactions` (`cli.py:2318`) - a new
  interaction begins when `turn.role == "user" and prev_role != "user"` (`cli.py:2340`).
  This is the chunk boundary. Per-turn line cost: `rendered_lines_for_turn`
  (`cli.py:2350`); whole-doc: `count_transcript_lines` (`cli.py:2372`, = 6 header +
  sum of per-turn lines).
- Filename authority: `canonical_recovery_name(session_id, dt, kind)` (`cli.py:3495`)
  -> `YYYYMMDD-HHMM-<safe_sid>.<kind>.md`; `RECOVERY_KINDS = ("transcript","restart",
  "prompt","compacted")` (`cli.py:3480`); inverse parser `parse_recovery_name`
  (`cli.py:3498`) already TOLERATES one trailing `.<segment>` before the kind suffix
  (that is how the filter output `...<scope>.compacted.md` round-trips, `cli.py:3505-3506`,
  `cli.py:7152-7160`). So a `.part-NNofMM` sub-segment fits WITHOUT touching
  `RECOVERY_KINDS`.
- Compaction: `run_compaction` (`cli.py:6624`) reads the `.prompt.md` and calls
  `call_compaction_api` (`cli.py:868`). Token/cost estimators already exist:
  `estimate_tokens` (`cli.py:825`, ~4 chars/token via `CHARS_PER_TOKEN_ESTIMATE`
  `cli.py:204`), `estimate_cost` (`cli.py:842`), `fmt_cost` (`cli.py:4434`). The
  multi-session compact path already aggregates estimates into a vistab GRAND TOTAL /
  AVERAGE table (`cli.py:13465-13510`) - prior art for per-chunk aggregation.
- Export: `bundle_session_data` (`cli.py:9358`) -> `_write_ocbox` (`cli.py:9262`),
  a `.ocbox` ZIP that ALREADY streams rows with `fetchmany(1000)` (`cli.py:9328-9336`),
  so its memory pressure is low; chunking export is about producing smaller,
  independently-importable bundles, not about memory.
- Config: `load_ocman_config` (`cli.py:305`) only honors keys present in
  `DEFAULT_CONFIG` (`cli.py:287`, `cli.py:325-326`); numeric example
  `filter_max_bytes` (`cli.py:299`), read as `int(config.get("filter_max_bytes", ...))`
  (`cli.py:6879`, `cli.py:7057`); template `CONFIG_TEMPLATE` (`cli.py:224-285`) has a
  `key = {key}` line per key. A new config key must be added in all three places.

## Design

### D-1 Threshold config (make chunk sizing configurable, per the backlog)

Add two config keys following the `filter_max_bytes` pattern (D-1 touches
`DEFAULT_CONFIG`, `CONFIG_TEMPLATE`, and a read site):

- `chunk_max_interactions` (default = `LONG_SESSION_INTERACTION_THRESHOLD` = 100)
- `chunk_max_lines` (default = `LONG_SESSION_LINE_THRESHOLD` = 2500)

These bound the SIZE of each part. `--max-interactions` / `--max-lines` on the CLI
override them per-run. Do NOT repurpose the existing `LONG_SESSION_*` constants for a
different meaning; they remain the "is this session large / should we prompt"
trigger. Chunk sizing reads config; the trigger stays constant-based (documented as a
deliberate split: one decides "prompt?", the other decides "part size").

### D-2 Core chunker (pure, testable seam)

Add a pure function next to the truncation helpers:

```python
def chunk_turns(turns: list[Turn], *, max_interactions: int, max_lines: int) -> list[list[Turn]]:
    """Split turns into ordered parts, packing whole INTERACTIONS into each part up to
    the size limits. Never splits a turn or an interaction across parts. A single
    interaction larger than a limit becomes its own oversized part (never dropped)."""
```

Rules:
- Walk turns, grouping by interaction boundary (reuse the `count_interactions` rule).
- Start a new part when adding the next whole interaction would exceed
  `max_interactions` (interactions-in-part + 1) OR `max_lines` (running
  `rendered_lines_for_turn` sum + this interaction's lines), whichever hits first.
- An interaction that alone exceeds `max_lines` still ships as its own part (log a
  note); we never split mid-interaction (invariant).
- Return `[all_turns]` (single part) when the input fits - so callers can treat
  chunking uniformly.

This is the one seam every phase reuses; it has NO I/O and is unit-tested directly.

### D-3 Filenames: `.part-NNofMM` stem sub-segment

Add one helper (the naming authority for parts), mirroring the filter stem pattern:

```python
def part_recovery_name(session_id: str, dt: datetime, kind: str, part: int, total: int) -> str:
    # e.g. YYYYMMDD-HHMM-<sid>.part-01of03.transcript.md ; zero-padded to width of `total`.
```

- Built by taking `canonical_recovery_name(sid, dt, kind)`, stripping the
  `.<kind>.md` suffix, inserting `.part-NNofMM`, re-appending `.<kind>.md`.
- Zero-pad NN/MM to the width of `total` (so `01of03`, `007of123` sort lexically).
- When `total == 1` we do NOT add a part segment (identical to today's names -> no
  regression for normal-size sessions even if `--chunk` is passed).
- `parse_recovery_name` already tolerates the extra segment; add a targeted test that
  a `.part-NNofMM.<kind>.md` name round-trips (sid + kind recovered, segment ignored
  or surfaced). Extend the parser ONLY if a test shows it mis-parses; prefer not to
  touch `RECOVERY_KINDS`.

### D-4 CLI surface

- Add `--chunk` (store_true) to the `session recover` and `session compact` actions
  and the `session export` action; thread through the normalizer (add
  `"chunk": False` to defaults, set it in each branch) and into the handlers.
- `--chunk` is mutually exclusive in EFFECT with truncation: when `--chunk` is set we
  never call `apply_truncation`; `--max-lines`/`--max-interactions` instead set the
  per-part size. If both `--chunk` and an explicit truncation-only intent are given,
  `--chunk` wins (document it; no hard error).
- Non-interactive + large + no `--chunk` + no `--max-*`: unchanged (writes full or
  per current non-interactive behavior at `cli.py:2566-2568`).

### D-5 Interactive prompt: add a "chunk" choice

Change `prompt_for_truncation` to also offer chunking. To avoid a fragile tuple
contract, change its return type to a small result object / 3-tuple that encodes the
CHOICE:

```python
@dataclass
class LargeSessionChoice:
    mode: str            # "full" | "truncate" | "chunk"
    max_lines: int | None
    max_interactions: int | None
```

- New prompt: `[N]o(full) / [l]ines / [i]nteractions / [b]oth / [c]hunk`.
- `[c]hunk` asks for per-part `Max interactions [<chunk_max_interactions>]` and
  `Max lines [<chunk_max_lines>]`, returns `mode="chunk"`.
- All existing call sites updated to read `.mode` / `.max_*`. This is an internal
  contract change; there is exactly one caller (`recover_from_export` `cli.py:3750`),
  so blast radius is small. A test locks the old-choice behavior (N/l/i/b) unchanged.

### D-6 Phasing

- **Phase 1 (recovery Markdown):** `recover_from_export` gains a chunk path. When
  chunking, call `chunk_turns`, then for each part emit `transcript`/`restart` (and
  `prompt`) with `part_recovery_name`. Restart doc per part includes a one-line
  "Part k of N" note. Return the full list of written paths (its signature already
  returns `list[Path]`). Cross-part continuity: each part's restart carries the
  existing `prior_context` seam so a reader knows it is a continuation.
- **Phase 2 (compaction):** when `--chunk`, run compaction PER PART: build a
  per-part compact prompt, call `call_compaction_api` per part, write
  `...part-NNofMM.compacted.md`. Aggregate the per-part token/cost estimates into the
  existing vistab GRAND TOTAL / AVERAGE style table before running (reuse the
  `cli.py:13465-13510` pattern), and print a per-part progress line. The
  running-OpenCode guard is NOT relevant (compaction/recovery are read-only on the
  DB); no guard change.
- **Phase 3 (export):** when `--chunk`, produce N `.ocbox` bundles, each a valid
  standalone single-session (sub)bundle importable on its own, named
  `...part-NNofMM.ocbox` (export currently has no auto-name; define one for the
  chunked case while still honoring an explicit `--to` directory). Split by the same
  interaction boundaries. Import is unchanged (each part imports like any bundle).
  Phase 3 may land in a follow-up commit if Phases 1-2 are already large; if
  deferred, record it explicitly rather than silently dropping it.

## Test plan

Unit (pure, no I/O), in `tests/`:

- `chunk_turns`: fits-in-one -> single part; exact-boundary; oversized single
  interaction -> own part (never split); interaction-limit vs line-limit whichever-
  first; ordering preserved; concatenating all parts == original turns (round-trip
  invariant); never-split-a-turn invariant.
- `part_recovery_name`: zero-pad width tracks `total`; `total==1` yields the plain
  canonical name (no segment); `parse_recovery_name` round-trips a part name (sid +
  kind recovered).
- `prompt_for_truncation` / `LargeSessionChoice`: old choices (N/l/i/b) return the
  same effective max_lines/max_interactions as before (anti-regression); new `[c]`
  returns `mode="chunk"` with the configured defaults; non-interactive returns
  `mode="full"`.
- config: `chunk_max_interactions` / `chunk_max_lines` present in `DEFAULT_CONFIG`
  and `CONFIG_TEMPLATE`; a written config round-trips; read helper returns the
  configured value and the default when absent.

Integration:

- `recover_from_export(..., chunk=True)` on a synthetic large session writes the
  expected N part files with correct names, each parseable, no turn duplicated or
  dropped across parts (concatenation equals full transcript minus per-part headers).
- Non-chunk path unchanged: a large session with `--chunk` absent still truncates/
  prompts exactly as today (reuse/extend existing recover tests).
- Phase 2: chunked compaction calls the (mocked) API once per part and writes N
  `.compacted` part files; cost table sums per-part estimates.
- Phase 3 (if landed): chunked export writes N importable `.ocbox` parts; importing
  every part reconstructs the full session subtree.

Run: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and paste real output.

## Docs

- README: document `--chunk` on recover/compact/export, the new interactive `[c]hunk`
  choice, the `.part-NNofMM` naming, and the two new config keys (with the
  truncate-vs-chunk distinction).
- ARCHITECTURE: a short subsection on the `chunk_turns` seam, the interaction-boundary
  invariant, and the `part_recovery_name` naming authority.
- CHANGELOG: Added entry.
- CONFIG_TEMPLATE doc comments for the two new keys.

## Risks and non-goals

- Risk: changing `prompt_for_truncation`'s return contract. Mitigated by a single
  caller + an anti-regression test locking the old choices.
- Risk: `parse_recovery_name` mis-handling the part segment. Mitigated by a round-trip
  test; only extend the parser if that test fails.
- Non-goal: changing the `LONG_SESSION_*` trigger thresholds or the default
  (truncate/prompt) behavior when `--chunk` is absent.
- Non-goal: cross-part semantic summarization/stitching of compaction output into one
  document (each part is compacted independently in Phase 2).
- Open (decide at execution): whether Phase 3 export ships in the same commit or a
  fast-follow; whether the restart doc's cross-part note should also embed a tiny
  index of sibling part filenames.
```
