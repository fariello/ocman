# Implementation Plan (Sections 1-6 -> Section 7)

## Summary of the audit

The 1.3.0 line is in strong shape. The feature code (reconnect, kill, session rename, doctor
insecure-server check, list filters + lr alias) was traced at the code level: the highest-risk
LIVE surface (process signalling) and the security-sensitive auth probe are correctly guarded
(no defect), the rename DB path is atomic/injection-safe, tests give comprehensive regression
coverage (473 passed, 2 skipped), all 4 design principles are adhered to, the change set is
additive/backward-compatible with no serialized-format drift, and PyPI 1.2.0 -> 1.3.0 is a valid
bump. No High/LIVE/MEM/security defect was found.

Everything to fix is **Low severity / Low Remediation Risk** release hygiene: finalize the
version string, sync stale metadata, and close small doc-sync gaps. Under the Fix Bar (fix by
default unless Remediation Risk >= Medium-High), all of these are fixed in Section 7.

## Actions to implement in Section 7 (all Low RR -> fix by default)

| Action | Source findings | Change | Files |
|---|---|---|---|
| **A-01 Version finalize** | DR01, PKG01 | `1.3.0rc4` -> `1.3.0` | pyproject.toml:7, ocman/cli.py:208 |
| **A-02 CITATION sync** | DR02 | software `version: "1.1.0"` -> `"1.3.0"` (leave cff-version 1.2.0) | CITATION.cff:16 |
| **A-03 CHANGELOG date** | D01 | `[1.3.0] - 2026-07-20` -> actual promotion date | CHANGELOG.md:5 |
| **A-04 Fix broken refs** | DR03 | reword AGENTS.md to point at existing homes (drop nonexistent RELEASING.md/CONTRIBUTING.md, or reword to what exists) | AGENTS.md:28 |
| **A-05 ARCHITECTURE verbs** | A01 | add reconnect/kill/rename to the enumerated top-level-verbs list | ARCHITECTURE.md:20-22 |
| **A-06 DECISIONS entry** | KD01, KD02 | append one dated entry: reconnect/kill process-signalling safety model + link the two IPDs | DECISIONS.md |
| **A-07 gitleaks baseline** | S2-S01 | add the 3 prior-run-artifact fingerprints to .gitleaksignore with a comment | .gitleaksignore |

## Not implementing (with reason)

- **Pruning SHIPPED stanzas from TODO.md**: user raised it as a separate CONVENTION question,
  not a release blocker; a review must not silently change it. Left for the user to decide.
- **cli.py monolith refactor**: documented deliberate KISS trade-off; high Remediation Risk
  (complexity/functionality); out of scope for a promotion review.
- **forked/shared-spend de-dup**: deferred stretch goal, out-of-scope-for-release, honestly labeled.

## Validation plan (Section 7 -> final)
1. After edits, re-run the full test suite (`pytest -q`): expect 473 passed, 2 skipped.
2. `python -m build` + `twine check`: expect ocman-1.3.0 sdist+wheel, both PASS.
3. `ocman --version`: expect `ocman 1.3.0`.
4. `grep -nP '[\u2013\u2014]'` on authored prose: expect only the sanctioned NOTICE attribution dash.
5. Local full-history `gitleaks detect`: expect 0 leaks after A-07.

## Ordering
Docs/metadata (A-02..A-07) can commit as one "release-prep docs" unit; the version bump (A-01)
+ CHANGELOG date (A-03) commit as the "release: 1.3.0" unit. Keep them coherent and path-scoped.
