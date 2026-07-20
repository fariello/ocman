# Decisions

This document records significant engineering decisions for `ocman`: the choice made,
why, and the alternatives that were rejected. It complements the executed-IPD trail under
`.agents/plans/executed/` and `CHANGELOG.md`; where an IPD covers a decision in depth, this
file links to it rather than duplicating the rationale. Entries are append-only and dated.

## 2026-07-18: CLI and TUI reach behavior parity, in five reviewed phases

### Context

The interactive TUI had drifted behind the CLI: it could delete more destructively than the
CLI (no recovery-extract option), lacked the storage checkup / guarded reclaim, had no
spend or running views, no bulk actions, and no project-bundle / move / backup-prune /
search / filter surface. Divergence between the two front ends is a correctness and safety
hazard, not just a feature gap: a user who trusts the TUI could lose data the CLI would have
protected.

### Decision

Bring the TUI to full parity with the CLI, staged as five separately reviewed and executed
IPDs under one umbrella roadmap, each reusing the CLI's underlying functions (never
re-implementing the logic in the widget layer):

- P1 delete-safety (`45eb8c4`): recovery-extract-first option on session/project delete;
  the dead "Clear Historical Activity Log (Planned)" button became a working, typed-yes
  guarded control.
- P2 Storage tab (`79f5818`): read-only checkup running the same checks as `ocman doctor`,
  plus guarded reclaim (checkpoint+VACUUM, temp, compacted parts, backup prune).
- P3 Spend + Running tabs (`2fde996`): read-only, rendered from the same `gather_spend()`
  and process-detection the CLI uses, so numbers match.
- P4 bulk multi-select + duration prune + chunk (`6e6286a`).
- P5 project bundles / local move / backup clean / search / filter (`5972d0c`).

### Rejected alternatives

- Re-implement each behavior inside the widgets: rejected. It would fork the guards and let
  the two front ends drift again. Every TUI action calls the same CLI-layer function, so a
  fix or guard applies to both at once.
- Expose the dangerous `reclaim --force-snapshots` in the TUI: rejected. A destructive
  snapshot-force reclaim is intentionally CLI-only; the TUI shows a note pointing to
  `ocman reclaim --force-snapshots` / `ocman doctor` rather than offering a
  one-click path to it.
- Ship parity as one large change: rejected in favor of five reviewed phases, each with its
  own IPD, so each destructive surface got its own review and anti-regression gate. See
  `.agents/plans/executed/20260718-1648-0[1-6]-tui-*`.

## 2026-07-19: Clean top-level error message by default, full traceback only under -v

### Context

Any command that raised an unexpected exception leaked a raw Python stack trace to the user.
A prior tail-only `try` covered only the last commands, leaving list/spend/doctor and most
of the CLI unguarded. This is a self-documentation failure: a naive user sees a wall of
traceback instead of a next step.

### Decision

Wrap the whole entrypoint: `main()` calls `_run_main()` inside a guard that catches any
non-`SystemExit` / non-`RecoveryError` / non-`KeyboardInterrupt` exception, prints a clean
one-line message plus a hint to re-run with `-v`, and re-raises the full traceback only when
`-v` is set. Also routed all seven "Database not found" sites through a shared
`_db_not_found_error()` helper so the guidance is identical everywhere. Shipped `3dcd44e`;
see `.agents/plans/executed/20260719-0125-01-assess-self-documentation.md`.

### Rejected alternatives

- Keep the tail-only `try` at the old `cli.py` site: rejected. It left most commands
  unguarded; the wrapper covers the whole program.
- Suppress tracebacks entirely: rejected. Developers and bug reporters need them, hence the
  `-v` escape hatch rather than a permanent swallow.

## 2026-07-19: save_ocman_config merges over the on-disk config, not over DEFAULT_CONFIG

### Context

`save_ocman_config(config_dict)` merged the caller's dict over `DEFAULT_CONFIG`, so any key
the caller omitted was written back at its DEFAULT rather than its current value. The TUI
config form manages only a subset of keys and saves automatically (on tab switch and
unmount), so it silently RESET a user's tuned `chunk_*`, `reclaim_*`, `filter_*`,
`copy_restart_to_project_prompts`, and `history_max_runs` values. This was found as FU-01
while executing TUI parity Phase 4, and fixed as a corrective IPD.

### Decision

Build the merge base from the EXISTING on-disk config (`base = load_ocman_config(path)`,
which itself falls back to `DEFAULT_CONFIG` for absent keys), then `base.update(config_dict)`
and render. Omitted keys keep their current value; keys never set anywhere still fall back
to defaults. Fixing it at the `save_ocman_config` layer covers ALL partial-save callers, not
just the TUI. Shipped `7698791`; see
`.agents/plans/executed/20260719-0110-01-config-save-preserve-keys-ipd.md`.

### Why it does not break reset

Full-config callers (`reset_tui_config`, `cli_create_config`) pass a complete dict, and
merging a complete dict over the existing config yields exactly that dict, so "reset to
defaults" still resets. The rendered template stays fully populated because
`load_ocman_config` returns every key.

### Rejected alternatives

- Add form fields for every key so the TUI always saves a full dict: rejected. It treats the
  symptom for one caller and leaves the layer bug in place for any future partial-save
  caller. Fixing the save layer is the correct general-case fix.

## 2026-07-19: Require vistab >= 1.3.0 (clean install broke on Python 3.12)

### Context

During release-review Section 9 (S9-REL2) a clean install of the published wheel raised
`NameError: 'Set'` on Python 3.12: the then-latest `vistab` 1.2.0 used a `Set` annotation
without importing it. The prior `vistab` 1.1.3 avoided that but lacked `vistab.set_color`,
which `ocman` now depends on, so pinning back was not an option. The vistab maintainer
published 1.3.0 (there is no 1.2.1) fixing the import while keeping `set_color`.

### Decision

Set the dependency floor to `vistab>=1.3.0` in `pyproject.toml` and add a CHANGELOG "Fixed"
note. Shipped `58399fe`.

### Rejected alternatives

- Pin `vistab==1.1.3`: rejected, it lacks `set_color`.
- Vendor or shim the broken annotation: rejected, the upstream fix (1.3.0) is clean and
  already available; carrying a shim would be dead weight.

## 2026-07-19: Support Linux, macOS, and Windows rather than narrowing the CI matrix

### Context

With `fail-fast: false` set (see next entry) the true per-cell CI picture emerged: Linux
5/5 green, but macOS 5/5 and Windows 5/5 failing on test-portability issues (POSIX-absolute
worktree strings that are not absolute on Windows; `/var` -> `/private/var` symlink prefix
mismatch on macOS; forward-slash path asserts and Textual modal-mount timing in TUI tests).
The cheap escape would have been to drop macOS and Windows from the matrix.

### Decision

Support all three operating systems and fix every macOS / Windows test failure, rather than
narrowing the matrix to hide them. The failures were in the TESTS, not the product; the
product code is already cross-platform, so the honest fix is to make the tests portable and
keep all 15 cells (3 OS x 5 Python) as gates.

### Rejected alternatives

- Drop macOS / Windows from the matrix: rejected. It would ship a "cross-platform" tool
  whose non-Linux behavior is never verified, and silently regress those users.
- `skipif` the failing tests off Linux: rejected for the same reason as the symlink case
  below, it drops real coverage on an OS where the behavior still applies. Skips are used
  only where the scenario genuinely cannot exist off the platform (e.g. real
  process-detection, POSIX-only temp-ownership).

## 2026-07-19: Cross-platform test helpers instead of platform skips

### Context

Making the suite pass on macOS and Windows without weakening assertions required a small set
of shared helpers rather than scattered `sys.platform` branches or skips.

### Decision

Add to `tests/conftest.py`:

- `abs_path(posix_like)`: keeps a POSIX-absolute seed path unchanged on POSIX and
  drive-anchors it on Windows (e.g. `/home/me/proj` -> `C:\home\me\proj`) so it stays
  absolute and uses the native separator, matching what `ocman` stores via `str(Path(...))`.
  This exists because `ocman` correctly refuses non-absolute worktrees, and
  `Path("/home/me/proj").is_absolute()` is False on Windows.
- `norm_real(path)`: `os.path.normcase(os.path.realpath(path))`, so comparisons survive the
  macOS `/var` -> `/private/var` symlink and Windows case-insensitivity.
- `make_symlink(...)` and `SYMLINKS_SUPPORTED` (see the dedicated 2026-07-20 entry below).

Test-only rebase assertions were rewritten to use `os.path.commonpath` under the new root
plus a negative check against the old worktree, and TUI path asserts were normalized.
Shipped across `4adfa26`, `ef04c01`, `febda16`.

### Rejected alternatives

- Hard-code Windows drive letters or POSIX separators inline in each test: rejected as
  unmaintainable and error-prone; the helpers centralize the OS knowledge.
- Assert exact string equality on realpaths: rejected, it breaks on the macOS symlink
  prefix; `norm_real` compares canonical paths instead.

## 2026-07-19: CI fail-fast disabled (temporarily) to reveal the true per-cell result

### Context

With the matrix's default `fail-fast: true`, the first failing cell caused GitHub to CANCEL
the rest, and a cancelled cell renders red, indistinguishable from a genuine failure. During
the cross-platform debugging this masked which cells truly failed and made each push an
expensive single-signal probe.

### Decision

Set `fail-fast: false` in `.github/workflows/ci.yml` TEMPORARILY, with an inline comment
stating it must be restored to the default once the matrix is green. This surfaced the real
picture (Linux green, macOS/Windows failing per-cell) in one run.

### Status / follow-up

This is a diagnostic setting, NOT the intended steady state. Restore `fail-fast: true` (drop
the override) once all 15 cells are green, then confirm CI stays green. Tracked as an
outstanding cleanup for the v1.2.0 release close-out.

### Rejected alternatives

- Leave fail-fast on and bisect by re-pushing: rejected as far slower and ambiguous (each
  run yields at most one real failing cell, the rest cancelled).
- Make `fail-fast: false` permanent: not decided here; it is set only until the matrix is
  green, then reverted, to keep the steady-state signal cheap.

## 2026-07-20: Symlink guard tests run on unprivileged Windows (real link, or simulate)

### Context

Three tests exercise real `ocman` security guards:

- `cli.py` refuses to write through a symlink at the filter output path
  (`_safe_destination` and the explicit `--output-compact` path).
- `scripts/migrate_recovery_names.py` skips symlinks when planning renames and re-checks
  `is_symlink()` immediately before `os.rename` to close a TOCTOU window.

The tests originally built their fixtures with `os.symlink()` / `Path.symlink_to()`. On
Windows, creating a symlink requires `SeCreateSymbolicLinkPrivilege` (Administrator, or
Developer Mode). An unprivileged account raises `OSError [WinError 1314]`, so the tests
errored during setup, before touching the code under test. This failed on plain developer
shells and would fail on any hardened or unprivileged Windows CI runner. GitHub's current
`windows-latest` runner happens to be privileged, so the same tests pass there. The guard
itself never needs elevation: only creating the fixture does.

### Decision

Add `tests/conftest.py::make_symlink(link, target, monkeypatch)`, which picks its regime
from actual OS capability (probed once via `SYMLINKS_SUPPORTED`), never from a
`sys.platform` guess:

- Where the OS allows it (Linux, macOS, privileged Windows including GitHub
  `windows-latest`): create a real on-disk symlink. Full fidelity, it proves the guard
  fires against a genuine link and that `Path.is_symlink()` is the detector actually
  being called.
- Where creation is forbidden (an unprivileged Windows user, the normal way `ocman` runs,
  and the only regime where the fallback triggers): create a regular file at `link` and
  monkeypatch `Path.is_symlink` to report `True` for that one path, delegating to the real
  implementation for every other path.

The three tests use `make_symlink` and carry a comment pointing here and to the
`make_symlink` docstring. No product code changed. Shipped in commit `32d8559`.

### Why the fallback is not a coverage dodge

On Windows the fallback faithfully models the exact production scenario the guard exists
for: a non-admin `ocman` process meeting a pre-existing symlink it did not and could not
create. It keeps the guard under test on Windows instead of skipping it. The simulation was
mutation-checked: temporarily disabling the guard in `cli.py` makes the test fail, so it
exercises the branch rather than passing vacuously.

### Rejected alternatives

- Skip on Windows (`pytest.mark.skipif`): rejected. It silently drops coverage of a
  security guard on an OS where the guard still applies. A green check would hide untested
  behavior, and coverage would vanish entirely if CI moved to a hardened or unprivileged
  Windows runner.
- Monkeypatch `is_symlink` on every OS: rejected. It would weaken all platforms by never
  verifying `ocman` calls the right detector against a genuine on-disk link, so a
  regression (for example swapping `is_symlink()` for `exists()`) could pass everywhere.
  The real link is kept wherever the OS allows it, and simulation is used only where it
  does not.

## 2026-07-20: `ocman` should warn when run elevated (admin / root), tracked as its own IPD

### Context

`ocman` administers a single-user, local OpenCode environment and needs no elevated
privileges. Running it as Administrator (Windows) or root (POSIX) is almost always a
mistake, and it can leave backups, exports, and config files owned by the elevated user,
which are then unreadable or undeletable from the user's normal session. This surfaced
while discussing why the symlink tests could not create fixtures on Windows: a non-admin
`ocman` is the expected, normal case.

### Decision

`ocman` will warn at startup when it detects it is running elevated (advisory only, never
blocking). This is a product behavior change, so it goes through the plan/IPD lifecycle:
author an IPD in `.agents/plans/pending/` (per `AGENTS.md`), reviewed and executed as its
own unit of work. It must NOT be bundled into the CI-green / symlink-test change. As of this
entry the IPD is not yet written; the feature is desired and pending, not implemented.

### Why separate

A drive-by product edit made while chasing a green CI matrix violates the repository's
agent-execution contract (feature/behavior work goes through an IPD, commits stay
path-scoped to the task at hand). An in-flight version of this warning was drafted directly
in `cli.py` during the CI work and then reverted precisely to honor that separation. Keeping
it as a distinct IPD preserves reviewability and keeps the test-only commit clean.

## 2026-07-20: Adopt a top-level DECISIONS.md (supersedes earlier "declined" calls)

### Context

Until now the project deliberately kept decision rationale in the executed-IPD trail under
`.agents/plans/executed/` plus `CHANGELOG.md`, and several release-review runs explicitly
DECLINED to create a dedicated `DECISIONS.md` (e.g. the 2026-07-05 and 2026-07-19 runs),
reasoning that a separate file would duplicate the IPD trail. `tests/conftest.py` even
carried a note phrased as "instead of a DECISIONS.md file". The trade-off of that convention
is real: cross-cutting decisions (support-all-OSes, fail-fast, a dependency floor) do not map
cleanly onto a single IPD, and a reader has to reconstruct them from many plans.

### Decision

Create and maintain this top-level `DECISIONS.md` as an append-only, dated, ADR-style log.
This is a deliberate, maintainer-directed reversal of the earlier "declined" calls. The file
COMPLEMENTS rather than replaces the IPD trail and CHANGELOG: where an IPD covers a decision
in depth, an entry here summarizes the decision, alternatives, and why, and links to the IPD
rather than duplicating it. The entries above backfill the significant decisions of the
v1.1 -> v1.2 cycle.

### Reconciliation of the old "no DECISIONS.md" statements

- `tests/conftest.py` was updated to point at `DECISIONS.md` (done in the Windows session).
- `.agents/workflows/getting-started/getting-started.md` already references `DECISIONS.md`
  positively; no change needed.
- The `release-review` workflow files list `DECISIONS.md` only as a GENERIC example of a
  decisions log (alongside ADR dirs, `METHODS/`), not as a claim that ocman lacks one; left
  as-is.
- The `workflow-artifacts/**/decisions.md` and cold-start notes that say "no dedicated
  DECISIONS.md, and none is needed" are dated, append-only RECORDS of past runs. They are not
  rewritten; this entry is the current, superseding decision. Future release-review runs
  should treat `DECISIONS.md` as the project's decisions log.

### Rejected alternatives

- Keep decisions only in IPDs + CHANGELOG (the prior convention): rejected by the maintainer;
  cross-cutting decisions were hard to find and easy to lose.
- Record these decisions as new IPDs instead of a decisions log: rejected as a poor fit; an
  IPD is a plan for a unit of work, whereas several of these (OS support policy, fail-fast,
  dependency floor) are standing decisions, not planned work items.
