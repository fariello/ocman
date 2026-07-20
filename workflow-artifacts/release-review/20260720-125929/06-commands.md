# 06 Commands

| Command | Purpose | Result |
|---|---|---|
| git log/status/ls/grep discovery | Section 1 inventory | clean; HEAD bebb520; no pending plans; TODO.md clean; fail-fast:false in ci.yml |
| grep TODO/FIXME in ocman/ocman_tui/scripts | in-code marker scan | 2 matches, both false positives |
| gitleaks detect --source . | authoritative secret scan (tree+history, 372 commits) | no leaks found |
| scan_secrets.py --repo . | built-in safety-net scan | 893 candidates; 22 high all = synthetic test fixtures (FP) |
| git diff 2554395..HEAD -- ocman/ pyproject.toml | isolate product-code delta | exactly the rebase fix + vistab>=1.3.0 |
| pytest -q (full suite) | authoritative test evidence | 408 passed, 2 skipped |
| git diff 2554395..HEAD -- tests/ | verify no weakened assertions / hidden skips | portability substitutions only; assertions intact; no new blanket skip |
| sed/grep CHANGELOG + DECISIONS review | verify docs match delta + dash convention | honest; dashes only in sanctioned exceptions; changelog date slightly stale (S4-D2) |
| python -m build | clean sdist+wheel build | Successfully built ocman-1.2.0 sdist+wheel |
| import ocman / vistab introspection | verify vistab 1.3.0 methods + clean import | set_color/set_header_style are Vistab instance methods; import clean on py3.14 |
| PyPI json lookup | published-version check | published 1.1.0 < proposed 1.2.0 (valid bump) |
