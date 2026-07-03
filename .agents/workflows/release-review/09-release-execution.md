# 09 Release Execution (Post-Go)

## Context contract

- **Read:** `00-run-protocol.md`, this file, `08-final-ship-review.md` result, `11-push-plan.md`. Derive concrete commands from the repo (README/CONTRIBUTING/release docs, manifests, CI).
- **Preconditions (MUST):** GO/CONDITIONAL GO from Section 8, explicit user approval to release, all CONDITIONAL prerequisites met, no unaddressed `LIVE`/High finding, working tree contains only intended release changes.
- **Produce:** `release-execution-log.md` and per-phase report `section-summaries/09-release-execution.md`.
- **Done when:** the Exit criteria at the bottom of this file are satisfied.

## Purpose

Execute the actual release - pushing, CI verification, version tagging, building release artifacts, publishing, and/or deploying - **only after** Section 8 produced a GO or CONDITIONAL GO and the user has **explicitly approved** performing the release.

This section is project-agnostic. It defines the universal release-execution discipline and tells you how to derive the concrete commands from the repository itself, rather than hardcoding any one project's toolchain. Adapt every step to the project type discovered in Section 1 (library, CLI, web app, static site, service, container image, dataset, docs site, etc.).

---

## Hard preconditions (do not start otherwise)

1. Section 8 recommendation is GO or CONDITIONAL GO.
2. The user has explicitly approved release execution **in this conversation**.
3. For CONDITIONAL GO: every stated prerequisite/blocker is resolved, or the user has explicitly waived it in writing.
4. No unaddressed `LIVE`/High data-integrity finding remains (the Section 8 live-surface gate is satisfied).
5. The working tree contains only intended release changes; unrelated pre-existing user changes are not bundled in.

If any precondition fails, stop and report. Do not push, tag, publish, or deploy.

---

## Standing constraints for this section

- You MUST NOT skip a required step, and you MUST record each step and its result in `06-commands.md` and a new `release-execution-log.md`.
- You MUST wait for and inspect remote CI output before producing or publishing final artifacts, when CI exists.
- You MUST verify that built artifacts correspond to the exact release commit (e.g., embedded commit hash/version), when the toolchain supports it.
- You MUST create release tags as annotated (and signed, if the project signs tags) tags, never lightweight tags.
- You MUST NOT publish to a package registry, deploy to a server, or change externally-visible state using credentials the user has not explicitly authorized for this release. Hand off any step requiring unavailable credentials or interactive server access to the user.
- You MUST perform a post-release verification ("smoke test") appropriate to the project type and report the result.

---

## Step-by-step release execution

Derive the concrete commands for each step from the repository: `README`/`CONTRIBUTING`/release docs, package/build manifests, `Makefile`/task runner, CI workflows, and any `RELEASING.md`. Prefer repository-native, already-documented commands over invented ones.

### 1. Finalize, version, and commit

- Confirm version metadata is bumped consistently (package manifest, `__version__`, `CHANGELOG.md`, docs) per the project's convention.
- Confirm `CHANGELOG.md`/release notes describe this release accurately, including any breaking changes flagged in Sections 6 and 8.
- Confirm the working tree is clean except for intended release changes; commit them as a coherent release commit referencing the relevant action IDs.

### 2. Push the release commit

- Push the release branch to its remote (e.g., `git push origin <branch>`), using the branch the project actually releases from.
- If the project uses submodules or nested repositories, push those to their own remotes **first**, then the parent, and verify the parent records the intended submodule commits.

### 3. Verify remote CI

- If CI exists, wait for and inspect the CI result for the pushed commit (e.g., `gh run list`/`gh run watch`, or the project's CI UI).
- Do NOT proceed to building or publishing artifacts until CI is green for the release commit. If CI fails, fix, recommit, repush, and restart this step.
- If no CI exists, run the project's full local validation suite on the release commit instead and record the result.

### 4. Build release artifacts

- Build the artifacts the project actually ships (e.g., wheels/sdists, compiled binaries, container images, a frontend production bundle, a static site, a tarball). Use the project's documented build command.
- Verify the artifacts exist, are non-empty, and match the release version/commit. Where supported, verify the embedded commit hash/version equals the release commit.

### 5. Tag the release

- If a stale/lightweight tag for this version exists locally, delete it first.
- Create an annotated tag matching the version (signed if the project signs tags): `git tag -a <vX.Y.Z> -m "Release <vX.Y.Z>"`.
- Push the tag to the remote and confirm it appears there.

### 6. Publish / deploy (only with explicit, authorized credentials)

- Publish to the package registry or deploy to the target environment **only** if the user has explicitly authorized it and the necessary credentials are available to this run.
- For registry publishing, prefer a dry run/validation first when the tooling supports it, then publish.
- For server/cloud deployment, follow the project's deployment procedure; verify the deployed revision matches the release commit/tag.
- If credentials are missing, interactive login is required, or the procedure prompts for environment-specific configuration, **hand off** to the user with exact, copy-pasteable steps. Do not guess credentials or endpoints.

### 7. Post-release verification (smoke test)

Perform verification appropriate to the project type and record results:

- **Library/package:** install the published artifact into a clean environment and import/invoke its public entry points.
- **CLI:** run `--version`/`--help` and one representative command.
- **Web app / site / service:** load the live URL(s) over HTTPS, confirm no server errors, key pages/endpoints respond, and any analytics/health checks behave as expected.
- **Container image:** pull the published tag and run a minimal smoke command.

If verification fails, treat it as a release incident: stop, report, and recommend rollback if the project supports it.

### 8. Record and report

- Update `release-execution-log.md` with each step, command, result, the release commit, the tag, published/deployed targets, and verification outcome.
- Create the per-phase report `section-summaries/09-release-execution.md` (what was done, why, what was considered but not done - including any step handed off to the user and why).

---

## Safety rules

Do not delete remote branches/tags or force-push over published history. Do not rotate or expose credentials. Do not deploy to production without explicit authorization. If anything is ambiguous or risky, stop and hand off to the user with precise instructions.

---

## Exit criteria

Release execution is complete only when:

1. The release commit is pushed and CI (if any) is green for it, or full local validation passed.
2. Release artifacts are built and verified against the release commit/version.
3. The annotated (signed if applicable) release tag is pushed and confirmed on the remote.
4. Publishing/deployment is either completed with authorized credentials and verified, or explicitly handed off to the user.
5. The post-release smoke test passed, or its failure is reported with a rollback recommendation.
6. `release-execution-log.md` and the Section 9 per-phase report are written.
