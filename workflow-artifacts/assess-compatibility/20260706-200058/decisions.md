# Decisions and assumptions - assess-compatibility run 20260706-200058

## Concern and scope
- Concern: compatibility. The user typed "compatability" (misspelling); resolved to the
  `compatibility` lens (`.agents/workflows/assess/lenses/compatibility.md`).
- Scope narrowed (pre-release sequence) to the 1.1.0 surface and its interop: naming helpers,
  `cli_filter`, migration script, the CLI recovery writer, the TUI recovery writer
  (`ocman_tui/app.py`), and the supported platform matrix.

## Project conventions discovered
- Principles: `ARCHITECTURE.md` + universal fallback.
- Supported set (compatibility oracle): CI matrix ubuntu/macos/windows x Python 3.10-3.14
  (`.github/workflows/ci.yml:14-15`), `requires-python >=3.10`. macOS (case-insensitive FS) and
  Windows are first-class targets.
- IPD lifecycle `.agents/plans/pending/` -> `executed/`; run records under
  `workflow-artifacts/assess-<concern>/<RUN_ID>/`. Scope exclusions honored (did not assess
  `.agents/workflows/` or `workflow-artifacts/`).

## Key decisions / assumptions
- **Verdict "needs work":** two Medium consistency defects that the 1.1.0 rename widened
  (CLI/TUI naming divergence COMP-1; stale naming-contract lookup COMP-2) plus a macOS FS gap
  (COMP-3). None loses data - backward read-compat (COMP-6) and Windows filename safety (COMP-4)
  are actually fine - but "same tool, consistent artifact names across CLI and TUI" is a real
  compatibility contract that is currently broken.
- **COMP-1/COMP-2 are pre-existing** (the TUI never used `base_name`; the `.compact-prompt.md`
  lookup mismatch predates 1.1.0 - verified against `HEAD~6`). They are IN SCOPE because the
  canonicalization work is the natural place to reconcile them and it widened the gap.
- **COMP-2 works today only by luck:** `generated_paths[-1]` happens to be the compact-prompt path
  (return order `[transcript, restart, prompt]`), so the failed `endswith(".compact-prompt.md")`
  match falls back correctly. Fragile; fix the lookup string.
- **COMP-3 is the compatibility face of edge-cases EC-5** - one shared fix, executed once, not
  duplicated across IPDs.
- **Findings verified against source and git history,** not inferred: read the CLI writer
  (3688-3692), the TUI writers (1267/1273/1279/1338), the lookup site (8906-8909), `safe_filename`
  (2517-2536), and confirmed the `.compact-prompt.md` mismatch is pre-1.1.0 via `git show HEAD~6`.

## What was intentionally NOT proposed and why (Remediation-Risk axis)
- **Windows reserved-device-name (CON/PRN/NUL/AUX...) sanitizer** in `safe_filename`: DEFERRED on
  the **complexity** axis (Medium-High). A correct per-component, extension-aware reserved-name
  filter is disproportionate; `ses_<base62>` session ids can never equal a reserved name, and a
  scope-slug collision is implausible and non-destructive.
- **A shared "artifact writer" abstraction** unifying CLI+TUI: NOT proposed (complexity). The KISS
  fix is to route the TUI's existing writes through `canonical_recovery_name`, not to build a
  framework.

## Open questions for the user (also in the IPD)
1. TUI compacted-copy parity (the TUI does not copy the compacted file into the project's
   `.agents/prompts/pending/` like the CLI does): fold into this naming unification, or a separate
   functionality follow-up? Proposed: separate follow-up (naming-only here).
2. Execution coordination: COMP-3 shares a fix with the edge-cases IPD and COMP-5 depends on the
   config keys from the security + edge-cases IPDs - execute all three together (proposed) or
   sequence security -> edge-cases -> compatibility?
