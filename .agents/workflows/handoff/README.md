# handoff

Session-continuity generator: capture this session's EPHEMERAL context (discussion, decisions and
their why, abandoned approaches, tacit preferences) into a resume document so a fresh session picks up
where this one left off. Session context is the core; the on-disk record is a thin supporting frame.
It writes a `Kind: session-handoff` draft to the gitignored `.agents/prompts/local/` lane, applies a
sensitivity/privacy gate + `aw check-local-leaks`, and NEVER auto-commits - the human promotes it. Run
`/handoff [focus]`, or from any agent: "read and execute `.agents/workflows/handoff/handoff.md`". See
`.agents/workflows/index.md` for the catalog and `/whatnext` for the short next-action ordering.
