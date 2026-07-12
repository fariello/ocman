# Agent Workflows

<!-- WORKFLOWS-VERSION: 1.1.0 -->
Version: `1.1.0` (source of truth: `.agents/workflows/VERSION`). Scheme:
git-tag-driven semantic versioning (baseline `v1.0.0`); `VERSION` is DERIVED from the
tag, not hand-edited. The installer stamps this into each target so `/list-workflows`
and `setup-repo` can report the installed version.

Reusable, tool-agnostic agent workflows for this repository. Each workflow is a
capability with its own subdirectory here. To run one, read and execute its body
file (the path below), or use the matching slash command in a tool that supports them
(`/<command>`).

These workflows are invoked on demand; they are not always-loaded context. `AGENTS.md`
carries only a one-line pointer to this index, not the workflow contents.

## Workflows

The table below is the manifest. The installer reads it to generate per-tool command
shims. Keep the columns stable: `command | body | lens | description`. The optional
`lens` column lets several commands share one body (the `assess` harness) while
focusing on different concerns; leave it `-` when not used.

<!-- WORKFLOWS-MANIFEST:BEGIN -->
| command | body | lens | description |
|---|---|---|---|
| release-review | .agents/workflows/release-review/README.md | - | Full pre-release repository review and hardening: deep audit through eight personas, the Fix Bar, fix/validate/report, push and release decisions. |
| release-review-plan | .agents/workflows/release-review/README.md | - | Release review in planning-only mode: audit and consolidated implementation plan, stopping before implementation. |
| plan-review | .agents/workflows/plan-review/plan-review.md | - | Pre-execution plan reviewer: review and improve a proposed implementation plan before any code is written (edits planning documents only). Single-file version. |
| plan-review-long | .agents/workflows/plan-review-long/plan-review-long.md | - | Same as plan-review, in a multi-file orchestrator form: a small memory-kernel orchestrator that loads one step at a time (discover/snapshot, review/revise, resolve/finalize) with a shared rubric and report template, to reduce directive drift on long runs. Kept in deliberate parity with the single-file plan-review. |
| verify-execution | .agents/workflows/verify-execution/verify-execution.md | - | Post-execution cross-check: verify an EXECUTED plan (IPD) was actually done as written (read the diff, check each required change, re-run the repo's real validation via /verify), always write a run record, and EMIT a corrective IPD for any gap (never fixes in place; commits only its own files path-scoped, safe to run while another agent works). Verdict MATCHES/DIVERGES/INCOMPLETE + GO/NO-GO on "truly executed?". Used to cross-check another agent's or a past session's work. |
| getting-started | .agents/workflows/getting-started/getting-started.md | - | Guided in-agent tour and router for newcomers: detect repo/toolkit context, explain the mental model briefly, ask the user's goal, and route to the right workflow (offering to run it with consent) with the exact invocation for their tool. Orients and routes; references `/list-workflows` for the full catalog. Read-only by default. |
| list-workflows | .agents/workflows/list-workflows/list-workflows.md | - | Toolkit discovery: list what this toolkit can do (core workflows, the `/assess` concerns, any personas) and the installed framework version, read from the manifest. Optional filter argument (`/list-workflows security`, `/list-workflows assess`). Read-only. |
| verify | .agents/workflows/verify/verify.md | - | Proof, not prose: discover the repo's own test/lint/build/type-check commands (`run_checks.py`), run the approved ones (confirm-per-check by default, `--yes` for batch; hard denylist for network/deploy/publish/install), and capture real exit codes/metrics/logs as committed evidence. Honest about what could not be verified. Reused by release-review and assess. |
| spec | .agents/workflows/spec/spec.md | - | Front of funnel: turn a fuzzy request into a reviewable specification (goals, non-goals, users, requirements, testable acceptance criteria, constraints, open questions). Guided/interactive; writes the spec to the repo's convention. Produces the artifact that `/advise spec-editor` interrogates and `plan-review` reviews. |
| incident | .agents/workflows/incident/incident.md | - | Blameless post-mortem for a production incident: timeline, impact, systemic contributing factors, what went right/wrong, and follow-up actions emitted as IPDs into pending/. Reactive complement to the reliability/logging-audit/intrusion-detection lenses. Repo-scoped and honest about it (operator holds the real monitoring/on-call data). |
| release-notes | .agents/workflows/release-notes/release-notes.md | - | Release discipline: decide the version bump from the actual changes, draft the changelog and human release notes (prose-style guide; breaking changes prominent), and update CHANGELOG/version files with confirmation. Never publishes, tags, pushes, or deploys. Distinct from release-review Section 9 (which executes a release). |
| migrate | .agents/workflows/migrate/migrate.md | - | Assess-and-plan a high-risk migration (framework/DB/dependency-major/layout): inventory the blast radius, name the invariants that must survive, and propose a staged, reversible plan with characterization tests first and per-stage rollback + verify checks. Emits an IPD; does not execute. |
| benchmark | .agents/workflows/benchmark/benchmark.md | - | Guided performance benchmarking (informational, not a regression gate): author an ISOLATED benchmarks/ suite in the target repo (inert when unused), deeply capture and diagnose the machine/environment (`bench_env.py`: CPU/RAM/GPU/load/filesystem, flags NFS working sets, powersave governor, swapping, busy/login-node with suggested remedies), run with warm-up and >=2 iterations, detect HPC schedulers and (on explicit per-submission consent) generate + submit a job script, and produce a shareable, anonymizable results bundle. Read-only on system state; never publishes. |
| setup-repo | .agents/workflows/setup-repo/setup-repo.md | - | Guided, idempotent, drift-aware repo setup AND conformance check: detect state, classify each area (conformant/partial/missing/outdated), then ask-before-each-change to install tools and add secret-scanning, the plan/IPD lifecycle (dirs + documented contract), .gitignore/CI/pre-commit/hygiene files. Safe to re-run after updates; stages changes. |
| scaffold | .agents/workflows/scaffold/scaffold.md | - | Guided, wizard-style creation of a new assess-* lens, standalone workflow, or command: generate from the existing patterns, wire the manifest, and regenerate shims. Authoring/meta workflow. |
| assess | .agents/workflows/assess/assess.md | - | Assess ONE concern deeply and propose an IPD. `/assess <concern> [scope]` (e.g. `/assess security`, `/assess prose src/`); bare `/assess` lists concerns and asks. The `assess-<concern>` rows below are the concern catalog (they define the lenses), not separate commands. |
| assess-all | .agents/workflows/assess-all/assess-all.md | - | Cross-concern rollup: run the assess family (all, a group, or a subset - confirms scope and cost first) and synthesize ONE prioritized, de-duplicated, cross-concern IPD plus a rollup record, instead of many separate IPDs. The broad propose-a-plan review (release-review is the broad fix-in-place review). Reuses the lenses as the single source of truth. |
| assess-performance | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/performance.md | Assess runtime/resource performance and propose an IPD. |
| assess-security | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/security.md | Assess security posture and propose an IPD. |
| assess-privacy | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/privacy.md | Assess privacy/data-protection handling and propose an IPD. |
| assess-accessibility | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/accessibility.md | Assess accessibility and propose an IPD: WCAG 2.1 AA for graphical UIs, plus a WCAG-inspired rubric for terminal/CLI/TUI output (color never the sole signal, no load-bearing dim/blink, honor NO_COLOR/FORCE_COLOR/TERM/non-TTY, screen-reader-friendly plain mode). Preserves polish via graceful degradation + an opt-out toggle rather than stripping color/spinners; consults interactively before proposing look/feel changes. |
| assess-ui-ux | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/ui-ux.md | Assess UI/UX usability and intuitiveness and propose an IPD. |
| assess-self-documentation | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/self-documentation.md | Assess in-product learn-as-you-go clarity and propose an IPD. |
| assess-documentation | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/documentation.md | Assess repository documentation and propose an IPD. |
| assess-functionality | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/functionality.md | Assess functionality completeness vs. user/stakeholder needs and propose an IPD. |
| assess-use-cases | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/use-cases.md | Assess use-case/scenario coverage and propose an IPD. |
| assess-edge-cases | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/edge-cases.md | Assess edge cases and failure modes and propose an IPD. |
| assess-bugs | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/bugs.md | Assess for bugs/correctness defects and propose an IPD. |
| assess-reliability | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/reliability.md | Assess reliability/resilience/fault-tolerance and propose an IPD. |
| assess-testing | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/testing.md | Assess testing rigor and completeness and propose an IPD. |
| assess-architecture | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/architecture.md | Assess architecture and extensibility and propose an IPD. |
| assess-api-design | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/api-design.md | Assess public API/contract design and propose an IPD. |
| assess-data-modeling | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/data-modeling.md | Assess object and data-modeling quality and propose an IPD. |
| assess-compatibility | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/compatibility.md | Assess compatibility and interoperability and propose an IPD. |
| assess-supply-chain | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/supply-chain.md | Assess dependencies/licensing/supply-chain and propose an IPD. |
| assess-guiding-principles | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/guiding-principles.md | Assess conformance to the project's guiding principles and propose an IPD. |
| assess-compliance | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/compliance.md | Assess compliance against applicable regimes (parameterized) and propose an IPD. |
| assess-memory-resources | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/memory-resources.md | Assess memory/resource/lifetime/concurrency safety and propose an IPD. |
| assess-data-exfiltration | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/data-exfiltration.md | Assess data-exfiltration resistance (egress paths, leakage, DLP-relevant patterns) and propose an IPD. |
| assess-intrusion-detection | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/intrusion-detection.md | Assess intrusion-detection readiness (security signals, audit-trail detectability) and propose an IPD. |
| assess-ransomware-resilience | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/ransomware-resilience.md | Assess ransomware resilience (immutable/tested backups, blast radius, integrity) and propose an IPD. |
| assess-threat-model | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/threat-model.md | Assess overall threat model and defense-in-depth hardening and propose an IPD. |
| assess-logging-audit | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/logging-audit.md | Assess logging and audit-trail quality/integrity/safety and propose an IPD. |
| assess-compliance-readiness | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/compliance-readiness.md | Assess readiness for a formal regime (FIPS / NIST 800-171 / CMMC L2, parameterized) - repo-slice only, not a certification - and propose an IPD. |
| assess-generalization | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/generalization.md | Assess generalization/extensibility/configurability (productization for reuse across orgs/tenants/deployments) and propose an IPD. |
| assess-secrets | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/secrets.md | Scan the working tree and git history for committed secrets/keys/PII/PHI (via tools/scan_secrets.py, read-only, redacted) and propose a rotate-first remediation IPD. |
| assess-prose | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/prose.md | Assess prose quality/style across ALL prose (docs, comments/docstrings, UI strings, error/help/CLI text, commit messages) against the distilled nonfiction style guide - quiet force, no mechanical fingerprints, modifier restraint, no em dashes. IPD by default; supports an optional author-in-the-loop interactive mode. |
| advise | .agents/workflows/advise/advise.md | - | Interrogate and coach: an expert persona examines the current context or a named artifact (spec/plan/design/decision), asks probing questions, surfaces gaps and assumptions, and coaches the author. `/advise <persona> [artifact]` (e.g. `/advise skeptic`, `/advise spec-editor plan.md`); bare `/advise` lists personas and asks. Interactive; edits planning/prose only with per-change consent; never runs code. The `advise-<persona>` rows below are the persona catalog, not separate commands. |
| advise-skeptic | .agents/workflows/advise/advise.md | .agents/workflows/advise/personas/skeptic.md | The "grill me": assume the artifact is flawed; interrogate assumptions, missing cases, and unstated risks. |
| advise-spec-editor | .agents/workflows/advise/advise.md | .agents/workflows/advise/personas/spec-editor.md | Requirements analyst: turn fuzzy intent into testable, unambiguous requirements; hunt ambiguity and missing acceptance criteria. |
| advise-architect | .agents/workflows/advise/advise.md | .agents/workflows/advise/personas/architect.md | Interrogate design trade-offs, coupling, boundaries, and extensibility vs. over-engineering. |
| advise-red-teamer | .agents/workflows/advise/advise.md | .agents/workflows/advise/personas/red-teamer.md | Adversary: interrogate security, abuse, and misuse paths from an attacker's viewpoint. |
| advise-staff-engineer | .agents/workflows/advise/advise.md | .agents/workflows/advise/personas/staff-engineer.md | Mentor: coach toward the simplest maintainable approach (KISS/YAGNI); cut accidental complexity. |
| advise-domain-expert | .agents/workflows/advise/advise.md | .agents/workflows/advise/personas/domain-expert.md | Stakeholder proxy: would a real user/buyer want this; does it serve the actual goal; what is missing. |
| advise-naive-user | .agents/workflows/advise/advise.md | .agents/workflows/advise/personas/naive-user.md | The uninitiated newcomer: surface unclear intent, undefined jargon, and unstated prerequisites. |
<!-- WORKFLOWS-MANIFEST:END -->

## Running a workflow (by tool)

Every workflow is just an instruction file plus (for some tools) a generated slash-
command shim that says "read and execute" it. The **substance works in any agent**; only
the convenience of a native `/command` is tool-specific.

| Tool | How to run a workflow |
|---|---|
| **OpenCode** | Native `/command`: type e.g. `/release-review`, `/assess security`, `/setup-repo`. Shims live in `.opencode/commands/`. The concern is the first argument; add a scope after it, e.g. `/assess performance src/server`. |
| **Claude Code** | Native `/command` via `.claude/commands/` (works; the repo also has these). Type e.g. `/assess security`. Arguments supported (`$ARGUMENTS`). |
| **Cursor, Codex, Antigravity, VS Code Copilot, or any other agent** | **No repo-file slash-command mechanism** - use the universal fallback: tell the agent to *read and execute* the workflow body, e.g. "Read and execute `.agents/workflows/assess/assess.md`, applying the lens `.agents/workflows/assess/lenses/security.md`" (or for a non-lens workflow, just its body path, e.g. "Read and execute `.agents/workflows/setup-repo/setup-repo.md`"). The body paths are listed in the manifest above. |

`AGENTS.md` at the repo root points here, so any tool that reads `AGENTS.md` can discover
the workflow list without being told the paths.

## Meta / authoring workflows (`setup-repo`, `scaffold`)

Two guided, wizard-style workflows differ from the reviewers above: they are
interactive and MAY change files (with per-step confirmation), rather than only
proposing.

- **`/setup-repo`** walks the repo owner through best-practices and security setup -
  installing tools (via `setup-repo/tools/setup_tools.py`, which detects and, on
  confirmation, installs gitleaks/pre-commit/detect-secrets), adding secret-scanning CI
  and a local hook, the **plan/IPD lifecycle** (`.agents/plans/pending/` + `executed/` +
  `superseded/` + `not-executed/` + `reusable/` plus a documented contract in
  `AGENTS.md`/`CONTRIBUTING` so coding agents
  follow it), `.gitignore` hygiene, hygiene files, a stack CI baseline, a pre-commit
  config, dependency hygiene, and branch-protection advice. Ask-before-each-change,
  stages (does not commit). It is **idempotent and drift-aware**: the same command is a
  fresh setup, a quiet re-run, or a post-update **conformance check** that classifies
  each area (conformant/partial/missing/outdated) and only proposes the gaps.
- **`/scaffold`** walks the owner through adding a new `assess-*` lens, standalone
  workflow, or command: generate from the existing pattern, wire the manifest, and
  regenerate shims. Authoring/meta; edits framework files only.

## The `assess-*` family (single-concern, IPD-producing)

The `assess-<concern>` workflows all share one body, the `assess/` harness, focused by
a per-concern **lens** file. Each one assesses a single concern deeply and writes two
durable outputs: a dated Implementation Plan Document (IPD) into the project's
pending-plans directory (default `.agents/plans/pending/`), and a run record (report +
full findings + decisions/evidence) under `workflow-artifacts/assess-<concern>/<RUN_ID>/`
- mirroring release-review's durability. It does NOT change code and does NOT
auto-execute. The intended pipeline is:

```
/assess <concern>  ->  IPD in pending/  ->  plan-review (optional)  ->  human approval  ->  execution
```

Use `release-review` for a broad, all-concerns review that fixes in place; use
`/assess <concern>` when you want a deep, single-concern pass that proposes a plan for
human approval first. The concern is the command's first argument; a bare `/assess`
lists the concerns and asks which to run.

**`assess-all`** is the cross-concern rollup: it runs the family (all, a group, or a
subset - confirming scope and cost first) and synthesizes ONE prioritized, de-duplicated
IPD plus a rollup record, rather than N disconnected IPDs. It orchestrates the existing
lenses (which remain the single source of truth for concerns) and adds the
synthesis/cross-prioritization layer. It is the broad propose-a-plan review, the companion
to `release-review`'s broad fix-in-place review. Its command gets its own shim despite the
`assess-` prefix (a documented exception in the installer).

The family includes engineering, UX, docs, and verification concerns, plus
**cybersecurity** lenses (`data-exfiltration`, `intrusion-detection`,
`ransomware-resilience`, `threat-model`, `logging-audit`) and a
**`compliance-readiness`** lens parameterized by regime (e.g.
`/assess compliance-readiness nist-800-171`).

`assess-generalization` covers **productization**: how ready the project is to be
reused, deployed, administered, and maintained by others across organizations, tenants,
and environments (de-hardcoding org-specific assumptions, configuration architecture,
admin/operability, and abstraction seams). It is the reuse-focused sibling of
`assess-architecture` (which centers on structural soundness), and defers to
`assess-security` for authorization and secrets.

> Honesty note on `assess-compliance-readiness`: regimes like FIPS, NIST 800-171, and
> CMMC L2 are mostly organizational/operational, not code. This workflow assesses only
> the technical slice visible in the repository, explicitly classifies each control as
> repo-verifiable vs. org-level-out-of-scope, and is NOT a certification or a
> substitute for a qualified assessor. It never reports an overall "compliant" verdict.

The **`advise`** family mirrors the assess architecture (one harness + a library of
persona charters) but is a different MODE: where assess/review find faults and report,
`/advise <persona>` is an interactive session in which an expert persona examines an
artifact (spec/plan/design/decision), asks probing questions, and coaches the author.
Personas: `skeptic` (the "grill me"), `spec-editor`, `architect`, `red-teamer`,
`staff-engineer` (mentor), `domain-expert`, `naive-user`. Bare `/advise` lists personas
and asks. It is interactive, edits planning/prose artifacts only with per-change consent,
and never runs code. Add personas with `scaffold`. The `advise-<persona>` manifest rows
are the persona catalog, not separate commands (same collapse as `assess-<concern>`).

The **lifecycle** workflows fill the delivery stages beyond assess/review, spanning
discover -> build -> review -> ship -> operate: **`spec`** (turn a fuzzy request into a
reviewable specification; produces the artifact that `/advise spec-editor` interrogates and
`plan-review` reviews), **`incident`** (a blameless, repo-scoped post-mortem that emits
follow-up action IPDs; the operator holds the real monitoring/on-call data), **`release-notes`**
(decide the version bump from the actual changes and draft the changelog + notes - it
prepares a release but never publishes/tags/pushes; `release-review` Section 9 references
it), and **`migrate`** (assess-and-plan a high-risk migration as a staged, reversible plan
with characterization tests and per-stage rollback/verify, emitted as an IPD). They are
distinct ACTIVITIES, so each is its own workflow rather than a concern or persona.

**`getting-started`** is the newcomer's entry point: a guided in-agent tour that detects
repo/toolkit context, explains the mental model briefly, asks the user's goal, and routes
to the right workflow (offering to run it, with consent) with the exact invocation for
their tool. It ORIENTS and ROUTES - read-only by default - and references `/list-workflows`
for the full catalog rather than duplicating it or the README.

## Notes

- `release-review-plan` shares the `release-review` body; it runs that runbook in
  planning-only mode (see the runbook's planning-only instructions).
- `release-review/` contains the shared policy (`fix-decision-policy.md`,
  `00-run-protocol.md`) that `plan-review` and the `assess` harness reference as a
  sibling (`../release-review/...`).
- The installer copies these workflows into a target repository, generates the
  per-tool command shims from this manifest (passing the `lens` to shared-body
  commands), and adds a one-line pointer to `AGENTS.md`. See
  `install-workflows.py`.
- **Parameterized command surface (assess and advise):** the single `assess` and `advise`
  rows each generate one parameterized command (`/assess <concern>`, `/advise <persona>`).
  The `assess-<concern>` and `advise-<persona>` rows are the **catalog** (the source of
  truth for each concern's lens / each persona's charter); the installer does NOT generate
  a shim per catalog row (`is_concern_catalog_row` / `CATALOG_ROW_PREFIXES` in
  `install-workflows.py`). Re-running the installer on an older install prunes retired
  per-item shims automatically. The run-record directory conventions remain
  `workflow-artifacts/assess-<concern>/<RUN_ID>/` and
  `workflow-artifacts/advise-<persona>/<RUN_ID>/`.
