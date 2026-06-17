# 02 Quality, Security, and Edge Cases

## Purpose

Review the current project for bugs, correctness issues, security concerns, privacy risks, edge cases, reliability risks, maintainability risks, and resource handling problems.

This section is an audit pass. Do not implement fixes yet unless needed to prevent immediate harm to the repository. Implementation happens in Section 7.

## Standing constraints for this section

- Preserve public behavior unless a change is clearly justified.
- Do not make speculative changes.
- Do not create broad refactors or formatting churn.
- Use run-specific unique IDs for every finding and action.
- Update the finding and action registers before leaving this section.
- Use TodoWrite if available, but treat `repository-review/<RUN_ID>/` as authoritative.
- Mark non-applicable checks explicitly rather than forcing findings.
- Prefer meaningful fixes, not checklist compliance.


## Required inputs

Read the repository inventory, execution plan, registers, source files, tests, configs, build files, dependency files, and docs relevant to correctness and security.

## Allowed actions

Allowed: inspect code and configuration, run non-destructive tests/builds/static checks if available and safe, record findings and candidate actions, update TodoWrite and run artifacts.

Not allowed: product code fixes, dependency changes, security tool installation, destructive cleanup, or public contract changes.

## Review checks

Review for bugs, correctness issues, security issues, privacy risks, unsafe file/path handling, unsafe serialization/deserialization, unsafe subprocess/shell/network behavior, authentication/authorization gaps, secret management issues, dependency/supply-chain concerns, input validation gaps, edge cases, error handling, recovery gaps, resource leaks, concurrency/state/caching/race/idempotency risks, performance improvements that preserve behavior, observability gaps, missing tests for important behavior, and code paths that appear obsolete, unreachable, or superseded.

## Finding requirements

For each issue, record ID, title, severity, affected area, evidence, explanation, impact, recommended fix, release-safety classification, public behavior change risk, and required artifact updates.

Use `B` for bugs, `S` for security/privacy, `E` for edge/error/resource issues, `M` for maintainability, and `DEP` for deprecation candidates.

## Required outputs

Update `03-findings-register.csv`, `04-action-register.csv`, `05-decisions.md`, `06-commands.md`, `08-checkpoints.md`, and `deprecation-candidates.md`.

Create or append a Section 2 summary covering highest-priority fixes, security concerns, edge cases needing tests, reliability/maintainability concerns, deprecated or obsolete candidates, and recommended next actions, all using IDs.

## TodoWrite guidance

If TodoWrite is available, mark Section 2 in progress, track major audit categories only, and mark complete after findings, actions, and checkpoints are updated.

## Judgment guidance

Favor evidence-based findings. If suspicious but unconfirmed, record uncertainty instead of overstating it. Do not recommend broad rewrites when a narrow fix would address the risk.

## Non-applicable guidance

If the repository has no server code, authentication, network behavior, file handling, or serialization, mark those checks not applicable where appropriate.

## Exit criteria

Before moving to Section 3, quality/security/privacy/edge/reliability findings are recorded, security-sensitive findings avoid exposing secrets, candidate actions are recorded, deprecation candidates are updated if relevant, and the checkpoint is recorded.
