# 00 Run Metadata

- Run ID: 20260707-004045
- Workflow: release-review
- Agent/model: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Repository: /home/gfariello/VC/ocman
- Git: yes; branch `main`; head `8b017df` at start; remote `origin git@github.com:fariello/ocman.git`
- Initial status: ahead of origin/main by 14 commits (this session's 1.1.0 work), working tree clean
- workflow-artifacts/ gitignored: NO (good; committed deliverable)
- Purpose: pre-release review of ocman 1.1.0 (new `filter` command, canonical recovery filenames,
  egress guards, collision safety, TUI parity) before moving the `v1.1.0` tag.
- Prior work this session (input, not re-litigated blindly): assess+plan-review+execute of security,
  edge-cases, compatibility IPDs (`.agents/plans/executed/20260706-*`), and a prose pass
  (`20260707-assess-prose`). This review independently verifies the shipped result.
- Environment: Linux; Python >=3.10; CI matrix ubuntu/macos/windows x 3.10-3.14.
