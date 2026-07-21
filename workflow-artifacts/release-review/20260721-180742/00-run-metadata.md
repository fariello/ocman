# 00 Run Metadata

- Run ID: 20260721-180742
- Workflow: release-review (full run, promotion review for 1.3.0)
- Agent/model: OpenCode (its_direct/pt3-claude-opus-4.8-1m-us)
- Repository path: /home/gfariello/VC/ocman
- Initial branch: main
- Head commit: 6913d1afd081fd9c6998e52f5b38fd2a486e72b1
- Remotes: origin git@github.com:fariello/ocman.git
- Working tree status: clean (in sync with origin/main; 0 ahead / 0 behind)
- Version string in repo: 1.3.0rc4 (pyproject.toml + ocman/cli.py __version__)
- Existing tags: v1.2.0 (last final release, on PyPI + GH Release), v1.3.0-rc1..rc4 (candidate tags)
- Environment: Linux, Python 3.14 venv at /home/gfariello/venv/p3.14
- Test command: PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q
- Interactive: yes (TTY / interactive session)
- workflow-artifacts/ gitignored: NO (verified; tracked as committed deliverables)

## Purpose of this run
Promotion review: decide whether the 1.3.0 line (currently candidate rc4, plus post-rc4
testing-followup commits already on main) is ready to promote to a final 1.3.0 release.
The whole 1.3.0 feature cycle (lr alias + list filters, session rename, reconnect, kill,
doctor insecure-server check, test-flake hardening + coverage tooling) sits between the
last final release (v1.2.0) and this review.

## Gate outcome
Section 1 pre-flight gate: CLEAN SKIP (no ask fired). Cursory look found no pending IPDs
(`.agents/plans/pending/` has only README.md), no staged prompts (`.agents/prompts/pending`
and `.../not-executed` hold only `.gitkeep`+README.md), empty comms inboxes, no in-code
TODO/FIXME markers, and TODO.md holds only 2 SHIPPED-annotated items plus 1 explicitly-deferred
stretch goal (forked/shared-spend de-dup) that the user has already been briefed on as deferred.
No real signal (no pending plan/prompt, no status/location mismatch, no obviously-risky item),
so per 00-run-protocol the ask is skipped and the audit proceeds. Cursory impressions discarded;
Section 5 TODO reconciliation runs independently from the full list.
