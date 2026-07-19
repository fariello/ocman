# Run metadata

- Run ID: 20260719-140024
- Workflow: release-review
- Agent/model: its_direct/pt3-claude-opus-4.8
- Repository: /home/gfariello/VC/ocman
- Git: yes; branch `main`; head `3dcd44e` at run start
- Remote: origin git@github.com:fariello/ocman.git (GitHub)
- Working tree at start: clean
- Commits ahead of origin/main at start: 40
- Last release tag: v1.1.0
- Current version: pyproject.toml 1.1.0; ocman/cli.py __version__ 1.1.0
- workflow-artifacts/ gitignored: no (good; artifacts are committed deliverables)
- Initial status: in progress
- Final status: HALTED at Section 9 (CI red; blocker S9-REL2: no published vistab works). main pushed; nothing tagged/released/published.

## Context (from the current session)

This release bundles a large, already-reviewed body of work completed this session, each
piece via assess -> plan-review -> approve -> execute -> commit -> IPD to executed/:
- Documentation accuracy fixes (README/ARCHITECTURE): commit 3784cdd.
- Extract-on-delete + bare-word `help`: 1d65d13; doctor/reclaim `.so` ownership fix 4ff44b2.
- Full CLI<->TUI parity (5 phases): 45eb8c4, 79f5818, 2fde996, 6e6286a, 5972d0c.
- FU-01 config-save preserve-keys fix: 7698791.
- Consolidated TUI docs: 22bf892.
- Self-documentation fixes (errors that teach, traceback guard, reclaim discoverability): 3dcd44e.

No plans remain in .agents/plans/pending/ (all executed). The maintainer chose to run
release-review now; it should prepare the 1.1.0 -> 1.2.0 version bump + CHANGELOG cut and
gate on an explicit GO before any push/tag/publish.
