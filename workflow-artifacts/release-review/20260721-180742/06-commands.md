# 06 Commands

| Command | Purpose | Result |
|---|---|---|
| git log/diff v1.2.0..HEAD | scope the 1.3.0 delta | 27 commits; product diff in cli.py/storage.py/packaging/docs/tests |
| grep TODO/FIXME/HACK/XXX in ocman/ ocman_tui/ | find in-code markers | 0 real markers (2 XXX are help-text placeholders) |
| ls .agents/plans/pending .agents/prompts/* | find pending work | none (README/.gitkeep only) |
| pytest -q | establish green baseline | 473 passed, 2 skipped, 131.81s |
| grep version pyproject/cli/CITATION | version consistency | rc4 vs CHANGELOG [1.3.0]; CITATION stale 1.1.0 |
| scan_secrets.py --format json | built-in secret scan | 953 heuristic hits, low false positives (env-var docs) |
| gitleaks detect --redact (full history) | authoritative secret scan | 3 hits, all synthetic fixtures in prior-run artifacts; not live |
| gh run list secret-scan | confirm CI scanner state | green (action range does not hit the 3) |
