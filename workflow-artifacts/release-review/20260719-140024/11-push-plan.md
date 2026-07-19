# Push / no-push plan

- Branch: main. Local commits ahead of origin/main: 48 (this release cycle's work +
  the release-review run artifacts + the v1.2.0 product commit 2554395).
- Working tree: clean.
- User push permission: NOT yet granted. This review does NOT push.
- Recommendation: after the maintainer's GO, push `main` to origin, then (per the chosen
  consent rung) tag/release. CI (matrix + gitleaks secret-scan) will run on push; gitleaks
  is now green locally, so the secret-scan job should pass.
- Suggested commands (Section 9, only after explicit GO + rung choice):
  - Rung C (full release): `git push origin main` then an annotated `git tag -a v1.2.0`,
    `git push origin v1.2.0`, GitHub Release, and (if desired) PyPI publish - each
    separately confirmed in Section 9.
- No-push rationale if declined: hold locally; nothing is externally visible.

## Consent decision (2026-07-19)
- Maintainer approved the review (GO) and chose RUNG A: close out only.
- NOTHING tagged, pushed, released, or published. The v1.2.0 commit (2554395) and all
  run artifacts remain LOCAL (48 commits ahead of origin/main; clean tree).
- Section 9 (release execution) was NOT run. It can be run later when the maintainer is
  ready (choose rung B or C then).
