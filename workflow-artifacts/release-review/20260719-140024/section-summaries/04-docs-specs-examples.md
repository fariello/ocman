# Section 4 - Documentation, specs, examples

## What I did
- Re-verified the accuracy fixes from this cycle's docs IPD still hold: no `ocman.py` /
  "zero-dependency" / "standard library only" stale claims remain in README/ARCHITECTURE;
  the README config template parses as valid TOML and covers every DEFAULT_CONFIG key.
- Confirmed the release features are documented in README (`--extracts`, `--older-than`,
  `doctor`, `reclaim`, `spend`, `list running`, `--chunk`) and that the 9-tab TUI (Storage/
  Spend/Running added) is described (updated this cycle in commit 22bf892).
- Confirmed the CHANGELOG `[Unreleased]` section covers the cycle's features
  (doctor/reclaim, TUI parity, extract-on-delete, spend/running, chunk, self-doc fixes).
- Cold-start (KD) assessment: README (intent/usage), ARCHITECTURE (structure + principles +
  CLI/TUI relationship), CHANGELOG (behavior history), and the executed IPDs under
  `.agents/plans/executed/` (decision rationale + alternatives) give a no-context engineer
  strong orientation. The project's decisions-log convention IS the IPD trail; respecting
  that existing convention (per the runbook), no dedicated DECISIONS.md is needed.
- Self-documenting bar: a dedicated self-documentation assess+fix pass already ran this
  cycle (executed IPD 20260719-0125-01: errors that teach, traceback guard, reclaim
  discoverability, self-explaining TUI labels), so the in-product learn-as-you-go surface
  is fresh. No new `U` finding.

## Why
- Docs must describe current behavior; the release added a large surface, so the docs'
  accuracy and the cold-start story are the release-critical doc concerns.

## What I considered but did NOT do
- Adding a dedicated DECISIONS.md/ADR dir: declined - the executed-IPD trail is the
  project's established decision-rationale convention; imposing a new file would duplicate
  it (the runbook says respect the existing convention).
- Pruning the SHIPPED notes from TODO.md: cosmetic; the doc is honest. Left for the
  Section 5 triage (kept: it documents what shipped and one deferred idea).
- No `D`/`A`/`U`/`KD` findings filed - docs were synced earlier this cycle and re-verified
  accurate here.
