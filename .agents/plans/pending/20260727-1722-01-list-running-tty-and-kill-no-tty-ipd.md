# IPD: `list running`/`lr` shows a TTY column and `ocman kill --no-tty` reaps detached instances

- Date: 2026-07-27
- Concern: UI/UX + capability (CLI). The maintainer runs several long-lived opencode
  instances and wants to see, in the running-instances listing, whether each instance is
  still attached to a live controlling terminal, and to be able to kill in one shot the ones
  that are NOT (orphaned / backgrounded / terminal-closed). The `ps -o tty` value is ALREADY
  captured per process (cli.py:7960) and flows into every enriched instance dict via the
  `**p` spread (cli.py:8246), but it is surfaced only in the mutation-guard error block
  (`_render_running_opencode`, cli.py:7972); `list running` and `kill` ignore it.
- Scope: `ocman/cli.py`, `tests/test_ocman.py`, `README.md`, `CHANGELOG.md`. Specifically:
  `cli_list_running` (add a TTY column + switch the table style), a small shared
  `_instance_tty` / `_is_detached` helper, `cli_kill` (new `--no-tty` batch selection), the
  `kill` subparser (new `--no-tty` flag), the `kill` normalization block
  (`_normalize`, cli.py:7001-7006 must emit `no_tty`) and the `run_kill` dispatch
  (cli.py:16348-16356 must pass `no_tty=`), and docs sync: the two affected README command-table
  rows (`list running`, `kill`) plus a `CHANGELOG.md` `[Unreleased]` entry, and the `kill`/`list
  running` `--help` text. No DB change, no dependency, no signal-handling change, no change to
  detection (`detect_running_instances` already carries `tty`). No `DECISIONS.md` entry: `--no-tty`
  reuses the existing confirm + PID-reuse-guard posture and introduces no new safety model
  (decided with maintainer 2026-07-27).
- Status: reviewed (not yet executed; awaiting human approval)
- Target version: rides the current in-flight line (final promotion decided at release-review).
- Approval: plan-review complete 2026-07-27; awaiting maintainer approval
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-27 (its_direct/pt3-claude-opus-4.8-1m-us): maintainer asked for a TTY indication in
  the listing and a way to kill just the instances no longer attached to an active terminal.
  Three initial design decisions resolved interactively (see Design decisions). The maintainer
  additionally asked that the running-instances table NOT be indented and to use vistab
  `style='none'` to save horizontal terminal space.
- 2026-07-27 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): two decisions resolved with the
  maintainer during review: (1) `ocman kill --no-tty` treats the WHOLE detached set as one batch
  (single preview + single confirm, works non-interactively), NOT the per-item numbered chooser
  (see NT-04a); (2) include docs sync (README rows + CHANGELOG `[Unreleased]` + `--help`), no
  DECISIONS.md entry.
- 2026-07-27 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PR-001..PR-004 all FIXED (docs-sync scope added NT-09; end-to-end flag wiring added NT-08;
  batch-reap semantics added NT-04a; `style='none'` header-rule trade-off recorded). Readiness:
  GO - PENDING HUMAN APPROVAL.

## Evidence
- `ps -o tty` value is captured at cli.py:7906 (fields include `tty`), parsed at cli.py:7932,
  stored as `"tty"` per process dict at cli.py:7960, and spread onto each enriched instance
  dict at cli.py:8246, so `it["tty"]` is available in both `cli_list_running` and the kill
  target dicts with NO detection change.
- Normalization precedent already exists: `_render_running_opencode` (cli.py:7972) maps a tty
  of `?` / `??` / `""` to the human string `"no tty"`. Tests assert both the `pts/3` capture
  and the `"no tty"` normalization (tests/test_ocman.py:916-918, :1215).
- `cli_list_running` builds its table at cli.py:12841-12864 with
  `header = ["PID","User","Uptime","Kind","Listener","Auth?","Project"]`,
  `align = ["r","l","r","l","l","l","l"]`, `vistab.Vistab(style="round-header", padding=0,...)`,
  optional `Session` column under `--long`. Rows are appended with NO leading-space indent
  today, so "not indented" is satisfied by the style switch alone (nothing prefixes the rows).
- vistab exposes a borderless `style='none'` (confirmed via `vistab.print_styles_list()`); it
  drops box borders and renders columns with single-space separation, which is the compact,
  no-wasted-realestate look the maintainer asked for.
- `kill` subparser: positional `pattern` (PID|PATTERN), `--dry-run`, `-9/--force`, `-y/--yes`
  at cli.py:6506-6515; normalized at cli.py:7001-7006; dispatched at cli.py:16348-16356.
- Kill target selection: `cli_kill` (cli.py:12682) routes a bare all-digits arg to
  `_kill_target_for_pid` (cli.py:12638), otherwise to `_kill_targets(cwd, pattern)`
  (cli.py:12613): `pattern is None` -> `_reconnect_candidates(cwd)` (cli.py:12314, cwd-scoped);
  else own-user instances matching `_instance_matches_pattern` (cli.py:12595). All own-user
  filtering uses the authoritative `os.stat("/proc/<pid>").st_uid == os.getuid()` check
  (cli.py:12629, :12332), NOT the truncatable ps username. The confirm/choose/kill loop
  (cli.py:12704-12774) and `_kill_pid_gracefully`/`_reuse_guard_ok`/`_pid_is_gone` guards are
  reused unchanged.

## Design decisions (RESOLVED with maintainer 2026-07-27)
- Which listing gets TTY: RESOLVED = `list running` / `lr` (`cli_list_running`) ONLY. `ocman ls`
  is `session list` over DB rows with no 1:1 live-process mapping; adding a fuzzy TTY column
  there would mostly be blank/misleading. Session listing is UNCHANGED.
- How kill selects detached instances: RESOLVED = a new `--no-tty` FLAG on `ocman kill`, not a
  reserved pattern keyword (a keyword would collide with substring PATTERN matching). `--no-tty`
  selects ALL own-user opencode instances whose controlling terminal is none, as a single BATCH
  (see the `--no-tty` multi-target decision below). It composes with `-y/--yes`, `--dry-run`,
  `-9/--force`. It is mutually exclusive with a positional PID|PATTERN (see NT-05).
- What counts as "no active TTY": RESOLVED = the `ps -o tty` value is `?` / `??` / empty. This
  reuses the exact normalization already in `_render_running_opencode` and the data already
  captured; no extra `/proc/<pid>/fd` probing. Detecting a TTY that once existed but whose
  `/dev/pts/N` was since removed is an explicit non-goal.
- `--no-tty` multi-target behavior: RESOLVED (plan-review 2026-07-27) = BATCH. When `--no-tty`
  matches 2+ detached instances it selects the WHOLE set (single preview listing all, single
  `confirm_destructive` gate), NOT the existing per-item numbered chooser. Rationale: the feature's
  purpose is "kill all the detached ones in one shot" and it must work non-interactively (a
  redirected/scripted reap); the numbered chooser (cli.py:12704-12731) would force a manual pick
  and `die` with "no TTY to choose" when stdout is not a terminal, defeating the intent. Safety is
  unchanged: one confirm by default (`-y` skips, `--dry-run` previews) and the per-signal
  PID-reuse guard still runs. The PID and PATTERN paths keep their existing chooser behavior.
- Table `style='none'` UX trade-off: ACCEPTED (maintainer-requested). `style='none'` is borderless
  and drops the header underline/rule that `round-header` drew (verified via
  `vistab.print_styles_list()`). This is a deliberate space-saving choice by the maintainer, not a
  regression to "fix" back; the bold header (color-gated) is retained. Recorded so the executor
  does not reintroduce a border.

## Requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| NT-01 | Single source of truth for "detached" | Add module-scope helpers near the existing running helpers: `_instance_tty(inst) -> str` returns the raw tty or `""`; `_is_detached(inst) -> bool` is `True` iff `_instance_tty(inst)` is in `("?", "??", "")` (after `.strip()`). Reuse this everywhere (list column + kill filter) so the rule cannot drift. | normalization at cli.py:7972; tty on dict cli.py:8246 |
| NT-02 | `list running`/`lr` shows a TTY column | In `cli_list_running`, insert a `"TTY"` column (left-aligned) into `header`/`align`, placed after `User` (`["PID","User","TTY","Uptime","Kind","Listener","Auth?","Project"]`). Cell value = `_instance_tty(it)` normalized to `"no tty"` when detached (same string as the guard block), else the raw `pts/N`. `--long` still appends `Session` last. `--json` is UNCHANGED (the raw `tty` key already rides on each instance dict via detection; no new JSON field is added). | table build cli.py:12841-12864; json emit cli.py:12822-12826 |
| NT-03 | The running-instances table is borderless / not indented | Switch `cli_list_running`'s table from `style="round-header"` to `style="none"` (keep `padding=0`, keep the color-gated bold header via `set_header_style`). Rows already carry no leading-space indent, so no other change is needed to satisfy "not indented." The `--long` hidden-Session hint line (cli.py:12865-12867) and the security banner block are UNCHANGED. | style list confirmed via vistab.print_styles_list(); build cli.py:12848-12851 |
| NT-04 | `ocman kill --no-tty` selects all own-user detached opencode instances | Add `--no-tty` to the `kill` subparser (store_true). In `cli_kill`, when `--no-tty` is set, resolve targets by enumerating `detect_running_instances(all_users=False)`, keeping own-user PIDs (authoritative `os.stat("/proc/<pid>").st_uid == getuid()`) that satisfy `_is_detached(it)`. Then send them straight to the EXISTING preview + `confirm_destructive` + kill loop and guards (`_kill_pid_gracefully`, `_reuse_guard_ok`, `_pid_is_gone`); `-y`, `--dry-run`, `-9/--force` behave exactly as for other selections. | own-user filter cli.py:12622-12634; kill loop cli.py:12734-12774 |
| NT-04a | `--no-tty` kills the WHOLE detached set as a batch (no per-item chooser) | `--no-tty` must BYPASS the multi-target numbered chooser (cli.py:12704-12731) and set `to_kill = targets` directly, so 2+ detached instances are shown in the single batch preview and killed after ONE confirm. This is required for the "reap them all" intent and to work non-interactively (the chooser `die`s with "no TTY to choose" when stdout is not a terminal). Implement by branching on the `--no-tty` selection before the `len(targets) == 1 / else` block (e.g. treat `--no-tty` like the pre-selected "all" case). One confirm still gates it (`-y` skips, `--dry-run` previews); the per-signal reuse guard is unchanged. | chooser to bypass cli.py:12704-12731; batch preview+confirm cli.py:12734-12758 |
| NT-05 | `--no-tty` is mutually exclusive with a positional PID\|PATTERN | If `--no-tty` is given AND a positional `pattern` is present, `die(...)` with a clear message ("`--no-tty` selects by terminal state; do not also pass a PID or PATTERN.") BEFORE any detection/preview. `--no-tty` alone (no positional) is the intended form; it does NOT fall through to the cwd-scoped `_reconnect_candidates` path. | cli_kill entry cli.py:12688-12695 |
| NT-06 | Zero-match `--no-tty` is a calm, explicit message (not an all-clear-looking blank) | When `--no-tty` matches nothing, print an informational line naming the criterion, e.g. `f"{info_prefix()} No detached opencode instances (all are attached to a terminal)."` and return without killing. Detection unavailability still raises `RunningDetectionError` and is translated by the existing `except` to the Linux-only message. | no-targets branch cli.py:12699-12702; RunningDetectionError xlate cli.py:12696-12697 |
| NT-07 | No behavior change to existing selection paths, signalling, guards, flags, dry-run, or exit codes | Only ADD the `--no-tty` branch at target resolution, the batch bypass, and the mutual-exclusion guard; the no-arg (cwd), PID, and PATTERN paths, their numbered chooser, and all reuse guards are untouched. The `reconnect` command and cross-user posture are untouched. | cli_kill loop + guards cli.py:12704-12774 unchanged |
| NT-08 | The `--no-tty` flag is wired end-to-end (parser -> normalize -> dispatch -> handler) | Add `--no-tty` (`store_true`) to the `kill` subparser; in `_normalize`'s `group == "kill"` block set `out["no_tty"] = bool(g("no_tty", False))`; in the `run_kill` dispatch pass `no_tty=getattr(args, "no_tty", False)` into `cli_kill`, and add a `no_tty: bool = False` parameter to `cli_kill`. Without all four the flag is parsed but never reaches the handler. | subparser cli.py:6506-6515; normalize cli.py:7001-7006; dispatch cli.py:16348-16356; cli_kill signature cli.py:12682-12683 |
| NT-09 | Docs stay honest (P8) | Update: (a) README command-table row for `list running`/`lr` (README.md:438) to mention the TTY column; (b) README row for `ocman kill` (README.md:444) to document `--no-tty` (reap all own-user instances no longer attached to a terminal; batch confirm; Linux-only); (c) a `CHANGELOG.md` `[Unreleased]` "Added" entry for both the TTY column and `kill --no-tty`; (d) the `kill` and `list running` subparser `--help`/help text. No DECISIONS.md entry (no new safety model). | README.md:438,444; CHANGELOG.md `[Unreleased]`; subparser help cli.py:6506-6515, list-running parser cli.py:6578 |

## Non-goals
- No TTY column or TTY filter on `ocman ls` / `session list` (sessions are DB rows, not live
  processes).
- No detection of a TTY that once existed but whose device node was later removed (only the
  `ps` `?`/none state is used).
- No `--no-tty` for `reconnect` (reconnect is cwd-scoped and relaunches; reaping detached
  instances is a `kill`-only concern here).
- No cross-user killing; no Windows/macOS support (kill stays Linux-only via existing guards).
- No new `--json` field for `kill`; `list running --json` keeps emitting the existing instance
  dicts (which already include `tty`).

## Validation plan
- `PYTHONPATH=. pytest -q` full suite green (paste ACTUAL output).
- New tests (monkeypatch `detect_running_instances` / `/proc` helpers; capsys; no real signals):
  - NT-02: an instance with `tty="pts/3"` renders a `TTY` column showing `pts/3`; an instance
    with `tty="?"` renders `no tty`. Assert the `TTY` header is present and positioned after
    `User`.
  - NT-03: `cli_list_running` output contains NO box-border glyphs (assert absence of `│`/`╭`
    round-header borders) and rows are not indented (no leading whitespace before `PID`), i.e.
    the `style='none'` switch took effect.
  - NT-04/04a: two detached instances (`tty` in `?`/none) + one attached (`pts/2`) -> `--no-tty`
    targets exactly the two detached PIDs and kills BOTH in one batch (no numbered chooser
    prompt); with `-y` both are killed, the attached one is not. Assert the numbered
    "Kill which? [1-N" prompt does NOT appear.
  - NT-04a non-interactive: with stdout NOT a TTY (monkeypatch `sys.stdout.isatty` -> False) and
    `-y`, `--no-tty` still kills all detached targets and does NOT `die` with "no TTY to choose"
    (proves the chooser is bypassed).
  - NT-04b: `--no-tty --dry-run` prints the two detached targets and sends ZERO signals.
  - NT-05: `--no-tty` together with a positional (PID or PATTERN) -> SystemExit with the
    mutual-exclusion message, zero detection/kills.
  - NT-06: `--no-tty` with all instances attached -> calm "No detached opencode instances..."
    message, zero kills, clean exit.
  - NT-07: an existing PATTERN kill and a bare-PID kill still resolve through their current
    paths unchanged (regression guard, incl. the PATTERN multi-match numbered chooser still
    prompting); `_is_detached` correctly classifies `""`, `"?"`, `"??"` as detached and `"pts/0"`
    as attached (unit test of the helper).
  - NT-08: parse `["kill", "--no-tty"]` through the real parser + `_normalize` and assert
    `no_tty` is True on the namespace and reaches `cli_kill` (e.g. monkeypatch `cli_kill` to
    record its `no_tty` kwarg, or assert via the dispatch path).
  - NT-09 (docs): a light assertion or manual check that README rows and the CHANGELOG
    `[Unreleased]` entry mention the TTY column and `--no-tty` (no runtime test required; verify
    by reading the edited files and noting it in the execution record).
- No em/en dash in authored prose.

## Gate / execution contract (MUST, per AGENTS.md)
Work the `## Detailed Implementation Checklist (TODO)` below top to bottom (mirror it in a
TodoWrite list while coding); a plan may claim completion only when every execution box AND its
matching `## Verification checklist` row are checked with concrete evidence.
- Open questions: none (all design decisions, the table-style request, the `--no-tty` batch
  semantics, and the docs-sync scope are resolved above).
- Scope fence: `ocman/cli.py` (`_instance_tty`/`_is_detached` helpers, `cli_list_running`
  column + style, `cli_kill` `--no-tty` batch selection + batch-bypass + mutual-exclusion guard,
  `kill` subparser flag, `_normalize` `no_tty`, `run_kill` dispatch), `tests/test_ocman.py`,
  `README.md` (rows for `list running` and `kill`), and `CHANGELOG.md` (`[Unreleased]`). Nothing
  else (no `DECISIONS.md`, no TUI, no `reconnect`).
- Honesty rule: paste the ACTUAL pytest output; do not claim a hand-run of the TUI (this is a
  CLI change, testable headlessly).
- Commits: path-scoped (`git commit -m msg -- ocman/cli.py tests/test_ocman.py README.md CHANGELOG.md <this ipd>`),
  never `git add -A`/`-a`, never push.
- Lifecycle: on completion + green tests, `git mv` this file pending/ -> executed/ and append an
  Execution record.
- Release: rides the in-flight line; covered by the eventual delta release-review. No tag / no
  release here.

## Detailed Implementation Checklist (TODO)
Execute top to bottom. Every box MUST be checked AND independently verified (see the
Verification checklist) before this plan may claim completion or move to `executed/`. Do NOT
check a box on intent; check it only when the action is actually done.

- [ ] C1 (NT-01) Add `_instance_tty(inst) -> str` (raw tty or `""`) and `_is_detached(inst) -> bool`
  (`True` iff `_instance_tty(inst).strip()` in `("?", "??", "")`) at module scope near the running
  helpers; both used by the list column AND the kill filter (single source of truth).
- [ ] C2 (NT-02) In `cli_list_running`, insert a `"TTY"` column (left-aligned) into `header`/`align`
  right after `User` -> `["PID","User","TTY","Uptime","Kind","Listener","Auth?","Project"]`; cell =
  `_instance_tty(it)` shown as `"no tty"` when detached else the raw `pts/N`; `--long` still appends
  `Session` last; `--json` path unchanged (no new field).
- [ ] C3 (NT-03) Switch that table from `style="round-header"` to `style="none"` (keep `padding=0`
  and the color-gated bold header); leave the `--long` hint line and the security banner as-is; do
  NOT reintroduce a border (recorded UX trade-off).
- [ ] C4 (NT-08) Add `--no-tty` (`store_true`) to the `kill` subparser; set
  `out["no_tty"] = bool(g("no_tty", False))` in `_normalize`'s `group == "kill"` block; add
  `no_tty=getattr(args, "no_tty", False)` to the `run_kill` dispatch; add a `no_tty: bool = False`
  parameter to `cli_kill`.
- [ ] C5 (NT-05) In `cli_kill`, if `no_tty` AND a positional `pattern` is present, `die(...)` with
  the mutual-exclusion message BEFORE any detection/preview.
- [ ] C6 (NT-04) When `no_tty` is set (and no positional), resolve targets = own-user
  (`os.stat("/proc/<pid>").st_uid == getuid()`) instances from `detect_running_instances(all_users=False)`
  that satisfy `_is_detached(it)`.
- [ ] C7 (NT-04a) BYPASS the numbered chooser for the `--no-tty` selection: set `to_kill = targets`
  directly (like the pre-selected "all" case) so 2+ detached instances go straight to the single
  batch preview + one `confirm_destructive` gate and work non-interactively (`sys.stdout.isatty()`
  False must NOT `die` with "no TTY to choose"). `-y`, `--dry-run`, `-9/--force` compose normally.
- [ ] C8 (NT-06) When `--no-tty` matches nothing, print the calm "No detached opencode instances
  (all are attached to a terminal)." line and return; detection unavailability still surfaces via
  the existing `RunningDetectionError` -> Linux-only translation.
- [ ] C9 (NT-07) Confirm NO change to the no-arg (cwd), PID, and PATTERN selection paths, their
  numbered chooser, the kill loop, or the reuse/`_pid_is_gone`/`_reuse_guard_ok` guards, and none
  to `reconnect` or the cross-user posture.
- [ ] C10 (NT-09) Docs sync: README `list running`/`lr` row (README.md:438) mentions the TTY column;
  README `kill` row (README.md:444) documents `--no-tty` (reap all own-user instances no longer
  attached to a terminal; batch confirm; Linux-only); a `CHANGELOG.md` `[Unreleased]` "Added" entry
  covers both; `kill` and `list running` `--help`/help text updated. No `DECISIONS.md` entry.
- [ ] C11 (tests) Add the tests enumerated in the Validation plan (NT-02, NT-03, NT-04/04a incl. the
  non-interactive case, NT-04b, NT-05, NT-06, NT-07 incl. `_is_detached` unit test, NT-08).
- [ ] C12 Run `PYTHONPATH=. pytest -q` and PASTE the ACTUAL runner output into the Execution record.
- [ ] C13 No em/en dash introduced in authored prose (cli help/error text, README, CHANGELOG, this
  plan). Run the leak sanitizer (`aw sanitize --agent`) over changed tracked files.

## Verification checklist (cross-check; concrete evidence per item)
Each row maps 1:1 to the execution checklist above and is satisfied ONLY by the concrete evidence
named. Do not mark this plan complete until every row has its evidence pasted or cited in the
Execution record.

- [ ] V1 (C1) Cite the `_instance_tty`/`_is_detached` definitions by `cli.py:<line>`; confirm BOTH
  the list column (C2) and the kill filter (C6) call the SAME helper (grep count == 2+ call sites).
- [ ] V2 (C2) Paste captured `cli_list_running` human output showing a `TTY` header after `User`, one
  row with `pts/N` and one with `no tty`; confirm `--json` output has no new key vs today.
- [ ] V3 (C3) Paste the rendered table showing NO box glyphs (`│`, `╭`, `╞`) and NO leading
  whitespace before `PID`; header still bold when color is enabled.
- [ ] V4 (C4/NT-08) Paste the NT-08 test proving `["kill","--no-tty"]` yields `no_tty=True` reaching
  `cli_kill` (recorded kwarg or dispatch assertion), test PASSED.
- [ ] V5 (C5/NT-05) Paste the test: `--no-tty` + positional -> `SystemExit`, zero detection/kills.
- [ ] V6 (C6+C7/NT-04/04a) Paste the test: 2 detached + 1 attached -> both detached PIDs killed in
  ONE batch, attached untouched, and the numbered "Kill which? [1-N" prompt is ABSENT; PLUS the
  non-interactive variant (isatty False, `-y`) kills all without the "no TTY to choose" `die`.
- [ ] V7 (C7/NT-04b) Paste the `--no-tty --dry-run` test: targets previewed, ZERO signals sent.
- [ ] V8 (C8/NT-06) Paste the all-attached test: calm "No detached opencode instances" message, zero
  kills, clean exit.
- [ ] V9 (C9/NT-07) Paste the regression test: a PATTERN multi-match still shows the numbered
  chooser and a bare-PID kill still routes through `_kill_target_for_pid`; `_is_detached` unit test
  classifies `""`/`"?"`/`"??"` detached and `"pts/0"` attached.
- [ ] V10 (C10/NT-09) Quote the edited README `list running` and `kill` rows and the CHANGELOG
  `[Unreleased]` entry showing the TTY column and `--no-tty`; confirm `--help` text updated.
- [ ] V11 (C12) Paste the FULL `pytest -q` summary line (e.g. `N passed, M skipped`); the new tests
  are included and green. No skips masking a new test.
- [ ] V12 (C13) Paste `aw sanitize --agent` result (clean) for changed tracked files and confirm no
  em/en dash was added.

## Deferred / open
- None. (Dead-device-node detection, `ls`/session TTY, and `reconnect --no-tty` are explicit
  non-goals for this IPD.)
