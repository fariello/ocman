# TODO

Informal backlog of ideas not yet promoted to an IPD in `.agents/plans/pending/`.

## Chunk large sessions on recover/compact: SHIPPED (2026-07-17)

Implemented via `.agents/plans/executed/20260717-chunk-large-sessions-ipd.md`:
`--chunk` on `session recover` and `session compact` splits a large session into
ordered, self-contained `YYYYMMDD-HHMM-<sid>.part-NNofMM.<kind>.md` files instead of
truncating (nothing dropped). Boundaries are whole interactions (never mid-turn);
`--max-lines`/`--max-interactions` set the per-part size, with defaults from the new
`chunk_max_lines` / `chunk_max_interactions` config keys. The interactive large-
session prompt gained a `[c]hunk` choice. `compact --chunk` sends each part to the LLM
separately (so each fits the context window) and sums the per-part cost table.

Resolved-differently vs the original idea: the ".ocbox export" was deliberately left
OUT of scope (a bundle is DB rows for wholesale import, not readable/LLM text, and
already streams; chunking it adds partial-bundle integrity cost for no use case). The
"is-large" TRIGGER stays the fixed 2500 lines / 100 interactions constants (the
original note's ">250 interactions" did not match the real 100); the two new config
keys size the PARTS, not the trigger.

## `ocman spend`: SHIPPED (2026-07-15)

Implemented via `.agents/plans/executed/20260715-assess-functionality-ipd.md` Step 8:
`ocman spend` (per-project table by default), `ocman spend <project> --sessions`
(per-session detail), `--historical` (adds the deletion ledger's saved spend as a
single global line; not attributable per project), and `--json`. Cost comes from the
live session `cost` columns plus the ledger `cumulative.cost_deleted`.

Deferred stretch goal (not yet built): forked/shared-spend de-duplication (attribute
shared ancestor tokens once across a fork tree rather than double-counting). Promote to
its own IPD if wanted.

## Pending-actions manifest: extend beyond the delete-family (FUTURE)

Shipped (2026-07-26): `--pend` / interactive `[p]` add-to-pending for the delete-family
(`session delete`, `project delete`, `db clean`, `db clean-orphans`) when OpenCode is running;
`ocman pending list/run/clear` with re-resolve + re-preview + re-confirm at drain; an
`[NOTIC] X items pending` reminder on every run; TUI banner + Pending tab. Manifest at
`~/.local/share/opencode/ocman_pending.json`.

Future candidates (same safety model, deferred from the initial IPD on the complexity axis):
extend deferral to `rename`, `move`, `db rebase`, and `reclaim`. Each needs its own staleness
semantics at drain (a rename/move target or a path-prefix rebase can conflict with intervening
edits). Also deferred: an opt-in auto-drain when no OpenCode is running (functionality axis:
auto-running deferred deletes is a surprise-destruction risk). Promote to its own IPD if wanted.

## `OCMAN_CONFIG_PATH` environment override: TO CONSIDER

The README once documented `OCMAN_CONFIG_PATH` as an environment variable that "overrides
the location of ocman.toml", but the code never read it from the environment: it is a
hardcoded module constant (`ocman/cli.py` `OCMAN_CONFIG_PATH`), overridable only
programmatically (tests rebind it) or, for the DB path alone, per-run via `--db`. The false
env-var row was removed from the README (assess-documentation IPD, 2026-07-25).

To reconsider: add a real environment override, e.g. read `os.environ.get("OCMAN_CONFIG_PATH")`
when the constant is initialized, so a user can relocate their config without editing code.
This is a small behavior change but needs its own IPD + tests (config load ordering, precedence
vs `--db`, and interaction with the test-suite rebinding). Promote to a code IPD if wanted;
until then there is no env override for the config-file path.

## workflow-artifacts leak sanitization: TO REMEDIATE

`aw sanitize` reports about 8,472 findings inside `workflow-artifacts/` run records: home paths
(`/home/<user>/...`), the maintainer username/handle, and some session ids. `workflow-artifacts/`
is now gitignored (commit 50774d9) so future re-adds stay untracked, and these files are not in
this repo's committed git history. Remaining work: confirm nothing sensitive from run records ever
reached committed history (a full `aw sanitize` over tracked files + git history), and keep run
records local only going forward. A framework-level fix was requested via a comms task to
agent-workflows (flip the "committed deliverable" default, add the gitignore in setup-repo).

## Persistent TUI pending-actions banner: CONSIDER

The pending-actions feature (executed 2026-07-26) surfaces the deferred-action count via a Pending
tab in the TUI, but not as an always-visible count in the TUI chrome. Consider adding a persistent
banner or footer indicator showing the pending count, mirroring the CLI `[NOTIC] X items pending`
reminder.

## CI: bump Node 20 GitHub Actions: CONSIDER

CI runs emit a deprecation warning that `actions/checkout@v4` and `actions/setup-python@v5` target
Node 20 and are being forced onto Node 24. Bump those actions to versions that run on Node 24
natively to silence the warning and stay current. Non-blocking; CI is green.
