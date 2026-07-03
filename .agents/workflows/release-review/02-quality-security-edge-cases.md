# 02 Quality, Security, and Edge Cases

## Context contract

- **Read:** `00-run-protocol.md`, `fix-decision-policy.md`, this file, `01-repository-inventory.md`, the registers. `reference.md` on demand. Lead personas: QA/QC, software engineer, security-minded architect.
- **Produce:** findings (with Remediation Risk) incl. `MEM`/`LIVE`; updates to registers, `05`/`06`/`08`, `deprecation-candidates.md`, `persona-review.md`, `todo-reconciliation.md`; per-phase report `section-summaries/02-quality-security-edge-cases.md`.
- **Done when:** the Exit gate at the bottom of this file is satisfied.

## Purpose

Review the current project for bugs, correctness issues, security concerns, privacy risks, edge cases, reliability risks, maintainability risks, and resource handling problems.

This section is an audit pass. Do not implement fixes yet unless needed to prevent immediate harm to the repository. Implementation happens in Section 7.

## Standing constraints for this section

- Preserve public behavior unless a change is clearly justified.
- Do not make speculative changes.
- Do not create broad refactors or formatting churn.
- Use run-specific unique IDs for every finding and action.
- Update the finding and action registers before leaving this section.
- Use TodoWrite if available, but treat `workflow-artifacts/release-review/<RUN_ID>/` as authoritative.
- Mark non-applicable checks explicitly rather than forcing findings.
- Prefer meaningful fixes, not checklist compliance.


## Required inputs

Read the repository inventory, execution plan, registers, source files, tests, configs, build files, dependency files, and docs relevant to correctness and security.

## Allowed actions

Allowed: inspect code and configuration, run non-destructive tests/builds/static checks if available and safe, record findings and candidate actions, update TodoWrite and run artifacts.

Not allowed: product code fixes, dependency changes, security tool installation, destructive cleanup, or public contract changes.

## Review checks

Review for bugs, correctness issues, security issues, privacy risks, unsafe file/path handling, unsafe serialization/deserialization, unsafe subprocess/shell/network behavior, authentication/authorization gaps, secret management issues, dependency/supply-chain concerns, input validation gaps, edge cases, error handling, recovery gaps, resource leaks, concurrency/state/caching/race/idempotency risks, performance improvements that preserve behavior, observability gaps, missing tests for important behavior, and code paths that appear obsolete, unreachable, or superseded.

Conduct this review with the lead personas for this section (QA/QC engineer, software engineer, and the security-minded architect lens; see the persona-to-section map in `00-run-protocol.md`), letting the other personas surface risk the leads miss. Forcing function: append at least one concrete observation per lead persona to `persona-review.md`, or explicitly note "no new finding from persona X in this section".

## Memory, resource, and lifetime review (mandatory; type `MEM`)

Per the shared memory/resource rule in `00-run-protocol.md`, hunt deliberately for:

- Leaks and unbounded growth: caches/maps/lists/queues/log or history buffers that never evict or cap; accumulation across a long-running process or loop.
- Unclosed or unreleased resources: files, sockets, handles, DB connections/cursors, locks, temp files, subprocesses - including on error/exception paths.
- Lifetime hazards: use-after-free/close, double-free/close, dangling references, retaining large buffers longer than needed, holding references that defeat GC.
- Concurrency/state hazards: races, missing synchronization, TOCTOU, non-idempotent retries, shared mutable state without protection.

Apply this to whatever the language exposes (manual memory, GC retention, RAII/ownership, context managers, `defer`/`finally`, connection pools). A confirmed leak or unbounded-growth path affecting long-running or production use is at least Medium, and High if it can exhaust memory/handles or destabilize a live system.

## Live-interaction-surface review (mandatory; do not skip because hermetic tests pass)

Per the shared live-interaction-surface rule in `00-run-protocol.md`: many incidents come from surfaces unit tests do not exercise. Green tests are NOT evidence these are correct. For surfaces that apply to this repository, trace the actual runtime behavior by reading the code paths:

- **Resume / skip / idempotency:** what exactly marks work "already done"? Does the skip key match every way the artifact can have been written? Can a re-run silently re-do and overwrite completed, paid-for, or human-verified output?
- **Multi-process / multi-run coordination:** start guards, pidfiles, stop/signal targeting, shared status/ledger writers. With two runs live at once, does each control/observe the right process?
- **Work selection / limits / pagination:** does selection advance through the backlog, or can it re-select the same already-complete items?
- **Spend / cap / budget accounting:** can a run spend real money or quota on work it should have skipped? Are caps cumulative vs per-run as documented?
- **Fetch / external-IO completeness:** does the fetch actually retrieve the relied-on content, and can an incomplete fetch drive a negative/exclusionary decision?
- **Input truncation/sampling reaching a model, a stored artifact, or an automated decision** without being recorded.

A defect found here is a correctness/data-integrity finding (`B`/`LIVE`), not a maintainability nicety, regardless of how hard it is to unit-test.

## Finding requirements

For each issue, record ID, title, severity, affected area, evidence, explanation, impact, recommended fix, release-safety classification, public behavior change risk, and required artifact updates.

Use `B` for bugs, `S` for security/privacy, `E` for edge/error/resource issues, `MEM` for memory/resource/lifetime/concurrency issues, `M` for maintainability, `GP` for guiding-principles violations, `TODO` for relevant backlog/`FIXME` items found in code, and `DEP` for deprecation candidates.

**Severity floor for live-interaction-surface defects.** A finding from the live-interaction-surface review that can (a) overwrite or destroy completed/verified/paid-for output or user data, (b) spend real money/quota on skippable work, (c) make an automated decision on incompletely-retrieved or truncated input, (d) signal/stop/coordinate the wrong process, or (e) prevent forward progress through a backlog, is at least **High** severity and is tagged `LIVE` in the finding title. Difficulty of automated testing does NOT lower its severity.

**Remediation Risk for every finding (Fix Bar input).** For each finding, record its Remediation Risk (Low / Medium / Medium-High / High) per the Fix Bar in `00-run-protocol.md`: the risk that the fix itself would harm complexity, usability, security, or functionality. Effort/time/cost are explicitly excluded. Under the Fix Bar, Section 7 fixes everything by default and defers only when Remediation Risk is Medium-High or higher, so Medium/Low live-surface and memory findings are fixed in-run by default. Make the basis of the Remediation-Risk rating explicit rather than asserting "low".

## In-code TODO/FIXME triage

While reading code, record `TODO`/`FIXME`/`HACK`/`XXX` markers that indicate a known defect, security gap, or unfinished critical path. File them as `TODO`-type findings (cross-referencing `B`/`S`/`MEM` as appropriate) and add them to `todo-reconciliation.md`.

## Required outputs

Update `03-findings-register.csv`, `04-action-register.csv`, `05-decisions.md`, `06-commands.md`, `08-checkpoints.md`, `deprecation-candidates.md`, `persona-review.md`, and `todo-reconciliation.md` (for any in-code TODO/FIXME items found).

Create the per-phase report `section-summaries/02-quality-security-edge-cases.md` (what was done, why, what was considered but not done) covering highest-priority fixes, security concerns, memory/resource and live-interaction-surface findings, edge cases needing tests, reliability/maintainability concerns, deprecated or obsolete candidates, and recommended next actions, all using IDs.

## TodoWrite guidance

If TodoWrite is available, mark Section 2 in progress, track major audit categories only, and mark complete after findings, actions, and checkpoints are updated.

## Judgment guidance

Favor evidence-based findings. If suspicious but unconfirmed, record uncertainty instead of overstating it. Do not recommend broad rewrites when a narrow fix would address the risk.

## Non-applicable guidance

If the repository has no server code, authentication, network behavior, file handling, or serialization, mark those checks not applicable where appropriate.

## Exit gate

Do not proceed to Section 3 until all are true (MUST):

- [ ] Quality/security/privacy/edge/reliability findings recorded with severity AND Remediation Risk.
- [ ] `MEM` and `LIVE` surfaces traced by reading code (not inferred from tests) or marked not applicable; any data-integrity `LIVE`/High finding tagged.
- [ ] Security-sensitive findings recorded without exposing secrets.
- [ ] In-code TODO/FIXME items triaged into `todo-reconciliation.md`.
- [ ] One observation per lead persona appended to `persona-review.md` (or "no new finding from persona X").
- [ ] Deprecation candidates updated if relevant.
- [ ] Per-phase report written; checkpoint recorded in `08-checkpoints.md` and committed.
