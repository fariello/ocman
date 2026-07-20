# Decisions

This document records significant engineering decisions for `ocman`: the choice made,
why, and the alternatives that were rejected. It complements the executed-IPD trail under
`.agents/plans/executed/` and `CHANGELOG.md`; where an IPD covers a decision in depth, this
file links to it rather than duplicating the rationale. Entries are append-only and dated.

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
