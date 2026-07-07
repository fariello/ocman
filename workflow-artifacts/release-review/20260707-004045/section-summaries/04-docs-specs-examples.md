# Section 4: Docs / Specs / Examples

## What I did
- Verified `--help` shows the new surface: `filter` command, `--scope`, `--allow-secrets`, with
  worked examples.
- Cross-checked README config template against `DEFAULT_CONFIG`: **0 undocumented keys** (both new
  keys `filter_max_bytes` and `filter_secret_scan` documented with defaults).
- Confirmed CHANGELOG has an accurate 1.1.0 entry and honestly flags the `--compact` egress
  behavior change (not aspirational).
- Confirmed ARCHITECTURE covers cold-start knowledge for the delta: `filter` command, canonical
  naming scheme, `canonical_recovery_name`/`parse_recovery_name` as source of truth, and the
  migration script.

## Findings
- **S4-D1 (Low / RR Low):** the one-shot migration script `scripts/migrate_recovery_names.py` is
  documented in ARCHITECTURE + CHANGELOG but not in README, so a user upgrading with old-scheme
  files on disk cannot discover it from the README. Fix in S7 (short README note; action S4-A1).

## Why
- Docs must be accurate (honest-documentation principle) and the upgrade path discoverable
  (self-documenting bar). Accuracy is met; discoverability of the migration has one small gap.

## What I considered but did NOT do
- Adding a full "filter" usage section to README: not needed - it is a secondary command well
  covered by `--help` + the arg table + CHANGELOG; a prose section would be over-documentation.
- Cold-start `KD` docs: ARCHITECTURE already carries intent/architecture/decisions incl. the delta;
  no new orientation file needed (respect existing convention).
