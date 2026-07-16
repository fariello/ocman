# IPD link

- IPD: `.agents/plans/pending/20260715-assess-functionality-ipd.md`
- Summary: Functionality assessment of ocman (whole project). Verdict adequate.
  Proposes 8 ordered, mostly-low-risk changes to close user-facing gaps: fix stale
  export help (F3); add missing move-sugar flags (F4); disambiguate --force vs -y (F6);
  add -y/--yes to project delete / db clean / clean-orphans / backup clean (F5); add
  --dry-run to move and import (F7); add --limit to lists (F8); add --json to
  read/report commands (F1); implement the backlogged `ocman spend` command (F2).
  Restore/history-clear dry-run, shell completion, resume/open, and forked-spend
  dedupe are deferred with named Remediation-Risk axes.
