# Implementation Plan (run 20260707-004045)

All five findings are Remediation Risk **Low** -> fix by default (none deferred). No High/BLOCKER/
LIVE/MEM findings. Ordered for a single coherent batch, then re-validate.

| Step | Finding | Change | File | RR | Validation |
|------|---------|--------|------|----|-----------|
| 1 | S6-C1 | Ship the migration script in the wheel: add `scripts/migrate_recovery_names.py` to `[tool.hatch.build.targets.wheel.force-include]` so `pip install` users have the documented upgrade tool. | pyproject.toml | Low | `python -m build --wheel`; confirm the script is in the wheel; `twine check` PASSED |
| 2 | S2-E1 | In `cli_filter`, add an `input_path.stat().st_size` pre-check against `filter_max_bytes` (respecting `force`) BEFORE `read_text`, so an oversized file is rejected without being fully read. Keep the post-read `check_egress_guards` too (covers the assembled prompt). | ocman.py (cli_filter) | Low | new test: oversized file rejected before read (monkeypatch read_text to assert not called), `--force` bypasses |
| 3 | S5-U1 | Extend the `--force` help text to note it also overrides the `filter`/`--compact` input size cap (`filter_max_bytes`), in addition to the process-lock. | ocman.py (parse_args --force) | Low | `ocman --help` shows the updated text |
| 4 | S4-D1 | Add a short README note (near the recovery-file naming tip) that files written by older ocman can be normalized with `python scripts/migrate_recovery_names.py <dir>` (`--dry-run` first). | README.md | Low | manual read; grep finds the note |
| 5 | S3-T1 | Extend `tests/test_tui.py` compaction test (or add one) to pin: the written name parses via `parse_recovery_name` as `(<full sid>, dt, 'compacted')`; a non-default `default_out_dir` is honored; `maybe_copy_compacted_to_project` is invoked. | tests/test_tui.py | Low | `PYTHONPATH=. pytest` green |

Validation after the batch: `PYTHONPATH=. pytest` (expect >= 172 passed + new tests), rebuild
wheel + `twine check`, `ocman --help` spot check. Then Section 8 Go/No-Go.
