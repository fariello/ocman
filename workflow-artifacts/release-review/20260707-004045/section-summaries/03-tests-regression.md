# Section 3: Tests / Regression

## What I did
- Ran the full suite (172 passed, 2 skipped) and the delta subset (66 tests across
  test_file_tools, test_recovery_naming, test_migrate_recovery_names, test_config_parsing,
  test_compacted_project_prompt).
- Mapped the 1.1.0 functions to tests: `scan_for_secrets`/`check_egress_guards` (size cap, secret
  block/allow, redaction), `resolve_recovery_collision` (running-instance refuse, backup default),
  `canonical_recovery_name`/`parse_recovery_name` (kind validation, case-insensitive, invalid-date,
  round-trip), migration (in-plan collision, symlink), config back-compat, cli_filter
  (empty/whitespace/binary/-oc/collision). All covered.
- Read `test_tui_compaction_end_to_end_network_mocked`: it drives the changed TUI compaction path
  and asserts a `.compacted.md` is written + success notified (so the parity change did not break
  end-to-end), but does NOT assert the new canonical name, default_out_dir honoring, or the
  compacted-copy call.

## Findings
- **S3-T1 (Medium sev / RR Low):** TUI parity specifics (canonical name / default_out_dir /
  compacted-copy) are not pinned by a test, though the compatibility IPD required them. Test-only
  fix in S7 (action S3-A1). Not a correctness risk (verified by reading + the e2e write test).

## Why
- Recently-changed behavior needs regression protection; the TUI parity was the one 1.1.0 change
  whose specific new behaviors lacked an assertion.

## What I considered but did NOT do
- Adding coverage tooling / a coverage gate: out of scope; the project deliberately avoids a
  coverage gate (prior assess-testing IPD, TEST-10). Not proposed.
- Rewriting the e2e TUI test: no; extend it with the missing assertions (minimal, targeted).
