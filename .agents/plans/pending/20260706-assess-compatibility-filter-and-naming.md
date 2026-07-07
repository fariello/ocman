# IPD: Assess compatibility - recovery naming, `filter`, TUI, and cross-platform

- Date: 2026-07-06
- Concern: compatibility (resolved from "compatability")
- Scope: the 1.1.0 surface and what it interoperates with - `canonical_recovery_name`/
  `parse_recovery_name`, `cli_filter`, `scripts/migrate_recovery_names.py`, the CLI recovery
  writer, the **TUI** recovery writer (`ocman_tui/app.py`), and the supported platform matrix.
- Status: PENDING (awaiting human approval; not executed)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Ensure the new canonical recovery-filename scheme preserves compatibility for existing users and
across the supported platform matrix: old on-disk files remain readable/migratable, the **CLI and
TUI produce consistent artifact names**, config changes keep old `ocman.toml` files working, and
the naming/parsing behaves correctly on macOS (case-insensitive FS) and Windows - all of which the
CI matrix claims to support.

## Project conventions discovered (Step 0)

- Guiding principles: `ARCHITECTURE.md` (intuitive/self-documenting, configurable-over-hardcoded,
  KISS, honest documentation) + universal fallback.
- Pending-plans: `.agents/plans/pending/` -> `.agents/plans/executed/` (IPD house format).
- Supported set (CI matrix, `.github/workflows/ci.yml:14-15`): **ubuntu/macos/windows x Python
  3.10-3.14**; `requires-python = ">=3.10"`. macOS (case-insensitive FS) and Windows are
  first-class targets.
- Domain invariants: old recovery files must stay readable/migratable; the artifact-naming
  "contract" (what readers expect) must not silently break.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Repro/evidence cited.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| COMP-1 | Medium | Low-Medium | power user / stakeholder | CLI/TUI consistency | The CLI now writes canonical `YYYYMMDD-HHMM-<full_sid>.<kind>.md`, but the **TUI still writes a different scheme**: `opencode-recovery-<sid[:8]>-<YYYYMMDD-HHMMSS>.<kind>.md` and uses `.compact-prompt.md`. Same artifacts, two naming styles / precisions / sid-lengths depending on entry point. The 1.1.0 canonicalization **widened** a pre-existing divergence, and the migration script does not normalize TUI outputs (truncated sid, `.compact-prompt.md` kind). | CLI: ocman.py:3688-3692, 4814; TUI: ocman_tui/app.py:1267,1273,1279,1338 |
| COMP-2 | Medium | Low | software eng / power user | naming contract | The compact-prompt file is written as `*.prompt.md` (ocman.py:3692) but the CLI compaction picker looks for `*.compact-prompt.md` (ocman.py:8907); the lookup never matches and only works by the `generated_paths[-1]` fallback (fragile, luck-dependent). `RECOVERY_KINDS` uses `prompt`, so the migration recognizes CLI `.prompt.md` but NOT the TUI's `.compact-prompt.md`. TUI button labels + a docstring also still say `.compact-prompt.md` (ocman_tui/app.py:841,1279; ocman.py:4752). Pre-existing, but it is a live naming-contract inconsistency in the exact area this work touches. | ocman.py:3692 vs 8906-8909, 4752; ocman_tui/app.py:841,1279 |
| COMP-3 | Medium | Low | operator | platform (macOS FS) | `parse_recovery_name` matches suffixes **case-sensitively**, so on macOS's case-insensitive FS an odd-cased legacy file (`*.RESTART.MD`) is silently NOT recognized/migrated. macOS is a supported CI target. (Same root as edge-cases EC-5; recorded here as the compatibility angle.) | ocman.py:3431-3440; cross-ref `20260706-assess-edge-cases-filter-and-naming.md` EC-5/Step 5 |
| COMP-4 | Low | Low | operator | platform (Windows) | (Positive/confirm) canonical names contain no Windows-illegal characters: `safe_filename` restricts to `[A-Za-z0-9._-]` (ocman.py:2530) and the timestamp is `YYYYMMDD-HHMM` (no `:`). No reserved-name (CON/PRN/NUL) guard, but session ids are `ses_...` so collisions with reserved device names are implausible. Confirm with a Windows-name test; otherwise OK. | ocman.py:2517-2536 |
| COMP-5 | Low | Low | operator / stakeholder | config compat | The security + edge-cases IPDs introduce new config keys (`filter_max_bytes`, `filter_secret_scan`). They MUST load with back-compat defaults so an existing `ocman.toml` (written by 1.0.x/1.1.0) keeps working unchanged and an absent key is not an error. | load_ocman_config; cross-ref the two sibling IPDs |
| COMP-6 | Low | Low | software eng | backward read-compat | (Positive) `parse_recovery_name` reads BOTH legacy on-disk forms (`opencode-YYYYMMDD-HHMMSS-<sid>` and date-only `YYYYMMDD-<sid>`) plus the canonical one, so files written by older ocman remain readable and migratable. Pin this with an explicit backward-compat test so it cannot regress. | ocman.py:3445-3475 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | COMP-1, COMP-2 | **Unify TUI naming with the CLI canonical scheme.** Make the TUI write via `canonical_recovery_name(session_id, dt, kind)` using the **full** session id and the same local timestamp, for transcript/restart/prompt/compacted - so both entry points produce identical, migratable names. Change the TUI's `.compact-prompt.md` output to `.prompt.md` and update the button label (`ocman_tui/app.py:841,1279`) to match. This also removes the sid `[:8]` truncation divergence. | ocman_tui/app.py:1267,1273,1279,1338,841 | Low-Medium | TUI writes `YYYYMMDD-HHMM-<full_sid>.<kind>.md`; a TUI-written file is recognized by `parse_recovery_name` and normalized by the migration; a test asserts CLI and TUI produce the same name for the same (session, kind, minute) |
| 2 | COMP-2 | Fix the stale lookup: change `endswith(".compact-prompt.md")` to `.prompt.md` at ocman.py:8907 so the compact-prompt file is selected by name rather than by the fragile `[-1]` fallback; fix the docstring at ocman.py:4752 (`.compact-prompt.md` -> `.prompt.md`). | ocman.py:8906-8909, 4752 | Low | Test: with reordered `generated_paths`, the compaction still selects the `.prompt.md` file by name |
| 3 | COMP-3 | Adopt the edge-cases IPD's case-insensitive `parse_recovery_name` fix (do NOT duplicate it - execute once, shared). Confirms macOS legacy files migrate. | ocman.py:3431-3440 (see edge-cases Step 5) | Low | macOS-style `*.RESTART.MD` recognized (case-insensitive test) |
| 4 | COMP-5 | Ensure new config keys default safely: `load_ocman_config` returns the documented default when a key is absent; loading a minimal/old `ocman.toml` never errors on the new keys. | load_ocman_config; config defaults | Low | Test: config without `filter_max_bytes`/`filter_secret_scan` loads and yields defaults |
| 5 | COMP-4, COMP-6 | Add compatibility regression tests: (a) canonical names are valid Windows filenames (no reserved chars); (b) `parse_recovery_name` round-trips/reads both legacy forms + canonical (backward read-compat pinned). No code change beyond tests. | tests | Low | Tests green on the matrix |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (Windows reserved-name guard, CON/PRN/NUL) | Medium-High | complexity | Adding a reserved-device-name sanitizer to `safe_filename` is disproportionate: session ids are `ses_<base62>` and can never equal a reserved name, and scope slugs are user-chosen free text where a `CON` collision is implausible and non-destructive. The complexity of a correct Windows-reserved-name filter (per-component, extension-aware) is not justified by the risk. | Revisit only if a real Windows collision is reported. |

## Scope check

- Over-scope: do NOT re-architect the TUI's recovery flow or introduce a shared "artifact writer"
  abstraction - the KISS fix is to route the TUI's existing writes through `canonical_recovery_name`
  (Complexity axis). Do not add a Windows reserved-name filter (deferred above).
- Under-scope (added above): TUI/CLI naming unification (COMP-1/2), the stale-lookup fix (COMP-2),
  and config back-compat defaults (COMP-5).

## Required tests / validation

- `tests/test_tui.py` (extend): TUI recovery writes use `canonical_recovery_name` (full sid,
  `.prompt.md` not `.compact-prompt.md`); a TUI-written name parses + migrates.
- `tests/test_recovery_naming.py`: Windows-valid-filename assertion; backward-read of both legacy
  forms (COMP-6); case-insensitive parse shared with edge-cases (COMP-3).
- `tests/test_core.py` or `test_ocman.py`: compaction selects the `.prompt.md` file by name (COMP-2).
- `tests/test_config_parsing.py`: old/minimal `ocman.toml` loads with new-key defaults (COMP-5).
- Full suite green on the CI matrix (ubuntu/macos/windows x 3.10-3.14): `PYTHONPATH=. pytest`
  (currently 150 passed, 2 skipped).

## Spec / documentation sync

- README/`--help`/ARCHITECTURE: state the single canonical scheme applies to BOTH CLI and TUI;
  fix any remaining `.compact-prompt.md` references (docstring ocman.py:4752, TUI label).
- CHANGELOG: note the TUI now writes canonical `YYYYMMDD-HHMM-<sid>.<kind>.md` names (a
  user-visible change to TUI output filenames) and that `.compact-prompt.md` is now `.prompt.md`.

## Open questions

1. **TUI compacted-copy parity:** the CLI copies the compacted file into a project's
   `.agents/prompts/pending/`; the TUI compaction (`ocman_tui/app.py:1338`) does not. Should Step 1
   also wire the TUI to the same project-copy behavior, or is that a separate follow-up? (Proposed:
   out of scope here - naming unification only; note it for a functionality follow-up.)
2. **Coordination:** COMP-3 shares the case-insensitive fix with the edge-cases IPD, and COMP-5
   depends on the config keys introduced by the security + edge-cases IPDs. Execute all three
   together (they touch overlapping code) or sequence security -> edge-cases -> compatibility?
   (Proposed: one combined execution pass.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute together with the sibling security + edge-cases IPDs (shared `cli_filter`,
   `parse_recovery_name`, and config code), run the validation, and sync docs.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
