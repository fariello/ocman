# Workflow: verify (proof, not prose)

Produce **machine-checkable evidence** that a repository's own checks pass, instead of an
LLM's self-report. This workflow discovers the repo's declared test/lint/build/type-check
commands, runs the ones the user approves, and records the real command, exit code,
duration, metrics, and a log excerpt into a run record that other workflows (and humans)
can cite.

The point: an enterprise reviewer will not accept "the agent looked and it is fine." A
`release-review` GO recommendation, or an `assess-testing` verdict, is only as strong as
the evidence behind it. `verify` is that evidence.

## What this is and is not

- It runs the repository's OWN checks and records the results. It is NOT a CI system, NOT
  a test runner of its own, and does NOT deploy anything.
- It does NOT write or fix tests. Discovering that there are no tests is a valid,
  honestly-reported outcome, not something to paper over.
- It relies on the deterministic helper `verify/tools/run_checks.py` (Python stdlib only,
  the same discipline as `scan_secrets.py`). Prefer running the helper over doing this by
  hand: it is the deterministic, auditable path.

## Safety (running repo commands is the core hazard)

Read this before running anything.

1. **Nothing runs without approval.** Discovery only PROPOSES commands. The default is
   confirm-before-each-check. `--yes` runs the eligible (allowlisted) set without
   prompts, for CI or trusted batches.
2. **Allowlist:** only commands classified as `test`, `lint`, `build`, or `typecheck` are
   eligible to run.
3. **Hard denylist (never run, even with `--yes`):** anything that looks like network,
   deploy, publish, release, install, push, docker push/login, infra apply, or
   destructive commands. The helper enforces this; do not override it by hand-running a
   denied command "to get a green."
4. **Unclassified commands are never auto-run.** They require an explicit interactive yes
   and are skipped under `--yes`.
5. **Bounded:** each check is time-limited (`--timeout`, default 600s). Output is
   captured, never acted upon.

If you believe a denied command genuinely needs to run for verification (rare), say so to
the user explicitly, explain the risk, and get direct human approval to run it yourself
outside the helper. Never silently bypass the denylist.

## Protocol

1. **Locate the helper:** `verify/tools/run_checks.py` under the installed workflows dir.
2. **Discover (run nothing):** run `python3 <path>/run_checks.py --repo <repo> --list`
   to see candidate checks, their categories, and which are DENIED. Show the user.
3. **Decide what to run** with the user:
   - Interactive: `run_checks.py --repo <repo>` and confirm each check.
   - Batch (CI/trusted): add `--yes` to run all eligible checks.
   - Narrow with `--only test,lint` etc.; add a command the discovery missed with
     `--add "<cmd>"` (still classified and denylist-checked).
4. **Run and capture evidence** as JSON into the run record:
   `python3 <path>/run_checks.py --repo <repo> --yes --format json --out <run>/verify-results.json`
   (drop `--yes` for interactive). Also capture the text summary for humans.
5. **Report honestly** (see below).

## The run record you produce

Create:

```
workflow-artifacts/verify/<RUN_ID>/
```

`<RUN_ID>` is a local-time timestamp `YYYYMMDD-HHMMSS`. Write:

- `verify-results.json` - the structured evidence from the helper (per-check command,
  exit code, duration, metrics, log excerpt, and the summary).
- `report.md` - a short human-readable summary: what ran, results, what was skipped and
  WHY (denied / unclassified / declined / timed-out / no-checks-found), and the honest
  bottom line.

These are committed deliverables (evidence), like release-review's and assess's records.

## Honesty requirement (non-negotiable)

- "Could not verify X" must be as prominent as "verified Y". A partial run must NEVER read
  as a full green.
- Report `ran`, `passed`, `failed`, `timed_out`, and `skipped` separately. If checks were
  skipped or none were found, say so plainly and do not imply the repo is verified.
- Never claim a check passed that you did not actually run to a zero exit. The helper's
  `all_ran_passed` is true only when at least one check ran and every check that ran
  passed; even then, state which relevant checks were NOT run.
- Distinguish "ran it" from "would run it" (discovery/`--list`).

## How other workflows use this

- **release-review:** its validation step should cite `verify-results.json` for any claim
  about tests/lint/build/type-check, and DOWNGRADE its GO recommendation (to
  CONDITIONAL-GO or NO-GO) when a relevant check could not be verified, saying so
  explicitly.
- **assess (testing lens, and others where relevant):** cite the evidence rather than
  self-reporting pass/fail; note unverifiable checks in the IPD.
- **CI:** `run_checks.py --yes --format json` produces a portable evidence artifact.

## Reminders

- Prefer the helper; it is deterministic and auditable.
- Never bypass the denylist to manufacture a green.
- Honest "unverified" beats a confident false "verified".
