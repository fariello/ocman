# Section 7 - Implementation

## What I did
Applied all 7 planned actions (every finding was Low severity / Low Remediation Risk, so all
were fixed by default under the Fix Bar; nothing deferred):

- **A-01** version `1.3.0rc4` -> `1.3.0` (pyproject.toml, ocman/cli.py). Commit b94eb95.
- **A-02** CITATION.cff software version `1.1.0` -> `1.3.0` + date-released -> 2026-07-21. 4f05e1d.
- **A-03** CHANGELOG `[1.3.0]` date -> 2026-07-21 (actual promotion date). b94eb95.
- **A-04** AGENTS.md: dropped the two broken references (RELEASING.md, CONTRIBUTING.md) and
  pointed instead at the actual authorities (release-review Section 9 file + the .agents/plans
  README). 4f05e1d.
- **A-05** ARCHITECTURE.md: added reconnect/kill/rename to the enumerated top-level-verbs list. 4f05e1d.
- **A-06** DECISIONS.md: appended a dated entry documenting the reconnect/kill process-signalling
  safety model (own-user-only, PID-reuse guard, zombie-aware, SIGTERM-then-optional-SIGKILL,
  no bare relaunch, Linux-only) with rejected alternatives, linking both IPDs. 4f05e1d.
- **A-07** .gitleaksignore: baselined the 3 prior-run-artifact fingerprints (synthetic AWS
  fixtures echoed into run 20260720-125929's artifacts). 4f05e1d.

Committed as two coherent path-scoped units (docs/metadata; then version bump), never `git add -A`.

## Why
- The audit found NO High/LIVE/MEM/security defect in the 1.3.0 code (S2-LIVE01/S02/B01 were
  traced-clear), so Section 7 is pure release hygiene: finalize the version, sync stale metadata,
  and complete cold-start docs. These are exactly the Fix-by-default Low-RR class.
- The DECISIONS entry (A-06) recovers the "why" of the signalling model; it is verifiable
  directly against the code (no user confirmation needed, not marked inferred).

## Validation (real output cited in 10-validation-results.md)
- pytest: 473 passed, 2 skipped in 136.32s (unchanged).
- `ocman --version` -> "ocman 1.3.0".
- `python -m build` -> ocman-1.3.0 sdist+wheel; `twine check` PASSED both.
- gitleaks full history (414 commits): no leaks found.
- No new em/en dash in authored prose.

## What I considered but did NOT do
- Did NOT touch product code: no code-level finding warranted a change; editing behavior-neutral
  would be churn.
- Did NOT prune the SHIPPED stanzas from TODO.md: that is the user's separate convention
  decision, not a release finding; a review must not silently change it. TODO.md is honest as-is
  (shipped items accurately annotated, the one open item honestly labeled deferred), so no
  TODO.md edit was required by this run.
- Did NOT create RELEASING.md/CONTRIBUTING.md to satisfy the broken refs: creating two new
  process docs is more scope than the finding needs; repointing to existing authorities is the
  lower-risk fix.
- Did NOT add or change any CI workflow: A-07 is a .gitleaksignore baseline edit, not a workflow
  change; CI needs nothing (16/16 green).
- No `LIVE`/High finding was escalated-unfixed (none existed).
