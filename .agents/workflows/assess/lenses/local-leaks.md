# Lens: Local leaks (maintainer/machine identifying info in a public artifact)

Focus the assessment on **identifying information about the author or their machine that
must not live in a public artifact**: absolute home-directory paths, usernames, other
local accounts, private sibling-repo names, hostnames, and captured session/instance ids.
The question is: **does this repo (or its shipped package, or its history) tell the world
who and where the maintainer is, or bake in paths that only resolve on one machine?**

This is distinct from adjacent lenses:
- `secrets` - credentials/keys and PII/PHI *committed* to the repo (an email address is
  covered there as PII; local-leaks reuses that, see below).
- `privacy` - how the *product* handles data subjects at runtime.
- `security` - the design habit of not hardcoding secrets.

Local leaks are the class ordinary secret scanners MISS: `/home/<you>`, a private repo
name, or a hostname has no credential shape, so gitleaks/git-secrets sail past it. This
is both a privacy leak (to every downstream user) and a correctness bug (paths that do
not resolve on their machines). See DECISIONS D92 (the first real incident) and D93.

## Lead personas

The stakeholder (privacy exposure of the maintainer), the software engineer (portable
paths, prevention), and the power user/operator running the published package.

## Do not eyeball it: run the deterministic engine and CONSUME its output

Run the packaged scanner rather than reading files by hand. It is read-only by default,
stdlib-only, and is ONE unified engine (`agent_workflows/leak_sanitizer.py`, the
`leak-sanitizer` Set) shared with the pre-commit hook and CI, so the lens cannot drift from
the gate. `aw check-local-leaks` and its broader alias `aw sanitize` are the same command.

CONSUME the deterministic `--agent` stream; do NOT re-derive the classification in prose.
The canonical invocation for this lens is:

```
aw check-local-leaks . --agent --warn            # working tree, machine-parseable, incl. advisory
aw check-local-leaks . --wheel dist/<built>.whl --agent --warn   # the shipped surface
aw check-local-leaks . --history --agent --warn  # git history (bounded; add --max-commits N)
```

`--agent` prints, to STDOUT, one tab-separated record per finding and NO prose:

```
<location>\t<rule>\t<severity>
```

where `<location>` is `path:line` (tree/staged), `commit:path:line` (history), or
`wheel!entry:line` (wheel); `<rule>` is the matched rule name; `<severity>` is the engine's
own `fail` or `warn`. Exit code is `1` if any `fail` record exists, else `0` (a `2` means git
was unavailable / a usage error). Parse these records and use the engine's `severity` field
directly - do not re-classify findings yourself. Human/prose output goes to stderr, so the
stdout record stream stays clean. Equivalent without the CLI installed:
`python3 -m agent_workflows check-local-leaks . --agent --warn`.

Other modes (human-facing, not the agent path): `--staged` (only staged blobs, what the hook
checks) and `aw sanitize . --fix --dry-run` (preview home-style path rewrites). `--fix`
rewrites home-style absolute paths to `~`, INTERACTIVE per file by default (`--yes`/`--force`
to batch); identity/private-repo/session tokens have no safe generic rewrite, so they are
reported for manual editing and never auto-changed. `--fix` is opt-in and NOT in the hook. The
IP ruleset (v4/v6) is OFF by default (`ip_enabled = true` per repo enables it). Author config
with `aw sanitize --configure`.

What the two severities in the stream mean (D93; you READ them off the record, you do not
compute them):
- **fail** records fail the non-interactive gate: structural patterns (home paths, the
  local-checkout dir style, session ids), curated repo-allowlist misses, and user-level hints.
- **warn** records are advisory (only present with `--warn`): auto-derived environment
  candidates (`$HOME` basename, `git config user.*`, `$USER`/`$USERNAME`, hostname, sibling
  dir names). They NEVER fail CI; they are the set a human confirms in triage below.

## What to cover

- **Shipped surface first** (highest stakes): build the wheel and scan it
  (`--wheel`). Anything identifying that ships is published to every installer and, once
  on a registry, is effectively immutable. Lead the IPD with these.
- **Working tree** and **history** (public on the forge even when not shipped): a leak
  reachable only via an old commit/tag is invisible to a tree scan; run `--history`.
- **Emails and usernames** (the interactive part - this IS judgment, and it stays): from the
  parsed records, enumerate every distinct email and username surfaced (emails are also flagged
  by `assess-secrets` as PII - do not contradict it; here the angle is author identity).
  Present the enumerated set to the human and **ask which are intended-public and which are
  leaks** (per GUIDING_PRINCIPLES P12, put that question and its context in the interactive
  prompt itself). Record the approved ones (see below) so the automated gate stops re-flagging
  them. The engine classifies fail-vs-warn deterministically; the human decides public-vs-leak.

## Triage (human judgment on the parsed records)

Drive triage from the `--agent` records (the `severity` field is the engine's, not yours):

1. **Intended-public identifiers** (the author email in package metadata, the public repo
   origin URL): confirm and ADD them to the repo-committed allowlist
   `.agents/local-leaks-allowlist.toml` (`allow_line_substrings = [...]`). This travels
   with the repo and keeps CI deterministic. `aw sanitize --configure` authors this file (and
   the personal hints + the IP/hostname toggles) interactively with a diff and confirmation,
   rather than hand-editing the TOML.
2. **`warn` records (advisory auto-derived candidates):** confirm interactively. If a derived
   token is a real leak, add it to the fail set (a repo `fail_patterns` entry, or the
   operator's never-committed `~/.config/agent-workflows/local-leaks-hints.json` if it is
   machine-wide). If it is a false positive (a common word that happens to match a username),
   leave it as warn-only.
3. **`fail` records that are real leaks:** classify and route to remediation.

## Remediation to propose

1. **Abstract in tracked files:** replace absolute paths with repo-relative or placeholder
   forms; replace private repo names / usernames / hostnames with neutral descriptions or
   placeholders. Editable docs can be rewritten; historical records (executed plans,
   recovery transcripts) get a noted redaction (never a silent rewrite) - see D92.
2. **Purge from history** if the leak is in past commits (a tree scrub leaves it in
   history). Propose `git filter-repo` with a reviewed replace-map; note it rewrites
   history (force-push, collaborators re-clone) and route the decision to the human.
3. **Un-ship it:** if a leak reached a published package, note that a registry yank HIDES
   but does not ALTER the already-uploaded bytes; deletion + a clean re-release may be
   needed. Route to the human.
4. **Prevent recurrence:** the pre-commit hook + the `local-leaks` CI backstop already run
   this engine; ensure they are installed. Add confirmed-public values to the committed
   allowlist rather than weakening the patterns.

## IPD emphasis

Lead with any leak in the SHIPPED wheel (published-artifact exposure), then history, then
working tree. Never write a raw leaked value into the IPD/run record/chat beyond the
`location` + redacted snippet the engine already prints. Be explicit that history rewrites
and registry yanks are operator actions this workflow proposes but does not perform.
