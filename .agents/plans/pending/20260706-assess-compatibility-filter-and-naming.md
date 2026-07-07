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
| 1 | COMP-1, COMP-2 | **Unify TUI naming with the CLI canonical scheme.** Make the TUI write via `canonical_recovery_name(session_id, dt, kind)` using the **full** `self.selected_session_id` for transcript/restart/prompt/compacted - so both entry points produce identical, migratable names. **PRC-2 (precision):** pass a `datetime` **object** (e.g. `datetime.now()`) to `canonical_recovery_name`, NOT the pre-formatted string at `app.py:1247` (that string may remain for any non-canonical use). Change the TUI's `.compact-prompt.md` output to `.prompt.md` and update the button label (`ocman_tui/app.py:841,1279`) to match. This also removes the sid `[:8]` truncation divergence. | ocman_tui/app.py:1247,1267,1273,1279,1338,841 | Low-Medium | Assert the TUI code path calls `canonical_recovery_name` with the full sid (test the helper usage, not the Textual UI; PRC-4); a name it produces is recognized by `parse_recovery_name` and normalized by the migration; the resulting name equals the CLI's for the same (session, kind, minute) |
| 2 | COMP-2 | **PRC-5 (anti-regression):** FIRST add a characterization test pinning the CURRENT selection (that today's compaction acts on the `.prompt.md` file - it works only via the `generated_paths[-1]` fallback), green before the change. THEN fix the stale lookup: change `endswith(".compact-prompt.md")` to `.prompt.md` at ocman.py:8907 so the file is selected by name, not by position; fix the docstring at ocman.py:4752 (`.compact-prompt.md` -> `.prompt.md`). Behavior must be identical (same file selected), just robust to reordering. | ocman.py:8906-8909, 4752 | Low | Characterization test green before + after; a reordered `generated_paths` still selects the `.prompt.md` file by name |
| 3 | COMP-3 | Adopt the edge-cases IPD's case-insensitive `parse_recovery_name` fix (do NOT duplicate it - execute once, shared). Confirms macOS legacy files migrate. | ocman.py:3431-3440 (see edge-cases Step 5) | Low | macOS-style `*.RESTART.MD` recognized (case-insensitive test) |
| 4 | COMP-5 | **VERIFY (not a separate fix; PRC-1).** `load_ocman_config` already starts from `dict(DEFAULT_CONFIG)` and ignores keys absent from `DEFAULT_CONFIG` (`if key not in config: continue`), so config back-compat is **automatic once the new keys are added to `DEFAULT_CONFIG` + the template** - which the **security** IPD (`filter_max_bytes`, `filter_secret_scan`) and **edge-cases** IPD own. This step is therefore a cross-reference/verification: confirm those keys land in `DEFAULT_CONFIG`/`DEFAULT_CONFIG_TEMPLATE`, not a duplicate config change here. | load_ocman_config (already handles it); DEFAULT_CONFIG (owned by sibling IPDs) | Low | Test: a minimal/old `ocman.toml` (without the new keys) loads and yields the defaults; no error on absent keys |
| 5 | COMP-4, COMP-6 | Add compatibility regression tests: (a) canonical names are valid Windows filenames (no reserved chars); (b) `parse_recovery_name` round-trips/reads both legacy forms + canonical (backward read-compat pinned). No code change beyond tests. | tests | Low | Tests green on the matrix |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (Windows reserved-name guard, CON/PRN/NUL) | Medium-High | complexity | Adding a reserved-device-name sanitizer to `safe_filename` is disproportionate: session ids are `ses_<base62>` and can never equal a reserved name, and scope slugs are user-chosen free text where a `CON` collision is implausible and non-destructive. The complexity of a correct Windows-reserved-name filter (per-component, extension-aware) is not justified by the risk. | Revisit only if a real Windows collision is reported. |

## Scope check

- Over-scope: do NOT re-architect the TUI's recovery flow or introduce a shared "artifact writer"
  abstraction - the KISS fix is to route the TUI's existing writes through `canonical_recovery_name`
  (Complexity axis). Do not add a Windows reserved-name filter (deferred above).
- Under-scope (added above): TUI/CLI naming unification (COMP-1/2), the stale-lookup fix (COMP-2).
  COMP-5 is a verification cross-reference, not a separate config change (PRC-1).
- **Noted, not silently dropped (PRC-3):** the TUI also **hardcodes** its output dir
  (`out_dir = Path("opencode-recovery")`, `ocman_tui/app.py:1253`) instead of honoring the CLI's
  configured `default_out_dir` - a real CLI/TUI consistency gap adjacent to COMP-1. It is out of
  this naming-focused scope; recorded as Open Question 3 so it is not lost.

### Plan-review revisions (2026-07-06, applied in place)

- **PRC-1 (Medium, over-scope):** COMP-5/Step 4 reframed from a "fix" to a **verification** -
  `load_ocman_config` already merges from `DEFAULT_CONFIG` and ignores absent keys, so back-compat
  is automatic once the sibling IPDs add the keys to `DEFAULT_CONFIG`; no duplicate work here.
- **PRC-2 (Low, precision):** Step 1 now specifies passing a `datetime` object (not the TUI's
  pre-formatted string) to `canonical_recovery_name`.
- **PRC-3 (Medium, under-scope):** recorded the TUI hardcoded-`out_dir` consistency gap as Open
  Question 3 rather than expanding scope silently.
- **PRC-4 (Low, testing):** Step 1 validation now tests the **helper usage** in the TUI code path,
  not the Textual UI (tractable).
- **PRC-5 (Low, anti-regression):** Step 2 now requires a **characterization test first** (pin the
  current `.prompt.md` selection) so the lookup fix is provably behavior-preserving.

## Required tests / validation

- `tests/test_tui.py` (extend): the TUI recovery code path uses `canonical_recovery_name` with the
  full sid and `.prompt.md` (not `.compact-prompt.md`) - test the helper usage, not the Textual UI
  (PRC-4); a TUI-produced name parses + migrates and equals the CLI name for the same minute.
- `tests/test_recovery_naming.py`: Windows-valid-filename assertion; backward-read of both legacy
  forms (COMP-6); case-insensitive parse shared with edge-cases (COMP-3).
- `tests/test_core.py` or `test_ocman.py`: **characterization test first** (current `.prompt.md`
  selection, PRC-5), then the by-name selection after the fix (COMP-2).
- `tests/test_config_parsing.py`: old/minimal `ocman.toml` loads with new-key defaults (COMP-5;
  the keys themselves come from the sibling IPDs).
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
3. **TUI hardcoded output dir (PRC-3):** the TUI writes to `Path("opencode-recovery")` (relative
   to CWD) while the CLI honors the configured `default_out_dir`. Fold this into the TUI
   unification (Step 1) or leave as a separate follow-up? (Proposed: separate follow-up - this
   IPD is naming-only - but flagged so it is not forgotten.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is
NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run `plan-review` to harden it).
2. On approval, execute together with the sibling security + edge-cases IPDs (shared `cli_filter`,
   `parse_recovery_name`, and config code), run the validation, and sync docs.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/executed/`.
