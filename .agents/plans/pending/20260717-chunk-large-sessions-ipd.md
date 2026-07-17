# IPD: chunk large sessions on recover / compact

- Date: 2026-07-17
- Concern: usability / scale (large sessions)
- Scope: split a large session into multiple ordered, self-contained parts so the
  recovered transcript/restart Markdown and the compaction LLM input stay manageable,
  instead of only being able to TRUNCATE (drop older turns). Export (.ocbox) chunking
  is explicitly OUT of scope (see Non-goals).
- Status: reviewed
- Author: its_direct/pt3-claude-opus-4.8

## Workflow history

- 2026-07-17 draft (its_direct/pt3-claude-opus-4.8): created at maintainer request
  from the TODO.md backlog entry. Researched the existing recover/compact/filter/
  export/config subsystems (see Evidence). Maintainer resolved the four open design
  questions: (1) BOTH a `--chunk` flag AND a new choice in the interactive large-
  session prompt; (2) apply to recovery + compaction (export chunking later revised
  OUT, see plan-review); (3) split on INTERACTION boundaries, never mid-turn; (4)
  filenames use the filter-style stem sub-segment `.part-NNofMM`. Promoted to to-review.
- 2026-07-17 /plan-review (its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED. Re-verified claims against cli.py. PR-001 (HIGH, FIXED): the filename claim was false - parse_recovery_name does NOT strip a trailing segment (greedy `(.+)` folds `.part-NNofMM` and even today's filter `.<scope>` INTO the sid, cli.py:3539,3556-3560); D-3 now REQUIRES fixing the parser + a filter regression test. PR-002 (HIGH, RESOLVED BY SCOPE CUT): export `--to` is a file not a dir (cli.py:12292-12305); maintainer decided export chunking is OUT of scope entirely, removing the problem. PR-003 (MEDIUM, FIXED): recover_from_export has THREE call sites (cli.py:13299,13322,13427), all must thread `chunk`. PR-004 (MEDIUM, FIXED): removed the silent "chunk wins / ignore --max-lines" framing - under --chunk, --max-* set per-part size (no conflict). PR-005 (LOW, FIXED): CONFIG_TEMPLATE must explain the two-knob (trigger vs part-size) relationship. PR-006 (LOW, FIXED): added the filter-parse regression test. Also removed a stray code-fence and added an execution-contract gate. Maintainer decisions: interactive prompt gets a [c]hunk choice AND a --chunk flag; export chunking dropped (YAGNI + partial-bundle integrity cost). Status -> reviewed.

## Goal

When a session is large, let the user split it into N ordered, complete parts rather
than truncating (which discards older turns). Chunking must:

- never split a single turn or interaction across two parts;
- produce round-trip-safe filenames consistent with the existing recovery/filter
  naming conventions;
- be opt-in (a `--chunk` flag) and also offered as a choice in the existing
  interactive "this session is large" prompt;
- cover the recovered transcript/restart Markdown (Phase 1) and the compaction LLM
  input with per-chunk API calls and aggregated cost (Phase 2);
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
  (`cli.py:3498`).
  CORRECTION (plan-review PR-001): `parse_recovery_name` does NOT currently strip a
  trailing segment. Its docstring at `cli.py:3505-3506,3526-3528` DESCRIBES dropping a
  trailing `.<scope>`, but the implementation calls `_try_parse(stem)` on the WHOLE stem
  (`cli.py:3556`) and the regexes use a greedy `(.+)` for the session id (`cli.py:3539`),
  so for `...<sid>.part-01of03.transcript.md` the session id parses as
  `"<sid>.part-01of03"` (WRONG). The same latent bug already affects the filter scope
  form: `...<sid>.<scope>.compacted.md` parses sid as `"<sid>.<scope>"`. So a
  `.part-NNofMM` sub-segment does NOT round-trip today; the parser MUST be fixed (see
  D-3). This still does not require touching `RECOVERY_KINDS`.
- Compaction: `run_compaction` (`cli.py:6624`) reads the `.prompt.md` and calls
  `call_compaction_api` (`cli.py:868`). Token/cost estimators already exist:
  `estimate_tokens` (`cli.py:825`, ~4 chars/token via `CHARS_PER_TOKEN_ESTIMATE`
  `cli.py:204`), `estimate_cost` (`cli.py:842`), `fmt_cost` (`cli.py:4434`). The
  multi-session compact path already aggregates estimates into a vistab GRAND TOTAL /
  AVERAGE table (`cli.py:13465-13510`) - prior art for per-chunk aggregation.
- Export: `bundle_session_data` (`cli.py:9358`) -> `_write_ocbox` (`cli.py:9262`),
  a `.ocbox` ZIP of DB rows + diffs that ALREADY streams rows with `fetchmany(1000)`
  (`cli.py:9328-9336`). Export chunking is OUT of scope (see Non-goals), so no export
  code path changes.
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
- PR-005: the `CONFIG_TEMPLATE` doc-comment for each new key MUST explain this
  two-knob relationship in one sentence (the `LONG_SESSION_*` trigger decides WHEN a
  session counts as large enough to prompt/chunk; `chunk_max_*` decides how big each
  resulting part is), so a config-file reader is not left guessing why there appear to
  be two thresholds.

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
- REQUIRED parser fix (PR-001): make `parse_recovery_name` actually do what its
  docstring promises. After slicing off `.<kind>.md`, if `_try_parse(stem)` yields a
  session id that still contains a trailing `.part-NNofMM` (or, for the pre-existing
  filter case, a trailing `.<scope>`) segment, strip that ONE trailing segment and
  re-parse, keeping it only if the shorter stem still parses as a timestamped stem.
  Concretely: try `_try_parse(stem)`; if the returned sid contains a `.`, also try
  `_try_parse(stem.rsplit(".", 1)[0])` and prefer the parse whose sid has NO embedded
  segment when both timestamp-parse. Add a `part_segment` / `scope_segment` out-value
  only if a caller needs it; otherwise just return the clean sid.
- Tests: `.part-NNofMM.<kind>.md` round-trips to the bare sid + correct kind; AND a
  regression test that the existing filter form `...<sid>.<scope>.compacted.md` now
  parses sid as the bare `<sid>` (this is a behavior CHANGE that fixes a latent bug;
  check no current caller depended on the old folded value - `cli_filter` at
  `cli.py:7140` uses the sid only to rebuild the stem, so a correct sid is strictly
  better). Do NOT touch `RECOVERY_KINDS`.

### D-4 CLI surface

- Add `--chunk` (store_true) to the `session recover` and `session compact` actions
  (NOT `export`); thread through the normalizer (add `"chunk": False` to defaults, set
  it in each branch) and into the handlers.
- Thread `chunk` into EVERY `recover_from_export` call site (there are THREE in the
  dispatch: `cli.py:13299`, `cli.py:13322`, `cli.py:13427`), not just one - add
  `chunk=` to `recover_from_export`'s signature and pass it at all three (PR-003).
- Under `--chunk`, `--max-lines` / `--max-interactions` set the PER-PART size (they do
  NOT truncate). There is therefore no `--chunk`-vs-truncation conflict: `--chunk`
  selects split mode, and `--max-*` parameterize the part size within it. If neither
  `--max-*` is given, parts use the `chunk_max_*` config defaults. (PR-004: removed the
  earlier "chunk wins / silently ignore --max-lines" framing, which implied a silent
  failure.)
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
  contract change; there is exactly one caller (inside `recover_from_export`,
  `cli.py:3751`), so blast radius is small. A test locks the old-choice behavior
  (N/l/i/b) unchanged.

### D-6 Phasing

Both phases land together in one execution (recovery is the shared foundation that
compaction builds on).

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
- **Export (.ocbox) is explicitly OUT of scope** (see Non-goals): a bundle is DB rows
  for wholesale import, is not readable text or LLM input (the two things this feature
  keeps manageable), and already streams to disk, so it has no size motivation.
  Chunking it would add real complexity (partial-bundle id remapping + subtree
  integrity across parts) for no identified use case. `export` and `--to` are
  unchanged; `export` gets no `--chunk` flag.

## Test plan

Unit (pure, no I/O), in `tests/`:

- `chunk_turns`: fits-in-one -> single part; exact-boundary; oversized single
  interaction -> own part (never split); interaction-limit vs line-limit whichever-
  first; ordering preserved; concatenating all parts == original turns (round-trip
  invariant); never-split-a-turn invariant.
- `part_recovery_name`: zero-pad width tracks `total`; `total==1` yields the plain
  canonical name (no segment); `parse_recovery_name` round-trips a part name (bare sid +
  correct kind).
- `parse_recovery_name` regression (PR-001/PR-006): the existing filter form
  `YYYYMMDD-HHMM-<sid>.<scope>.compacted.md` now parses the session id as the BARE
  `<sid>` (not `<sid>.<scope>`); assert `cli_filter`'s stem-rebuild
  (`cli.py:7140,7152,7160`) still produces the same output filename it did before the
  fix (so the parser correction is behavior-preserving for filter's observable output).
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
- `export` unaffected: existing export tests still pass unchanged (no `--chunk` on
  export; sanity that the flag is rejected there if the parser would otherwise accept
  an unknown flag).

Run: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and paste real output.

## Docs

- README: document `--chunk` on recover/compact (not export), the new interactive
  `[c]hunk` choice, the `.part-NNofMM` naming, and the two new config keys (with the
  truncate-vs-chunk distinction).
- ARCHITECTURE: a short subsection on the `chunk_turns` seam, the interaction-boundary
  invariant, and the `part_recovery_name` naming authority.
- CHANGELOG: Added entry.
- CONFIG_TEMPLATE doc comments for the two new keys.

## Risks and non-goals

- Risk: changing `prompt_for_truncation`'s return contract. Mitigated by a single
  caller (`cli.py:3751`) + an anti-regression test locking the old choices.
- Risk: `parse_recovery_name` mis-parses the part segment (and already mis-parses the
  filter scope segment). This is a REQUIRED fix in D-3 (not "only if a test fails"),
  covered by the round-trip + filter-regression tests.
- Non-goal: changing the `LONG_SESSION_*` trigger thresholds or the default
  (truncate/prompt) behavior when `--chunk` is absent.
- Non-goal: cross-part semantic summarization/stitching of compaction output into one
  document (each part is compacted independently in Phase 2).
- Non-goal (maintainer decision, plan-review): chunking the `.ocbox` EXPORT. A bundle
  is DB rows for wholesale import, not readable/LLM text, already streams, and has no
  identified chunking use case; the partial-bundle integrity cost is not justified.
  `export` is untouched.

## Open questions

- O-1 (decide at execution, non-blocking): whether the per-part restart doc embeds a
  tiny index of sibling part filenames (nice-to-have, not required for correctness).

## Execution contract (gate)

An executing agent MUST:
- Treat O-1 as an execution-time nicety to record in the Workflow history; do not
  invent other scope. Export chunking is OUT (do not add it back).
- Scope fence: touch only the recover/compact/config/filename subsystems named above
  and their tests + the four docs (README, ARCHITECTURE, CHANGELOG, CONFIG_TEMPLATE).
  Do NOT modify the export code path. No unrelated refactors.
- Honesty rule (hard MUST): paste the ACTUAL `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`
  output; never claim a pass not run.
- Commit path-scoped (`git commit -m msg -- <paths>`), NEVER `-A`/`-a`, NEVER push,
  NEVER tag.
- On completion, set `Status: EXECUTED`, add a Workflow-history execution line, and
  `git mv` this IPD from `pending/` to `executed/` (verify no pending/executed dup
  with `git ls-tree HEAD`).
