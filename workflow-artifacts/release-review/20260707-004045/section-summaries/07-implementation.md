# Section 7: Implementation

## What I did
Applied all five findings (all Remediation Risk Low -> fix by default; none deferred):
- **S6-C1** (Medium sev): added `scripts/migrate_recovery_names.py` to the wheel force-include so
  `pip install` users get the documented migration tool. Verified in the rebuilt wheel.
- **S2-E1** (Low): `cli_filter` now checks `input_path.stat().st_size` against `filter_max_bytes`
  (respecting `--force`) BEFORE `read_text`, so an oversized file is rejected without being read.
  Added a test asserting `read_text` is not called on rejection.
- **S5-U1** (Low): `--force` help text now states it also overrides the filter/--compact size cap.
- **S4-D1** (Low): README NOTE pointing upgraders to `scripts/migrate_recovery_names.py`
  (`--dry-run` first).
- **S3-T1** (Medium sev): `tests/test_tui.py` now pins TUI/CLI naming parity (canonical full-sid
  name via `parse_recovery_name`), honoring `default_out_dir`, and the compacted-copy call.

Re-opened the actual source cited by the findings before editing (per protocol): the `cli_filter`
read path, the `--force` arg, the wheel config, the TUI compaction worker.

## Why
- Fix Bar: every finding was Low remediation risk, so all are fixed in-run. No LIVE/High/MEM
  findings existed. S6-C1 is the most user-visible (packaging delivering what docs promise).

## Validation
- `PYTHONPATH=. pytest`: 174 passed, 2 skipped. Wheel rebuilt (migration script present);
  `twine check` PASSED; `--help` confirms the --force text.

## What I considered but did NOT do
- The advisory gitleaks-in-CI step (CI-1): left as a recommendation, not committed (infra change,
  user holds release timing). Recorded in ci-assessment.md.
- Turning migration into a subcommand: rejected (KISS; the standalone script + shipping it is smaller).
