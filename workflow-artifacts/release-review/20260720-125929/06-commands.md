# 06 Commands

| Command | Purpose | Result |
|---|---|---|
| git log/status/ls/grep discovery | Section 1 inventory | clean; HEAD bebb520; no pending plans; TODO.md clean; fail-fast:false in ci.yml |
| grep TODO/FIXME in ocman/ocman_tui/scripts | in-code marker scan | 2 matches, both false positives |
| gitleaks detect --source . | authoritative secret scan (tree+history, 372 commits) | no leaks found |
| scan_secrets.py --repo . | built-in safety-net scan | 893 candidates; 22 high all = synthetic test fixtures (FP) |
| git diff 2554395..HEAD -- ocman/ pyproject.toml | isolate product-code delta | exactly the rebase fix + vistab>=1.3.0 |
