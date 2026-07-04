# Lens: Committed secrets and sensitive data

Focus the assessment on **secrets, credentials, keys, and sensitive personal data
(PII/PHI) that are committed to the repository** - in the working tree AND, crucially,
anywhere in the git history. This is distinct from the `security` lens (which checks
the *design habit* of not hardcoding secrets) and the `data-exfiltration` lens (which
checks secrets *leaking outward at runtime*). Here the question is: **is there a secret
or sensitive datum sitting in this repo or its history right now?**

## Lead personas

The security-minded architect and the stakeholder (breach/compliance/legal exposure),
with the software engineer on prevention (gitignore, hooks, secret managers).

## Do not rely on the LLM to crawl everything

A repo can have millions of lines and thousands of commits. **Run the deterministic
scanner** rather than eyeballing: `.agents/workflows/assess/tools/scan_secrets.py`.
It is read-only, redacts every match (so it is safe to save), and scans the working
tree and full git history. Recommended invocation:

```
python3 .agents/workflows/assess/tools/scan_secrets.py --repo . --format json \
  --out workflow-artifacts/assess-secrets/<RUN_ID>/scan.json
```

On very large repos, bound history with `--max-commits N` or `--since DATE`, or start
with `--working-tree-only` and note that history was not fully scanned.

**Prefer mature, dedicated scanners when available.** The built-in tool is a
dependency-free safety net, not a replacement. If `gitleaks`, `trufflehog`, or
`detect-secrets` is installed, the built-in tool runs it and merges results; if none
is installed, the tool prints install guidance. In the IPD, **recommend installing and
running a mature scanner** (e.g. `gitleaks detect`) as part of the remediation and in
CI, and note that this run used only the built-in safety net if that was the case.

## What the scanner (and your triage) cover

- **Secrets/credentials/keys:** API keys (cloud, SaaS, model providers), private-key
  (PEM) blocks, tokens (JWT, bearer, PATs), passwords in assignments/URLs/connection
  strings, high-entropy strings, and sensitive filenames (`.env`, `*.pem`, keystores,
  `service-account*.json`, `.npmrc`/`.pypirc`/`.netrc`).
- **PII/PHI:** SSNs, Luhn-valid card-number candidates, emails, phone numbers, IBANs,
  and similar - the sensitive personal data that should not be committed.
- **Coverage:** working tree AND git history (a secret removed from HEAD but still in
  history is the most dangerous case and the whole point of the history scan).

## Triage (LLM judgment on the scanner output)

The scanner emits CANDIDATES; you decide:

1. **False positives:** test fixtures, example/dummy values, documentation, public
   keys, obviously-fake data. Mark them as such; do not propose churn on them. Consider
   proposing an allow-list / baseline (e.g. `.gitleaksignore`, detect-secrets baseline)
   so future scans stay quiet.
2. **Real secrets/sensitive data:** classify severity. A live credential or real
   PII/PHI committed to the repo (especially present in history) is **High or Blocker**.
3. **Never write a raw secret value into the IPD, run record, findings, or chat** -
   reference it by location (`file:line` / `commit:path`) and the redacted preview
   only. Surfacing the value again is a new leak.

## Remediation to propose (order matters: rotate first)

For each confirmed real secret, the IPD must propose, in this order:

1. **Rotate/revoke first.** Assume any committed secret is compromised - the top
   priority is to invalidate it at the provider, not to delete the text. (This is an
   operator action; flag it as the immediate step.)
2. **Purge from history**, not just from HEAD. Deleting the line in a new commit leaves
   it in history. Propose `git filter-repo` (preferred) or BFG, note that it rewrites
   history and requires coordination (force-push, collaborators re-clone), and route
   the rewrite decision to the human.
3. **Prevent recurrence:** move the secret to a secret manager / env var; add the file
   pattern to `.gitignore`; add a pre-commit hook and/or CI job running a mature
   scanner; add an allow-list baseline for known false positives.

For confirmed committed PII/PHI, propose removal + history purge + retention/handling
per the `privacy` and (if applicable) `compliance` lenses, and rotation only if
credentials are involved.

## IPD emphasis

Lead the IPD with any High/Blocker confirmed secrets and the rotate-first instruction,
clearly separated from prevention work. Attach the scanner output (redacted) to the run
record. Be explicit that findings are candidates requiring the operator to confirm
which are live, and that history rewrites and credential rotation are operator actions
this workflow proposes but does not perform.
