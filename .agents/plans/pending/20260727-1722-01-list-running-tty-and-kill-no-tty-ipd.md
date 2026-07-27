# IPD: `list running`/`lr` shows a TTY column and `ocman kill --no-tty` reaps detached instances

- Date: 2026-07-27
- Concern: UI/UX + capability (CLI). The maintainer runs several long-lived opencode
  instances and wants to see, in the running-instances listing, whether each instance is
  still attached to a live controlling terminal, and to be able to kill in one shot the ones
  that are NOT (orphaned / backgrounded / terminal-closed). The `ps -o tty` value is ALREADY
  captured per process (cli.py:7960) and flows into every enriched instance dict via the
  `**p` spread (cli.py:8246), but it is surfaced only in the mutation-guard error block
  (`_render_running_opencode`, cli.py:7972); `list running` and `kill` ignore it.
- Scope: `ocman/cli.py` only, plus `tests/test_ocman.py`. Specifically:
  `cli_list_running` (add a TTY column + switch the table style), a small shared
  `_instance_tty` / `_is_detached` helper, `_kill_targets` / `cli_kill` (new `--no-tty`
  selection), and the `kill` subparser (new `--no-tty` flag). No DB change, no dependency, no
  signal-handling change, no change to detection (`detect_running_instances` already carries
  `tty`).
- Status: PROPOSED (not yet executed)
- Target version: rides the current in-flight line (final promotion decided at release-review).
- Approval: awaiting plan-review + maintainer approval
- Author: its_direct/pt3-claude-opus-4.8-1m-us

## Workflow history
- 2026-07-27 (its_direct/pt3-claude-opus-4.8-1m-us): maintainer asked for a TTY indication in
  the listing and a way to kill just the instances no longer attached to an active terminal.
  Three design decisions resolved interactively (see Design decisions). The maintainer
  additionally asked that the running-instances table NOT be indented and to use vistab
  `style='none'` to save horizontal terminal space.

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
  selects ALL own-user opencode instances whose controlling terminal is none. It composes with
  `-y/--yes`, `--dry-run`, `-9/--force`. It is mutually exclusive with a positional PID|PATTERN
  (see NT-05).
- What counts as "no active TTY": RESOLVED = the `ps -o tty` value is `?` / `??` / empty. This
  reuses the exact normalization already in `_render_running_opencode` and the data already
  captured; no extra `/proc/<pid>/fd` probing. Detecting a TTY that once existed but whose
  `/dev/pts/N` was since removed is an explicit non-goal.

## Requirements

| ID | Item | Approach | Evidence |
|----|------|----------|----------|
| NT-01 | Single source of truth for "detached" | Add module-scope helpers near the existing running helpers: `_instance_tty(inst) -> str` returns the raw tty or `""`; `_is_detached(inst) -> bool` is `True` iff `_instance_tty(inst)` is in `("?", "??", "")` (after `.strip()`). Reuse this everywhere (list column + kill filter) so the rule cannot drift. | normalization at cli.py:7972; tty on dict cli.py:8246 |
| NT-02 | `list running`/`lr` shows a TTY column | In `cli_list_running`, insert a `"TTY"` column (left-aligned) into `header`/`align`, placed after `User` (`["PID","User","TTY","Uptime","Kind","Listener","Auth?","Project"]`). Cell value = `_instance_tty(it)` normalized to `"no tty"` when detached (same string as the guard block), else the raw `pts/N`. `--long` still appends `Session` last. `--json` is UNCHANGED (the raw `tty` key already rides on each instance dict via detection; no new JSON field is added). | table build cli.py:12841-12864; json emit cli.py:12822-12826 |
| NT-03 | The running-instances table is borderless / not indented | Switch `cli_list_running`'s table from `style="round-header"` to `style="none"` (keep `padding=0`, keep the color-gated bold header via `set_header_style`). Rows already carry no leading-space indent, so no other change is needed to satisfy "not indented." The `--long` hidden-Session hint line (cli.py:12865-12867) and the security banner block are UNCHANGED. | style list confirmed via vistab.print_styles_list(); build cli.py:12848-12851 |
| NT-04 | `ocman kill --no-tty` selects all own-user detached opencode instances | Add `--no-tty` to the `kill` subparser (store_true). In `cli_kill`, when `--no-tty` is set, resolve targets by enumerating `detect_running_instances(all_users=False)`, keeping own-user PIDs (authoritative `os.stat("/proc/<pid>").st_uid == getuid()`) that satisfy `_is_detached(it)`. Reuse the EXISTING multi-target confirm/choose/kill loop and guards verbatim (`_kill_pid_gracefully`, `_reuse_guard_ok`, `_pid_is_gone`); `-y`, `--dry-run`, `-9/--force` behave exactly as for other selections. | `_kill_targets` own-user filter cli.py:12622-12634; kill loop cli.py:12704-12774 |
| NT-05 | `--no-tty` is mutually exclusive with a positional PID\|PATTERN | If `--no-tty` is given AND a positional `pattern` is present, `die(...)` with a clear message ("`--no-tty` selects by terminal state; do not also pass a PID or PATTERN.") BEFORE any detection/preview. `--no-tty` alone (no positional) is the intended form; it does NOT fall through to the cwd-scoped `_reconnect_candidates` path. | cli_kill entry cli.py:12688-12695 |
| NT-06 | Zero-match `--no-tty` is a calm, explicit message (not an all-clear-looking blank) | When `--no-tty` matches nothing, print an informational line naming the criterion, e.g. `f"{info_prefix()} No detached opencode instances (all are attached to a terminal)."` and return without killing. Detection unavailability still raises `RunningDetectionError` and is translated by the existing `except` to the Linux-only message. | no-targets branch cli.py:12699-12702; RunningDetectionError xlate cli.py:12696-12697 |
| NT-07 | No behavior change to existing selection paths, signalling, guards, flags, dry-run, or exit codes | Only ADD the `--no-tty` branch at target resolution and the mutual-exclusion guard; the no-arg (cwd), PID, and PATTERN paths, the confirm/choose/kill loop, and all reuse guards are untouched. The `reconnect` command and cross-user posture are untouched. | cli_kill loop + guards cli.py:12704-12774 unchanged |

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
  - NT-04a: two detached instances (`tty` in `?`/none) + one attached (`pts/2`) -> `--no-tty`
    targets exactly the two detached PIDs; with `-y` both are killed, the attached one is not.
  - NT-04b: `--no-tty --dry-run` prints the two detached targets and sends ZERO signals.
  - NT-05: `--no-tty` together with a positional (PID or PATTERN) -> SystemExit with the
    mutual-exclusion message, zero detection/kills.
  - NT-06: `--no-tty` with all instances attached -> calm "No detached opencode instances..."
    message, zero kills, clean exit.
  - NT-07: an existing PATTERN kill and a bare-PID kill still resolve through their current
    paths unchanged (regression guard); `_is_detached` correctly classifies `""`, `"?"`, `"??"`
    as detached and `"pts/0"` as attached (unit test of the helper).
- No em/en dash in authored prose.

## Gate / execution contract (MUST, per AGENTS.md)
Create a step-granular TodoWrite checklist (one per NT-*) BEFORE coding.
- Open questions: none (all three design decisions + the table-style request are resolved above).
- Scope fence: `ocman/cli.py` (`_instance_tty`/`_is_detached` helpers, `cli_list_running`
  column + style, `cli_kill` `--no-tty` selection + mutual-exclusion guard, `kill` subparser
  flag) and `tests/test_ocman.py`. Nothing else.
- Honesty rule: paste the ACTUAL pytest output; do not claim a hand-run of the TUI (this is a
  CLI change, testable headlessly).
- Commits: path-scoped (`git commit -m msg -- ocman/cli.py tests/test_ocman.py <this ipd>`),
  never `git add -A`/`-a`, never push.
- Lifecycle: on completion + green tests, `git mv` this file pending/ -> executed/ and append an
  Execution record.
- Release: rides the in-flight line; covered by the eventual delta release-review. No tag / no
  release here.

## Deferred / open
- None. (Dead-device-node detection, `ls`/session TTY, and `reconnect --no-tty` are explicit
  non-goals for this IPD.)
