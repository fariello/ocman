# Guiding Principles Assessment

Principles home: ARCHITECTURE.md "Design principles" (~line 248). No standalone GUIDING_PRINCIPLES.md; universal fallback principles also apply. Per-principle adherence appended in Section 5.

## Per-principle adherence (Section 5) - against ARCHITECTURE.md "Design principles"

1. **Intuitive / self-documenting.** ADHERES. The 5 new commands follow the established
   noun-based grammar (`session rename`) with natural top-level aliases (`rename ... to`,
   `lr`, `reconnect`, `kill`), typed/confirmed destructive actions (reconnect/kill confirm
   by default, `-y` to skip, `--dry-run` to preview), and actionable output (killed vs
   survived PIDs, remediation strings on insecure servers). Errors tell the user how to
   recover (e.g. "Re-run with --force to send SIGKILL", "cd to the project first"). No GP
   violation.

2. **Configurable over hardcoded.** ADHERES. The new commands add no magic constants that
   should be config; timeouts are sensible defaults with `--force` escape hatches. The
   `_instance_matches_pattern` helper is a single source of truth shared by lr + kill (no
   special-casing/forking). No GP violation.

3. **KISS.** ADHERES. Features reuse existing seams (reconnect/kill build on
   `detect_running_instances`/`_reconnect_candidates`; doctor server check reuses the same
   detection; rename is one guarded DB function). No new dependency. The one-module trade-off
   is unchanged. No GP violation.

4. **Honest documentation.** ADHERES (with 3 Low doc-sync findings). README/CHANGELOG describe
   actual behavior. The rename running-guard prints an honest caveat that ocman cannot tell
   which process uses which session. Gaps are staleness (A01 ARCH verb list, KD01 DECISIONS
   entry, D01 changelog date), not dishonest claims.

Verdict: FULL adherence to all 4 principles; no GP violations. Doc-sync gaps are Low/Low.
