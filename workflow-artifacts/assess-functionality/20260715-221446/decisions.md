# Decisions and assumptions - assess functionality (20260715-221446)

## Concern and scope

- Concern: functionality completeness (does ocman provide what its users/stakeholders
  need; does implemented functionality work end to end).
- Scope: whole project. No `$ARGUMENTS` narrowing was given beyond the concern name.

## Project conventions discovered

- Plan lifecycle: two-directory (`.agents/plans/pending/` -> `executed/`), `Status:`
  in front matter. Existing repo plans are named `YYYYMMDD-<slug>-ipd.md`. I followed
  the EXISTING repo naming (`20260715-assess-functionality-ipd.md`) rather than the
  harness canonical `YYYYMMDD-HHMM-NN-...`, to stay consistent with the repo. Recorded
  here as the deliberate choice.
- IPD `Status:` set to `to-review` per the assess template (a complete, review-ready
  proposal). This coexists with the repo's simpler PROPOSED/EXECUTED usage; `to-review`
  is the more specific readiness state and is compatible.
- Prose: no em/en dashes in authored Markdown (AGENTS.md). Applied to all outputs.
- Review-scope exclusions honored: did NOT assess `.agents/workflows/` or
  `workflow-artifacts/` as if they were the product.

## Key judgments

- Verdict "adequate" (not "needs work"): the command surface is broad and fully wired
  (no NotImplementedError/TODO/stub markers found in cli.py; every parser action has a
  handler). The gaps are real but are additive/consistency issues, not broken core
  functionality.
- Distinguished required vs expected vs nice-to-have per the lens:
  - Expected/high: machine-readable output (F1), spend reporting (F2, an explicit
    backlog item = demanded).
  - Expected/medium: safety-affordance parity (F4 sugar flags, F5 `-y`, F7 dry-run) and
    the confusing dual-meaning `--force` (F6).
  - Doc correctness: F3 (stale "project export not supported" help).
  - Nice-to-have: list pagination (F8).

## What was intentionally NOT proposed (and why)

- `backup restore` / `history clear` dry-run: deferred, Remediation Risk Medium-High on
  functionality. A faithful restore preview must share the real restore's planning code
  or it risks giving false assurance; out of scope for a quick add.
- Shell completion: deferred, Medium on complexity (dependency/packaging surface); a
  priority call, its own IPD.
- `resume`/`open` a session: deferred, High on functionality; it is a scope/identity
  decision (ocman manages and recovers; opencode runs). Routed to an open question, not
  assumed.
- `ocman spend` forked/shared-spend dedupe: deferred, Medium-High on complexity;
  explicitly optional in the backlog ("do not block the core command on it").

## Assumptions (to confirm with the human)

- The JSON output (F1/Step 7), once added, is treated as a documented, semi-stable
  contract. Assumed yes.
- Keeping `--force` as a working back-compat alias on `history clear` while steering to
  `-y` is acceptable (no breaking change). Assumed yes.
- ocman is NOT expected to launch/resume OpenCode sessions. Assumed, pending
  confirmation (open question).

## Open questions routed to the human

1. `--json` schema stability commitment.
2. `ocman spend` data source and the precise meaning of "historically saved spend"
   (from TODO.md); blocks Step 8.
3. `resume`/`open` in scope for ocman or an explicit non-goal.
4. `--force`/`-y` convergence acceptability (F6).
