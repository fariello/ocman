# Commits (this run)

Run-artifact commits (section boundaries): c62b6fa (S1), 3ca7be1 (S2), 38bf59d (S3),
21b53b8 (S4), 84b34e4 (S5), 7254efc (S6). Plus this S7 artifact commit.

Product commit (Section 7):
- 2554395 "release: v1.2.0 (version bump + CHANGELOG cut + gitleaks baseline)"
  Files: pyproject.toml, ocman/cli.py, CHANGELOG.md, .gitleaksignore.
  Source actions: A1 (S1-REL1), A2 (S2-S1), A3 (S1-REL1).
  Validation: ocman -V=1.2.0; gitleaks no leaks; suite 407 passed/2 skipped; wheel
  ocman-1.2.0 builds.
