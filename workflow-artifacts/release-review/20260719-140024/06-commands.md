# Commands run (Section 1)

- git rev-parse / status / remote / rev-list origin/main..HEAD -> branch main, head 3dcd44e,
  clean tree, 40 ahead, remote GitHub. Purpose: baseline. Clean.
- ls -la; ls .github/workflows; cat TODO.md; cat pyproject.toml; grep TODO/FIXME markers.
  Purpose: inventory. Result: TODO.md has no release blockers; 2 marker hits are false
  positives; CI = ci.yml + secret-scan.yml; version 1.1.0.
