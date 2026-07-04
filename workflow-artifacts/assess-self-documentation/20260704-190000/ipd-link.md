# IPD link

- IPD: `.agents/plans/pending/2026-07-04-assess-self-documentation-clean-backups-preview.md`
- Summary: Self-documentation/UI-UX IPD for `ocman --clean-backups`: list ALL backups with color-independent
  DELETE/KEEP tags, summarize KEEP rows at scale, show the concrete cutoff timestamp (relabel Created→Modified),
  and print a forceful warning when the purge would remove ALL backups. Output-only; preserves the typed-yes
  confirm + dry-run and the set of deleted items.
- Cross-cutting note (see decisions.md): the same "show full outcome + warn on total/irreversible loss"
  pattern applies to `--clean`, session/project delete (CLI + TUI modals), `--restore`, `--clear-history`,
  and `--clean-orphans`. Recommend a shared "confirm destructive action" helper via a future assess-architecture
  pass rather than per-command reimplementation.
- Verdict: needs work.
