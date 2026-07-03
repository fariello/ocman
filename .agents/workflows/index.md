# Agent Workflows

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
| plan-review | .agents/workflows/plan-review/plan-review.md | - | Pre-execution plan reviewer: review and improve a proposed implementation plan before any code is written (edits planning documents only). |
| assess-performance | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/performance.md | Assess runtime/resource performance and propose an IPD. |
| assess-security | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/security.md | Assess security posture and propose an IPD. |
| assess-privacy | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/privacy.md | Assess privacy/data-protection handling and propose an IPD. |
| assess-accessibility | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/accessibility.md | Assess accessibility (WCAG 2.1 AA) and propose an IPD. |
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
<!-- WORKFLOWS-MANIFEST:END -->

## Running a workflow

- **OpenCode / Claude Code (native):** type the slash command, e.g.
  `/release-review`, `/plan-review`, or any `/assess-<concern>`. Pass an optional
  target scope or flags as arguments, e.g. `/assess-performance src/server` or
  `/assess-compliance gdpr`.
- **Any other agent (universal fallback):** tell it to "read and execute" the body
  path, e.g. "Read and execute .agents/workflows/assess/assess.md, applying the lens
  .agents/workflows/assess/lenses/security.md".

## The `assess-*` family (single-concern, IPD-producing)

The `assess-<concern>` workflows all share one body, the `assess/` harness, focused by
a per-concern **lens** file. Each one assesses a single concern deeply and writes two
durable outputs: a dated Implementation Plan Document (IPD) into the project's
pending-plans directory (default `.agents/plans/pending/`), and a run record (report +
full findings + decisions/evidence) under `workflow-artifacts/assess-<concern>/<RUN_ID>/`
- mirroring release-review's durability. It does NOT change code and does NOT
auto-execute. The intended pipeline is:

```
assess-<concern>  ->  IPD in pending/  ->  plan-review (optional)  ->  human approval  ->  execution
```

Use `release-review` for a broad, all-concerns review that fixes in place; use an
`assess-<concern>` when you want a deep, single-concern pass that proposes a plan for
human approval first.

The family includes engineering, UX, docs, and verification concerns, plus
**cybersecurity** lenses (`assess-data-exfiltration`, `assess-intrusion-detection`,
`assess-ransomware-resilience`, `assess-threat-model`, `assess-logging-audit`) and a
**`assess-compliance-readiness`** lens parameterized by regime (e.g.
`/assess-compliance-readiness nist-800-171`).

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
