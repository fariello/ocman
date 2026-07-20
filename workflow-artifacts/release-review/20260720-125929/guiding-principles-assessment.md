# Guiding Principles Assessment

No `GUIDING_PRINCIPLES.md` exists; the universal fallback principles from `00-run-protocol.md`
apply: (1) intuitive/self-documenting, (2) general-case/configurable over hardcoded, (3) KISS,
(4) honest documentation. Per-principle adherence assessed in Section 5.

## Per-principle assessment (universal fallback; delta re-review)

| Principle | Adherence | Evidence (delta focus) |
|---|---|---|
| Intuitive / self-documenting | PASS | Delta changed no user-facing text; the prior GO's curated help/errors/first-run guidance stand. The macOS fix is invisible to users (import now simply works correctly on macOS). |
| General-case / configurable over hardcoded | PASS | The fix generalizes rebasing to resolve the stored dir (handles ANY OS canonicalization), rather than special-casing macOS. `_rebased_dir` is the shared general helper reused here. |
| KISS | PASS | The fix is minimal (route through an existing helper + keep the lexical fallback); no new abstraction or dependency added beyond the vistab floor bump. |
| Honest documentation | PASS | CHANGELOG + DECISIONS.md describe exactly what changed and why (S4). |

No GP violations found in the delta.
