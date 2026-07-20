# Section 6 - Compatibility, Packaging, CI, Release (per-phase report)

## What I did

- Verified the vistab>=1.3.0 floor end to end: vistab 1.3.0 imports cleanly on Python 3.14
  (the `NameError: 'Set'` that broke 1.2.0 on 3.12 is fixed; `Set` is now in vistab's API), and
  it provides `Vistab.set_color` / `Vistab.set_header_style` as INSTANCE methods, which is
  exactly how ocman uses them (`cli.py:4758-4760`). The `hasattr(vistab,'set_color')==False`
  observation is a red herring (they are class methods, not module functions).
- Ran a clean, isolated `python -m build`: produced `ocman-1.2.0.tar.gz` + wheel; the wheel
  contains `ocman/`, `ocman_tui/`, and the force-included `migrate_recovery_names.py`.
- Published-version check: PyPI latest is **1.1.0**; proposed **1.2.0** is a valid bump.
- CI assessment: the matrix (ubuntu/macos/windows x py3.10-3.14) + secret-scan are appropriate
  and green at `bebb520`. The one action is restoring `fail-fast: true` (S1-CI1 / S6-CI1).
- Schema: the delta did not touch the `.ocbox` format, DB-schema handling, or config schema;
  no drift introduced.

## Why

- Packaging and compatibility are the highest-risk part of THIS delta (the vistab floor exists
  precisely because a bad transitive version broke clean install on 3.12). I verified the fix
  resolves it and that the build/version are release-ready, rather than trusting the CHANGELOG.

## Findings

- S6-P1 (P, Medium/Low, completed): vistab floor correct; clean build + import; valid version bump.
- S6-CI1 (CI, Low/Low, identified): matrix green; restore fail-fast (== S1-CI1) in Section 7.

## What I considered but did NOT do

- **Add lint/type-check CI:** not warranted; not part of the repo's native validation, and
  adding it is scope creep for a release-hardening pass (would risk new red on style rules).
- **Publish/upload to TestPyPI to fully validate the wheel:** out of scope for the audit; a
  local isolated build + import is sufficient evidence. Actual publish is a Section 9 operator
  step requiring explicit approval and a token this run does not hold.
- **Tighten the CHANGELOG "module-level set_color" phrasing:** optional cosmetic; noted but not
  filed as a required fix (the dependency statement is functionally correct).
