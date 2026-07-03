# 11 Push Plan

- **Current branch:** main
- **Local commits this run (ahead of e6c5943):**
  - a176b4d chore: Section 1 artifacts
  - 3f40ca8 chore: Section 2 audit
  - (Section 3-6 chores)
  - 41867c7 fix: harden restore/export/TUI
  - 28ff29e test: regressions
  - 5216f09 docs: changelog/architecture/version
  - + Section 7/8 artifact chores
- **Git status:** clean.
- **Push permission:** NOT granted for this run (user authorized local commits only).
- **Recommendation:** Do NOT push automatically. The changes are safe, tested (58 passing), and additive.
  When ready, the user can push with:
  ```
  git push origin main
  ```
- **Local remote note:** `origin` currently points to `git@github.com:fariello/opencode-recover.git`, but the
  user reports GitHub only shows `ocman`. Verify/repoint the local remote before pushing:
  ```
  git remote set-url origin https://github.com/fariello/ocman.git   # if that is the canonical URL
  ```
- **Risks of pushing:** Low. No remote state beyond the branch; CI (tests only) will run on push/PR.
