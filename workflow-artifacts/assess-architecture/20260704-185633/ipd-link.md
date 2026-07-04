# IPD link

- IPD: `.agents/plans/pending/2026-07-04-assess-architecture-destructive-confirm-helper.md`
- Summary: Architecture IPD to introduce a small shared destructive-confirmation/preview seam in ocman.py —
  a `DestructivePreview`/`PreviewItem` dataclass, a pure color-independent `render_destructive_preview()`
  (KEEP/DELETE + forceful all-affected warning), and a `confirm_destructive()` I/O seam — replacing 4
  duplicated typed-`yes` blocks and giving the KEEP/DELETE clean-backups request a home. Characterization
  tests first; clean-backups is the first adopter; other ops migrate one-at-a-time; `--clear-history` gains a
  confirmation. Deferred: unifying CLI+TUI confirm I/O (Med-High functionality) and any config/plugin
  generalization (Med-High complexity). Supersedes the bespoke renderer in the clean-backups IPD.
- Verdict: needs work.
