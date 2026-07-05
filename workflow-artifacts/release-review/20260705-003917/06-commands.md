# 06 Commands

| # | Command | Purpose | Result |
|---|---|---|---|
| 1 | `git rev-parse / remote -v / status --short / log` | Run setup: baseline state | clean tree, main @ 9a7c1b5, origin set |
| 2 | `git log --oneline v1.0.4..HEAD \| wc -l` | Size of delta | 34 commits |
| 3 | `python3 --version` | Env | 3.14.4 |

(Appended as the run proceeds.)
| 4 | `scan_secrets.py --repo . --format json` | secrets/PII scan (tree+history) | 4432 candidates, all FP; saved secrets-scan.json |
| 5 | `py_compile ocman.py ocman_tui/*.py` | syntax check | OK |
| 6 | `ocman --version` / `--help` | smoke | ocman 1.0.4; help OK |
| 7 | `PYTHONPATH=. pytest -q` | full suite | 126 passed, 2 skipped |
