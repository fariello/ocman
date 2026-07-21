# IPD: `ocman doctor` lists opencode server/listeners (insecure-server checkup)

- Date: 2026-07-21
- Concern: feature (health checkup surfaces insecure/exposed opencode servers)
- Scope: `ocman/cli.py` (new `check_listening_servers` doctor check + wire into
  `run_doctor_checks` + a `--all-servers` doctor flag + normalize/pass-through), tests, README,
  CHANGELOG. No TUI in this IPD. No DB schema change. doctor stays READ-ONLY.
- Status: PROPOSED (not yet executed)
- Target version: rides the in-flight 1.3.0 line (candidate `v1.3.0-rc3` is out; a later
  `v1.3.0-rc4` may follow on request). NOT promoting to final `1.3.0` yet.
- Approval: awaiting maintainer review/approval
- Author: its_direct/pt3-claude-opus-4.8

## Goal / motivation

`ocman doctor` is the routine health checkup. Today, the insecure/exposed-opencode-server
detection (unauthenticated control server, non-loopback bind) exists ONLY in `list running` /
`lr` (its bold-red SECURITY WARNING banner). A user who runs `ocman doctor` without knowing to
run `lr` never sees "you have an exposed, unauthenticated opencode server." This adds that as a
first-class doctor check so the checkup surfaces the security risk.

Nearly all detection already exists and is battle-tested (it powers `lr`); this is mostly
"surface it in doctor".

## Design decisions (settled with maintainer)

- **New check** `check_listening_servers` appended in `run_doctor_checks`, reusing
  `detect_running_instances(all_users=..., probe=..., verbosity=...)` (cli.py:8085), which
  already yields per-instance `listeners`, `auth` (secured|unsecured|unknown|n/a), `exposed`,
  `vulnerable`.
- **opencode listeners only** (detect_running_instances is opencode-filtered). NOT a generic
  "all listening sockets on the box" audit (off-mission; that is an ss/netstat job).
- **Own-user by default**; `doctor --all-servers` widens process enumeration to `ps -e`
  (forwarded as `all_users=True`). Honest note in the detail/help: without root, foreign
  listeners show `auth=unknown` and often cannot be pid-attributed by `ss`, so the widened view
  is limited (same caveat as `lr --all-users`).
- **Severity mapping:** any `vulnerable` instance (has a listener AND `auth==unsecured`) ->
  `DOCTOR_ERROR`; else any `exposed` (non-loopback bind) -> `DOCTOR_WARN`; else if there are
  authed/loopback opencode listeners -> `DOCTOR_OK` (or INFO with a count); no listeners at all
  -> `DOCTOR_OK`. Reuse the EXACT `lr` remediation wording ("set OPENCODE_SERVER_PASSWORD before
  launch; bind 127.0.0.1; avoid --mdns on shared hosts") in the detail. `bucket="report"`
  (nothing reclaimable), `fix_cmd=None` (no ocman command reclaims this; the fix is how the user
  launches opencode). Optionally point `issue_url`/detail at `ocman list running` for the full view.
- **Probe** (real read-only HTTP `GET /app` on the user's OWN loopback listeners, via
  `_probe_app_auth`, cli.py:8057) is done ONLY under the EXISTING `doctor --deep` flag (opt-in),
  by passing `probe=True` to `detect_running_instances`. No new probe flag. This keeps doctor
  read-only (the GET is the same read-only own-loopback request `lr --probe` already makes).
- **Degrade gracefully (MUST):** the check catches `RunningDetectionError` (non-Linux, `ss`
  missing, unreliable enumeration) and returns `DOCTOR_UNKNOWN` (or `DOCTOR_SKIPPED`) with a
  clear detail, NEVER failing the whole doctor run. doctor must stay usable everywhere.
- **Read-only invariant preserved:** the check only enumerates + optionally GETs /app on own
  loopback; it never signals, kills, or mutates.

## Project conventions discovered (Step 0)

- No em/en dashes in authored prose. Plans `.agents/plans/pending/` -> `executed/`. Path-scoped
  commits, never push without approval, paste REAL pytest output.
- doctor: `run_doctor_checks(loc=None, *, retention_days=None, running=None, progress=None,
  fast=False, deep=False) -> list[dict]` (cli.py:14659); `cli_doctor(args)` (cli.py:14822);
  checks appended ~cli.py:14709-14757; record via `_check_record(key,title,status,*,size_bytes,
  count,detail,fix_cmd,issue_url,bucket)` (cli.py:14012). Status constants (cli.py:13585-13592):
  DOCTOR_OK/NOTICE/WARN/INFO/ERROR/UNKNOWN/SKIPPED. `--json` emits `emit_json("doctor", records)`.
  Flags: `--fast`(doctor_fast), `--deep`(doctor_deep), `--json` (argparse cli.py:6533-6540, map
  6985-6989).
- Detection (all reusable): `detect_running_instances` (8085, Linux-only, raises
  RunningDetectionError on win32), `_listening_sockets_by_pid` (7991, `ss -tlnpH`, fail-loud),
  `_bind_is_loopback` (8024), `_server_password_env_state` (8035, own /proc/environ),
  `_probe_app_auth` (8057, read-only GET /app on own loopback), `all_users` scoping
  (ps -u vs ps -e, cli.py:7834; UID own-check 8114).
- `cli_list_running` security banner + remediation wording at cli.py:12478-12493 (reuse text).

## Findings / requirements

| ID | Requirement | Evidence |
|----|-------------|----------|
| DS-01 | New `check_listening_servers` reuses `detect_running_instances`; opencode-only | cli.py:8085 |
| DS-02 | Own-user default; `doctor --all-servers` -> all_users=True; honest root caveat | ps scoping 7834; lr --all-users 6525 |
| DS-03 | vulnerable->ERROR, exposed->WARN, authed/none->OK; report bucket, no fix_cmd | _check_record 14012; banner 12478 |
| DS-04 | `--deep` -> probe=True (GET /app own loopback only); no new flag | doctor_deep 6537; _probe_app_auth 8057 |
| DS-05 | Degrade to UNKNOWN/SKIPPED on RunningDetectionError / non-Linux; never fail doctor | detect_running_instances raises 8095 |
| DS-06 | doctor stays READ-ONLY (enumerate + optional own-loopback GET; no mutation/signal) | doctor read-only invariant 14662 |
| DS-07 | reuse the exact lr remediation wording in the detail | banner text 12490-12492 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Rem.Risk | Validation |
|------|--------|--------|-------|----------|------------|
| 1 | DS-01,DS-03,DS-04,DS-05,DS-07 | Add `check_listening_servers(*, all_users=False, probe=False) -> dict` (a `_check_record`): call `detect_running_instances(all_users=all_users, probe=probe)` inside try/except `RunningDetectionError` -> on error return `_check_record("listening_servers","Listening opencode servers",DOCTOR_UNKNOWN, detail="<reason> (Linux-only; needs 'ss')", bucket="report")`. Filter to instances with `listeners`. Compute `vulns=[it for it if it["vulnerable"]]`, `exposed=[... if it["exposed"] and not vulnerable]`. status = ERROR if vulns else WARN if exposed else OK. count = number of listening opencode servers. detail lists pids + binds for vulns/exposed + the exact lr remediation text (DS-07); when OK with authed loopback servers, a short "N authed loopback server(s)" INFO-style detail. `bucket="report"`, `fix_cmd=None`. Point detail at `ocman list running` for the full view. | cli.py | Low | unit: fake detect_running_instances -> vulnerable=ERROR; exposed=WARN; authed-loopback=OK; none=OK; RunningDetectionError=UNKNOWN |
| 2 | DS-01,DS-02,DS-04 | Wire into `run_doctor_checks`: add params `all_servers: bool=False` (thread from cli_doctor) and reuse the existing `deep` param for probe. Append `check_listening_servers(all_users=all_servers, probe=deep)` alongside the filesystem checks (~cli.py:14753-14757). Keep it AFTER the DB/filesystem checks so security shows near the end summary. It must not gate on schema/DB readability (a server can run with any DB state). | cli.py | Low | records include key "listening_servers"; present even when no DB |
| 3 | DS-02 | Add `doctor --all-servers` flag (argparse ~cli.py:6533-6540; dest `doctor_all_servers`) + normalize (map ~6985-6989 -> `out["doctor_all_servers"]`). `cli_doctor` passes `all_servers=getattr(args,"doctor_all_servers",False)` into `run_doctor_checks`. `--deep` already exists and maps to probe. Help text notes the root caveat. | cli.py | Low | `doctor --all-servers` parses; forwarded to the check |
| 4 | DS-03,DS-06 | Ensure presentation: the new record flows through the existing detail-lines + summary + table (Check/Status/Size/Count/Recommended fix) with no special-casing; ERROR renders bold-red like other errors. Confirm doctor remains read-only (no new writes; the only new outbound is the opt-in `--deep` GET /app on own loopback). | cli.py | Low | `cli_doctor` JSON + text render the record; a vulnerable fake shows ERROR |
| 5 | all | Help text: doctor help mentions the listening-servers check + `--all-servers` (+ that `--deep` probes own loopback auth). | cli.py | Low | `ocman doctor -h` / help shows it |
| 6 | all | CHANGELOG `[1.3.0]` Added entry; README doctor section (new check, `--all-servers`, `--deep` probe, Linux-only, own-user default + root caveat, points to `list running`). | CHANGELOG.md, README.md | Low | docs accurate |

## Deferred / out of scope

- **Generic "all listening sockets" audit** (non-opencode): out of scope (off-mission; noisy;
  root-attribution issues). doctor reports only opencode servers.
- **A dedicated `doctor --probe` flag:** not added; probing folds into the existing `--deep`.
- **TUI Storage-tab surfacing** of the new check: the TUI already renders `run_doctor_checks`
  records, so it will appear automatically; no dedicated TUI work in this IPD. (Confirm it
  renders; if a security record needs special emphasis in the TUI, that is a separate IPD.)
- **Auto-remediation** (killing/securing the server): out of scope; doctor is read-only. (The
  user can act via `ocman kill` / relaunch with a password.)

## Anti-regression / invariants

- doctor remains READ-ONLY: the new check enumerates processes/sockets and, only under `--deep`,
  does a read-only GET /app on the user's OWN loopback listeners (never other hosts, never
  mutating). Assert read-only in tests (state unchanged after a doctor run).
- Existing doctor checks/records unchanged; this is purely additive (one new record key).
- `detect_running_instances` / `lr` behavior unchanged; doctor is a new consumer.
- Non-Linux / no-`ss`: doctor still completes; the new record is UNKNOWN/SKIPPED, not a failure.
- No new dependency.

## Required tests / validation

- `PYTHONPATH=. /home/gfariello/venv/p3.14/bin/pytest -q` and PASTE ACTUAL output.
- Unit (`check_listening_servers`, monkeypatch `detect_running_instances` to return fake
  instances, mirroring the dict shape used by `test_list_running_filter_...`): vulnerable ->
  ERROR + remediation text in detail; exposed-but-authed -> WARN; authed loopback only -> OK;
  no listeners -> OK; `detect_running_instances` raising `RunningDetectionError` -> UNKNOWN (no
  exception escapes). `all_users`/`probe` pass-through asserted.
- `run_doctor_checks` includes the `listening_servers` record (with and without a DB).
- `cli_doctor` e2e: `--json` envelope contains the record; a vulnerable fake -> ERROR record;
  `--all-servers` forwards all_users=True; `--deep` forwards probe=True (assert via a
  monkeypatched detect_running_instances capturing kwargs).
- Read-only: doctor run does not change DB/files (reuse the existing doctor read-only assertion
  pattern).
- Cross-platform: the detection is Linux-only; tests monkeypatch `detect_running_instances`, so
  they run everywhere. Add one guard/skip only if a test touches real `ss`/`/proc`. No weakened
  assertions.

## Spec / documentation sync

- CHANGELOG `[1.3.0]` Added: "`ocman doctor` now checks for insecure/exposed opencode servers
  (own-user by default; `--all-servers` to widen; `--deep` confirms auth via a read-only loopback
  probe). Surfaces the same insecure-server warning previously only in `list running`."
- README: doctor section update (new check, flags, Linux-only, own-user + root caveat).
- Help text (doctor -h / build_help).

## Open questions

None (scope, own-user default + `--all-servers`, opencode-only, severity mapping, `--deep`
probe reuse, and graceful degradation all settled with the maintainer).

## Approval and execution gate

- Execution checklist (MUST): before coding, create a TodoWrite step-granular checklist tracking
  Steps 1-6, the unit + e2e tests, the full-suite run with pasted output, README+CHANGELOG+help
  sync, the path-scoped commit(s), and the Status-executed + `git mv` to `executed/`.
- Scope fence: ONLY the doctor listening-servers surface (`check_listening_servers`, its wiring
  into `run_doctor_checks`, the `--all-servers` flag + normalize + `cli_doctor` pass-through,
  help, README/CHANGELOG, tests). Reuse `detect_running_instances` unchanged. No TUI code, no DB
  schema, no new dependency, no generic-socket audit, no auto-remediation, no change to
  `lr`/detection.
- Honesty rules (hard MUST): paste ACTUAL `pytest -q` output; never claim a pass not run. Tests
  monkeypatch `detect_running_instances` (no real `ss`/network in unit tests). doctor MUST remain
  read-only; the `--deep` probe is a read-only own-loopback GET only.
- Safety MUST: graceful degradation (never fail the doctor run on detection error); own-user
  default; `--all-servers` honestly notes the root limitation.
- Commits: path-scoped, NEVER push without approval, NEVER tag outside an approved release step.
- Lifecycle: on completion set `Status: executed` and `git mv` this IPD to `executed/`.

Next: human review (optionally `/plan-review`) sets `Status: approved`; then execute per the above.
