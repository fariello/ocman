# 10 Validation Results

## Section 3 validation

- Command: `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q`
- Result: **408 passed, 2 skipped** in ~110s (Linux, Python 3.14). VERIFIED (actual runner output).
- 2 skipped = perf benchmarks gated on OCMAN_BENCHMARK=1.
- CI matrix at HEAD bebb520: all 15 cells GREEN (ubuntu/macos/windows x py3.10-3.14),
  verified earlier this session via `gh run watch` (exit 0). Off-Linux: real_process_detection
  detector tests skip (Linux-only path); the firmlink regression test runs everywhere.
