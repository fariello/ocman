# Setup Repo (guided best-practices and security setup)

Treat this file as the controlling instruction for a **guided, wizard-style setup** of
a repository for best practices, security checks, and developer-experience hygiene. You
act as an interactive wizard: **detect the current state, then walk the user through
each area one step at a time, ask before making any change, and apply only what they
approve.**

Unlike the `assess-*` workflows (which only propose an IPD), this workflow MAY create
files and install tools - but ONLY with per-step user confirmation. It is idempotent
(safe to re-run) and respects whatever the repo already has.

**One command for three situations - it is a conformance check, not just first-time
setup.** Run it on a fresh repo (sets things up), on an already-set-up repo (a re-run:
finds nothing to do and says so), or after updating the framework (finds what the new
version now expects and offers to close the gap). For each area you MUST classify the
current state as **conformant** (matches the current baseline, skip), **partial** (some
of it present - offer to complete), **missing** (offer to add), or **outdated** (present
but behind the current baseline, e.g. an old generated file or tool version - offer to
refresh). Report the classification per area up front so the user sees the drift, then
only propose changes for the non-conformant items.

## Operating principles (MUST)

- **Ask before each change.** Present each proposed change, explain why, and wait for
  the user's yes/no/skip before doing it. Never batch-apply without consent.
- **Idempotent + respectful.** Detect what already exists; do not overwrite or duplicate
  it. Re-running should converge, not churn. If a thing is already done, say "already
  set up" and move on.
- **Stage, do not commit** (unless the user asks you to commit). Leave changes staged so
  the user reviews the diff. Never push.
- **Tool installs go through the helper**, and only after confirmation: run
  `python3 .agents/workflows/setup-repo/tools/setup_tools.py` to detect, and
  `... --install <tool>` to install once the user agrees. The helper uses the platform's
  own package manager; it never pipes a download to a shell.
- **Fix Bar applies:** propose everything sensible by default; the only reason to skip a
  best-practice is real Remediation Risk (complexity/usability/security/functionality),
  not effort. But the USER's "skip" is always honored.
- **Honesty:** be clear about what is a repo change vs. an out-of-repo/organizational
  action you can only advise on (e.g. GitHub branch protection).

## Step 0: Discover the repo

Before proposing anything, determine and briefly report:

1. Is this a git repo? Current branch, remote, clean/dirty working tree. (If dirty, note
   it and offer to proceed carefully, changing only setup files.)
2. Project type / stack (languages, package manager, frameworks, whether it has an app /
   library / CLI / UI / just docs). This tailors the .gitignore, CI, and hygiene steps.
3. What is already present: `.agents/workflows/`, `.agents/plans/` (and its
   `pending/` + terminal `executed/` or `done/` subdirs), `.github/workflows/`,
   `.pre-commit-config.yaml`, `.gitignore`, `.gitleaksignore`, `README`, `CONTRIBUTING`,
   `AGENTS.md` (and whether it documents the plan lifecycle), `LICENSE`, `.editorconfig`,
   lockfiles, `GUIDING_PRINCIPLES.md`.
4. Tool availability: run the helper in detect mode
   (`setup_tools.py`) and report which of gitleaks / pre-commit / detect-secrets exist.
5. Drift check (for re-runs / post-update): is `.agents/workflows/` present but behind
   the source you were invoked from (renamed/removed files, missing new lenses)? If so,
   the framework-install step (1) is "outdated", not "conformant".

Then present a short **conformance report + checklist**: for each applicable step, its
classification (conformant / partial / missing / outdated / not applicable) and the
proposed action. Tell the user you will go through the non-conformant ones a step at a
time. Let them reorder or skip any. If everything is conformant, say so plainly and stop.

## The setup steps (go through each; ask before applying)

For each step: state its **conformance classification** (conformant / partial / missing /
outdated / not applicable), what you propose (nothing, if conformant), and why. Apply
only on confirmation. Mark clearly when a step is already-satisfied so re-runs are quiet.

### 1. Agent-workflows framework installed (and up to date)

If `.agents/workflows/` is absent, offer to run the installer (`install-workflows.py`, at
the agent-workflows repo root; not present inside an installed target)
so `/release-review`, `/assess-*`, etc. are available. If it is present but **outdated**
(the drift check in Step 0 found renamed/removed/missing files vs. the source), offer to
re-run the installer to update it (it clean-syncs and regenerates shims). This is the
natural first step (setup-repo may itself have been run from an installed copy).

### 1b. Plan / IPD lifecycle (so coding agents pick it up)

The `assess-*` and `plan-review` workflows use an Implementation-Plan-Document (IPD)
lifecycle. Establish it so any coding agent working in the repo follows it, not just
these workflows:

- **Directories:** discover the existing convention and respect it; otherwise offer to
  create `.agents/plans/pending/` (new/awaiting-approval IPDs) and
  `.agents/plans/executed/` (completed IPDs) - each with a committed `.gitkeep` so the
  empty dirs are tracked. If the repo already uses a terminal dir named `done/` (or
  another), keep it - do not rename; just record which is canonical for this repo.
- **Documented contract (this is the part that makes agents pick it up):** offer to add
  a short, marker-delimited "Plan/IPD lifecycle" note to `AGENTS.md` (and/or
  `CONTRIBUTING.md`) stating: proposals are dated IPDs in `.agents/plans/pending/`; they
  are reviewed (optionally via `plan-review`), approved by a human, executed, then moved
  to the terminal dir. Marker-delimited so re-running updates it in place without
  duplicating (same discipline as the AGENTS workflow pointer).
- **Conformance:** if the dirs exist but the contract is undocumented, that is
  "partial" - offer to add the doc. If both exist, "conformant" - skip.

### 2. Secret scanning (CI + local hook)

- Ensure `gitleaks` is installed (offer to install via the helper if missing).
- Offer to add a CI secret-scan workflow (`gitleaks` over full history on push/PR) if
  none exists. If the repo has no CI host (e.g. not on GitHub), say so and skip/adapt.
- Offer a local pre-commit hook that runs `gitleaks protect` (see step 6 for the
  pre-commit framework; if the user does not want the full framework, offer a simple
  `.git/hooks/pre-commit` script instead, and explain hooks are per-clone/local).
- Offer a `.gitleaksignore` baseline (empty, documented) for future false positives.
- If the repo already has committed-secret risk, recommend running `/assess-secrets`.

### 3. .gitignore hygiene

Propose adding, to the appropriate sections and WITHOUT duplicating existing lines:
- Credential/key patterns: `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`,
  `*.keystore`, `.netrc`, `.npmrc`, `.pypirc`, `service-account*.json`,
  `credentials*.json`.
- Language/tooling artifacts appropriate to the detected stack (e.g. `__pycache__/`,
  `*.pyc`, `node_modules/`, `dist/`, `build/`, `.venv/`, coverage output).
- OS/editor cruft (`.DS_Store`, `Thumbs.db`, `*.swp`, `.idea/`, `.vscode/` if not used).
Validate with `git check-ignore` and confirm NO already-tracked file becomes ignored.

### 4. Repo hygiene files

For each missing standard file, offer to scaffold a minimal, honest starter (never a
bloated template): `README.md` (what it is, how to run), `CONTRIBUTING.md`, `LICENSE`
(ASK which license - do not assume; this is the user's legal choice), `.editorconfig`,
and (if the project has agent tooling) an `AGENTS.md` pointer. Skip any that exist.

### 5. CI baseline for the stack

If the repo has a CI host and no build/test/lint CI, offer a minimal workflow matched to
the detected stack (e.g. Python: lint + pytest; Node: install + lint + test). Keep it
minimal and use repo-native commands; do not invent tests. Skip if CI already covers it
or the repo is docs-only.

### 6. Pre-commit framework (multi-hook)

Offer to install `pre-commit` (via the helper) and add a `.pre-commit-config.yaml` with
common, low-friction hooks: gitleaks (secrets), a large-file guard, end-of-file/
trailing-whitespace fixers, and a stack-appropriate formatter/linter if the user wants.
Then offer to run `pre-commit install`. Explain it is local per clone (each contributor
runs `pre-commit install`), and that CI (step 2/5) is the enforcement backstop.

### 7. Dependency / supply-chain hygiene

- Check that lockfiles exist and are committed for the detected package manager; if the
  ecosystem supports pinning and they are missing, recommend generating them.
- Offer a dependency-audit CI step (e.g. `pip-audit`, `npm audit`, or the language's
  equivalent) if a CI host exists.
- For a deeper pass, recommend `/assess-supply-chain`.

### 8. Branch protection / repo settings (advisory only)

These live in the git host, not the repo, so you CANNOT set them - print clear
recommendations for the user to apply in their host settings: require PR review, require
status checks (the CI + secret-scan above) to pass, protect the default branch, restrict
force-push, and enable secret-scanning/Dependabot if the host offers it.

## Finish

Summarize: what was set up, what was skipped (and why), what tools were installed, and
the out-of-repo/advisory items the user must do themselves. Remind them the changes are
staged (not committed) and suggest a single setup commit. Point them at `/release-review`
and the relevant `/assess-*` workflows for deeper, ongoing checks.

Do not push. Do not commit unless the user asks.
