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

- Confirm version metadata is bumped consistently (package manifest, `__version__`, `CHANGELOG.md`, docs) per the project's convention. The `release-notes` workflow prepares this step (version bump + changelog/notes drafting); use it here if the notes and bump are not already done, then continue with execution.
- **Re-bake any DERIVED version artifact from the INTENDED release version, and commit it BEFORE tagging (bake-then-tag).** If the project bakes a version into a tracked file that is copied into consumers (for this framework, `.agents/workflows/VERSION`, which the installer stamps into every target), regenerate it to the exact intended `vX.Y.Z` and include it in the release commit, so the tag's tree contains a version equal to its own tag. For this framework: `make version-file VERSION=<X.Y.Z>` (the explicit-version mode), then commit, then tag that commit. Do NOT tag first and re-bake after: that leaves the tag's tree carrying the PREVIOUS release's baked version, so a checkout of the tag (or an install from it) stamps a stale number. (This is the fix for the stale-VERSION install bug; the wheel version is resolver-computed and was unaffected, but the baked file the installer copies must match the tag.)
- Confirm `CHANGELOG.md`/release notes describe this release accurately, including any breaking changes flagged in Sections 6 and 8.
- Confirm the working tree is clean except for intended release changes; commit them as a coherent release commit referencing the relevant action IDs.

### 2. Push the release commit

- Push the release branch to its remote, using the exact remote + branch + ref recorded in
  `11-push-plan.md` (that artifact is the confirmed push target). If there are multiple remotes or
  any ambiguity (e.g. `origin` vs `upstream`, a fork), STOP and require an explicit human choice;
  never guess a default remote.
- CONDITIONAL GO: do not push on a bare conditional. The named conditions must be met and the human
  must re-approve with an explicit GO first; then push.
- If the project uses submodules or nested repositories, push those to their own remotes **first**, then the parent, and verify the parent records the intended submodule commits.

### 3. Push-then-verify remote CI

After pushing, actively VERIFY CI rather than only recommending it:

- If the remote is GitHub and `gh` is available and authenticated: identify the run(s) triggered by
  the pushed commit (`gh run list`), then poll to completion with a BOUNDED timeout (default ~10-15
  minutes; state the timeout used) - report progress while waiting. Cross-OS/matrix runs can take
  minutes; never hang indefinitely.
  - **Green:** report success and proceed.
  - **Red:** report the AGGREGATE pass/fail AND name EVERY failing workflow/job/step (matrix
    failures are often OS-specific; give the full picture, not just the first). Then fix, recommit,
    repush, and restart this step. Do NOT proceed to building/publishing until green.
  - **Timeout exceeded:** report the `gh run` URL/ID and the last known status, and stop waiting
    (hand the watch back to the user); do not proceed to publish on an unverified run.
- **`gh` graceful degradation:** if `gh` is unavailable/unauthenticated or the remote is not GitHub,
  say so plainly, provide the manual check command / CI URL, and do NOT block or fail the release on
  the tool's absence. When no CI exists at all, run the project's full local validation suite on the
  release commit instead and record the result.
- Record the push+verify outcome (ref pushed, run URL/ID, result) in `ci-assessment.md` and
  `11-push-plan.md`, and surface it in the report's "CI assessment summary" section.

This push-then-verify runs only in the serial Section 9 phase (post-approval); it MUST NOT run inside
a parallel audit lane (lanes must not push), consistent with `00-run-protocol.md`.

### 4. Build release artifacts

- Build the artifacts the project actually ships (e.g., wheels/sdists, compiled binaries, container images, a frontend production bundle, a static site, a tarball). Use the project's documented build command.
- Verify the artifacts exist, are non-empty, and match the release version/commit. Where supported, verify the embedded commit hash/version equals the release commit.

### 5. Tag the release (each externally-visible action is a separate, default-NO confirmation)

You entered Section 9 via a rung chosen in Section 8: **B (release candidate)** or **C (full release)**. Never bundle the actions below under one "yes"; confirm each one explicitly, defaulting to NO, naming its exact consequence. A bare `vX.Y.Z` tag means "intended for a registry release"; a candidate MUST be `vX.Y.Z-rc.N` (a pre-release the resolver emits as PEP 440 `X.Y.ZrcN`, which pip does not install without `--pre`). Tags are ALWAYS annotated (signed if the project signs tags), never lightweight.

- **Tag?** "Create annotated tag `<vX.Y.Z-rc.N>` (rung B) or `<vX.Y.Z>` (rung C)?" If a stale/lightweight tag for this exact version exists locally, delete that local tag first. Then `git tag -a <ref> -m "Release <ref>"`.
- **Push the tag/commit?** Separate confirmation, default NO, even for a candidate: "Push `<ref>` to `<remote>`?" Preserve the multi-remote STOP rule above (never guess a remote). A candidate that is only tagged locally is fully reversible; pushing it is not.
- **GitHub Release?** (rung C only) "Create a PUBLISHED, latest GitHub Release for `<tag>`, visible to everyone?" This is its own separate, default-NO confirmation naming that exact consequence. When the human CONFIRMS it, the release ends PUBLISHED and marked Latest, not a draft, because rung C means fully released: `gh release create <tag> --latest --notes-file <notes>` (no `--draft`). If notes or assets must be staged first, the equivalent two-step is `gh release create <tag> --draft ...` then `gh release edit <tag> --draft=false --latest`. Declining this confirmation (or not reaching it) leaves NO GitHub Release at all, never a dangling, invisible draft. Do not run any `gh release` command without this explicit confirmation. If `gh` is unavailable/unauthenticated, say so and hand off the exact command rather than leaving a draft. (Rung B, if it creates a GitHub Release at all, uses `--prerelease` and never `--latest`.)

Rung B stops here (candidate: tag, optionally pushed; no published GitHub Release - a clearly-marked `--prerelease` only if any; no publish). Rung C continues to publish/deploy below.

### 6. Publish / deploy (rung C only; only with explicit, authorized credentials)

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

### 8. Verify the end state, then record and report

First VERIFY the actual release end state (do not assume a step took effect just because its command was issued):

- **Tag on the remote:** confirm the tag is pushed and present on the remote (`git ls-remote --tags <remote> <ref>`), matching Step 2/5.
- **GitHub Release published + Latest (rung C):** confirm the release exists and is NOT a draft with `gh release view <tag> --json isDraft,isPrerelease` and assert `isDraft=false` (and, for a full release, `isPrerelease=false`). Note: `gh release view --json` has NO `isLatest` field ("Latest" is GitHub-derived); verify Latest by having created/edited with `--latest`, and/or by checking `gh release list`, which flags the Latest release in its output. If `gh` is unavailable/unauthenticated, say so and give the manual check instead of blocking.
- **Registry has the version (when checkable):** if the toolchain can check (e.g. query the package index for `<name>==<version>`), confirm the published version is present; otherwise report it as unverified with the manual check command.

Then, if ANY externally-visible step is incomplete - an unpublished draft, an un-uploaded registry artifact, a tag not on the remote, or a step genuinely handed off because credentials were absent or interactive login was required - surface it in a loud, explicit block, never a silent completion:

```
REMAINING MANUAL STEPS (release NOT fully live):
- <exact copy-pasteable command #1, e.g. gh release edit <tag> --draft=false --latest>
- <exact copy-pasteable command #2, e.g. the registry publish/upload command>
```

If every checked action is confirmed complete, state that explicitly ("no remaining manual steps; release is fully live").

- Update `release-execution-log.md` with each step, command, result, the release commit, the tag, published/deployed targets, the end-state verification, and any REMAINING MANUAL STEPS block.
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
4. On rung C, the GitHub Release (when the human confirmed that step) is verified PUBLISHED (not a draft) and marked Latest - or, if it could not be published in this run (e.g. `gh` unavailable, missing auth), it is surfaced in the REMAINING MANUAL STEPS block with the exact command. A rung-C run MUST NOT complete leaving a silent, unpublished draft.
5. Publishing/deployment is either completed with authorized credentials and verified, or explicitly handed off to the user in the REMAINING MANUAL STEPS block. Where checkable, the registry is verified to have the version; otherwise it is reported as unverified with the manual check.
6. The post-release smoke test passed, or its failure is reported with a rollback recommendation.
7. The end-state verification ran and either confirmed the release is fully live (no remaining manual steps) or printed the REMAINING MANUAL STEPS block.
8. `release-execution-log.md` and the Section 9 per-phase report are written.
